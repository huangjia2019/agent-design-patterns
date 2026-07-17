"""Invariants for the contract-bound Adversarial Review pattern."""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass, replace

import pytest


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    AcceptanceDecision,
    AdversarialReview,
    ArtifactEnvelope,
    Objection,
    Outcome,
    ReviewGate,
    ReviewPanel,
    ReviewPolicy,
    ReviewerSpec,
    ReviserSpec,
    Severity,
    TaskContract,
)


@dataclass(frozen=True)
class Candidate:
    amount: float
    note: str = ""


def contract() -> TaskContract:
    return TaskContract(
        contract_id="release-candidate",
        version=1,
        objective="release a reviewed candidate",
        output_schema="Candidate",
        accountable_owner="controller",
        boundary="reviewers may object; only the gate may release",
    )


def fingerprint(candidate: Candidate) -> str:
    return f"{candidate.amount:.2f}|{candidate.note}"


def artifact(
    candidate: Candidate,
    *,
    artifact_id: str = "candidate-r0",
    producer: str = "author",
) -> ArtifactEnvelope[Candidate]:
    return ArtifactEnvelope(
        artifact_id=artifact_id,
        contract_digest=contract().digest,
        schema=contract().output_schema,
        produced_by=producer,
        payload=candidate,
        evidence_refs=("ledger://candidate",),
    )


def objection(
    *,
    severity: Severity = Severity.BLOCKER,
    rule_id: str = "amount-limit",
) -> Objection:
    return Objection(
        code="amount_over_limit",
        rule_id=rule_id,
        severity=severity,
        field="amount",
        claim="amount exceeds 100",
        evidence_refs=("policy://amount-limit/v1",),
    )


def reviewer(
    *,
    actor_id: str = "reviewer",
    rule_ids: tuple[str, ...] = ("amount-limit",),
    result: tuple[Objection, ...] = (),
    reviewer_id: str = "amount-reviewer",
) -> ReviewerSpec[Candidate]:
    async def review(request):
        return result

    return ReviewerSpec(
        reviewer_id=reviewer_id,
        actor_id=actor_id,
        rule_ids=rule_ids,
        evidence_scope=("policy://amount-limit/v1",),
        review=review,
    )


def policy(
    *,
    required: tuple[str, ...] = ("amount-limit",),
    max_rounds: int = 3,
) -> ReviewPolicy:
    return ReviewPolicy(
        rubric_version="rubric-v1",
        required_rule_ids=required,
        max_rounds=max_rounds,
    )


def run(
    panel: ReviewPanel[Candidate],
    *,
    candidate: Candidate = Candidate(50.0),
    reviser: ReviserSpec[Candidate] | None = None,
    review_policy: ReviewPolicy | None = None,
):
    review = AdversarialReview(
        panel,
        review_policy or policy(),
        author_actor_id="author",
        fingerprint=fingerprint,
        reviser=reviser,
    )
    return asyncio.run(review.run(contract(), artifact(candidate)))


def test_clean_complete_review_confirms_and_binds_both_receipts() -> None:
    result = run(ReviewPanel("panel", (reviewer(),)))

    assert result.outcome is Outcome.CONFIRMED
    assert result.acceptance_receipt.decision is AcceptanceDecision.ACCEPTED
    assert result.acceptance_receipt.artifact_id == result.artifact.artifact_id
    receipt = result.latest_review
    assert receipt is not None
    assert receipt.contract_digest == contract().digest
    assert receipt.artifact_fingerprint == fingerprint(result.artifact.payload)
    assert receipt.rubric_version == "rubric-v1"
    assert receipt.checked_rule_ids == ("amount-limit",)


def test_warning_is_preserved_but_does_not_hold_release() -> None:
    warning = objection(severity=Severity.WARNING)
    result = run(ReviewPanel("panel", (reviewer(result=(warning,)),)))

    assert result.outcome is Outcome.CONFIRMED
    assert result.acceptance_receipt.accepted
    assert result.acceptance_receipt.findings[0].severity is Severity.WARNING


def test_blocker_is_revised_then_the_new_artifact_is_reviewed() -> None:
    calls: list[str] = []

    async def inspect(request):
        calls.append(request.artifact_fingerprint)
        if request.artifact.payload.amount > 100:
            return (objection(),)
        return ()

    spec = ReviewerSpec(
        reviewer_id="amount-reviewer",
        actor_id="reviewer",
        rule_ids=("amount-limit",),
        evidence_scope=("policy://amount-limit/v1",),
        review=inspect,
    )

    async def revise(request, blockers):
        return artifact(
            Candidate(100.0, "capped"),
            artifact_id="candidate-r1",
            producer="reviser",
        )

    result = run(
        ReviewPanel("panel", (spec,)),
        candidate=Candidate(120.0),
        reviser=ReviserSpec("reviser", "reviser", revise),
    )

    assert result.outcome is Outcome.CONFIRMED
    assert result.artifact_revision == 1
    assert result.artifact.artifact_id == "candidate-r1"
    assert [item.receipt.artifact_id for item in result.rounds] == [
        "candidate-r0",
        "candidate-r1",
    ]
    assert calls == ["120.00|", "100.00|capped"]


