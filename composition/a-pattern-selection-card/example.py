"""Run the minimal Pattern Selection Card lifecycle."""
from __future__ import annotations

from pattern import (
    ArchitectureCandidate,
    Assumption,
    Comparison,
    DependencyShape,
    ExperimentPlan,
    MetricGate,
    PatternSelectionCard,
    PatternSpec,
    ProblemContract,
    RejectedAlternative,
    Topology,
    TrialResult,
)


problem = ProblemContract(
    problem_id="june-reconciliation",
    objective="locate the payroll discrepancy",
    workload_ref="fixture://payroll/june/v1",
    input_refs=("snapshot://payroll", "snapshot://ledger"),
    output_contract="evidenced discrepancy report",
    dependency_shape=DependencyShape.INDEPENDENT,
    constraints=("read-only",),
    observed_baseline_failure="single-source check missed one disagreement",
)

baseline = ArchitectureCandidate(
    candidate_id="single-source",
    patterns=(),
    rationale="smallest viable read-only check",
)
proposal = ArchitectureCandidate(
    candidate_id="fanout",
    patterns=(
        PatternSpec(
            name="Fan-out and Gather",
            cognitive_function="collaborate",
            topology=Topology.PARALLEL,
            solves="compare independent source readings",
            preconditions=("independent_sources",),
        ),
    ),
    rationale="the source snapshots are independently owned",
    assumptions=(
        Assumption(
            key="independent_sources",
            claim="each source owns a separate snapshot",
            evidence_ref="schema://source-lineage/v1",
        ),
    ),
)

card = PatternSelectionCard(
    card_id="psc-payroll-001",
    version=1,
    problem=problem,
    baseline=baseline,
    proposal=proposal,
    rejected_alternatives=(
        RejectedAlternative(
            candidate_id="iterative-hypothesis",
            reason="one source result does not change the next source query",
            evidence_ref="fixture://payroll/june/dependency-map",
        ),
    ),
    experiment=ExperimentPlan(
        workload_ref=problem.workload_ref,
        gates=(
            MetricGate("defect_recall", Comparison.AT_LEAST, 1.0),
            MetricGate("false_consensus", Comparison.AT_MOST, 0.0),
        ),
        disconfirming_signals=("sources share an upstream baseline",),
        rollback_plan="retain the single-source check",
    ),
)

trials = (
    TrialResult(
        candidate_id="single-source",
        workload_ref=problem.workload_ref,
        metrics=(("defect_recall", 0.0), ("false_consensus", 0.0)),
        evidence_refs=("run://single-source/1",),
    ),
    TrialResult(
        candidate_id="fanout",
        workload_ref=problem.workload_ref,
        metrics=(("defect_recall", 1.0), ("false_consensus", 0.0)),
        evidence_refs=("run://fanout/1",),
    ),
)

print(f"card: {card.card_id}@v{card.version} digest={card.digest}")
print(f"before trial: {card.evaluate().state.value}")
print(f"after trial:  {card.evaluate(trials).state.value}")
