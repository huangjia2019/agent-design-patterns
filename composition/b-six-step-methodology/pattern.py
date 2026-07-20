"""Evidence-driven Six-Step Methodology.

The methodology turns architecture selection into a staged, reviewable
decision process:

1. bound one decision and its representative workload;
2. run the smallest viable baseline;
3. diagnose the binding constraints exposed by that baseline;
4. generate a small set of falsifiable architecture candidates;
5. specify pattern seams and full-versus-ablation experiments;
6. compare the results, issue a decision receipt, and name reopen triggers.

This module validates the process and its evidence. It intentionally does not
map a business description to a supposedly correct pattern bundle. A catalog
generates candidates; bound experiments decide whether their extra complexity
has earned a place.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Mapping


class MethodStep(str, Enum):
    BOUND = "bound"
    BASELINE = "baseline"
    DIAGNOSE = "diagnose"
    CANDIDATES = "candidates"
    SEAMS_AND_TRIALS = "seams_and_trials"
    DECIDE = "decide"


class Comparison(str, Enum):
    AT_LEAST = "at_least"
    AT_MOST = "at_most"
    EQUALS = "equals"


class MutationPolicy(str, Enum):
    READ_ONLY = "read_only"
    REPLACEABLE_UNTIL_COMMIT = "replaceable_until_commit"
    APPEND_ONLY = "append_only"


class FindingSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


class DecisionStatus(str, Enum):
    KEEP_BASELINE = "keep_baseline"
    ADOPT_CANDIDATE = "adopt_candidate"
    REJECT_ALL = "reject_all"
    NEEDS_REVIEW = "needs_review"


@dataclass(frozen=True)
class QualityGate:
    """One observable condition shared by the baseline and every trial."""

    metric: str
    comparison: Comparison
    target: float

    def __post_init__(self) -> None:
        if not self.metric.strip():
            raise ValueError("quality gate metric must not be empty")

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
class BoundDecision:
    """Step 1: one bounded architecture decision before patterns are named."""

    objective: str
    workload_ref: str
    output_contract: str
    constraints: tuple[str, ...]
    excluded_scope: tuple[str, ...]
    gates: tuple[QualityGate, ...]

    def __post_init__(self) -> None:
        required = (self.objective, self.workload_ref, self.output_contract)
        if not all(value.strip() for value in required):
            raise ValueError("objective, workload, and output contract are required")
        if not self.constraints:
            raise ValueError("at least one constraint is required")
        if not self.excluded_scope:
            raise ValueError("excluded scope must be explicit")
        if not self.gates:
            raise ValueError("at least one quality gate is required")
        metrics = [gate.metric for gate in self.gates]
        if len(metrics) != len(set(metrics)):
            raise ValueError("quality gate metrics must be unique")


@dataclass(frozen=True)
class BaselineEvidence:
    """Step 2: measured behavior of the smallest viable implementation."""

    baseline_id: str
    workload_ref: str
    metrics: tuple[tuple[str, float], ...]
    evidence_refs: tuple[str, ...]
    observed_failures: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.baseline_id.strip() or not self.workload_ref.strip():
            raise ValueError("baseline identity and workload are required")
        names = [name for name, _ in self.metrics]
        if not names or len(names) != len(set(names)):
            raise ValueError("baseline metrics must be non-empty and unique")
        if not self.evidence_refs:
            raise ValueError("baseline evidence references are required")
        if not self.observed_failures:
            raise ValueError("record the observed baseline failure")

    @property
    def measured(self) -> dict[str, float]:
        return dict(self.metrics)


@dataclass(frozen=True)
class ConstraintDiagnosis:
    """Step 3: an evidenced explanation for one failed baseline property."""

    code: str
    claim: str
    failed_gate: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not all(value.strip() for value in (self.code, self.claim, self.failed_gate)):
            raise ValueError("diagnosis code, claim, and failed gate are required")
        if not self.evidence_refs:
            raise ValueError("a diagnosis must cite evidence")


@dataclass(frozen=True)
class PatternBinding:
    """One pattern's data role inside a candidate composition."""

    pattern_name: str
    consumes: tuple[str, ...] = ()
    produces: tuple[str, ...] = ()
    mutates: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.pattern_name.strip():
            raise ValueError("pattern name must not be empty")
        fields = self.consumes + self.produces + self.mutates
        if any(not item.strip() for item in fields):
            raise ValueError("artifact names must not be empty")
        if set(self.produces).intersection(self.mutates):
            raise ValueError("an artifact cannot be both produced and mutated")


