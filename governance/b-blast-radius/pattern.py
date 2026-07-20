"""Blast Radius Control pattern.

Containment is a hierarchy of budgets. A child scope may narrow its parent but
must never widen it. Before an external effect runs, the controller reserves
amount, subjects, and effect count across the complete ancestor path. This
prevents individually valid sibling actions from racing past a portfolio limit.
Each external effect must then exchange part of that reservation for a one-use
live permit. An uncertain result keeps its capacity quarantined until
reconciliation instead of silently reopening the budget.

The controller must not:

* register a child with more authority than its parent;
* count only the leaf while ignoring aggregate parent consumption;
* execute first and discover the quota breach afterward;
* let a killed scope keep using leases that were reserved earlier.
* release capacity for an in-flight effect whose outcome is still unknown.
"""
from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from boundary_contract import (  # noqa: E402
    ActionProposal,
    ControlDecision,
    GovernanceFinding,
    GovernanceReceipt,
    PolicyRef,
    Reversibility as Reversibility,
    RiskLevel as RiskLevel,
)


@dataclass(frozen=True)
class BlastBudget:
    max_amount: float
    max_subjects: int
    max_effects: int
    allowed_actions: tuple[str, ...]
    resource_prefixes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.max_amount < 0:
            raise ValueError("max_amount must not be negative")
        if self.max_subjects < 0:
            raise ValueError("max_subjects must not be negative")
        if self.max_effects < 1:
            raise ValueError("max_effects must be positive")
        if not self.allowed_actions or not self.resource_prefixes:
            raise ValueError("actions and resource prefixes must not be empty")


@dataclass(frozen=True)
class ContainmentScope:
    scope_id: str
    budget: BlastBudget
    parent_id: str | None = None

    def __post_init__(self) -> None:
        if not self.scope_id.strip():
            raise ValueError("scope_id must not be empty")
        if self.parent_id is not None and not self.parent_id.strip():
            raise ValueError("parent_id must not be blank")
        if self.parent_id == self.scope_id:
            raise ValueError("a scope cannot parent itself")


@dataclass
class BudgetUsage:
    reserved_amount: float = 0.0
    reserved_subjects: int = 0
    reserved_effects: int = 0
    in_flight_amount: float = 0.0
    in_flight_subjects: int = 0
    in_flight_effects: int = 0
    unknown_amount: float = 0.0
    unknown_subjects: int = 0
    unknown_effects: int = 0
    committed_amount: float = 0.0
    committed_subjects: int = 0
    committed_effects: int = 0


class LeaseStatus(str, Enum):
    RESERVED = "reserved"
    ACTIVE = "active"
    RECONCILING = "reconciling"
    COMMITTED = "committed"
    CANCELLED = "cancelled"
    REVOKED = "revoked"


@dataclass(frozen=True)
class ContainmentLease:
    lease_id: str
    proposal_digest: str
    policy_digest: str
    scope_id: str
    amount: float
    subject_count: int
    effect_count: int
    idempotency_key: str
    created_at: str
    allowed_refs: tuple[str, ...] = ()
    parent_receipts: tuple[str, ...] = ()


@dataclass
class LeaseUsage:
    remaining_amount: float
    remaining_subjects: int
    remaining_effects: int
    in_flight_amount: float = 0.0
    in_flight_subjects: int = 0
    in_flight_effects: int = 0
    unknown_amount: float = 0.0
    unknown_subjects: int = 0
    unknown_effects: int = 0
    committed_amount: float = 0.0
    committed_subjects: int = 0
    committed_effects: int = 0


class EffectStatus(str, Enum):
    IN_FLIGHT = "in_flight"
    UNKNOWN = "unknown"
    COMMITTED = "committed"
    RELEASED = "released"


@dataclass(frozen=True)
class EffectPermit:
    permit_id: str
    lease_id: str
    proposal_digest: str
    policy_digest: str
    effect_ref: str
    amount: float
    subject_count: int
    effect_count: int
    idempotency_key: str
    started_at: str


