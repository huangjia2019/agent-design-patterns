"""Shared boundary contract for collaboration patterns.

Collaboration patterns differ in topology, but every cross-agent transfer needs
the same four durable objects:

``TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt``

The contract is immutable and content-addressed. Artifacts and receipts bind to
that exact digest, so approval cannot drift to a different task version. This
module defines the transport-neutral interface; each pattern still owns how it
decomposes, dispatches, aggregates, challenges, or sequences work.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar


PayloadT = TypeVar("PayloadT")


class FindingSeverity(str, Enum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


class AcceptanceDecision(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class ExecutionBudget:
    max_attempts: int = 1
    timeout_seconds: int = 60
    max_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be at least 1")
        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError("max_tokens must be positive when provided")


@dataclass(frozen=True)
class TaskContract:
    """Versioned task ownership and admission requirements."""

    contract_id: str
    version: int
    objective: str
    output_schema: str
    accountable_owner: str
    input_refs: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    authority_scope: tuple[str, ...] = ()
    boundary: str = ""
    budget: ExecutionBudget = ExecutionBudget()

    def __post_init__(self) -> None:
        required = {
            "contract_id": self.contract_id,
            "objective": self.objective,
            "output_schema": self.output_schema,
            "accountable_owner": self.accountable_owner,
        }
        for name, value in required.items():
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
        if self.version < 1:
            raise ValueError("version must be at least 1")

    @property
    def digest(self) -> str:
        canonical = json.dumps(
            {
                "contract_id": self.contract_id,
                "version": self.version,
                "objective": self.objective,
                "output_schema": self.output_schema,
                "accountable_owner": self.accountable_owner,
                "input_refs": self.input_refs,
                "constraints": self.constraints,
                "allowed_tools": self.allowed_tools,
                "authority_scope": self.authority_scope,
                "boundary": self.boundary,
                "budget": {
                    "max_attempts": self.budget.max_attempts,
                    "timeout_seconds": self.budget.timeout_seconds,
                    "max_tokens": self.budget.max_tokens,
                },
            },
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class Finding:
    code: str
    field: str
    message: str
    evidence: str
    severity: FindingSeverity = FindingSeverity.BLOCKER

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("finding code must not be empty")
        if not self.evidence.strip():
            raise ValueError("findings must carry evidence")


@dataclass(frozen=True)
class AcceptanceReceipt:
    receipt_id: str
    contract_digest: str
    artifact_id: str
    checked_by: str
    decision: AcceptanceDecision
    findings: tuple[Finding, ...] = ()

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.receipt_id,
                self.contract_digest,
                self.artifact_id,
                self.checked_by,
            )
        ):
            raise ValueError("receipt identity fields must not be empty")
        blockers = [
            finding
            for finding in self.findings
            if finding.severity is FindingSeverity.BLOCKER
        ]
        if self.decision is AcceptanceDecision.ACCEPTED and blockers:
            raise ValueError("an accepted receipt cannot carry blocker findings")
        if self.decision is AcceptanceDecision.REJECTED and not blockers:
            raise ValueError("a rejected receipt must explain at least one blocker")

    @property
    def accepted(self) -> bool:
        return self.decision is AcceptanceDecision.ACCEPTED


@dataclass(frozen=True)
class HandoffEnvelope:
    """A valid handoff always carries the complete task contract."""

    handoff_id: str
    sender: str
    receiver: str
    contract: TaskContract
    attempt: int = 1
    prior_receipt: AcceptanceReceipt | None = None

    def __post_init__(self) -> None:
        if not all(
            value.strip() for value in (self.handoff_id, self.sender, self.receiver)
        ):
            raise ValueError("handoff identity fields must not be empty")
        if not 1 <= self.attempt <= self.contract.budget.max_attempts:
            raise ValueError("handoff attempt is outside the contract budget")
        if self.attempt == 1 and self.prior_receipt is not None:
            raise ValueError("a first attempt cannot carry a prior receipt")
        if self.attempt > 1 and self.prior_receipt is None:
            raise ValueError("a retry must carry the prior acceptance receipt")
        if (
            self.prior_receipt is not None
            and self.prior_receipt.contract_digest != self.contract.digest
        ):
            raise ValueError("prior receipt belongs to another contract version")
        if (
            self.prior_receipt is not None
            and self.prior_receipt.decision is AcceptanceDecision.ACCEPTED
        ):
            raise ValueError("an accepted artifact must not enter a repair retry")


@dataclass(frozen=True)
class ArtifactEnvelope(Generic[PayloadT]):
    """A result bound to the exact contract version that produced it."""

    artifact_id: str
    contract_digest: str
    schema: str
    produced_by: str
    payload: PayloadT
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not all(
            value.strip()
            for value in (
                self.artifact_id,
                self.contract_digest,
                self.schema,
                self.produced_by,
            )
        ):
            raise ValueError("artifact identity fields must not be empty")

    @classmethod
    def bind(
        cls,
        handoff: HandoffEnvelope,
        *,
        artifact_id: str,
        produced_by: str,
        payload: PayloadT,
        evidence_refs: tuple[str, ...] = (),
    ) -> ArtifactEnvelope[PayloadT]:
        """Bind a worker result to the exact contract carried by its handoff."""
        if produced_by != handoff.receiver:
            raise ValueError("only the designated receiver may bind this artifact")
        return cls(
            artifact_id=artifact_id,
            contract_digest=handoff.contract.digest,
            schema=handoff.contract.output_schema,
            produced_by=produced_by,
            payload=payload,
            evidence_refs=evidence_refs,
        )
