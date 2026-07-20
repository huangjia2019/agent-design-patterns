"""Run a minimal Six-Step Methodology decision."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from pattern import (  # noqa: E402
    BaselineEvidence,
    BoundDecision,
    CandidateArchitecture,
    Comparison,
    ConstraintDiagnosis,
    DecisionStatus,
    ExperimentCase,
    MutationPolicy,
    PatternBinding,
    QualityGate,
    SeamContract,
    SixStepSession,
    TrialResult,
)


WORKLOAD = "fixture://payroll/seam/v1"
METRICS = (
    ("recovery_success", 1.0),
    ("committed_fact_overwrites", 0.0),
    ("settlement_receipts", 1.0),
)


session = SixStepSession("payroll-seam").bound(
    BoundDecision(
        objective="Recover a failed payroll plan without rewriting settled facts.",
        workload_ref=WORKLOAD,
        output_contract="Versioned plan plus immutable settlement receipt",
        constraints=("one writer per committed fact",),
        excluded_scope=("bank settlement",),
        gates=(
            QualityGate("recovery_success", Comparison.AT_LEAST, 1.0),
            QualityGate("committed_fact_overwrites", Comparison.AT_MOST, 0.0),
            QualityGate("settlement_receipts", Comparison.AT_LEAST, 1.0),
        ),
    )
)
session.record_baseline(
    BaselineEvidence(
        baseline_id="mutable-dict",
        workload_ref=WORKLOAD,
        metrics=(
            ("recovery_success", 0.0),
            ("committed_fact_overwrites", 1.0),
            ("settlement_receipts", 0.0),
        ),
        evidence_refs=("trace://baseline",),
        observed_failures=("settled amount was overwritten",),
    )
)
session.diagnose(
    (
        ConstraintDiagnosis(
            "missing_recovery",
            "The workflow has no local recovery boundary.",
            "recovery_success",
            ("trace://baseline#failure",),
        ),
        ConstraintDiagnosis(
            "missing_ownership",
            "Planning and settlement share one mutable amount field.",
            "committed_fact_overwrites",
            ("trace://baseline#overwrite",),
        ),
        ConstraintDiagnosis(
            "missing_receipt",
            "The workflow cannot prove which settlement version crossed the seam.",
            "settlement_receipts",
            ("trace://baseline#no-receipt",),
        ),
    )
)
session.generate_candidates(
    (
        CandidateArchitecture(
            candidate_id="split-plan-and-settlement",
            patterns=(
                PatternBinding(
                    "Plan and Execute",
                    produces=("payroll_plan",),
                    mutates=("payroll_plan_draft",),
                ),
                PatternBinding(
                    "Handoff Chain",
                    consumes=("payroll_plan",),
                    produces=("settled_net_amount",),
                ),
            ),
            targets=("missing_recovery", "missing_ownership", "missing_receipt"),
            rationale="Planning owns revisions; the handoff owns committed settlement.",
            assumption_refs=("design://payroll/fact-ownership/v1",),
            seams=(
                SeamContract(
                    artifact="payroll_plan",
                    producer="Plan and Execute",
                    consumer="Handoff Chain",
                    owner="Plan and Execute",
                    mutation_policy=MutationPolicy.REPLACEABLE_UNTIL_COMMIT,
                    version_field="plan_version",
                ),
            ),
        ),
    )
)
session.specify_seams_and_trials(
    (
        ExperimentCase(
            "full",
            "split-plan-and-settlement",
            WORKLOAD,
            None,
            "Recovery succeeds and settlement stays append-only.",
        ),
        ExperimentCase(
            "without-plan",
            "split-plan-and-settlement",
            WORKLOAD,
            "Plan and Execute",
            "Transient failure remains unrecovered.",
        ),
        ExperimentCase(
            "without-handoff",
            "split-plan-and-settlement",
            WORKLOAD,
            "Handoff Chain",
            "No version-bound settlement receipt exists.",
        ),
    )
)
receipt = session.decide(
    (
        TrialResult("full", WORKLOAD, METRICS, ("receipt://full",)),
        TrialResult(
            "without-plan",
            WORKLOAD,
            (
                ("recovery_success", 0.0),
                ("committed_fact_overwrites", 0.0),
                ("settlement_receipts", 0.0),
            ),
            ("trace://without-plan",),
            ("transient failure was not recovered",),
        ),
        TrialResult(
            "without-handoff",
            WORKLOAD,
            (
                ("recovery_success", 1.0),
                ("committed_fact_overwrites", 1.0),
                ("settlement_receipts", 0.0),
            ),
            ("trace://without-handoff",),
            ("committed amount was rewritten",),
        ),
    ),
    reopen_triggers=("workload dependency changes", "settlement authority changes"),
)

assert receipt.status is DecisionStatus.ADOPT_CANDIDATE
print(receipt)