class ContainmentError(RuntimeError):
    """Raised when an effect would cross a containment boundary."""


class BlastRadiusController:
    """Thread-safe hierarchical budget reservation and kill switch."""

    def __init__(
        self,
        *,
        policy_id: str = "blast-radius",
        version: int = 1,
    ) -> None:
        if not policy_id.strip() or version < 1:
            raise ValueError("policy identity is invalid")
        self.policy_id = policy_id
        self.version = version
        self.scopes: dict[str, ContainmentScope] = {}
        self.usage: dict[str, BudgetUsage] = {}
        self.leases: dict[str, ContainmentLease] = {}
        self.lease_usage: dict[str, LeaseUsage] = {}
        self.lease_status: dict[str, LeaseStatus] = {}
        self.idempotency: dict[str, str] = {}
        self.effect_permits: dict[str, EffectPermit] = {}
        self.effect_status: dict[str, EffectStatus] = {}
        self.effect_idempotency: dict[str, str] = {}
        self.claimed_refs: dict[tuple[str, str], str] = {}
        self.killed_scopes: set[str] = set()
        self._sealed = False
        self._policy_ref: PolicyRef | None = None
        self._lock = threading.RLock()

    def register_scope(self, scope: ContainmentScope) -> None:
        with self._lock:
            if self._sealed:
                raise ContainmentError("the containment policy is sealed")
            if scope.scope_id in self.scopes:
                raise ContainmentError(f"duplicate scope {scope.scope_id!r}")
            if scope.parent_id is None:
                if any(item.parent_id is None for item in self.scopes.values()):
                    raise ContainmentError("the policy may have only one root scope")
            else:
                parent = self.scopes.get(scope.parent_id)
                if parent is None:
                    raise ContainmentError("parent scope must be registered first")
                self._assert_narrower(scope.budget, parent.budget)
            self.scopes[scope.scope_id] = scope
            self.usage[scope.scope_id] = BudgetUsage()

    def seal(self) -> PolicyRef:
        with self._lock:
            if not self.scopes:
                raise ContainmentError("cannot seal an empty containment policy")
            if self._policy_ref is None:
                self._policy_ref = PolicyRef.from_content(
                    self.policy_id,
                    self.version,
                    {
                        scope_id: {
                            "parent_id": scope.parent_id,
                            "max_amount": scope.budget.max_amount,
                            "max_subjects": scope.budget.max_subjects,
                            "max_effects": scope.budget.max_effects,
                            "allowed_actions": scope.budget.allowed_actions,
                            "resource_prefixes": scope.budget.resource_prefixes,
                        }
                        for scope_id, scope in sorted(self.scopes.items())
                    },
                )
                self._sealed = True
            return self._policy_ref

    @property
    def policy_ref(self) -> PolicyRef:
        return self.seal()

    def reserve(
        self,
        proposal: ActionProposal,
        *,
        scope_id: str,
        at: str,
        effect_count: int = 1,
        allowed_refs: tuple[str, ...] = (),
        parent_receipts: tuple[str, ...] = (),
    ) -> ContainmentLease:
        with self._lock:
            if effect_count < 1:
                raise ValueError("effect_count must be positive")
            if any(not ref.strip() for ref in allowed_refs):
                raise ValueError("allowed_refs must not contain blank values")
            if len(set(allowed_refs)) != len(allowed_refs):
                raise ValueError("allowed_refs must not contain duplicates")
            policy = self.seal()
            scope = self._scope(scope_id)
            path = self._path(scope_id)
            if any(item.scope_id in self.killed_scopes for item in path):
                raise ContainmentError("scope or ancestor is stopped by the kill switch")
            self._check_scope(scope, proposal)

            existing_id = self.idempotency.get(proposal.idempotency_key)
            if existing_id is not None:
                existing = self.leases[existing_id]
                if existing.proposal_digest != proposal.digest:
                    raise ContainmentError(
                        "idempotency key is already bound to another proposal"
                    )
                if (
                    existing.scope_id != scope_id
                    or existing.effect_count != effect_count
                    or existing.allowed_refs != allowed_refs
                ):
                    raise ContainmentError(
                        "idempotency key is already bound to another containment claim"
                    )
                return existing

            for item in path:
                self._check_capacity(item, proposal, effect_count)

            lease = ContainmentLease(
                lease_id=f"lease::{proposal.proposal_id}::{proposal.digest}",
                proposal_digest=proposal.digest,
                policy_digest=policy.digest,
                scope_id=scope_id,
                amount=proposal.amount,
                subject_count=proposal.subject_count,
                effect_count=effect_count,
                idempotency_key=proposal.idempotency_key,
                created_at=at,
                allowed_refs=allowed_refs,
                parent_receipts=parent_receipts,
            )
            for item in path:
                usage = self.usage[item.scope_id]
                usage.reserved_amount += proposal.amount
                usage.reserved_subjects += proposal.subject_count
                usage.reserved_effects += effect_count
            self.leases[lease.lease_id] = lease
            self.lease_usage[lease.lease_id] = LeaseUsage(
                proposal.amount,
                proposal.subject_count,
                effect_count,
            )
            self.lease_status[lease.lease_id] = LeaseStatus.RESERVED
            self.idempotency[proposal.idempotency_key] = lease.lease_id
            return lease

    def authorizes(
        self,
        lease: ContainmentLease,
        proposal: ActionProposal,
    ) -> bool:
        with self._lock:
            if self.lease_status.get(lease.lease_id) not in {
                LeaseStatus.RESERVED,
                LeaseStatus.ACTIVE,
            }:
                return False
            if lease.proposal_digest != proposal.digest:
                return False
            if lease.policy_digest != self.policy_ref.digest:
                return False
            return not any(
                item.scope_id in self.killed_scopes
                for item in self._path(lease.scope_id)
            )

    def begin_effect(
        self,
        lease: ContainmentLease,
        proposal: ActionProposal,
        *,
        effect_ref: str,
        amount: float,
        idempotency_key: str,
        at: str,
        subject_count: int = 1,
        effect_count: int = 1,
    ) -> EffectPermit:
        """Atomically exchange reserved capacity for a one-use effect permit."""
        with self._lock:
            if amount < 0 or subject_count < 1 or effect_count < 1:
                raise ValueError("effect usage must be non-negative and non-zero")
            if not effect_ref.strip() or not idempotency_key.strip():
                raise ValueError("effect identity must not be blank")
            stored = self._lease(lease.lease_id)
            if stored != lease:
                raise ContainmentError("effect permit references an altered lease")
            if self.lease_status.get(lease.lease_id) not in {
                LeaseStatus.RESERVED,
                LeaseStatus.ACTIVE,
            }:
                raise ContainmentError("lease has no live capacity for another effect")
            if not self.authorizes(lease, proposal):
                raise ContainmentError("live lease does not authorize this effect")
            if idempotency_key in self.effect_idempotency:
                raise ContainmentError(
                    "effect idempotency key has already issued a one-use permit"
                )
            ref_key = (lease.lease_id, effect_ref)
            if ref_key in self.claimed_refs:
                raise ContainmentError(
                    "effect reference has already consumed this lease"
                )
            if lease.allowed_refs and effect_ref not in lease.allowed_refs:
                raise ContainmentError("effect reference is outside the lease scope")

            usage = self.lease_usage[lease.lease_id]
            if amount > usage.remaining_amount:
                raise ContainmentError("effect amount exceeds the remaining lease")
            if subject_count > usage.remaining_subjects:
                raise ContainmentError("effect subjects exceed the remaining lease")
            if effect_count > usage.remaining_effects:
                raise ContainmentError("effect count exceeds the remaining lease")

            permit = EffectPermit(
                permit_id=f"permit::{lease.lease_id}::{idempotency_key}",
                lease_id=lease.lease_id,
                proposal_digest=proposal.digest,
                policy_digest=lease.policy_digest,
                effect_ref=effect_ref,
                amount=amount,
                subject_count=subject_count,
                effect_count=effect_count,
                idempotency_key=idempotency_key,
                started_at=at,
            )
            self._move_reserved_to_in_flight(lease, permit)
            self.effect_permits[permit.permit_id] = permit
            self.effect_status[permit.permit_id] = EffectStatus.IN_FLIGHT
            self.effect_idempotency[idempotency_key] = permit.permit_id
            self.claimed_refs[ref_key] = permit.permit_id
            self.lease_status[lease.lease_id] = LeaseStatus.ACTIVE
            return permit

    def effect_authorizes(
        self,
        permit: EffectPermit,
        proposal: ActionProposal,
    ) -> bool:
        """Recheck live containment state at the final effect boundary."""
        with self._lock:
            stored = self.effect_permits.get(permit.permit_id)
            if stored != permit:
                return False
            if self.effect_status.get(permit.permit_id) is not EffectStatus.IN_FLIGHT:
                return False
            lease = self._lease(permit.lease_id)
            if self.lease_status.get(lease.lease_id) is not LeaseStatus.ACTIVE:
                return False
            if permit.proposal_digest != proposal.digest:
                return False
            if permit.policy_digest != self.policy_ref.digest:
                return False
            return not any(
                item.scope_id in self.killed_scopes
                for item in self._path(lease.scope_id)
            )

    def confirm_effect(
        self,
        permit_id: str,
        *,
        succeeded: bool | None,
        at: str,
    ) -> GovernanceReceipt:
        """Record a known success, known failure, or uncertain external result."""
        with self._lock:
            permit = self._permit(permit_id)
            status = self.effect_status[permit_id]
            if succeeded is None:
                if status is not EffectStatus.IN_FLIGHT:
                    raise ContainmentError("only an in-flight effect may become unknown")
                self._move_in_flight_to_unknown(permit)
                self.effect_status[permit_id] = EffectStatus.UNKNOWN
                self.lease_status[permit.lease_id] = LeaseStatus.RECONCILING
                return self._effect_receipt(
                    permit,
                    at,
                    ControlDecision.PENDING,
                    "effect_result_unknown",
                )
            if succeeded:
                if status not in {EffectStatus.IN_FLIGHT, EffectStatus.UNKNOWN}:
                    raise ContainmentError(
                        "only an in-flight or unknown effect may be committed"
                    )
                self._move_effect_to_committed(permit, status)
                self.effect_status[permit_id] = EffectStatus.COMMITTED
                self._refresh_lease_status(permit.lease_id)
                return self._effect_receipt(
                    permit,
                    at,
                    ControlDecision.ALLOWED,
                    "effect_confirmed",
                )
            if status not in {EffectStatus.IN_FLIGHT, EffectStatus.UNKNOWN}:
                raise ContainmentError(
                    "only an in-flight or unknown effect may be released"
                )
            self._release_effect(permit, status)
            self.effect_status[permit_id] = EffectStatus.RELEASED
            self.claimed_refs.pop((permit.lease_id, permit.effect_ref), None)
            self._refresh_lease_status(permit.lease_id)
            return self._effect_receipt(
                permit,
                at,
                ControlDecision.REVOKED,
                "effect_confirmed_failed",
            )

    def reservation_receipt(
        self,
        lease: ContainmentLease,
        proposal: ActionProposal,
        *,
        at: str,
    ) -> GovernanceReceipt:
        with self._lock:
            if not self.authorizes(lease, proposal):
                raise ContainmentError("lease does not authorize this proposal")
            return GovernanceReceipt(
                receipt_id=f"containment-reservation::{lease.lease_id}",
                control="blast-radius",
                proposal_digest=lease.proposal_digest,
                policy_digest=lease.policy_digest,
                decided_by="blast-radius-controller",
                decision=ControlDecision.ALLOWED,
                issued_at=at,
                evidence_refs=(
                    f"containment://{lease.scope_id}/{lease.lease_id}/reserved",
                ),
                parent_receipts=lease.parent_receipts,
            )

    def commit(self, lease_id: str, *, at: str) -> GovernanceReceipt:
        with self._lock:
            lease = self._lease(lease_id)
            if self.lease_status[lease_id] is not LeaseStatus.RESERVED:
                raise ContainmentError("only a reserved lease may be committed")

            for item in self._path(lease.scope_id):
                usage = self.usage[item.scope_id]
                usage.reserved_amount -= lease.amount
                usage.reserved_subjects -= lease.subject_count
                usage.reserved_effects -= lease.effect_count
                usage.committed_amount += lease.amount
                usage.committed_subjects += lease.subject_count
                usage.committed_effects += lease.effect_count
            self.lease_status[lease_id] = LeaseStatus.COMMITTED
            lease_usage = self.lease_usage[lease_id]
            lease_usage.remaining_amount = 0.0
            lease_usage.remaining_subjects = 0
            lease_usage.remaining_effects = 0
            lease_usage.committed_amount = lease.amount
            lease_usage.committed_subjects = lease.subject_count
            lease_usage.committed_effects = lease.effect_count
            return GovernanceReceipt(
                receipt_id=f"containment-receipt::{lease.lease_id}",
                control="blast-radius",
                proposal_digest=lease.proposal_digest,
                policy_digest=lease.policy_digest,
                decided_by="blast-radius-controller",
                decision=ControlDecision.ALLOWED,
                issued_at=at,
                evidence_refs=(
                    f"containment://{lease.scope_id}/{lease.lease_id}",
                ),
                parent_receipts=lease.parent_receipts,
            )

    def cancel(self, lease_id: str, *, at: str) -> GovernanceReceipt:
        with self._lock:
            lease = self._lease(lease_id)
            if self.lease_status[lease_id] is not LeaseStatus.RESERVED:
                raise ContainmentError("only a reserved lease may be cancelled")
            self._release_reserved(lease)
            self.lease_status[lease_id] = LeaseStatus.CANCELLED
            return self._revoked_receipt(lease, at, "lease_cancelled")

    def trip_kill_switch(self, scope_id: str, *, at: str) -> tuple[GovernanceReceipt, ...]:
        with self._lock:
            self._scope(scope_id)
            self.killed_scopes.add(scope_id)
            revoked: list[GovernanceReceipt] = []
            for lease in self.leases.values():
                if self.lease_status[lease.lease_id] not in {
                    LeaseStatus.RESERVED,
                    LeaseStatus.ACTIVE,
                }:
                    continue
                if scope_id not in {
                    item.scope_id for item in self._path(lease.scope_id)
                }:
                    continue
                lease_usage = self.lease_usage[lease.lease_id]
                if self.lease_status[lease.lease_id] is LeaseStatus.RESERVED:
                    self._revoke(lease)
                else:
                    self._release_remaining(lease)
                    for permit in self.effect_permits.values():
                        if (
                            permit.lease_id == lease.lease_id
                            and self.effect_status[permit.permit_id]
                            is EffectStatus.IN_FLIGHT
                        ):
                            self._move_in_flight_to_unknown(permit)
                            self.effect_status[permit.permit_id] = EffectStatus.UNKNOWN
                    self.lease_status[lease.lease_id] = (
                        LeaseStatus.RECONCILING
                        if lease_usage.unknown_effects
                        else LeaseStatus.REVOKED
                    )
                revoked.append(
                    self._revoked_receipt(lease, at, "kill_switch_active")
                )
            return tuple(revoked)

    def snapshot(self) -> dict[str, dict[str, float | int | bool]]:
        with self._lock:
            return {
                scope_id: {
                    "reserved_amount": usage.reserved_amount,
                    "in_flight_amount": usage.in_flight_amount,
                    "unknown_amount": usage.unknown_amount,
                    "committed_amount": usage.committed_amount,
                    "reserved_subjects": usage.reserved_subjects,
                    "in_flight_subjects": usage.in_flight_subjects,
                    "unknown_subjects": usage.unknown_subjects,
                    "committed_subjects": usage.committed_subjects,
                    "reserved_effects": usage.reserved_effects,
                    "in_flight_effects": usage.in_flight_effects,
                    "unknown_effects": usage.unknown_effects,
                    "committed_effects": usage.committed_effects,
                    "killed": scope_id in self.killed_scopes,
                }
                for scope_id, usage in self.usage.items()
            }

    @staticmethod
    def _assert_narrower(child: BlastBudget, parent: BlastBudget) -> None:
        if child.max_amount > parent.max_amount:
            raise ContainmentError("child amount budget exceeds parent")
        if child.max_subjects > parent.max_subjects:
            raise ContainmentError("child subject budget exceeds parent")
        if child.max_effects > parent.max_effects:
            raise ContainmentError("child effect budget exceeds parent")
        if not set(child.allowed_actions) <= set(parent.allowed_actions):
            raise ContainmentError("child actions exceed parent authority")
        resources_narrower = all(
            any(
                child_prefix.startswith(parent_prefix)
                for parent_prefix in parent.resource_prefixes
            )
            for child_prefix in child.resource_prefixes
        )
        if not resources_narrower:
            raise ContainmentError("child resources exceed parent authority")

    @staticmethod
    def _resource_allowed(prefixes: tuple[str, ...], resource: str) -> bool:
        return any(resource.startswith(prefix) for prefix in prefixes)

    def _check_scope(
        self,
        scope: ContainmentScope,
        proposal: ActionProposal,
    ) -> None:
        if proposal.action not in scope.budget.allowed_actions:
            raise ContainmentError("action is outside the leaf scope")
        denied = [
            resource
            for resource in proposal.resource_scope
            if not self._resource_allowed(scope.budget.resource_prefixes, resource)
        ]
        if denied:
            raise ContainmentError(f"resources are outside the leaf scope: {denied}")

    def _check_capacity(
        self,
        scope: ContainmentScope,
        proposal: ActionProposal,
        effect_count: int,
    ) -> None:
        usage = self.usage[scope.scope_id]
        budget = scope.budget
        if (
            usage.reserved_amount
            + usage.in_flight_amount
            + usage.unknown_amount
            + usage.committed_amount
            + proposal.amount
            > budget.max_amount
        ):
            raise ContainmentError(f"amount budget exceeded at {scope.scope_id}")
        if (
            usage.reserved_subjects
            + usage.in_flight_subjects
            + usage.unknown_subjects
            + usage.committed_subjects
            + proposal.subject_count
            > budget.max_subjects
        ):
            raise ContainmentError(f"subject budget exceeded at {scope.scope_id}")
        if (
            usage.reserved_effects
            + usage.in_flight_effects
            + usage.unknown_effects
            + usage.committed_effects
            + effect_count
            > budget.max_effects
        ):
            raise ContainmentError(f"effect budget exceeded at {scope.scope_id}")

    def _path(self, scope_id: str) -> tuple[ContainmentScope, ...]:
        path: list[ContainmentScope] = []
        current = self._scope(scope_id)
        while True:
            path.append(current)
            if current.parent_id is None:
                break
            current = self._scope(current.parent_id)
        return tuple(path)

    def _scope(self, scope_id: str) -> ContainmentScope:
        try:
            return self.scopes[scope_id]
        except KeyError as error:
            raise ContainmentError(f"unknown scope {scope_id!r}") from error

    def _lease(self, lease_id: str) -> ContainmentLease:
        try:
            return self.leases[lease_id]
        except KeyError as error:
            raise ContainmentError(f"unknown lease {lease_id!r}") from error

    def _permit(self, permit_id: str) -> EffectPermit:
        try:
            return self.effect_permits[permit_id]
        except KeyError as error:
            raise ContainmentError(f"unknown effect permit {permit_id!r}") from error

    def _move_reserved_to_in_flight(
        self,
        lease: ContainmentLease,
        permit: EffectPermit,
    ) -> None:
        lease_usage = self.lease_usage[lease.lease_id]
        lease_usage.remaining_amount -= permit.amount
        lease_usage.remaining_subjects -= permit.subject_count
        lease_usage.remaining_effects -= permit.effect_count
        lease_usage.in_flight_amount += permit.amount
        lease_usage.in_flight_subjects += permit.subject_count
        lease_usage.in_flight_effects += permit.effect_count
        for item in self._path(lease.scope_id):
            usage = self.usage[item.scope_id]
            usage.reserved_amount -= permit.amount
            usage.reserved_subjects -= permit.subject_count
            usage.reserved_effects -= permit.effect_count
            usage.in_flight_amount += permit.amount
            usage.in_flight_subjects += permit.subject_count
            usage.in_flight_effects += permit.effect_count

    def _move_in_flight_to_unknown(self, permit: EffectPermit) -> None:
        lease = self._lease(permit.lease_id)
        lease_usage = self.lease_usage[lease.lease_id]
        lease_usage.in_flight_amount -= permit.amount
        lease_usage.in_flight_subjects -= permit.subject_count
        lease_usage.in_flight_effects -= permit.effect_count
        lease_usage.unknown_amount += permit.amount
        lease_usage.unknown_subjects += permit.subject_count
        lease_usage.unknown_effects += permit.effect_count
        for item in self._path(lease.scope_id):
            usage = self.usage[item.scope_id]
            usage.in_flight_amount -= permit.amount
            usage.in_flight_subjects -= permit.subject_count
            usage.in_flight_effects -= permit.effect_count
            usage.unknown_amount += permit.amount
            usage.unknown_subjects += permit.subject_count
            usage.unknown_effects += permit.effect_count

    def _move_effect_to_committed(
        self,
        permit: EffectPermit,
        status: EffectStatus,
    ) -> None:
        lease = self._lease(permit.lease_id)
        lease_usage = self.lease_usage[lease.lease_id]
        source = "unknown" if status is EffectStatus.UNKNOWN else "in_flight"
        setattr(
            lease_usage,
            f"{source}_amount",
            getattr(lease_usage, f"{source}_amount") - permit.amount,
        )
        setattr(
            lease_usage,
            f"{source}_subjects",
            getattr(lease_usage, f"{source}_subjects") - permit.subject_count,
        )
        setattr(
            lease_usage,
            f"{source}_effects",
            getattr(lease_usage, f"{source}_effects") - permit.effect_count,
        )
        lease_usage.committed_amount += permit.amount
        lease_usage.committed_subjects += permit.subject_count
        lease_usage.committed_effects += permit.effect_count
        for item in self._path(lease.scope_id):
            usage = self.usage[item.scope_id]
            setattr(
                usage,
                f"{source}_amount",
                getattr(usage, f"{source}_amount") - permit.amount,
            )
            setattr(
                usage,
                f"{source}_subjects",
                getattr(usage, f"{source}_subjects") - permit.subject_count,
            )
            setattr(
                usage,
                f"{source}_effects",
                getattr(usage, f"{source}_effects") - permit.effect_count,
            )
            usage.committed_amount += permit.amount
            usage.committed_subjects += permit.subject_count
            usage.committed_effects += permit.effect_count

    def _release_effect(
        self,
        permit: EffectPermit,
        status: EffectStatus,
    ) -> None:
        lease = self._lease(permit.lease_id)
        lease_usage = self.lease_usage[lease.lease_id]
        source = "unknown" if status is EffectStatus.UNKNOWN else "in_flight"
        setattr(
            lease_usage,
            f"{source}_amount",
            getattr(lease_usage, f"{source}_amount") - permit.amount,
        )
        setattr(
            lease_usage,
            f"{source}_subjects",
            getattr(lease_usage, f"{source}_subjects") - permit.subject_count,
        )
        setattr(
            lease_usage,
            f"{source}_effects",
            getattr(lease_usage, f"{source}_effects") - permit.effect_count,
        )
        stopped = self.lease_status[lease.lease_id] is LeaseStatus.RECONCILING
        for item in self._path(lease.scope_id):
            usage = self.usage[item.scope_id]
            setattr(
                usage,
                f"{source}_amount",
                getattr(usage, f"{source}_amount") - permit.amount,
            )
            setattr(
                usage,
                f"{source}_subjects",
                getattr(usage, f"{source}_subjects") - permit.subject_count,
            )
            setattr(
                usage,
                f"{source}_effects",
                getattr(usage, f"{source}_effects") - permit.effect_count,
            )
            if not stopped:
                usage.reserved_amount += permit.amount
                usage.reserved_subjects += permit.subject_count
                usage.reserved_effects += permit.effect_count
        if not stopped:
            lease_usage.remaining_amount += permit.amount
            lease_usage.remaining_subjects += permit.subject_count
            lease_usage.remaining_effects += permit.effect_count

    def _release_remaining(self, lease: ContainmentLease) -> None:
        lease_usage = self.lease_usage[lease.lease_id]
        for item in self._path(lease.scope_id):
            usage = self.usage[item.scope_id]
            usage.reserved_amount -= lease_usage.remaining_amount
            usage.reserved_subjects -= lease_usage.remaining_subjects
            usage.reserved_effects -= lease_usage.remaining_effects
        lease_usage.remaining_amount = 0.0
        lease_usage.remaining_subjects = 0
        lease_usage.remaining_effects = 0

    def _refresh_lease_status(self, lease_id: str) -> None:
        usage = self.lease_usage[lease_id]
        current = self.lease_status[lease_id]
        if usage.unknown_effects:
            self.lease_status[lease_id] = LeaseStatus.RECONCILING
        elif current is LeaseStatus.RECONCILING:
            self.lease_status[lease_id] = LeaseStatus.REVOKED
        elif (
            usage.remaining_effects == 0
            and usage.in_flight_effects == 0
            and usage.committed_effects > 0
        ):
            self._release_remaining(self._lease(lease_id))
            self.lease_status[lease_id] = LeaseStatus.COMMITTED
        elif current is LeaseStatus.ACTIVE:
            self.lease_status[lease_id] = LeaseStatus.ACTIVE

    def _release_reserved(self, lease: ContainmentLease) -> None:
        self._release_remaining(lease)

    def _revoke(self, lease: ContainmentLease) -> None:
        self._release_reserved(lease)
        self.lease_status[lease.lease_id] = LeaseStatus.REVOKED

    def _revoked_receipt(
        self,
        lease: ContainmentLease,
        at: str,
        code: str,
    ) -> GovernanceReceipt:
        return GovernanceReceipt(
            receipt_id=f"containment-receipt::{lease.lease_id}::{code}",
            control="blast-radius",
            proposal_digest=lease.proposal_digest,
            policy_digest=lease.policy_digest,
            decided_by="blast-radius-controller",
            decision=ControlDecision.REVOKED,
            issued_at=at,
            findings=(
                GovernanceFinding(
                    code,
                    "the reserved effect no longer has containment authority",
                    f"containment://{lease.scope_id}/{lease.lease_id}",
                ),
            ),
            evidence_refs=(f"containment://{lease.scope_id}/{lease.lease_id}",),
            parent_receipts=lease.parent_receipts,
        )

    def _effect_receipt(
        self,
        permit: EffectPermit,
        at: str,
        decision: ControlDecision,
        code: str,
    ) -> GovernanceReceipt:
        lease = self._lease(permit.lease_id)
        findings = ()
        if decision is not ControlDecision.ALLOWED:
            findings = (
                GovernanceFinding(
                    code,
                    "the external effect requires reconciliation or was not applied",
                    f"containment://{lease.scope_id}/{permit.permit_id}",
                ),
            )
        return GovernanceReceipt(
            receipt_id=f"containment-effect::{permit.permit_id}::{code}",
            control="blast-radius",
            proposal_digest=permit.proposal_digest,
            policy_digest=permit.policy_digest,
            decided_by="blast-radius-controller",
            decision=decision,
            issued_at=at,
            findings=findings,
            evidence_refs=(
                f"containment://{lease.scope_id}/{permit.permit_id}/{code}",
            ),
            parent_receipts=lease.parent_receipts,
        )