@dataclass(frozen=True)
class SeamContract:
    """The ownership and mutation rule at one pattern boundary."""

    artifact: str
    producer: str
    consumer: str
    owner: str
    mutation_policy: MutationPolicy
    version_field: str

    def __post_init__(self) -> None:
        required = (
            self.artifact,
            self.producer,
            self.consumer,
            self.owner,
            self.version_field,
        )
        if not all(value.strip() for value in required):
            raise ValueError("seam identity, ownership, and version are required")


@dataclass(frozen=True)
class CandidateArchitecture:
    """Step 4: one falsifiable architecture hypothesis."""

    candidate_id: str
    patterns: tuple[PatternBinding, ...]
    targets: tuple[str, ...]
    rationale: str
    assumption_refs: tuple[str, ...]
    seams: tuple[SeamContract, ...] = ()

    def __post_init__(self) -> None:
        if not self.candidate_id.strip() or not self.rationale.strip():
            raise ValueError("candidate identity and rationale are required")
        if not self.patterns:
            raise ValueError("a candidate needs at least one pattern")
        names = [pattern.pattern_name for pattern in self.patterns]
        if len(names) != len(set(names)):
            raise ValueError("pattern names must be unique within a candidate")
        if not self.targets:
            raise ValueError("a candidate must target at least one diagnosis")
        if not self.assumption_refs:
            raise ValueError("candidate assumptions must be evidenced")


@dataclass(frozen=True)
class MethodFinding:
    severity: FindingSeverity
    code: str
    detail: str
    candidate_id: str | None = None


@dataclass(frozen=True)
class ExperimentCase:
    """Step 5: one full or ablated run on the bound workload."""

    case_id: str
    candidate_id: str
    workload_ref: str
    removed_pattern: str | None
    expected_signal: str

    def __post_init__(self) -> None:
        required = (
            self.case_id,
            self.candidate_id,
            self.workload_ref,
            self.expected_signal,
        )
        if not all(value.strip() for value in required):
            raise ValueError("experiment case identity and expectation are required")
        if self.removed_pattern is not None and not self.removed_pattern.strip():
            raise ValueError("removed pattern must be a real pattern name")


@dataclass(frozen=True)
class TrialResult:
    """Measured evidence for one experiment case."""

    case_id: str
    workload_ref: str
    metrics: tuple[tuple[str, float], ...]
    evidence_refs: tuple[str, ...]
    observed_failures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.case_id.strip() or not self.workload_ref.strip():
            raise ValueError("trial case and workload are required")
        names = [name for name, _ in self.metrics]
        if not names or len(names) != len(set(names)):
            raise ValueError("trial metrics must be non-empty and unique")
        if not self.evidence_refs:
            raise ValueError("trial evidence references are required")

    @property
    def measured(self) -> dict[str, float]:
        return dict(self.metrics)


@dataclass(frozen=True)
class DecisionReceipt:
    """Step 6: a version-bound architecture decision and its reopen triggers."""

    decision_id: str
    version: int
    status: DecisionStatus
    selected_candidate: str | None
    reason: str
    evidence_refs: tuple[str, ...]
    reopen_triggers: tuple[str, ...]
    prior_receipt_digest: str | None = None

    @property
    def digest(self) -> str:
        payload = json.dumps(
            asdict(self),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode()).hexdigest()[:16]


