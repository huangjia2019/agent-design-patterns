import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    BaselineEvidence,
    BoundDecision,
    CandidateArchitecture,
    Comparison,
    ConstraintDiagnosis,
    DecisionStatus,
    ExperimentCase,
    FindingSeverity,
    MutationPolicy,
    PatternBinding,
    QualityGate,
    SeamContract,
    SixStepSession,
    TrialResult,
    review_candidate,
)


WORKLOAD = "fixture://six-step/v1"


def problem():
    return BoundDecision(
        objective="Recover a plan without rewriting a committed fact.",
        workload_ref=WORKLOAD,
        output_contract="Versioned plan and settlement receipt",
        constraints=("single writer",),
        excluded_scope=("bank settlement",),
        gates=(
            QualityGate("recovery", Comparison.AT_LEAST, 1.0),
            QualityGate("overwrites", Comparison.AT_MOST, 0.0),
            QualityGate("receipts", Comparison.AT_LEAST, 1.0),
        ),
    )


def baseline(*, passes=False):
    metrics = (
        ("recovery", 1.0 if passes else 0.0),
        ("overwrites", 0.0 if passes else 1.0),
        ("receipts", 1.0 if passes else 0.0),
    )
    return BaselineEvidence(
        baseline_id="baseline",
        workload_ref=WORKLOAD,
        metrics=metrics,
        evidence_refs=("trace://baseline",),
        observed_failures=("shared state",),
    )


def diagnoses():
    return (
        ConstraintDiagnosis(
            "recovery_gap",
            "No local recovery.",
            "recovery",
            ("trace://baseline#recovery",),
        ),
        ConstraintDiagnosis(
            "ownership_gap",
            "One mutable field has two writers.",
            "overwrites",
            ("trace://baseline#ownership",),
        ),
        ConstraintDiagnosis(
            "receipt_gap",
            "No seam receipt.",
            "receipts",
            ("trace://baseline#receipt",),
        ),
    )


def candidate():
    return CandidateArchitecture(
        candidate_id="split",
        patterns=(
            PatternBinding(
                "Plan and Execute",
                produces=("plan",),
                mutates=("plan_draft",),
            ),
            PatternBinding(
                "Handoff Chain",
                consumes=("plan",),
                produces=("settlement",),
            ),
        ),
        targets=("recovery_gap", "ownership_gap", "receipt_gap"),
        rationale="Separate mutable planning from committed settlement.",
        assumption_refs=("design://ownership/v1",),
        seams=(
            SeamContract(
                artifact="plan",
                producer="Plan and Execute",
                consumer="Handoff Chain",
                owner="Plan and Execute",
                mutation_policy=MutationPolicy.REPLACEABLE_UNTIL_COMMIT,
                version_field="plan_version",
            ),
        ),
    )


def experiments():
    return (
        ExperimentCase("full", "split", WORKLOAD, None, "all gates pass"),
        ExperimentCase(
            "without-plan",
            "split",
            WORKLOAD,
            "Plan and Execute",
            "recovery fails",
        ),
        ExperimentCase(
            "without-handoff",
            "split",
            WORKLOAD,
            "Handoff Chain",
            "receipt fails",
        ),
    )


def results(*, redundant=False):
    return (
        TrialResult(
            "full",
            WORKLOAD,
            (("recovery", 1.0), ("overwrites", 0.0), ("receipts", 1.0)),
            ("trace://full",),
        ),
        TrialResult(
            "without-plan",
            WORKLOAD,
            (
                ("recovery", 1.0 if redundant else 0.0),
                ("overwrites", 0.0),
                ("receipts", 1.0 if redundant else 0.0),
            ),
            ("trace://without-plan",),
            () if redundant else ("no recovery",),
        ),
        TrialResult(
            "without-handoff",
            WORKLOAD,
            (("recovery", 1.0), ("overwrites", 1.0), ("receipts", 0.0)),
            ("trace://without-handoff",),
            ("no receipt",),
        ),
    )


def ready_session(*, passing_baseline=False):
    session = SixStepSession("decision").bound(problem())
    session.record_baseline(baseline(passes=passing_baseline))
    session.diagnose(diagnoses())
    session.generate_candidates((candidate(),))
    session.specify_seams_and_trials(experiments())
    return session


