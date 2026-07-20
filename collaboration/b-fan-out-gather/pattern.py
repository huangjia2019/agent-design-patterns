"""Fan-out / Gather pattern.

Several independent sources answer one contracted question in parallel.
Every source must return a contract-bound artifact.
The gather must apply explicit comparison or contribution semantics.
The output is one typed reconciliation report with an acceptance receipt.

The shared collaboration chain remains:

``TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt``

This module adds the parallel topology: source contracts, source admission,
competing or additive aggregation, conflict resolution, seam review, and a final
root receipt. Fan-out is deliberately small; gather owns the semantics.
"""
from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from collaboration.boundary_contract import (  # noqa: E402
    AcceptanceDecision,
    AcceptanceReceipt,
    ArtifactEnvelope,
    ExecutionBudget,
    Finding,
    HandoffEnvelope,
    TaskContract,
)


Row = Mapping[str, object]


class Strategy(str, Enum):
    """Whether workers contribute facets or compete on the same fact."""

    ADDITIVE = "additive"
    COMPETING = "competing"


class Layer(str, Enum):
    """Where one compared line item lands."""

    AGREE = "agree"
    ATTRIBUTABLE = "attributable"
    UNEXPLAINED = "unexplained"


class ContributionRule(str, Enum):
    """How contributions under one canonical identity become one value."""

    SUM = "sum"
    MAX = "max"
    COUNT_SOURCES = "count-sources"


class ReconciliationStatus(str, Enum):
    RECONCILED = "reconciled"
    INSUFFICIENT_SOURCES = "insufficient_sources"


@dataclass(frozen=True)
class Tolerance:
    """Absolute and relative tolerance for competing numeric readings."""

    absolute: float = 1.0
    relative: float = 0.0

    def __post_init__(self) -> None:
        if self.absolute < 0 or self.relative < 0:
            raise ValueError("tolerances must not be negative")

    def matches(self, low: float, high: float) -> bool:
        span = abs(high - low)
        allowed = max(
            self.absolute,
            max(abs(low), abs(high)) * self.relative,
        )
        return span <= allowed


@dataclass(frozen=True)
class SourceSpec:
    """Comparable source identity, scope, and expected output contract."""

    source_id: str
    snapshot_ref: str
    period: str
    unit: str
    boundary: str
    required: bool = True
    expected_items: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    authority_scope: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = (
            self.source_id,
            self.snapshot_ref,
            self.period,
            self.unit,
            self.boundary,
        )
        if not all(value.strip() for value in required):
            raise ValueError("source identity, snapshot, period, unit, and boundary are required")
        if len(self.expected_items) != len(set(self.expected_items)):
            raise ValueError("expected_items must not contain duplicates")


