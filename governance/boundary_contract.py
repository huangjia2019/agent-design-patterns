"""Shared boundary contract for governance patterns.

Governance starts after an upstream component has produced a valid artifact.
Artifact acceptance does not grant authority to change the world. The durable
control chain is:

``ActionProposal -> PolicyRef -> GovernanceReceipt``

The proposal binds the requested effect to the exact task and artifact version
that produced it. Every receipt binds to both the proposal digest and the policy
digest used to decide it. A receipt therefore must not be transferred to a
changed proposal, inherited by a new policy version, or treated as timeless.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Mapping


class RiskLevel(IntEnum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Reversibility(str, Enum):
    REVERSIBLE = "reversible"
    COMPENSATABLE = "compensatable"
    IRREVERSIBLE = "irreversible"


class ControlDecision(str, Enum):
    ALLOWED = "allowed"
    PENDING = "pending"
    DENIED = "denied"
    REVOKED = "revoked"


class FindingSeverity(str, Enum):
    BLOCKER = "blocker"
    WARNING = "warning"
    INFO = "info"


def _digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def _instant(value: str) -> datetime:
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None:
        raise ValueError("governance timestamps must include a timezone")
    return instant


@dataclass(frozen=True)
class ActionProposal:
    """One requested external effect bound to an accepted upstream artifact."""

    proposal_id: str
    version: int
    contract_digest: str
    artifact_id: str
    artifact_digest: str
    requested_by: str
    action: str
    resource_scope: tuple[str, ...]
    idempotency_key: str
    risk: RiskLevel
    reversibility: Reversibility
    amount: float = 0.0
    subject_count: int = 0
    evidence_refs: tuple[str, ...] = ()
    attributes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        required = {
            "proposal_id": self.proposal_id,
            "contract_digest": self.contract_digest,
            "artifact_id": self.artifact_id,
            "artifact_digest": self.artifact_digest,
            "requested_by": self.requested_by,
            "action": self.action,
            "idempotency_key": self.idempotency_key,
        }
        for name, value in required.items():
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
        if self.version < 1:
            raise ValueError("version must be at least 1")
        if not self.resource_scope:
            raise ValueError("resource_scope must not be empty")
        if any(not value.strip() for value in self.resource_scope):
            raise ValueError("resource_scope entries must not be empty")
        if self.amount < 0:
            raise ValueError("amount must not be negative")
        if self.subject_count < 0:
            raise ValueError("subject_count must not be negative")
        if not self.evidence_refs:
            raise ValueError("a governance proposal must carry durable evidence")
        if len({key for key, _value in self.attributes}) != len(self.attributes):
            raise ValueError("attribute keys must be unique")

    @property
    def digest(self) -> str:
        return _digest(
            {
                "proposal_id": self.proposal_id,
                "version": self.version,
                "contract_digest": self.contract_digest,
                "artifact_id": self.artifact_id,
                "artifact_digest": self.artifact_digest,
                "requested_by": self.requested_by,
                "action": self.action,
                "resource_scope": self.resource_scope,
                "idempotency_key": self.idempotency_key,
                "risk": self.risk.name,
                "reversibility": self.reversibility.value,
                "amount": self.amount,
                "subject_count": self.subject_count,
                "evidence_refs": self.evidence_refs,
                "attributes": self.attributes,
            }
        )


@dataclass(frozen=True)
class PolicyRef:
    """Content-addressed identity of the exact policy used for a decision."""

    policy_id: str
    version: int
    content_digest: str

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("policy_id must not be empty")
        if self.version < 1:
            raise ValueError("policy version must be at least 1")
        if not self.content_digest.strip():
            raise ValueError("content_digest must not be empty")

    @property
    def digest(self) -> str:
        return _digest(
            {
                "policy_id": self.policy_id,
                "version": self.version,
                "content_digest": self.content_digest,
            }
        )

    @classmethod
    def from_content(
        cls,
        policy_id: str,
        version: int,
        content: Mapping[str, Any],
    ) -> "PolicyRef":
        return cls(policy_id, version, _digest(content))


@dataclass(frozen=True)
class GovernanceFinding:
    code: str
    message: str
    evidence: str
    severity: FindingSeverity = FindingSeverity.BLOCKER

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("finding code must not be empty")
        if not self.message.strip():
            raise ValueError("finding message must not be empty")
        if not self.evidence.strip():
            raise ValueError("governance findings must carry evidence")


@dataclass(frozen=True)
class GovernanceReceipt:
    """Durable control result bound to one proposal and one policy version."""

    receipt_id: str
    control: str
    proposal_digest: str
    policy_digest: str
    decided_by: str
    decision: ControlDecision
    issued_at: str
    expires_at: str | None = None
    findings: tuple[GovernanceFinding, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    parent_receipts: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        required = {
            "receipt_id": self.receipt_id,
            "control": self.control,
            "proposal_digest": self.proposal_digest,
            "policy_digest": self.policy_digest,
            "decided_by": self.decided_by,
            "issued_at": self.issued_at,
        }
        for name, value in required.items():
            if not value.strip():
                raise ValueError(f"{name} must not be empty")

        blockers = [
            finding
            for finding in self.findings
            if finding.severity is FindingSeverity.BLOCKER
        ]
        if self.decision is ControlDecision.ALLOWED and blockers:
            raise ValueError("an allowed receipt cannot carry blocker findings")
        if self.decision in {ControlDecision.DENIED, ControlDecision.REVOKED} and not blockers:
            raise ValueError("a denied or revoked receipt must explain a blocker")
        if self.decision is ControlDecision.PENDING and self.expires_at is None:
            raise ValueError("a pending receipt must expire")

    @property
    def digest(self) -> str:
        return _digest(
            {
                "receipt_id": self.receipt_id,
                "control": self.control,
                "proposal_digest": self.proposal_digest,
                "policy_digest": self.policy_digest,
                "decided_by": self.decided_by,
                "decision": self.decision.value,
                "issued_at": self.issued_at,
                "expires_at": self.expires_at,
                "findings": tuple(
                    (
                        finding.code,
                        finding.message,
                        finding.evidence,
                        finding.severity.value,
                    )
                    for finding in self.findings
                ),
                "evidence_refs": self.evidence_refs,
                "parent_receipts": self.parent_receipts,
            }
        )

    def authorizes(
        self,
        proposal: ActionProposal,
        policy: PolicyRef,
        *,
        at: str,
    ) -> bool:
        if self.decision is not ControlDecision.ALLOWED:
            return False
        if self.proposal_digest != proposal.digest:
            return False
        if self.policy_digest != policy.digest:
            return False
        return self.expires_at is None or _instant(at) <= _instant(self.expires_at)
