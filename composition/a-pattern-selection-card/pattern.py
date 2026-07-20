"""Pattern Selection Card.

A pattern catalog can suggest architectural moves. It cannot prove that a
particular composition will work for a particular workload. This module keeps
that epistemic boundary explicit:

* the card records the problem, constraints, and observed baseline failure;
* a candidate names its pattern bundle, assumptions, and seam contracts;
* an experiment compares the candidate with the smallest viable baseline;
* only measured evidence can promote the card from a proposal to an accepted
  architecture decision.

The implementation intentionally does not auto-select patterns. Pattern choice
is an architecture hypothesis. The runtime validates the hypothesis and its
evidence.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Mapping


class DependencyShape(str, Enum):
    """How one unit of work relates to the next."""

    INDEPENDENT = "independent"
    ORDERED = "ordered"
    SHARED_STATE = "shared_state"


class Topology(str, Enum):
    CHAIN = "chain"
    PARALLEL = "parallel"
    ROUTE = "route"
    LOOP = "loop"
    ORCHESTRATE = "orchestrate"
    HIERARCHY = "hierarchy"


class Comparison(str, Enum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    EQUALS = "equals"


class FindingSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class CardState(str, Enum):
    DRAFT = "draft"
    READY_FOR_TRIAL = "ready_for_trial"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True)
class MetricGate:
    """One measurable condition the architecture must satisfy."""

    metric: str
    comparison: Comparison
    target: float

    def __post_init__(self) -> None:
        if not self.metric.strip():
            raise ValueError("metric must not be empty")

    def passes(self, metrics: Mapping[str, float]) -> bool:
        if self.metric not in metrics:
            return False
        actual = metrics[self.metric]
        if self.comparison is Comparison.AT_LEAST:
            return actual >= self.target
        if self.comparison is Comparison.AT_MOST:
            return actual <= self.target
        return actual == self.target


@dataclass(frozen=True)
class ProblemContract:
    """The bounded decision problem before any pattern is named."""

    problem_id: str
    objective: str
    workload_ref: str
    input_refs: tuple[str, ...]
    output_contract: str
    dependency_shape: DependencyShape
    constraints: tuple[str, ...]
    observed_baseline_failure: str

    def __post_init__(self) -> None:
        required = (
            self.problem_id,
            self.objective,
            self.workload_ref,
            self.output_contract,
        )
        if not all(value.strip() for value in required):
            raise ValueError("problem identity, objective, workload, and output are required")
        if not self.input_refs:
            raise ValueError("at least one input reference is required")
        if not self.constraints:
            raise ValueError("at least one constraint is required")


@dataclass(frozen=True)
class PatternSpec:
    """One reusable pattern and the conditions under which it is plausible."""

    name: str
    cognitive_function: str
    topology: Topology
    solves: str
    preconditions: tuple[str, ...] = ()
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (self.name, self.cognitive_function, self.solves)
        if not all(value.strip() for value in required):
            raise ValueError("pattern name, cognitive function, and purpose are required")


@dataclass(frozen=True)
class Assumption:
    """A candidate precondition and the evidence supporting it."""

    key: str
    claim: str
    evidence_ref: str | None = None

    def __post_init__(self) -> None:
        if not self.key.strip() or not self.claim.strip():
            raise ValueError("assumption key and claim are required")


@dataclass(frozen=True)
class SeamContract:
    """The ownership and mutation rule where two patterns meet."""

    producer: str
    consumer: str
    artifact: str
    owner: str
    mutation_rule: str
    version_field: str

    def __post_init__(self) -> None:
        required = (
            self.producer,
            self.consumer,
            self.artifact,
            self.owner,
            self.mutation_rule,
            self.version_field,
        )
        if not all(value.strip() for value in required):
            raise ValueError("a seam contract must define both sides and its data rules")


@dataclass(frozen=True)
class ArchitectureCandidate:
    """A pattern bundle proposed as one falsifiable architecture hypothesis."""

    candidate_id: str
    patterns: tuple[PatternSpec, ...]
    rationale: str
    assumptions: tuple[Assumption, ...] = ()
    seams: tuple[SeamContract, ...] = ()

    def __post_init__(self) -> None:
        if not self.candidate_id.strip() or not self.rationale.strip():
            raise ValueError("candidate identity and rationale are required")


@dataclass(frozen=True)
class RejectedAlternative:
    """A real alternative considered and the evidence for rejecting it."""

    candidate_id: str
    reason: str
    evidence_ref: str

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (self.candidate_id, self.reason, self.evidence_ref)
        ):
            raise ValueError("rejected alternatives require identity, reason, and evidence")


@dataclass(frozen=True)
class ExperimentPlan:
    """The test that is allowed to accept or reject the proposed bundle."""

    workload_ref: str
    gates: tuple[MetricGate, ...]
    disconfirming_signals: tuple[str, ...]
    rollback_plan: str

    def __post_init__(self) -> None:
        if not self.workload_ref.strip():
            raise ValueError("experiment workload is required")
        if not self.gates:
            raise ValueError("at least one metric gate is required")
        if not self.disconfirming_signals:
            raise ValueError("at least one disconfirming signal is required")
        if not self.rollback_plan.strip():
            raise ValueError("rollback plan is required")


@dataclass(frozen=True)
class TrialResult:
    """Measured output for one candidate on the card's bound workload."""

    candidate_id: str
    workload_ref: str
    metrics: tuple[tuple[str, float], ...]
    evidence_refs: tuple[str, ...]
    observed_failures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.candidate_id.strip() or not self.workload_ref.strip():
            raise ValueError("trial candidate and workload are required")
        metric_names = [name for name, _ in self.metrics]
        if not metric_names or len(metric_names) != len(set(metric_names)):
            raise ValueError("trial metrics must be non-empty and unique")
        if not self.evidence_refs:
            raise ValueError("trial results require evidence references")

    @property
    def measured(self) -> dict[str, float]:
        return dict(self.metrics)


