"""Invariants for the Pattern Selection Card."""
from __future__ import annotations

import os
import sys
from dataclasses import replace


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    ArchitectureCandidate,
    Assumption,
    CardState,
    Comparison,
    DependencyShape,
    ExperimentPlan,
    MetricGate,
    PatternSelectionCard,
    PatternSpec,
    ProblemContract,
    RejectedAlternative,
    SeamContract,
    Topology,
    TrialResult,
)


def problem() -> ProblemContract:
    return ProblemContract(
        problem_id="june-reconciliation",
        objective="locate the June payroll discrepancy",
        workload_ref="fixture://payroll/june/v1",
        input_refs=("snapshot://payroll", "snapshot://ledger"),
        output_contract="one evidenced discrepancy report",
        dependency_shape=DependencyShape.INDEPENDENT,
        constraints=("read-only", "finish under 30 seconds"),
        observed_baseline_failure="one-source check missed a ledger disagreement",
    )


def baseline() -> ArchitectureCandidate:
    return ArchitectureCandidate(
        candidate_id="single-source",
        patterns=(),
        rationale="smallest read-only baseline",
    )


def fanout() -> PatternSpec:
    return PatternSpec(
        name="Fan-out and Gather",
        cognitive_function="collaborate",
        topology=Topology.PARALLEL,
        solves="compare independent source readings",
        preconditions=("independent_sources",),
        produces=("reconciliation_report",),
    )


def card() -> PatternSelectionCard:
    return PatternSelectionCard(
        card_id="psc-payroll-001",
        version=1,
        problem=problem(),
        baseline=baseline(),
        proposal=ArchitectureCandidate(
            candidate_id="fanout",
            patterns=(fanout(),),
            rationale="independent ledgers can be compared concurrently",
            assumptions=(
                Assumption(
                    key="independent_sources",
                    claim="each source owns its snapshot",
                    evidence_ref="schema://source-lineage/v1",
                ),
            ),
        ),
        rejected_alternatives=(
            RejectedAlternative(
                candidate_id="iterative-hypothesis",
                reason="no finding changes which source must be read next",
                evidence_ref="fixture://payroll/june/dependency-map",
            ),
        ),
        experiment=ExperimentPlan(
            workload_ref=problem().workload_ref,
            gates=(
                MetricGate("defect_recall", Comparison.AT_LEAST, 1.0),
                MetricGate("false_consensus", Comparison.AT_MOST, 0.0),
            ),
            disconfirming_signals=("sources share an upstream state",),
            rollback_plan="keep the single-source checker",
        ),
    )


def trial(candidate_id: str, recall: float, false_consensus: float) -> TrialResult:
    return TrialResult(
        candidate_id=candidate_id,
        workload_ref=problem().workload_ref,
        metrics=(
            ("defect_recall", recall),
            ("false_consensus", false_consensus),
        ),
        evidence_refs=(f"run://{candidate_id}/1",),
    )


def test_well_formed_card_is_ready_but_not_preapproved() -> None:
    current = card()

    assert current.review() == ()
    assert current.evaluate().state is CardState.READY_FOR_TRIAL
    assert len(current.digest) == 16


def test_unproven_pattern_precondition_keeps_card_in_draft() -> None:
    current = card()
    proposal = replace(
        current.proposal,
        assumptions=(
            Assumption(
                key="independent_sources",
                claim="sources appear independent",
            ),
        ),
    )

    outcome = replace(current, proposal=proposal).evaluate()

    assert outcome.state is CardState.DRAFT
    assert "precondition_not_evidenced" in outcome.reason


def test_added_complexity_is_rejected_when_baseline_already_passes() -> None:
    outcome = card().evaluate(
        (
            trial("single-source", 1.0, 0.0),
            trial("fanout", 1.0, 0.0),
        )
    )

    assert outcome.state is CardState.REJECTED
    assert outcome.baseline_passed is True


def test_candidate_is_accepted_only_when_baseline_fails_and_proposal_passes() -> None:
    outcome = card().evaluate(
        (
            trial("single-source", 0.0, 0.0),
            trial("fanout", 1.0, 0.0),
        )
    )

    assert outcome.state is CardState.ACCEPTED
    assert outcome.baseline_passed is False
    assert outcome.proposal_passed is True


def test_failed_proposal_is_rejected_even_when_pattern_name_looks_right() -> None:
    outcome = card().evaluate(
        (
            trial("single-source", 0.0, 1.0),
            trial("fanout", 0.0, 1.0),
        )
    )

    assert outcome.state is CardState.REJECTED
    assert set(outcome.failed_gates) == {"defect_recall", "false_consensus"}


def test_multi_pattern_candidate_requires_an_explicit_seam_contract() -> None:
    current = card()
    second = PatternSpec(
        name="Approval Gate",
        cognitive_function="govern",
        topology=Topology.ROUTE,
        solves="hold high-risk release for approval",
    )
    proposal = replace(current.proposal, patterns=(fanout(), second))

    outcome = replace(current, proposal=proposal).evaluate()

    assert outcome.state is CardState.DRAFT
    assert "missing_seam_contract" in outcome.reason

    with_seam = replace(
        proposal,
        seams=(
            SeamContract(
                producer="Fan-out and Gather",
                consumer="Approval Gate",
                artifact="reconciliation_report",
                owner="payroll-controller",
                mutation_rule="append-only",
                version_field="report_digest",
            ),
        ),
    )
    assert replace(current, proposal=with_seam).review() == ()