def review_candidate(candidate: CandidateArchitecture) -> tuple[MethodFinding, ...]:
    """Check pattern ownership and seam compatibility before any trial runs."""

    findings: list[MethodFinding] = []
    patterns = {binding.pattern_name: binding for binding in candidate.patterns}
    producers: dict[str, list[str]] = {}
    for binding in candidate.patterns:
        for artifact in binding.produces:
            producers.setdefault(artifact, []).append(binding.pattern_name)

    for artifact, owners in producers.items():
        if len(owners) > 1:
            findings.append(
                MethodFinding(
                    FindingSeverity.ERROR,
                    "multiple_writers",
                    f"{artifact!r} has multiple producers: {owners}",
                    candidate.candidate_id,
                )
            )

    seam_keys: set[tuple[str, str, str]] = set()
    for seam in candidate.seams:
        key = (seam.artifact, seam.producer, seam.consumer)
        if key in seam_keys:
            findings.append(
                MethodFinding(
                    FindingSeverity.ERROR,
                    "duplicate_seam",
                    f"duplicate seam contract for {key}",
                    candidate.candidate_id,
                )
            )
            continue
        seam_keys.add(key)

        producer = patterns.get(seam.producer)
        consumer = patterns.get(seam.consumer)
        if producer is None or consumer is None:
            findings.append(
                MethodFinding(
                    FindingSeverity.ERROR,
                    "unknown_seam_endpoint",
                    f"seam endpoints must be patterns in {candidate.candidate_id}",
                    candidate.candidate_id,
                )
            )
            continue
        if seam.artifact not in producer.produces and seam.artifact not in producer.mutates:
            findings.append(
                MethodFinding(
                    FindingSeverity.ERROR,
                    "producer_contract_mismatch",
                    f"{seam.producer} does not produce or mutate {seam.artifact!r}",
                    candidate.candidate_id,
                )
            )
        if seam.artifact not in consumer.consumes:
            findings.append(
                MethodFinding(
                    FindingSeverity.ERROR,
                    "consumer_contract_mismatch",
                    f"{seam.consumer} does not consume {seam.artifact!r}",
                    candidate.candidate_id,
                )
            )
        if seam.owner not in (seam.producer, seam.consumer):
            findings.append(
                MethodFinding(
                    FindingSeverity.ERROR,
                    "invalid_seam_owner",
                    f"{seam.owner} is not an endpoint of the {seam.artifact!r} seam",
                    candidate.candidate_id,
                )
            )
        writers = [
            binding.pattern_name
            for binding in candidate.patterns
            if seam.artifact in binding.produces or seam.artifact in binding.mutates
        ]
        if seam.mutation_policy is MutationPolicy.APPEND_ONLY and any(
            seam.artifact in patterns[name].mutates for name in writers
        ):
            findings.append(
                MethodFinding(
                    FindingSeverity.ERROR,
                    "append_only_rewrite",
                    f"{seam.artifact!r} is append-only but is mutated by {writers}",
                    candidate.candidate_id,
                )
            )

    for producer in candidate.patterns:
        for artifact in producer.produces:
            for consumer in candidate.patterns:
                if producer is consumer or artifact not in consumer.consumes:
                    continue
                key = (artifact, producer.pattern_name, consumer.pattern_name)
                if key not in seam_keys:
                    findings.append(
                        MethodFinding(
                            FindingSeverity.ERROR,
                            "missing_seam_contract",
                            (
                                f"{producer.pattern_name} -> {consumer.pattern_name} "
                                f"passes {artifact!r} without a seam contract"
                            ),
                            candidate.candidate_id,
                        )
                    )

    return tuple(findings)