@dataclass(frozen=True)
class SourceResult:
    """Immutable source reading carried inside an artifact envelope."""

    source_id: str
    snapshot_ref: str
    period: str
    unit: str
    line_items: tuple[tuple[str, float], ...] = ()
    confidence: float = 1.0
    failure_code: str | None = None
    retryable: bool = False

    def __post_init__(self) -> None:
        required = (self.source_id, self.snapshot_ref, self.period, self.unit)
        if not all(value.strip() for value in required):
            raise ValueError("source reading identity fields must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        keys = [item for item, _ in self.line_items]
        if len(keys) != len(set(keys)):
            raise ValueError("line_items must not contain duplicate keys")
        if self.failure_code and self.line_items:
            raise ValueError("failed source readings must not carry business values")

    @classmethod
    def from_mapping(
        cls,
        *,
        source_id: str,
        snapshot_ref: str,
        period: str,
        unit: str,
        line_items: Mapping[str, float],
        confidence: float = 1.0,
    ) -> SourceResult:
        return cls(
            source_id=source_id,
            snapshot_ref=snapshot_ref,
            period=period,
            unit=unit,
            line_items=tuple(sorted(line_items.items())),
            confidence=confidence,
        )

    @property
    def ok(self) -> bool:
        return self.failure_code is None

    @property
    def values(self) -> dict[str, float]:
        return dict(self.line_items)


@dataclass(frozen=True)
class ConflictResolution:
    selected_value: float
    rule: str
    evidence: str

    def __post_init__(self) -> None:
        if not self.rule.strip() or not self.evidence.strip():
            raise ValueError("conflict resolution must name its rule and evidence")


@dataclass(frozen=True)
class LineItemVerdict:
    """One compared item, its source evidence, and any explicit resolution."""

    item: str
    layer: Layer
    by_source: tuple[tuple[str, float], ...]
    gap: float = 0.0
    low_sources: tuple[str, ...] = ()
    high_sources: tuple[str, ...] = ()
    reason: str = ""
    resolution: ConflictResolution | None = None

    @property
    def values(self) -> dict[str, float]:
        return dict(self.by_source)


@dataclass(frozen=True)
class MergedItem:
    item: str
    value: float
    contributions: tuple[tuple[str, float], ...]
    raw_keys: tuple[str, ...]


@dataclass(frozen=True)
class ReconciliationReport:
    """Typed gather result. No conflict channel disappears into a loose dict."""

    status: ReconciliationStatus
    strategy: Strategy
    source_ids: tuple[str, ...]
    source_receipt_ids: tuple[str, ...] = ()
    verdicts: tuple[LineItemVerdict, ...] = ()
    merged_items: tuple[MergedItem, ...] = ()
    seam_findings: tuple[str, ...] = ()
    missing_required_sources: tuple[str, ...] = ()

    @property
    def agreed_items(self) -> tuple[str, ...]:
        return tuple(
            verdict.item
            for verdict in self.verdicts
            if verdict.layer is Layer.AGREE
        )

    @property
    def attributable_divergences(self) -> tuple[LineItemVerdict, ...]:
        return tuple(
            verdict
            for verdict in self.verdicts
            if verdict.layer is Layer.ATTRIBUTABLE
        )

    @property
    def to_human(self) -> tuple[LineItemVerdict, ...]:
        return tuple(
            verdict
            for verdict in self.verdicts
            if verdict.layer is Layer.UNEXPLAINED
            or (
                verdict.layer is Layer.ATTRIBUTABLE
                and verdict.resolution is None
            )
        )

    @property
    def merged(self) -> dict[str, float]:
        return {item.item: item.value for item in self.merged_items}

    @property
    def total(self) -> float:
        return round(sum(item.value for item in self.merged_items), 2)


ConflictResolver = Callable[[LineItemVerdict], ConflictResolution | None]
IdentityKey = Callable[[str], str]
SeamReviewer = Callable[[ReconciliationReport], tuple[str, ...]]


@dataclass(frozen=True)
class AggregatorPolicy:
    """Four gather questions encoded as executable policy."""

    strategy: Strategy = Strategy.COMPETING
    conflict_resolver: ConflictResolver | None = None
    identity_key: IdentityKey | None = None
    contribution_rule: ContributionRule = ContributionRule.SUM
    seam_reviewer: SeamReviewer | None = None
    tolerance: Tolerance = Tolerance()


@dataclass(frozen=True)
class SourceAdmissionPolicy:
    """Validate one source artifact before it can enter reconciliation."""

    min_confidence: float = 0.0
    require_evidence: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")

    def evaluate(
        self,
        spec: SourceSpec,
        handoff: HandoffEnvelope,
        artifact: ArtifactEnvelope[SourceResult],
    ) -> AcceptanceReceipt:
        findings: list[Finding] = []

        def add(code: str, field: str, evidence: str) -> None:
            findings.append(
                Finding(
                    code=code,
                    field=field,
                    message=code.replace("_", " "),
                    evidence=evidence,
                )
            )

        contract = handoff.contract
        if artifact.contract_digest != contract.digest:
            add(
                "contract_digest_mismatch",
                "contract_digest",
                f"expected={contract.digest} observed={artifact.contract_digest}",
            )
        if artifact.schema != contract.output_schema:
            add(
                "schema_mismatch",
                "schema",
                f"expected={contract.output_schema} observed={artifact.schema}",
            )
        if artifact.produced_by != handoff.receiver:
            add(
                "producer_mismatch",
                "produced_by",
                f"expected={handoff.receiver} observed={artifact.produced_by}",
            )
        if self.require_evidence and not artifact.evidence_refs:
            add("missing_evidence", "evidence_refs", "evidence_refs=()")

        result = artifact.payload
        if not isinstance(result, SourceResult):
            add(
                "payload_type_mismatch",
                "payload",
                f"observed_type={type(result).__name__}",
            )
        else:
            expected = {
                "source_id": spec.source_id,
                "snapshot_ref": spec.snapshot_ref,
                "period": spec.period,
                "unit": spec.unit,
            }
            observed = {
                "source_id": result.source_id,
                "snapshot_ref": result.snapshot_ref,
                "period": result.period,
                "unit": result.unit,
            }
            for field, value in expected.items():
                if observed[field] != value:
                    add(
                        f"{field}_mismatch",
                        field,
                        f"expected={value} observed={observed[field]}",
                    )
            missing_items = sorted(
                set(spec.expected_items) - set(result.values)
            )
            if missing_items:
                add(
                    "expected_items_missing",
                    "line_items",
                    f"missing={','.join(missing_items)}",
                )
            if result.confidence < self.min_confidence:
                add(
                    "confidence_below_floor",
                    "confidence",
                    f"floor={self.min_confidence} observed={result.confidence}",
                )
            if not result.ok:
                add(
                    "source_failed",
                    "failure_code",
                    (
                        f"failure_code={result.failure_code} "
                        f"retryable={result.retryable}"
                    ),
                )

        decision = (
            AcceptanceDecision.ACCEPTED
            if not findings
            else AcceptanceDecision.ESCALATED
        )
        return AcceptanceReceipt(
            receipt_id=f"receipt::{artifact.artifact_id}",
            contract_digest=contract.digest,
            artifact_id=artifact.artifact_id,
            checked_by="source-admission-policy",
            decision=decision,
            findings=tuple(findings),
        )


class Reconciler:
    """Gather accepted source readings according to explicit result semantics."""

    def __init__(
        self,
        policy: AggregatorPolicy | None = None,
        *,
        tol: float | None = None,
    ):
        self.policy = policy or AggregatorPolicy()
        if tol is not None:
            self.policy = replace(
                self.policy,
                tolerance=Tolerance(absolute=tol),
            )

    def reconcile(self, results: Sequence[SourceResult]) -> ReconciliationReport:
        if self.policy.strategy is Strategy.ADDITIVE:
            report = self._merge_additive(results)
        else:
            report = self._reconcile_competing(results)
        if self.policy.seam_reviewer:
            report = replace(
                report,
                seam_findings=tuple(self.policy.seam_reviewer(report)),
            )
        return report

    def _reconcile_competing(
        self,
        results: Sequence[SourceResult],
    ) -> ReconciliationReport:
        items = {item for result in results for item, _ in result.line_items}
        verdicts: list[LineItemVerdict] = []
        for item in sorted(items):
            pairs = [
                (result.source_id, result.values[item])
                for result in results
                if item in result.values
            ]
            by_source = tuple(sorted(pairs))
            if len(pairs) < 2:
                verdicts.append(
                    LineItemVerdict(
                        item=item,
                        layer=Layer.UNEXPLAINED,
                        by_source=by_source,
                        reason="single-source",
                    )
                )
                continue

            clusters = _cluster(pairs, self.policy.tolerance)
            if len(clusters) == 1:
                verdicts.append(
                    LineItemVerdict(
                        item=item,
                        layer=Layer.AGREE,
                        by_source=by_source,
                    )
                )
                continue
            if len(clusters) == 2:
                low, high = clusters
                verdict = LineItemVerdict(
                    item=item,
                    layer=Layer.ATTRIBUTABLE,
                    by_source=by_source,
                    gap=round(high[-1][1] - low[0][1], 2),
                    low_sources=tuple(source for source, _ in low),
                    high_sources=tuple(source for source, _ in high),
                    reason="two-source-clusters",
                )
                if self.policy.conflict_resolver:
                    verdict = replace(
                        verdict,
                        resolution=self.policy.conflict_resolver(verdict),
                    )
                verdicts.append(verdict)
                continue
            verdicts.append(
                LineItemVerdict(
                    item=item,
                    layer=Layer.UNEXPLAINED,
                    by_source=by_source,
                    gap=round(clusters[-1][-1][1] - clusters[0][0][1], 2),
                    reason="unexplained-divergence",
                )
            )

        return ReconciliationReport(
            status=ReconciliationStatus.RECONCILED,
            strategy=Strategy.COMPETING,
            source_ids=tuple(sorted(result.source_id for result in results)),
            verdicts=tuple(verdicts),
        )

    def _merge_additive(
        self,
        results: Sequence[SourceResult],
    ) -> ReconciliationReport:
        identity = self.policy.identity_key or (lambda item: item)
        grouped: dict[str, list[tuple[str, str, float]]] = {}
        for result in results:
            for raw_key, amount in result.line_items:
                grouped.setdefault(identity(raw_key), []).append(
                    (result.source_id, raw_key, amount)
                )

        merged: list[MergedItem] = []
        for item, contributions in sorted(grouped.items()):
            values = [amount for _, _, amount in contributions]
            if self.policy.contribution_rule is ContributionRule.MAX:
                value = max(values)
            elif self.policy.contribution_rule is ContributionRule.COUNT_SOURCES:
                value = float(len({source for source, _, _ in contributions}))
            else:
                value = sum(values)
            merged.append(
                MergedItem(
                    item=item,
                    value=round(value, 2),
                    contributions=tuple(
                        (source, amount)
                        for source, _, amount in contributions
                    ),
                    raw_keys=tuple(raw_key for _, raw_key, _ in contributions),
                )
            )

        return ReconciliationReport(
            status=ReconciliationStatus.RECONCILED,
            strategy=Strategy.ADDITIVE,
            source_ids=tuple(sorted(result.source_id for result in results)),
            merged_items=tuple(merged),
        )


@dataclass(frozen=True)
class AggregationBoundary:
    """Issue the root receipt for the assembled reconciliation report."""

    def evaluate(
        self,
        root_contract: TaskContract,
        artifact: ArtifactEnvelope[ReconciliationReport],
    ) -> AcceptanceReceipt:
        report = artifact.payload
        findings: list[Finding] = []

        def add(code: str, field: str, evidence: str) -> None:
            findings.append(
                Finding(
                    code=code,
                    field=field,
                    message=code.replace("_", " "),
                    evidence=evidence,
                )
            )

        if artifact.contract_digest != root_contract.digest:
            add(
                "root_contract_digest_mismatch",
                "contract_digest",
                f"expected={root_contract.digest} observed={artifact.contract_digest}",
            )
        if artifact.schema != root_contract.output_schema:
            add(
                "report_schema_mismatch",
                "schema",
                f"expected={root_contract.output_schema} observed={artifact.schema}",
            )
        if artifact.produced_by != root_contract.accountable_owner:
            add(
                "report_producer_mismatch",
                "produced_by",
                (
                    f"expected={root_contract.accountable_owner} "
                    f"observed={artifact.produced_by}"
                ),
            )
        if not artifact.evidence_refs:
            add(
                "report_evidence_missing",
                "evidence_refs",
                "evidence_refs=()",
            )
        if report.status is ReconciliationStatus.INSUFFICIENT_SOURCES:
            add(
                "insufficient_sources",
                "source_ids",
                (
                    f"accepted={','.join(report.source_ids)} "
                    f"missing_required={','.join(report.missing_required_sources)}"
                ),
            )
        for verdict in report.to_human:
            add(
                "unresolved_line_item",
                verdict.item,
                (
                    f"layer={verdict.layer.value} reason={verdict.reason} "
                    f"gap={verdict.gap}"
                ),
            )
        for index, finding in enumerate(report.seam_findings, start=1):
            add(
                "seam_finding",
                f"seam_findings[{index}]",
                finding,
            )

        decision = (
            AcceptanceDecision.ACCEPTED
            if not findings
            else AcceptanceDecision.ESCALATED
        )
        return AcceptanceReceipt(
            receipt_id=f"receipt::{artifact.artifact_id}",
            contract_digest=root_contract.digest,
            artifact_id=artifact.artifact_id,
            checked_by="aggregation-boundary",
            decision=decision,
            findings=tuple(findings),
        )


@dataclass(frozen=True)
class AggregationRun:
    root_contract: TaskContract
    source_artifacts: tuple[ArtifactEnvelope[SourceResult], ...]
    source_receipts: tuple[AcceptanceReceipt, ...]
    report_artifact: ArtifactEnvelope[ReconciliationReport]
    report_receipt: AcceptanceReceipt

    @property
    def report(self) -> ReconciliationReport:
        return self.report_artifact.payload


FanoutFn = Callable[
    [HandoffEnvelope, tuple[Row, ...]],
    Awaitable[ArtifactEnvelope[SourceResult]],
]


def bind_source_result(
    handoff: HandoffEnvelope,
    result: SourceResult,
    *,
    evidence_refs: tuple[str, ...],
    artifact_id: str | None = None,
) -> ArtifactEnvelope[SourceResult]:
    return ArtifactEnvelope.bind(
        handoff,
        artifact_id=artifact_id or f"artifact::{result.source_id}",
        produced_by=handoff.receiver,
        payload=result,
        evidence_refs=evidence_refs,
    )


class FanOutGather:
    """Fan out one root contract, admit source artifacts, then gather."""

    def __init__(
        self,
        sources: Sequence[tuple[SourceSpec, FanoutFn]],
        reconciler: Reconciler | None = None,
        source_policy: SourceAdmissionPolicy | None = None,
        aggregation_boundary: AggregationBoundary | None = None,
        *,
        max_concurrent: int = 5,
        worker_timeout: float = 90.0,
        min_success_rate: float = 0.95,
    ):
        if not sources:
            raise ValueError("at least one source is required")
        source_ids = [spec.source_id for spec, _ in sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("source ids must be unique")
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        if worker_timeout <= 0:
            raise ValueError("worker_timeout must be positive")
        if not 0.0 <= min_success_rate <= 1.0:
            raise ValueError("min_success_rate must be between 0 and 1")
        self.sources = tuple(sources)
        self.reconciler = reconciler or Reconciler()
        self.source_policy = source_policy or SourceAdmissionPolicy()
        self.aggregation_boundary = aggregation_boundary or AggregationBoundary()
        self._sem = asyncio.Semaphore(max_concurrent)
        self.worker_timeout = worker_timeout
        self.min_success_rate = min_success_rate

    def handoff_for(
        self,
        root_contract: TaskContract,
        spec: SourceSpec,
    ) -> HandoffEnvelope:
        contract = TaskContract(
            contract_id=f"source::{spec.source_id}",
            version=root_contract.version,
            objective=root_contract.objective,
            output_schema="SourceResult",
            accountable_owner=f"source-agent::{spec.source_id}",
            input_refs=(spec.snapshot_ref,),
            constraints=(
                f"parent_contract_digest={root_contract.digest}",
                f"period={spec.period}",
                f"unit={spec.unit}",
                f"expected_items={','.join(spec.expected_items)}",
            ),
            allowed_tools=spec.allowed_tools,
            authority_scope=spec.authority_scope,
            boundary=spec.boundary,
            budget=ExecutionBudget(
                max_attempts=1,
                timeout_seconds=max(1, int(self.worker_timeout)),
            ),
        )
        return HandoffEnvelope(
            handoff_id=f"handoff::{spec.source_id}",
            sender=root_contract.accountable_owner,
            receiver=contract.accountable_owner,
            contract=contract,
        )

    async def _run_one(
        self,
        spec: SourceSpec,
        handoff: HandoffEnvelope,
        fn: FanoutFn,
        rows: tuple[Row, ...],
    ) -> ArtifactEnvelope[SourceResult]:
        async with self._sem:
            try:
                artifact = await asyncio.wait_for(
                    fn(handoff, rows),
                    self.worker_timeout,
                )
                if not isinstance(artifact, ArtifactEnvelope):
                    raise TypeError("source must return an ArtifactEnvelope")
                return artifact
            except Exception as exc:
                result = SourceResult(
                    source_id=spec.source_id,
                    snapshot_ref=spec.snapshot_ref,
                    period=spec.period,
                    unit=spec.unit,
                    confidence=0.0,
                    failure_code=f"{type(exc).__name__}: {exc}",
                    retryable=isinstance(exc, (TimeoutError, asyncio.TimeoutError)),
                )
                return bind_source_result(
                    handoff,
                    result,
                    evidence_refs=(f"runtime://{handoff.handoff_id}",),
                )

    async def run(
        self,
        root_contract: TaskContract,
        rows: Sequence[Row],
    ) -> AggregationRun:
        handoffs = tuple(
            self.handoff_for(root_contract, spec)
            for spec, _ in self.sources
        )
        row_tuple = tuple(rows)
        artifacts = tuple(
            await asyncio.gather(
                *(
                    self._run_one(spec, handoff, fn, row_tuple)
                    for (spec, fn), handoff in zip(
                        self.sources,
                        handoffs,
                        strict=True,
                    )
                )
            )
        )
        receipts = tuple(
            self.source_policy.evaluate(spec, handoff, artifact)
            for (spec, _), handoff, artifact in zip(
                self.sources,
                handoffs,
                artifacts,
                strict=True,
            )
        )
        accepted = tuple(
            artifact.payload
            for artifact, receipt in zip(artifacts, receipts, strict=True)
            if receipt.decision is AcceptanceDecision.ACCEPTED
        )
        accepted_ids = {result.source_id for result in accepted}
        missing_required = tuple(
            spec.source_id
            for spec, _ in self.sources
            if spec.required and spec.source_id not in accepted_ids
        )
        success_rate = len(accepted) / len(self.sources)

        if missing_required or success_rate < self.min_success_rate:
            report = ReconciliationReport(
                status=ReconciliationStatus.INSUFFICIENT_SOURCES,
                strategy=self.reconciler.policy.strategy,
                source_ids=tuple(sorted(accepted_ids)),
                source_receipt_ids=tuple(
                    receipt.receipt_id for receipt in receipts
                ),
                missing_required_sources=missing_required,
            )
        else:
            report = replace(
                self.reconciler.reconcile(accepted),
                source_receipt_ids=tuple(
                    receipt.receipt_id for receipt in receipts
                ),
            )

        report_artifact = ArtifactEnvelope(
            artifact_id=f"artifact::{root_contract.contract_id}",
            contract_digest=root_contract.digest,
            schema=root_contract.output_schema,
            produced_by=root_contract.accountable_owner,
            payload=report,
            evidence_refs=report.source_receipt_ids,
        )
        report_receipt = self.aggregation_boundary.evaluate(
            root_contract,
            report_artifact,
        )
        return AggregationRun(
            root_contract=root_contract,
            source_artifacts=artifacts,
            source_receipts=receipts,
            report_artifact=report_artifact,
            report_receipt=report_receipt,
        )


def _cluster(
    pairs: Sequence[tuple[str, float]],
    tolerance: Tolerance,
) -> list[list[tuple[str, float]]]:
    """Cluster sorted values only while the full cluster range stays in tolerance."""
    ordered = sorted(pairs, key=lambda pair: pair[1])
    clusters: list[list[tuple[str, float]]] = []
    for pair in ordered:
        if not clusters or not tolerance.matches(clusters[-1][0][1], pair[1]):
            clusters.append([pair])
        else:
            clusters[-1].append(pair)
    return clusters
