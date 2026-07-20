"""End-to-end checks for the lecture 34 adversarial review lab."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab = load_module(HERE / "adversarial_review_lab.py", "review_lab")
review = sys.modules["review_pattern"]

GROSS = 13_744_541.0
NET = 13_706_097.0


def test_reversed_lines_are_blocked_then_the_loop_converges() -> None:
    con = lab.month_end()
    draft = lab.draft_from_obligation(con)
    result = lab.run_reviewed(
        draft,
        lab.full_panel(con),
        lab.full_policy(),
        reviser=lab.reviser(),
    )

    assert draft.declared_total == GROSS
    assert result.outcome is review.Outcome.CONFIRMED
    assert result.acceptance_receipt.accepted
    assert [len(item.receipt.blockers) for item in result.rounds] == [3, 0]
    employee_ids = [line.emp_id for line in result.artifact.payload.lines]
    assert "E0007" not in employee_ids
    assert "E0012" not in employee_ids
    assert result.artifact.payload.declared_total == NET


def test_review_receipt_binds_artifact_fingerprint_and_rubric() -> None:
    con = lab.month_end()
    result = lab.run_reviewed(
        lab.draft_from_obligation(con),
        lab.full_panel(con),
        lab.full_policy(),
        reviser=lab.reviser(),
    )
    receipt = result.latest_review

    assert receipt.artifact_id == result.artifact.artifact_id
    assert receipt.artifact_fingerprint == lab.payrun_fingerprint(
        result.artifact.payload
    )
    assert receipt.rubric_version == "payroll-release-v1"
    assert receipt.checked_rule_ids == tuple(sorted(lab.REQUIRED_RULES))
    assert result.acceptance_receipt.artifact_id == result.artifact.artifact_id


def test_machine_readable_objections_drive_the_reviser() -> None:
    con = lab.month_end()
    result = lab.run_reviewed(
        lab.draft_from_obligation(con),
        lab.full_panel(con),
        lab.full_policy(),
        reviser=lab.reviser(),
    )
    first = result.rounds[0].receipt

    assert {item.code for item in first.blockers} == {
        "bank_total_mismatch",
        "reversed_in_run",
    }
    assert all(item.evidence_refs for item in first.objections)
    assert all(item.reviewer_id for item in first.objections)


def test_reviewer_reviser_actor_collision_is_refused_before_review() -> None:
    con = lab.month_end()
    status = lab.make_reviewers(con)[0]
    self_panel = lab.ReviewPanel(
        "self-review-panel",
        (
            lab.ReviewerSpec(
                reviewer_id=status.reviewer_id,
                actor_id=lab.REVISER,
                rule_ids=status.rule_ids,
                evidence_scope=status.evidence_scope,
                review=status.review,
            ),
        ),
    )
    result = lab.run_reviewed(
        lab.draft_from_obligation(con),
        self_panel,
        lab.status_only_policy(),
        reviser=lab.reviser(),
    )

    assert result.outcome is review.Outcome.NO_REVIEWER
    assert {
        finding.code for finding in result.run_findings
    } == {"reviser_is_reviewer"}
    assert result.rounds == ()


def test_narrow_rubric_can_confirm_a_double_pay() -> None:
    con = lab.month_end()
    status = lab.make_reviewers(con)[0]
    result = lab.run_reviewed(
        lab.draft_with_duplicate(con),
        lab.ReviewPanel("status-only-panel", (status,)),
        lab.status_only_policy(),
        reviser=None,
    )

    assert result.outcome is review.Outcome.CONFIRMED
    assert result.acceptance_receipt.accepted
    duplicates = [
        line
        for line in result.artifact.payload.lines
        if line.emp_id == "E0100"
    ]
    assert len(duplicates) == 2


def test_release_rubric_holds_the_same_lone_reviewer_for_missing_rules() -> None:
    con = lab.month_end()
    status = lab.make_reviewers(con)[0]
    result = lab.run_reviewed(
        lab.draft_with_duplicate(con),
        lab.ReviewPanel("status-only-panel", (status,)),
        lab.full_policy(),
        reviser=None,
    )

    assert result.outcome is review.Outcome.HELD_FOR_HUMAN
    assert result.latest_review.missing_rule_ids == (
        "duplicate-line",
        "total-reconciliation",
    )
    assert not result.acceptance_receipt.accepted


def test_full_panel_catches_the_duplicate_and_reconciles() -> None:
    con = lab.month_end()
    result = lab.run_reviewed(
        lab.draft_with_duplicate(con),
        lab.full_panel(con),
        lab.full_policy(),
        reviser=lab.reviser(),
    )

    assert result.outcome is review.Outcome.CONFIRMED
    employee_ids = [line.emp_id for line in result.artifact.payload.lines]
    assert employee_ids.count("E0100") == 1
    assert result.artifact.payload.declared_total == NET


def test_blockers_without_a_reviser_are_held_on_the_reviewed_version() -> None:
    con = lab.month_end()
    result = lab.run_reviewed(
        lab.draft_from_obligation(con),
        lab.full_panel(con),
        lab.full_policy(),
        reviser=None,
    )

    assert result.outcome is review.Outcome.HELD_FOR_HUMAN
    assert result.artifact.artifact_id == result.latest_review.artifact_id
    assert result.artifact_revision == result.latest_review.artifact_revision


def test_accepted_shared_receipt_never_carries_a_blocker() -> None:
    con = lab.month_end()
    result = lab.run_reviewed(
        lab.draft_from_obligation(con),
        lab.full_panel(con),
        lab.full_policy(),
        reviser=lab.reviser(),
    )

    assert result.acceptance_receipt.accepted
    assert all(
        finding.severity is not review.Severity.BLOCKER
        for finding in result.acceptance_receipt.findings
    )