@dataclass(frozen=True)
class SelectionFinding:
    severity: FindingSeverity
    code: str
    detail: str


@dataclass(frozen=True)
class SelectionOutcome:
    state: CardState
    reason: str
    baseline_passed: bool | None = None
    proposal_passed: bool | None = None
    failed_gates: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class PatternSelectionCard:
    """A versioned architecture hypothesis, not an automatic selector."""

    card_id: str
    version: int
    problem: ProblemContract
    baseline: ArchitectureCandidate
    proposal: ArchitectureCandidate
    rejected_alternatives: tuple[RejectedAlternative, ...]
    experiment: ExperimentPlan

    def __post_init__(self) -> None:
        if not self.card_id.strip():
            raise ValueError("card_id must not be empty")
        if self.version < 1:
            raise ValueError("version must be >= 1")
        if self.baseline.candidate_id == self.proposal.candidate_id:
            raise ValueError("baseline and proposal must be distinct candidates")

    def review(self) -> tuple[SelectionFinding, ...]:
        findings: list[SelectionFinding] = []
        assumptions = {item.key: item for item in self.proposal.assumptions}

        if not self.problem.observed_baseline_failure.strip():
            findings.append(
                SelectionFinding(
                    FindingSeverity.WARNING,
                    "baseline_failure_not_observed",
                    "No measured baseline failure explains why more architecture is needed.",
                )
            )

        for pattern in self.proposal.patterns:
            for precondition in pattern.preconditions:
                assumption = assumptions.get(precondition)
                if assumption is None:
                    findings.append(
                        SelectionFinding(
                            FindingSeverity.ERROR,
                            "precondition_not_claimed",
                            f"{pattern.name} requires {precondition!r}, but the card does not claim it.",
                        )
                    )
                elif not assumption.evidence_ref:
                    findings.append(
                        SelectionFinding(
                            FindingSeverity.ERROR,
                            "precondition_not_evidenced",
                            f"{pattern.name} requires {precondition!r}, but the claim has no evidence.",
                        )
                    )

        if len(self.proposal.patterns) > 1 and not self.proposal.seams:
            findings.append(
                SelectionFinding(
                    FindingSeverity.ERROR,
                    "missing_seam_contract",
                    "A multi-pattern candidate must define at least one seam contract.",
                )
            )

        if not self.rejected_alternatives:
            findings.append(
                SelectionFinding(
                    FindingSeverity.ERROR,
                    "alternative_not_considered",
                    "Name at least one rejected alternative and the evidence for rejecting it.",
                )
            )

        if self.experiment.workload_ref != self.problem.workload_ref:
            findings.append(
                SelectionFinding(
                    FindingSeverity.ERROR,
                    "workload_binding_mismatch",
                    "The experiment must use the workload bound into the problem contract.",
                )
            )

        return tuple(findings)

    @property
    def digest(self) -> str:
        payload = json.dumps(
            asdict(self),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]

    def evaluate(self, trials: tuple[TrialResult, ...] = ()) -> SelectionOutcome:
        errors = tuple(
            finding
            for finding in self.review()
            if finding.severity is FindingSeverity.ERROR
        )
        if errors:
            return SelectionOutcome(
                state=CardState.DRAFT,
                reason="; ".join(finding.code for finding in errors),
            )

        if not trials:
            return SelectionOutcome(
                state=CardState.READY_FOR_TRIAL,
                reason="The hypothesis is well formed and awaits a bound comparison.",
            )

        by_candidate = {trial.candidate_id: trial for trial in trials}
        baseline_trial = by_candidate.get(self.baseline.candidate_id)
        proposal_trial = by_candidate.get(self.proposal.candidate_id)
        if baseline_trial is None or proposal_trial is None:
            return SelectionOutcome(
                state=CardState.DRAFT,
                reason="Both baseline and proposal must run on the bound workload.",
            )

        if (
            baseline_trial.workload_ref != self.experiment.workload_ref
            or proposal_trial.workload_ref != self.experiment.workload_ref
        ):
            return SelectionOutcome(
                state=CardState.DRAFT,
                reason="Trial workload does not match the experiment plan.",
            )

        baseline_failed = tuple(
            gate.metric
            for gate in self.experiment.gates
            if not gate.passes(baseline_trial.measured)
        )
        proposal_failed = tuple(
            gate.metric
            for gate in self.experiment.gates
            if not gate.passes(proposal_trial.measured)
        )
        evidence_refs = tuple(
            dict.fromkeys(baseline_trial.evidence_refs + proposal_trial.evidence_refs)
        )

        if not baseline_failed:
            return SelectionOutcome(
                state=CardState.REJECTED,
                reason="The baseline already satisfies every gate; added complexity is not justified.",
                baseline_passed=True,
                proposal_passed=not proposal_failed,
                failed_gates=proposal_failed,
                evidence_refs=evidence_refs,
            )

        if proposal_failed or proposal_trial.observed_failures:
            failures = proposal_failed or proposal_trial.observed_failures
            return SelectionOutcome(
                state=CardState.REJECTED,
                reason="The proposed architecture failed its acceptance evidence.",
                baseline_passed=False,
                proposal_passed=False,
                failed_gates=tuple(failures),
                evidence_refs=evidence_refs,
            )

        return SelectionOutcome(
            state=CardState.ACCEPTED,
            reason="The baseline failed and the proposal passed every bound gate.",
            baseline_passed=False,
            proposal_passed=True,
            evidence_refs=evidence_refs,
        )
