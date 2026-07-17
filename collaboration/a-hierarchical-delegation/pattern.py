"""Hierarchical Delegation pattern.

A stable supervisor decomposes one root contract into non-overlapping child
contracts, dispatches each child through an isolated handoff, and accepts only
contract-bound artifacts. Batch receipts preserve local decisions. A second
portfolio receipt checks facts that no single worker can see, such as roster
coverage and the aggregate cash limit.

The transport-neutral collaboration chain is:

``TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt``

This module adds the hierarchical topology: one root contract, many child
contracts, batch-level admission, and portfolio-level admission. The dispatch
callable remains the framework seam for LangGraph, an agent SDK, or a test
double.
"""
from __future__ import annotations

import asyncio
import hashlib
import sys
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
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


class Verdict(str, Enum):
    """Worker outcome. Partial and failed batches cannot be auto-admitted."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"


def batch_fingerprint(employee_ids: Sequence[str]) -> str:
    """Return a stable digest for the exact roster slice assigned to a worker."""
    canonical = "\n".join(sorted(employee_ids))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class SalaryBatchResult:
    """Business payload carried inside a contract-bound artifact envelope."""

    batch_id: str
    verdict: Verdict
    employee_count: int
    total_amount: float
    input_fingerprint: str
    anomalies: tuple[str, ...] = ()
    needs_review: tuple[str, ...] = ()
    confidence: float = 1.0
    failure_code: str | None = None
    retryable: bool = False
    attempt: int = 1

    def __post_init__(self) -> None:
        if not self.batch_id:
            raise ValueError("batch_id must not be empty")
        if self.employee_count < 0:
            raise ValueError("employee_count must not be negative")
        if self.total_amount < 0:
            raise ValueError("total_amount must not be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.input_fingerprint:
            raise ValueError("input_fingerprint must not be empty")
        if self.attempt < 1:
            raise ValueError("attempt must be at least 1")
        if self.verdict is Verdict.FAILURE and not self.failure_code:
            raise ValueError("failed results must preserve a failure_code")
        if self.verdict is not Verdict.FAILURE and self.failure_code:
            raise ValueError("only failed results may carry a failure_code")


@dataclass(frozen=True)
class BatchAssignment:
    """One isolated worker handoff plus the exact rows named by its contract."""

    handoff: HandoffEnvelope
    rows: tuple[Row, ...]

    def __post_init__(self) -> None:
        if self.handoff.contract.output_schema != "SalaryBatchResult":
            raise ValueError("batch contract must request SalaryBatchResult")

    @property
    def batch_id(self) -> str:
        return self.handoff.contract.contract_id


def bind_salary_result(
    handoff: HandoffEnvelope,
    result: SalaryBatchResult,
    *,
    artifact_id: str | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> ArtifactEnvelope[SalaryBatchResult]:
    """Bind a salary payload to the exact child contract that produced it."""
    return ArtifactEnvelope.bind(
        handoff,
        artifact_id=artifact_id
        or f"artifact::{handoff.contract.contract_id}::attempt-{handoff.attempt}",
        produced_by=handoff.receiver,
        payload=result,
        evidence_refs=evidence_refs,
    )


Dispatch = Callable[
    [HandoffEnvelope, tuple[Row, ...]],
    Awaitable[ArtifactEnvelope[SalaryBatchResult]],
]


@dataclass(frozen=True)
class SafetyBoundary:
    """Batch admission policy that returns evidence-bearing acceptance receipts."""

    amount_threshold: float = 100_000
    min_confidence: float = 0.85
    require_evidence: bool = True

    def __post_init__(self) -> None:
        if self.amount_threshold <= 0:
            raise ValueError("amount_threshold must be positive")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")

    def evaluate(
        self,
        handoff: HandoffEnvelope,
        artifact: ArtifactEnvelope[SalaryBatchResult],
    ) -> AcceptanceReceipt:
        contract = handoff.contract
        findings: list[Finding] = []

        def add(code: str, field: str, message: str, evidence: str) -> None:
            findings.append(
                Finding(
                    code=code,
                    field=field,
                    message=message,
                    evidence=evidence,
                )
            )

        if artifact.contract_digest != contract.digest:
            add(
                "contract_digest_mismatch",
                "contract_digest",
                "artifact belongs to another task contract version",
                f"expected={contract.digest} observed={artifact.contract_digest}",
            )
        if artifact.schema != contract.output_schema:
            add(
                "schema_mismatch",
                "schema",
                "artifact schema does not match the contract",
                f"expected={contract.output_schema} observed={artifact.schema}",
            )
        if artifact.produced_by != handoff.receiver:
            add(
                "producer_mismatch",
                "produced_by",
                "artifact was not produced by the designated receiver",
                f"expected={handoff.receiver} observed={artifact.produced_by}",
            )
        if self.require_evidence and not artifact.evidence_refs:
            add(
                "missing_evidence",
                "evidence_refs",
                "artifact has no durable evidence reference",
                "evidence_refs=()",
            )

        result = artifact.payload
        if not isinstance(result, SalaryBatchResult):
            add(
                "payload_type_mismatch",
                "payload",
                "artifact payload is not a SalaryBatchResult",
                f"observed_type={type(result).__name__}",
            )
        else:
            expected_count = len(contract.input_refs)
            expected_fingerprint = batch_fingerprint(contract.input_refs)
            if result.batch_id != contract.contract_id:
                add(
                    "batch_id_mismatch",
                    "batch_id",
                    "worker result names a different batch",
                    f"expected={contract.contract_id} observed={result.batch_id}",
                )
            if result.employee_count != expected_count:
                add(
                    "roster_count_mismatch",
                    "employee_count",
                    "worker result does not cover the contracted roster slice",
                    f"expected={expected_count} observed={result.employee_count}",
                )
            if result.input_fingerprint != expected_fingerprint:
                add(
                    "roster_fingerprint_mismatch",
                    "input_fingerprint",
                    "worker result was computed from a different roster slice",
                    f"expected={expected_fingerprint} observed={result.input_fingerprint}",
                )
            if result.total_amount > self.amount_threshold:
                add(
                    "amount_threshold_exceeded",
                    "total_amount",
                    "batch amount requires human review",
                    f"threshold={self.amount_threshold} observed={result.total_amount}",
                )
            if result.confidence < self.min_confidence:
                add(
                    "confidence_below_floor",
                    "confidence",
                    "worker confidence is below the admission floor",
                    f"floor={self.min_confidence} observed={result.confidence}",
                )
            if result.needs_review:
                add(
                    "worker_requested_review",
                    "needs_review",
                    "worker surfaced rows that require human review",
                    f"employee_ids={','.join(result.needs_review)}",
                )
            if result.verdict is not Verdict.SUCCESS:
                add(
                    "worker_not_successful",
                    "verdict",
                    "partial or failed work cannot be auto-admitted",
                    (
                        f"verdict={result.verdict.value} "
                        f"failure_code={result.failure_code or 'n/a'}"
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
            checked_by="batch-safety-boundary",
            decision=decision,
            findings=tuple(findings),
        )


@dataclass(frozen=True)
class PayrollPortfolioResult:
    """Supervisor synthesis over every child artifact and batch receipt."""

    claimed_total_amount: float
    admitted_total_amount: float
    employee_count: int
    auto_approved: tuple[str, ...]
    human_review: tuple[str, ...]
    child_receipt_ids: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioBoundary:
    """Global admission policy for facts invisible to any one batch worker."""

    max_total_amount: float | None = None
    require_all_batches_accepted: bool = True

    def __post_init__(self) -> None:
        if self.max_total_amount is not None and self.max_total_amount <= 0:
            raise ValueError("max_total_amount must be positive when provided")

    def evaluate(
        self,
        root_contract: TaskContract,
        artifact: ArtifactEnvelope[PayrollPortfolioResult],
    ) -> AcceptanceReceipt:
        result = artifact.payload
        findings: list[Finding] = []

        def add(code: str, field: str, message: str, evidence: str) -> None:
            findings.append(
                Finding(
                    code=code,
                    field=field,
                    message=message,
                    evidence=evidence,
                )
            )

        if artifact.contract_digest != root_contract.digest:
            add(
                "root_contract_digest_mismatch",
                "contract_digest",
                "portfolio belongs to another root contract version",
                f"expected={root_contract.digest} observed={artifact.contract_digest}",
            )
        if artifact.schema != root_contract.output_schema:
            add(
                "portfolio_schema_mismatch",
                "schema",
                "portfolio schema does not match the root contract",
                f"expected={root_contract.output_schema} observed={artifact.schema}",
            )
        expected_count = len(root_contract.input_refs)
        if result.employee_count != expected_count:
            add(
                "portfolio_coverage_mismatch",
                "employee_count",
                "child artifacts do not cover the root roster",
                f"expected={expected_count} observed={result.employee_count}",
            )
        if (
            self.max_total_amount is not None
            and result.claimed_total_amount > self.max_total_amount
        ):
            add(
                "portfolio_amount_exceeded",
                "claimed_total_amount",
                "combined batch amount exceeds the portfolio limit",
                (
                    f"limit={self.max_total_amount} "
                    f"observed={result.claimed_total_amount}"
                ),
            )
        if self.require_all_batches_accepted and result.human_review:
            add(
                "child_batches_unresolved",
                "human_review",
                "the root contract still has unresolved child batches",
                f"batch_ids={','.join(result.human_review)}",
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
            checked_by="portfolio-safety-boundary",
            decision=decision,
            findings=tuple(findings),
        )


@dataclass(frozen=True)
class DelegationSummary:
    """Complete evidence for one hierarchical delegation run."""

    root_contract: TaskContract
    batch_artifacts: tuple[ArtifactEnvelope[SalaryBatchResult], ...]
    batch_receipts: tuple[AcceptanceReceipt, ...]
    portfolio_artifact: ArtifactEnvelope[PayrollPortfolioResult]
    portfolio_receipt: AcceptanceReceipt

    @property
    def total(self) -> float:
        return self.portfolio_artifact.payload.admitted_total_amount

    @property
    def employee_count(self) -> int:
        return self.portfolio_artifact.payload.employee_count

    @property
    def auto_approved(self) -> tuple[str, ...]:
        return self.portfolio_artifact.payload.auto_approved

    @property
    def human_review(self) -> tuple[str, ...]:
        return self.portfolio_artifact.payload.human_review


class SettlementSupervisor:
    """Decompose, dispatch, synthesize, and gate; never compute line work."""

    def __init__(
        self,
        dispatch: Dispatch,
        boundary: SafetyBoundary | None = None,
        portfolio_boundary: PortfolioBoundary | None = None,
        *,
        max_concurrent: int = 5,
        worker_timeout: float = 120.0,
    ):
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        if worker_timeout <= 0:
            raise ValueError("worker_timeout must be positive")
        self.dispatch = dispatch
        self.boundary = boundary or SafetyBoundary()
        self.portfolio_boundary = portfolio_boundary or PortfolioBoundary()
        self._sem = asyncio.Semaphore(max_concurrent)
        self.worker_timeout = worker_timeout

    def root_contract(self, roster: Sequence[Row]) -> TaskContract:
        return TaskContract(
            contract_id="payroll::month-end",
            version=1,
            objective="settle payroll for every employee in the roster",
            output_schema="PayrollPortfolioResult",
            accountable_owner="settlement-supervisor",
            input_refs=tuple(str(row["id"]) for row in roster),
            constraints=("every employee must belong to exactly one child contract",),
            allowed_tools=("delegate_payroll_batch",),
            authority_scope=("read:roster", "propose:payroll-settlement"),
            boundary="supervisor may coordinate and admit; it must not compute line pay",
            budget=ExecutionBudget(
                max_attempts=1,
                timeout_seconds=max(1, int(self.worker_timeout)),
            ),
        )

    def decompose(
        self,
        roster: Sequence[Row],
        root_contract: TaskContract | None = None,
    ) -> list[BatchAssignment]:
        """Partition the root roster into disjoint child contracts."""
        root = root_contract or self.root_contract(roster)
        by_client: dict[str, list[Row]] = {}
        for row in roster:
            by_client.setdefault(str(row["client"]), []).append(row)

        assignments: list[BatchAssignment] = []
        for client in sorted(by_client):
            rows = tuple(by_client[client])
            contract = TaskContract(
                contract_id=f"batch::{client}",
                version=root.version,
                objective=f"compute payroll for {client} only",
                output_schema="SalaryBatchResult",
                accountable_owner=f"payroll-worker::{client}",
                input_refs=tuple(str(row["id"]) for row in rows),
                constraints=(
                    f"parent_contract_digest={root.digest}",
                    "return one contract-bound artifact",
                ),
                allowed_tools=("read_roster", "calc_salary"),
                authority_scope=("read:assigned-roster", "compute:salary"),
                boundary="only this batch; never read another batch or write the HR DB",
                budget=ExecutionBudget(
                    max_attempts=1,
                    timeout_seconds=max(1, int(self.worker_timeout)),
                ),
            )
            handoff = HandoffEnvelope(
                handoff_id=f"handoff::{contract.contract_id}",
                sender=root.accountable_owner,
                receiver=contract.accountable_owner,
                contract=contract,
            )
            assignments.append(BatchAssignment(handoff=handoff, rows=rows))
        return assignments

    async def _run_one(
        self,
        assignment: BatchAssignment,
    ) -> ArtifactEnvelope[SalaryBatchResult]:
        handoff = assignment.handoff
        async with self._sem:
            try:
                artifact = await asyncio.wait_for(
                    self.dispatch(handoff, assignment.rows),
                    self.worker_timeout,
                )
                if not isinstance(artifact, ArtifactEnvelope):
                    raise TypeError("dispatch must return an ArtifactEnvelope")
                return artifact
            except Exception as exc:
                result = SalaryBatchResult(
                    batch_id=handoff.contract.contract_id,
                    verdict=Verdict.FAILURE,
                    employee_count=len(assignment.rows),
                    total_amount=0.0,
                    input_fingerprint=batch_fingerprint(handoff.contract.input_refs),
                    needs_review=handoff.contract.input_refs,
                    confidence=0.0,
                    failure_code=f"{type(exc).__name__}: {exc}",
                    retryable=isinstance(exc, (TimeoutError, asyncio.TimeoutError)),
                    attempt=handoff.attempt,
                )
                return bind_salary_result(
                    handoff,
                    result,
                    evidence_refs=(f"runtime://{handoff.handoff_id}",),
                )

    async def run(
        self,
        roster: Sequence[Row],
        root_contract: TaskContract | None = None,
    ) -> DelegationSummary:
        root = root_contract or self.root_contract(roster)
        assignments = self.decompose(roster, root)
        artifacts = tuple(
            await asyncio.gather(
                *(self._run_one(assignment) for assignment in assignments)
            )
        )
        receipts = tuple(
            self.boundary.evaluate(assignment.handoff, artifact)
            for assignment, artifact in zip(assignments, artifacts, strict=True)
        )
        return self.synthesize(root, artifacts, receipts)

    def synthesize(
        self,
        root_contract: TaskContract,
        artifacts: tuple[ArtifactEnvelope[SalaryBatchResult], ...],
        receipts: tuple[AcceptanceReceipt, ...],
    ) -> DelegationSummary:
        """Create a root artifact, then apply checks no child can perform alone."""
        accepted_ids = {
            receipt.artifact_id
            for receipt in receipts
            if receipt.decision is AcceptanceDecision.ACCEPTED
        }
        auto_approved = tuple(
            artifact.payload.batch_id
            for artifact in artifacts
            if artifact.artifact_id in accepted_ids
        )
        human_review = tuple(
            artifact.payload.batch_id
            for artifact in artifacts
            if artifact.artifact_id not in accepted_ids
        )

        result = PayrollPortfolioResult(
            claimed_total_amount=round(
                sum(artifact.payload.total_amount for artifact in artifacts),
                2,
            ),
            admitted_total_amount=round(
                sum(
                    artifact.payload.total_amount
                    for artifact in artifacts
                    if artifact.artifact_id in accepted_ids
                ),
                2,
            ),
            employee_count=sum(
                artifact.payload.employee_count for artifact in artifacts
            ),
            auto_approved=auto_approved,
            human_review=human_review,
            child_receipt_ids=tuple(receipt.receipt_id for receipt in receipts),
        )
        portfolio_artifact = ArtifactEnvelope(
            artifact_id=f"artifact::{root_contract.contract_id}",
            contract_digest=root_contract.digest,
            schema=root_contract.output_schema,
            produced_by=root_contract.accountable_owner,
            payload=result,
            evidence_refs=result.child_receipt_ids,
        )
        portfolio_receipt = self.portfolio_boundary.evaluate(
            root_contract,
            portfolio_artifact,
        )
        return DelegationSummary(
            root_contract=root_contract,
            batch_artifacts=artifacts,
            batch_receipts=receipts,
            portfolio_artifact=portfolio_artifact,
            portfolio_receipt=portfolio_receipt,
        )