def test_steps_cannot_be_skipped():
    session = SixStepSession("decision")
    with pytest.raises(RuntimeError, match="expected step bound"):
        session.record_baseline(baseline())


def test_baseline_must_use_bound_workload():
    session = SixStepSession("decision").bound(problem())
    other = BaselineEvidence(
        "baseline",
        "fixture://other",
        baseline().metrics,
        ("trace://other",),
        ("failure",),
    )
    with pytest.raises(ValueError, match="bound workload"):
        session.record_baseline(other)


def test_candidate_must_target_observed_diagnosis():
    session = SixStepSession("decision").bound(problem())
    session.record_baseline(baseline())
    session.diagnose(diagnoses())
    invalid = CandidateArchitecture(
        candidate_id="invalid",
        patterns=(PatternBinding("Unknown"),),
        targets=("imagined_gap",),
        rationale="Guess.",
        assumption_refs=("meeting://guess",),
    )
    with pytest.raises(ValueError, match="unknown diagnoses"):
        session.generate_candidates((invalid,))


def test_review_catches_multiple_writers():
    invalid = CandidateArchitecture(
        candidate_id="two-writers",
        patterns=(
            PatternBinding("Plan and Execute", produces=("net_amount",)),
            PatternBinding("Handoff Chain", produces=("net_amount",)),
        ),
        targets=("ownership_gap",),
        rationale="Both patterns publish one field.",
        assumption_refs=("design://bad",),
    )
    findings = review_candidate(invalid)
    assert any(
        item.code == "multiple_writers"
        and item.severity is FindingSeverity.ERROR
        for item in findings
    )


def test_review_catches_missing_seam_contract():
    invalid = CandidateArchitecture(
        candidate_id="no-seam",
        patterns=(
            PatternBinding("Plan and Execute", produces=("plan",)),
            PatternBinding("Handoff Chain", consumes=("plan",)),
        ),
        targets=("ownership_gap",),
        rationale="The data handoff is undocumented.",
        assumption_refs=("design://bad",),
    )
    assert any(
        item.code == "missing_seam_contract"
        for item in review_candidate(invalid)
    )


def test_review_catches_append_only_rewrite():
    invalid = CandidateArchitecture(
        candidate_id="rewrite",
        patterns=(
            PatternBinding("Plan and Execute", mutates=("settlement",)),
            PatternBinding("Handoff Chain", consumes=("settlement",)),
        ),
        targets=("ownership_gap",),
        rationale="A committed settlement is replanned.",
        assumption_refs=("design://bad",),
        seams=(
            SeamContract(
                "settlement",
                "Plan and Execute",
                "Handoff Chain",
                "Handoff Chain",
                MutationPolicy.APPEND_ONLY,
                "settlement_version",
            ),
        ),
    )
    assert any(
        item.code == "append_only_rewrite"
        for item in review_candidate(invalid)
    )


def test_multi_pattern_candidate_requires_each_ablation():
    session = SixStepSession("decision").bound(problem())
    session.record_baseline(baseline())
    session.diagnose(diagnoses())
    session.generate_candidates((candidate(),))
    with pytest.raises(ValueError, match="lacks ablations"):
        session.specify_seams_and_trials((experiments()[0],))


def test_one_candidate_can_earn_adoption():
    receipt = ready_session().decide(
        results(),
        reopen_triggers=("dependency changes",),
    )
    assert receipt.status is DecisionStatus.ADOPT_CANDIDATE
    assert receipt.selected_candidate == "split"


def test_passing_baseline_blocks_added_complexity():
    receipt = ready_session(passing_baseline=True).decide(
        results(),
        reopen_triggers=("dependency changes",),
    )
    assert receipt.status is DecisionStatus.KEEP_BASELINE
    assert receipt.selected_candidate == "baseline"


def test_passing_ablation_exposes_unearned_pattern():
    receipt = ready_session().decide(
        results(redundant=True),
        reopen_triggers=("dependency changes",),
    )
    assert receipt.status is DecisionStatus.REJECT_ALL
    assert "removing" in receipt.reason


def test_reopen_increments_version_and_binds_prior_receipt():
    session = ready_session()
    receipt = session.decide(
        results(),
        reopen_triggers=("dependency changes",),
    )
    reopened = session.reopen("shared state introduced")
    assert reopened.version == 2
    assert reopened.prior_receipt_digest == receipt.digest