def test_final_review_round_never_creates_an_unreviewed_artifact() -> None:
    revise_calls = 0

    async def revise(request, blockers):
        nonlocal revise_calls
        revise_calls += 1
        return artifact(
            Candidate(100.0),
            artifact_id="candidate-r1",
            producer="reviser",
        )

    result = run(
        ReviewPanel("panel", (reviewer(result=(objection(),)),)),
        candidate=Candidate(120.0),
        reviser=ReviserSpec("reviser", "reviser", revise),
        review_policy=policy(max_rounds=1),
    )

    assert result.outcome is Outcome.HELD_FOR_HUMAN
    assert result.artifact.artifact_id == "candidate-r0"
    assert result.latest_review.artifact_id == result.artifact.artifact_id
    assert revise_calls == 0


def test_blocker_without_reviser_is_held_for_human() -> None:
    result = run(
        ReviewPanel("panel", (reviewer(result=(objection(),)),)),
        candidate=Candidate(120.0),
    )

    assert result.outcome is Outcome.HELD_FOR_HUMAN
    assert result.acceptance_receipt.decision is AcceptanceDecision.ESCALATED


def test_empty_objections_do_not_override_missing_required_coverage() -> None:
    result = run(
        ReviewPanel(
            "panel",
            (reviewer(rule_ids=("amount-limit",)),),
        ),
        review_policy=policy(required=("amount-limit", "duplicate-line")),
    )

    assert result.outcome is Outcome.HELD_FOR_HUMAN
    assert result.latest_review.missing_rule_ids == ("duplicate-line",)
    assert not ReviewGate().may_confirm(result.latest_review)


def test_failed_reviewer_removes_its_rules_from_checked_coverage() -> None:
    async def broken(request):
        raise TimeoutError("review service timed out")

    spec = ReviewerSpec(
        reviewer_id="amount-reviewer",
        actor_id="reviewer",
        rule_ids=("amount-limit",),
        evidence_scope=("policy://amount-limit/v1",),
        review=broken,
    )
    result = run(ReviewPanel("panel", (spec,)))

    assert result.outcome is Outcome.HELD_FOR_HUMAN
    assert result.latest_review.checked_rule_ids == ()
    assert result.latest_review.missing_rule_ids == ("amount-limit",)
    assert result.latest_review.reviewer_failures[0].retryable


def test_undeclared_objection_rule_becomes_a_reviewer_failure() -> None:
    spec = reviewer(result=(objection(rule_id="unknown-rule"),))
    result = run(ReviewPanel("panel", (spec,)))

    assert result.outcome is Outcome.HELD_FOR_HUMAN
    assert "undeclared rule" in result.latest_review.reviewer_failures[0].error


@pytest.mark.parametrize(
    ("panel", "reviser", "finding_code"),
    [
        (
            ReviewPanel("panel", (reviewer(actor_id="author"),)),
            None,
            "author_is_reviewer",
        ),
        (
            ReviewPanel("panel", (reviewer(actor_id="reviser"),)),
            ReviserSpec("reviser", "reviser", lambda request, blockers: None),
            "reviser_is_reviewer",
        ),
        (
            ReviewPanel(
                "panel",
                (
                    reviewer(actor_id="same", reviewer_id="one"),
                    reviewer(actor_id="same", reviewer_id="two"),
                ),
            ),
            None,
            "duplicate_reviewer_actor",
        ),
    ],
)
def test_actor_independence_is_checked_before_review(
    panel,
    reviser,
    finding_code: str,
) -> None:
    result = run(panel, reviser=reviser)

    assert result.outcome is Outcome.NO_REVIEWER
    assert finding_code in {finding.code for finding in result.run_findings}
    assert result.rounds == ()


@pytest.mark.parametrize(
    ("mutate", "finding_code"),
    [
        (
            lambda item: replace(item, contract_digest="wrong"),
            "contract_digest_mismatch",
        ),
        (
            lambda item: replace(item, schema="WrongSchema"),
            "schema_mismatch",
        ),
        (
            lambda item: replace(item, produced_by="someone-else"),
            "producer_mismatch",
        ),
        (
            lambda item: replace(item, evidence_refs=()),
            "missing_evidence",
        ),
    ],
)
def test_invalid_candidate_never_enters_review(
    mutate,
    finding_code: str,
) -> None:
    panel = ReviewPanel("panel", (reviewer(),))
    review = AdversarialReview(
        panel,
        policy(),
        author_actor_id="author",
        fingerprint=fingerprint,
    )
    result = asyncio.run(review.run(contract(), mutate(artifact(Candidate(50.0)))))

    assert result.outcome is Outcome.INVALID_ARTIFACT
    assert finding_code in {finding.code for finding in result.run_findings}
    assert result.rounds == ()


def test_reviser_must_change_business_content() -> None:
    async def revise(request, blockers):
        return artifact(
            request.artifact.payload,
            artifact_id="candidate-r1",
            producer="reviser",
        )

    result = run(
        ReviewPanel("panel", (reviewer(result=(objection(),)),)),
        candidate=Candidate(120.0),
        reviser=ReviserSpec("reviser", "reviser", revise),
    )

    assert result.outcome is Outcome.HELD_FOR_HUMAN
    assert result.artifact.artifact_id == "candidate-r0"
    assert {
        finding.code for finding in result.run_findings
    } == {"reviser_made_no_progress"}


def test_policy_and_panel_configuration_are_validated() -> None:
    with pytest.raises(ValueError, match="required"):
        ReviewPolicy(rubric_version="v1", required_rule_ids=())
    with pytest.raises(ValueError, match="unique"):
        ReviewPanel(
            "panel",
            (
                reviewer(reviewer_id="duplicate"),
                reviewer(actor_id="other", reviewer_id="duplicate"),
            ),
        )