class SixStepSession:
    """Enforce evidence order without pretending to choose the architecture."""

    def __init__(
        self,
        decision_id: str,
        *,
        version: int = 1,
        prior_receipt_digest: str | None = None,
    ) -> None:
        if not decision_id.strip():
            raise ValueError("decision_id must not be empty")
        if version < 1:
            raise ValueError("version must be >= 1")
        self.decision_id = decision_id
        self.version = version
        self.prior_receipt_digest = prior_receipt_digest
        self.current_step: MethodStep | None = None
        self.problem: BoundDecision | None = None
        self.baseline: BaselineEvidence | None = None
        self.diagnoses: tuple[ConstraintDiagnosis, ...] = ()
        self.candidates: tuple[CandidateArchitecture, ...] = ()
        self.findings: tuple[MethodFinding, ...] = ()
        self.experiments: tuple[ExperimentCase, ...] = ()
        self.trial_ready_ids: tuple[str, ...] = ()
        self.receipt: DecisionReceipt | None = None

    def _expect(self, expected: MethodStep | None) -> None:
        if self.current_step is not expected:
            actual = self.current_step.value if self.current_step else "not_started"
            wanted = expected.value if expected else "not_started"
            raise RuntimeError(f"expected step {wanted}, current step is {actual}")

    def bound(self, problem: BoundDecision) -> "SixStepSession":
        self._expect(None)
        self.problem = problem
        self.current_step = MethodStep.BOUND
        return self

    def record_baseline(self, baseline: BaselineEvidence) -> "SixStepSession":
        self._expect(MethodStep.BOUND)
        assert self.problem is not None
        if baseline.workload_ref != self.problem.workload_ref:
            raise ValueError("baseline must run on the bound workload")
        missing = [
            gate.metric
            for gate in self.problem.gates
            if gate.metric not in baseline.measured
        ]
        if missing:
            raise ValueError(f"baseline is missing quality metrics: {missing}")
        self.baseline = baseline
        self.current_step = MethodStep.BASELINE
        return self

    def diagnose(
        self,
        diagnoses: tuple[ConstraintDiagnosis, ...],
    ) -> "SixStepSession":
        self._expect(MethodStep.BASELINE)
        assert self.problem is not None
        if not diagnoses:
            raise ValueError("at least one constraint diagnosis is required")
        gate_names = {gate.metric for gate in self.problem.gates}
        unknown = sorted(
            {diagnosis.failed_gate for diagnosis in diagnoses} - gate_names
        )
        if unknown:
            raise ValueError(f"diagnoses reference unknown gates: {unknown}")
        codes = [diagnosis.code for diagnosis in diagnoses]
        if len(codes) != len(set(codes)):
            raise ValueError("diagnosis codes must be unique")
        self.diagnoses = diagnoses
        self.current_step = MethodStep.DIAGNOSE
        return self

    def generate_candidates(
        self,
        candidates: tuple[CandidateArchitecture, ...],
    ) -> "SixStepSession":
        self._expect(MethodStep.DIAGNOSE)
        if not candidates:
            raise ValueError("at least one candidate is required")
        candidate_ids = [candidate.candidate_id for candidate in candidates]
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("candidate ids must be unique")
        diagnosis_codes = {diagnosis.code for diagnosis in self.diagnoses}
        for candidate in candidates:
            unknown = sorted(set(candidate.targets) - diagnosis_codes)
            if unknown:
                raise ValueError(
                    f"{candidate.candidate_id} targets unknown diagnoses: {unknown}"
                )
        self.candidates = candidates
        self.current_step = MethodStep.CANDIDATES
        return self

    def specify_seams_and_trials(
        self,
        experiments: tuple[ExperimentCase, ...],
    ) -> "SixStepSession":
        self._expect(MethodStep.CANDIDATES)
        assert self.problem is not None
        candidate_by_id = {
            candidate.candidate_id: candidate for candidate in self.candidates
        }
        findings = [
            finding
            for candidate in self.candidates
            for finding in review_candidate(candidate)
        ]
        blocked = {
            finding.candidate_id
            for finding in findings
            if finding.severity is FindingSeverity.ERROR
        }
        trial_ready = tuple(
            candidate_id
            for candidate_id in candidate_by_id
            if candidate_id not in blocked
        )
        if not trial_ready:
            raise ValueError("every candidate failed seam review")

        cases_by_candidate: dict[str, list[ExperimentCase]] = {}
        case_ids: set[str] = set()
        for case in experiments:
            if case.case_id in case_ids:
                raise ValueError(f"duplicate experiment case: {case.case_id}")
            case_ids.add(case.case_id)
            if case.candidate_id not in trial_ready:
                raise ValueError(
                    f"experiment {case.case_id} targets a blocked or unknown candidate"
                )
            if case.workload_ref != self.problem.workload_ref:
                raise ValueError("all experiments must use the bound workload")
            cases_by_candidate.setdefault(case.candidate_id, []).append(case)

        for candidate_id in trial_ready:
            candidate = candidate_by_id[candidate_id]
            cases = cases_by_candidate.get(candidate_id, [])
            full_cases = [case for case in cases if case.removed_pattern is None]
            if len(full_cases) != 1:
                raise ValueError(
                    f"{candidate_id} needs exactly one full-bundle experiment"
                )
            removed = {
                case.removed_pattern
                for case in cases
                if case.removed_pattern is not None
            }
            pattern_names = {
                pattern.pattern_name for pattern in candidate.patterns
            }
            missing_ablations = sorted(pattern_names - removed)
            if len(pattern_names) > 1 and missing_ablations:
                raise ValueError(
                    f"{candidate_id} lacks ablations for {missing_ablations}"
                )
            unknown_ablations = sorted(removed - pattern_names)
            if unknown_ablations:
                raise ValueError(
                    f"{candidate_id} removes unknown patterns: {unknown_ablations}"
                )

        self.findings = tuple(findings)
        self.experiments = experiments
        self.trial_ready_ids = trial_ready
        self.current_step = MethodStep.SEAMS_AND_TRIALS
        return self

    def decide(
        self,
        results: tuple[TrialResult, ...],
        *,
        reopen_triggers: tuple[str, ...],
    ) -> DecisionReceipt:
        self._expect(MethodStep.SEAMS_AND_TRIALS)
        assert self.problem is not None
        assert self.baseline is not None
        if not reopen_triggers:
            raise ValueError("decision receipts require reopen triggers")

        result_by_case = {result.case_id: result for result in results}
        if len(result_by_case) != len(results):
            raise ValueError("trial result case ids must be unique")
        expected_case_ids = {case.case_id for case in self.experiments}
        if set(result_by_case) != expected_case_ids:
            missing = sorted(expected_case_ids - set(result_by_case))
            extra = sorted(set(result_by_case) - expected_case_ids)
            raise ValueError(f"trial result mismatch: missing={missing} extra={extra}")
        if any(
            result.workload_ref != self.problem.workload_ref
            for result in results
        ):
            raise ValueError("all trial results must use the bound workload")

        baseline_passes = self._passes(self.baseline.measured)
        evidence_refs = list(self.baseline.evidence_refs)
        evidence_refs.extend(
            ref
            for result in results
            for ref in result.evidence_refs
        )

        qualified: list[str] = []
        unearned: list[str] = []
        for candidate_id in self.trial_ready_ids:
            cases = [
                case
                for case in self.experiments
                if case.candidate_id == candidate_id
            ]
            full_case = next(
                case for case in cases if case.removed_pattern is None
            )
            full_result = result_by_case[full_case.case_id]
            full_passes = (
                self._passes(full_result.measured)
                and not full_result.observed_failures
            )
            ablations = [
                result_by_case[case.case_id]
                for case in cases
                if case.removed_pattern is not None
            ]
            redundant = [
                case.removed_pattern
                for case in cases
                if case.removed_pattern is not None
                and self._passes(result_by_case[case.case_id].measured)
                and not result_by_case[case.case_id].observed_failures
            ]
            if full_passes and ablations and redundant:
                unearned.append(
                    f"{candidate_id}: removing {sorted(redundant)} still passed"
                )
                continue
            if full_passes:
                qualified.append(candidate_id)

        if baseline_passes:
            status = DecisionStatus.KEEP_BASELINE
            selected = self.baseline.baseline_id
            reason = "The smallest viable baseline already satisfies every gate."
        elif len(qualified) == 1:
            status = DecisionStatus.ADOPT_CANDIDATE
            selected = qualified[0]
            reason = "One candidate passed every gate and its ablations failed."
        elif len(qualified) > 1:
            status = DecisionStatus.NEEDS_REVIEW
            selected = None
            reason = (
                "Multiple candidates passed. A human must decide the remaining "
                "cost and risk tradeoff."
            )
        else:
            status = DecisionStatus.REJECT_ALL
            selected = None
            reason = "No candidate earned adoption."
            if unearned:
                reason += " " + " | ".join(unearned)

        self.receipt = DecisionReceipt(
            decision_id=self.decision_id,
            version=self.version,
            status=status,
            selected_candidate=selected,
            reason=reason,
            evidence_refs=tuple(dict.fromkeys(evidence_refs)),
            reopen_triggers=reopen_triggers,
            prior_receipt_digest=self.prior_receipt_digest,
        )
        self.current_step = MethodStep.DECIDE
        return self.receipt

    def reopen(self, reason: str) -> "SixStepSession":
        self._expect(MethodStep.DECIDE)
        if not reason.strip():
            raise ValueError("reopen reason must not be empty")
        assert self.receipt is not None
        return SixStepSession(
            self.decision_id,
            version=self.version + 1,
            prior_receipt_digest=self.receipt.digest,
        )

    def _passes(self, metrics: Mapping[str, float]) -> bool:
        assert self.problem is not None
        return all(gate.passes(metrics) for gate in self.problem.gates)

