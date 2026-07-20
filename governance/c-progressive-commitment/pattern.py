"""Progressive Commitment pattern.

Authority advances through a versioned chain:

``OBSERVE -> RECOMMEND -> SHADOW -> LIMITED -> AUTONOMOUS``

Promotion consumes a fresh evidence window and an explicit human decision. It
is never inferred from age, model version, or a single successful run. A live
effect also needs the upstream approval and containment receipts required by
its capability profile. Critical incidents demote immediately and invalidate
the old credential.

The pattern must not:

* auto-promote an agent because it has been running for a long time;
* let historical successes survive a policy or authority-level change;
* interpret shadow execution as permission for a live external effect;
* allow an old credential after promotion or demotion.
"""
from __future__ import annotations

import sys
import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import IntEnum
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


class AuthorityLevel(IntEnum):
    OBSERVE = 0
    RECOMMEND = 1
    SHADOW = 2
    LIMITED = 3
    AUTONOMOUS = 4


class IncidentSeverity(IntEnum):
    WARNING = 1
    MAJOR = 2
    CRITICAL = 3


def _instant(value: str) -> datetime:
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None:
        raise ValueError("progressive commitment timestamps must include a timezone")
    return instant


@dataclass(frozen=True)
class CapabilityProfile:
    level: AuthorityLevel
    allowed_actions: tuple[str, ...]
    live_effects: bool
    max_amount: float
    max_subjects: int
    required_controls: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.max_amount < 0 or self.max_subjects < 0:
            raise ValueError("capability limits must not be negative")
        if len(set(self.required_controls)) != len(self.required_controls):
            raise ValueError("required controls must be unique")


DEFAULT_PROFILES = (
    CapabilityProfile(
        AuthorityLevel.OBSERVE,
        ("payroll.read",),
        False,
        0,
        0,
    ),
    CapabilityProfile(
        AuthorityLevel.RECOMMEND,
        ("payroll.read", "payroll.propose"),
        False,
        0,
        0,
    ),
    CapabilityProfile(
        AuthorityLevel.SHADOW,
        ("payroll.read", "payroll.propose", "payroll.disburse"),
        False,
        15_000_000,
        800,
    ),
    CapabilityProfile(
        AuthorityLevel.LIMITED,
        ("payroll.read", "payroll.propose", "payroll.disburse"),
        True,
        1_000_000,
        50,
        ("approval-gate", "blast-radius"),
    ),
    CapabilityProfile(
        AuthorityLevel.AUTONOMOUS,
        ("payroll.read", "payroll.propose", "payroll.disburse"),
        True,
        15_000_000,
        800,
        ("approval-gate", "blast-radius"),
    ),
)


@dataclass(frozen=True)
class ProgressivePolicy:
    policy_id: str = "progressive-commitment"
    version: int = 1
    min_runs: int = 5
    min_success_rate: float = 0.98
    max_blockers: int = 0
    evidence_max_age_days: int = 30
    required_evaluation_slices: tuple[str, ...] = ()
    promotion_role: str = "governance-owner"
    demotion_role: str = "incident-responder"
    profiles: tuple[CapabilityProfile, ...] = DEFAULT_PROFILES

    def __post_init__(self) -> None:
        if (
            not self.policy_id.strip()
            or not self.promotion_role.strip()
            or not self.demotion_role.strip()
        ):
            raise ValueError("policy identity and authority roles must not be empty")
        if self.version < 1 or self.min_runs < 1:
            raise ValueError("policy version and min_runs must be positive")
        if not 0 <= self.min_success_rate <= 1:
            raise ValueError("min_success_rate must be between 0 and 1")
        if self.max_blockers < 0:
            raise ValueError("max_blockers must not be negative")
        if self.evidence_max_age_days < 1:
            raise ValueError("evidence_max_age_days must be positive")
        if any(not value.strip() for value in self.required_evaluation_slices):
            raise ValueError("required evaluation slices must not be blank")
        if len(set(self.required_evaluation_slices)) != len(
            self.required_evaluation_slices
        ):
            raise ValueError("required evaluation slices must be unique")
        levels = tuple(profile.level for profile in self.profiles)
        if levels != tuple(AuthorityLevel):
            raise ValueError("profiles must define every authority level in order")
        for lower, higher in zip(self.profiles, self.profiles[1:]):
            if not set(lower.allowed_actions).issubset(higher.allowed_actions):
                raise ValueError(
                    "higher authority levels must retain lower-level actions"
                )
            if lower.live_effects and not higher.live_effects:
                raise ValueError(
                    "higher authority levels must not revoke live-effect capability"
                )
            if lower.live_effects and higher.live_effects:
                if (
                    higher.max_amount < lower.max_amount
                    or higher.max_subjects < lower.max_subjects
                ):
                    raise ValueError(
                        "live authority limits must grow monotonically"
                    )
                if not set(lower.required_controls).issubset(
                    higher.required_controls
                ):
                    raise ValueError(
                        "higher live authority must retain upstream controls"
                    )

    @property
    def ref(self) -> PolicyRef:
        return PolicyRef.from_content(
            self.policy_id,
            self.version,
            {
                "min_runs": self.min_runs,
                "min_success_rate": self.min_success_rate,
                "max_blockers": self.max_blockers,
                "evidence_max_age_days": self.evidence_max_age_days,
                "required_evaluation_slices": self.required_evaluation_slices,
                "promotion_role": self.promotion_role,
                "demotion_role": self.demotion_role,
                "profiles": tuple(
                    {
                        "level": profile.level.name,
                        "allowed_actions": profile.allowed_actions,
                        "live_effects": profile.live_effects,
                        "max_amount": profile.max_amount,
                        "max_subjects": profile.max_subjects,
                        "required_controls": profile.required_controls,
                    }
                    for profile in self.profiles
                ),
            },
        )

    def profile(self, level: AuthorityLevel) -> CapabilityProfile:
        return self.profiles[int(level)]


@dataclass(frozen=True)
class RunOutcome:
    run_id: str
    success: bool
    blocker: bool
    evidence_ref: str
    evaluation_slice: str
    occurred_at: str
    recorded_by: str

    def __post_init__(self) -> None:
        required = (
            self.run_id,
            self.evidence_ref,
            self.evaluation_slice,
            self.recorded_by,
        )
        if any(not value.strip() for value in required):
            raise ValueError("run outcome must carry identity, evidence, and provenance")
        _instant(self.occurred_at)


@dataclass(frozen=True)
class EvidenceWindow:
    agent_id: str
    policy_digest: str
    authority_version: int
    outcomes: tuple[RunOutcome, ...] = ()

    @property
    def runs(self) -> int:
        return len(self.outcomes)

    @property
    def successes(self) -> int:
        return sum(outcome.success for outcome in self.outcomes)

    @property
    def blockers(self) -> int:
        return sum(outcome.blocker for outcome in self.outcomes)

    @property
    def success_rate(self) -> float:
        return self.successes / self.runs if self.runs else 0.0

    @property
    def evaluation_slices(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(outcome.evaluation_slice for outcome in self.outcomes)
        )

    @property
    def digest(self) -> str:
        return PolicyRef.from_content(
            "progressive-evidence-window",
            self.authority_version,
            {
                "agent_id": self.agent_id,
                "policy_digest": self.policy_digest,
                "outcomes": tuple(
                    {
                        "run_id": outcome.run_id,
                        "success": outcome.success,
                        "blocker": outcome.blocker,
                        "evidence_ref": outcome.evidence_ref,
                        "evaluation_slice": outcome.evaluation_slice,
                        "occurred_at": outcome.occurred_at,
                        "recorded_by": outcome.recorded_by,
                    }
                    for outcome in self.outcomes
                ),
            },
        ).digest


@dataclass(frozen=True)
class AuthorityCredential:
    credential_id: str
    agent_id: str
    level: AuthorityLevel
    authority_version: int
    policy_digest: str
    issued_by: str
    issued_at: str


@dataclass(frozen=True)
class PromotionRequest:
    request_id: str
    agent_id: str
    from_level: AuthorityLevel
    to_level: AuthorityLevel
    authority_version: int
    policy_digest: str
    runs: int
    success_rate: float
    blockers: int
    evidence_digest: str
    evidence_refs: tuple[str, ...]
    requested_at: str


@dataclass(frozen=True)
class AuthorityTransition:
    transition_id: str
    agent_id: str
    from_level: AuthorityLevel | None
    to_level: AuthorityLevel
    from_version: int | None
    to_version: int
    policy_digest: str
    reason_code: str
    evidence_refs: tuple[str, ...]
    decided_by: str
    occurred_at: str


class CommitmentError(RuntimeError):
    """Raised when promotion or authorization crosses an authority boundary."""


class ProgressiveCommitment:
    """Evidence-backed authority credentials with fast demotion."""

    def __init__(
        self,
        policy: ProgressivePolicy | None = None,
        *,
        role_resolver: Callable[[str], tuple[str, ...]] | None = None,
        outcome_verifier: Callable[[RunOutcome], bool] | None = None,
    ) -> None:
        self.policy = policy or ProgressivePolicy()
        self._role_resolver = role_resolver
        self._outcome_verifier = outcome_verifier
        self.credentials: dict[str, AuthorityCredential] = {}
        self.windows: dict[str, EvidenceWindow] = {}
        self.transitions: dict[str, list[AuthorityTransition]] = {}
        self._lock = threading.RLock()

    def enroll(self, agent_id: str, *, at: str) -> AuthorityCredential:
        with self._lock:
            if not agent_id.strip():
                raise ValueError("agent_id must not be empty")
            _instant(at)
            if agent_id in self.credentials:
                raise CommitmentError("agent is already enrolled")
            credential = AuthorityCredential(
                credential_id=f"authority::{agent_id}::v1",
                agent_id=agent_id,
                level=AuthorityLevel.OBSERVE,
                authority_version=1,
                policy_digest=self.policy.ref.digest,
                issued_by="progressive-commitment",
                issued_at=at,
            )
            self.credentials[agent_id] = credential
            self.windows[agent_id] = self._empty_window(credential)
            self.transitions[agent_id] = [
                AuthorityTransition(
                    transition_id=f"transition::{agent_id}::v1",
                    agent_id=agent_id,
                    from_level=None,
                    to_level=AuthorityLevel.OBSERVE,
                    from_version=None,
                    to_version=1,
                    policy_digest=self.policy.ref.digest,
                    reason_code="enrolled",
                    evidence_refs=(),
                    decided_by="progressive-commitment",
                    occurred_at=at,
                )
            ]
            return credential

    def record_outcome(self, agent_id: str, outcome: RunOutcome) -> EvidenceWindow:
        with self._lock:
            credential = self._current(agent_id)
            window = self.windows[agent_id]
            if window.policy_digest != self.policy.ref.digest:
                raise CommitmentError("evidence window belongs to another policy version")
            if window.authority_version != credential.authority_version:
                raise CommitmentError(
                    "evidence window belongs to another authority version"
                )
            if self._outcome_verifier is None:
                raise CommitmentError("a trusted outcome verifier is required")
            if not self._outcome_verifier(outcome):
                raise CommitmentError("run outcome failed trusted evidence verification")
            if _instant(outcome.occurred_at) < _instant(credential.issued_at):
                raise CommitmentError(
                    "run outcome predates the current authority version"
                )
            if any(item.run_id == outcome.run_id for item in window.outcomes):
                raise CommitmentError("run outcome identity is already recorded")
            if any(item.evidence_ref == outcome.evidence_ref for item in window.outcomes):
                raise CommitmentError("run outcome evidence is already recorded")
            updated = EvidenceWindow(
                agent_id,
                window.policy_digest,
                window.authority_version,
                window.outcomes + (outcome,),
            )
            self.windows[agent_id] = updated
            return updated

    def request_promotion(self, agent_id: str, *, at: str) -> PromotionRequest:
        with self._lock:
            credential = self._current(agent_id)
            requested_at = _instant(at)
            if requested_at < _instant(credential.issued_at):
                raise CommitmentError(
                    "promotion request predates the current authority version"
                )
            if credential.level is AuthorityLevel.AUTONOMOUS:
                raise CommitmentError("agent is already at the highest authority level")
            window = self.windows[agent_id]
            failures = self._promotion_failures(window, at=at)
            if failures:
                raise CommitmentError(
                    "promotion evidence is insufficient: " + ", ".join(failures)
                )
            return PromotionRequest(
                request_id=(
                    f"promotion::{agent_id}::{credential.level.name.lower()}"
                    f"-to-{AuthorityLevel(credential.level + 1).name.lower()}"
                    f"::{window.digest}"
                ),
                agent_id=agent_id,
                from_level=credential.level,
                to_level=AuthorityLevel(credential.level + 1),
                authority_version=credential.authority_version,
                policy_digest=self.policy.ref.digest,
                runs=window.runs,
                success_rate=window.success_rate,
                blockers=window.blockers,
                evidence_digest=window.digest,
                evidence_refs=tuple(
                    outcome.evidence_ref for outcome in window.outcomes
                ),
                requested_at=at,
            )

    def approve_promotion(
        self,
        request: PromotionRequest,
        *,
        approver_id: str,
        role: str,
        at: str,
    ) -> AuthorityCredential:
        with self._lock:
            current = self._current(request.agent_id)
            approval_at = _instant(at)
            requested_at = _instant(request.requested_at)
            if approval_at < requested_at:
                raise CommitmentError("promotion approval predates its request")
            if requested_at < _instant(current.issued_at):
                raise CommitmentError(
                    "promotion request predates the current authority version"
                )
            if role != self.policy.promotion_role:
                raise CommitmentError("approver does not hold the promotion role")
            if approver_id == request.agent_id:
                raise CommitmentError("an agent cannot promote itself")
            if self._role_resolver is None:
                raise CommitmentError("a trusted promotion role resolver is required")
            if role not in self._role_resolver(approver_id):
                raise CommitmentError(
                    "identity provider does not grant the promotion role"
                )
            if request.policy_digest != self.policy.ref.digest:
                raise CommitmentError(
                    "promotion request belongs to another policy version"
                )
            if request.authority_version != current.authority_version:
                raise CommitmentError("promotion request is stale")
            if request.from_level is not current.level:
                raise CommitmentError("promotion request starts from a stale level")
            if request.to_level is not AuthorityLevel(current.level + 1):
                raise CommitmentError("promotion must advance exactly one level")

            window = self.windows[request.agent_id]
            if request.evidence_digest != window.digest:
                raise CommitmentError("promotion request belongs to a stale evidence window")
            expected_refs = tuple(
                outcome.evidence_ref for outcome in window.outcomes
            )
            if (
                request.runs != window.runs
                or request.success_rate != window.success_rate
                or request.blockers != window.blockers
                or request.evidence_refs != expected_refs
            ):
                raise CommitmentError(
                    "promotion request summary does not match its evidence window"
                )
            expected_request_id = (
                f"promotion::{request.agent_id}::"
                f"{current.level.name.lower()}-to-"
                f"{AuthorityLevel(current.level + 1).name.lower()}::"
                f"{window.digest}"
            )
            if request.request_id != expected_request_id:
                raise CommitmentError(
                    "promotion request identity does not match its evidence window"
                )
            failures = self._promotion_failures(window, at=at)
            if failures:
                raise CommitmentError(
                    "promotion evidence is insufficient: " + ", ".join(failures)
                )

            credential = AuthorityCredential(
                credential_id=(
                    f"authority::{request.agent_id}::v"
                    f"{current.authority_version + 1}"
                ),
                agent_id=request.agent_id,
                level=request.to_level,
                authority_version=current.authority_version + 1,
                policy_digest=self.policy.ref.digest,
                issued_by=approver_id,
                issued_at=at,
            )
            self.credentials[request.agent_id] = credential
            self.windows[request.agent_id] = self._empty_window(credential)
            self.transitions[request.agent_id].append(
                AuthorityTransition(
                    transition_id=(
                        f"transition::{request.agent_id}::"
                        f"v{credential.authority_version}"
                    ),
                    agent_id=request.agent_id,
                    from_level=current.level,
                    to_level=credential.level,
                    from_version=current.authority_version,
                    to_version=credential.authority_version,
                    policy_digest=self.policy.ref.digest,
                    reason_code="promotion_approved",
                    evidence_refs=request.evidence_refs,
                    decided_by=approver_id,
                    occurred_at=at,
                )
            )
            return credential

    def authorize(
        self,
        proposal: ActionProposal,
        credential: AuthorityCredential,
        *,
        at: str,
        parent_receipts: tuple[GovernanceReceipt, ...] = (),
    ) -> GovernanceReceipt:
        with self._lock:
            current = self._current(credential.agent_id)
            decision_at = _instant(at)
            findings: list[GovernanceFinding] = []
            if decision_at < _instant(current.issued_at):
                findings.append(
                    self._finding(
                        "credential_not_yet_valid",
                        "authorization predates the current authority credential",
                        f"authority://{current.credential_id}",
                    )
                )
            if credential != current:
                findings.append(
                    self._finding(
                        "stale_credential",
                        "the supplied authority credential is no longer current",
                        f"authority://{credential.credential_id}",
                    )
                )
            if credential.policy_digest != self.policy.ref.digest:
                findings.append(
                    self._finding(
                        "policy_mismatch",
                        "credential belongs to another policy version",
                        f"policy://{self.policy.policy_id}/v{self.policy.version}",
                    )
                )

            profile = self.policy.profile(current.level)
            if proposal.action not in profile.allowed_actions:
                findings.append(
                    self._finding(
                        "action_not_authorized",
                        f"{current.level.name} does not authorize {proposal.action}",
                        f"authority://{current.credential_id}",
                    )
                )

            execution_mode = dict(proposal.attributes).get("execution_mode", "live")
            live = execution_mode == "live"
            if live and not profile.live_effects:
                findings.append(
                    self._finding(
                        "live_effect_not_authorized",
                        f"{current.level.name} permits observation or simulation only",
                        f"authority://{current.credential_id}",
                    )
                )
            if proposal.amount > profile.max_amount:
                findings.append(
                    self._finding(
                        "amount_above_authority",
                        "proposal amount exceeds the current authority profile",
                        f"authority://{current.credential_id}",
                    )
                )
            if proposal.subject_count > profile.max_subjects:
                findings.append(
                    self._finding(
                        "subjects_above_authority",
                        "proposal subject count exceeds the current authority profile",
                        f"authority://{current.credential_id}",
                    )
                )

            receipt_by_control = {
                receipt.control: receipt for receipt in parent_receipts
            }
            if len(receipt_by_control) != len(parent_receipts):
                findings.append(
                    self._finding(
                        "duplicate_parent_control",
                        "multiple parent receipts claim the same control",
                        f"proposal://{proposal.digest}",
                    )
                )
            if live:
                for control in profile.required_controls:
                    parent = receipt_by_control.get(control)
                    if (
                        parent is None
                        or parent.decision is not ControlDecision.ALLOWED
                        or parent.proposal_digest != proposal.digest
                        or _instant(parent.issued_at) > decision_at
                        or (
                            parent.expires_at is not None
                            and _instant(parent.expires_at) < decision_at
                        )
                    ):
                        findings.append(
                            self._finding(
                                "required_control_missing",
                                f"live authority requires an allowed {control} receipt",
                                f"proposal://{proposal.digest}",
                            )
                        )

            decision = ControlDecision.DENIED if findings else ControlDecision.ALLOWED
            return GovernanceReceipt(
                receipt_id=(
                    f"authority-receipt::{proposal.digest}::"
                    f"v{current.authority_version}::{decision.value}"
                ),
                control="progressive-commitment",
                proposal_digest=proposal.digest,
                policy_digest=self.policy.ref.digest,
                decided_by="progressive-commitment",
                decision=decision,
                issued_at=at,
                findings=tuple(findings),
                evidence_refs=(
                    f"authority://{current.credential_id}",
                    *tuple(
                        evidence
                        for parent in parent_receipts
                        for evidence in parent.evidence_refs
                    ),
                ),
                parent_receipts=tuple(receipt.digest for receipt in parent_receipts),
            )

    def demote(
        self,
        agent_id: str,
        *,
        severity: IncidentSeverity,
        reason_code: str,
        evidence_ref: str,
        decided_by: str,
        role: str,
        at: str,
    ) -> AuthorityCredential:
        with self._lock:
            current = self._current(agent_id)
            if (
                not reason_code.strip()
                or not evidence_ref.strip()
                or not decided_by.strip()
            ):
                raise ValueError(
                    "demotion must carry a reason, evidence, and decision owner"
                )
            decision_at = _instant(at)
            if decision_at < _instant(current.issued_at):
                raise CommitmentError(
                    "demotion predates the current authority version"
                )
            if role != self.policy.demotion_role:
                raise CommitmentError("decision owner does not hold the demotion role")
            if self._role_resolver is None:
                raise CommitmentError("a trusted demotion role resolver is required")
            if role not in self._role_resolver(decided_by):
                raise CommitmentError(
                    "identity provider does not grant the demotion role"
                )
            if severity is IncidentSeverity.CRITICAL:
                target = AuthorityLevel.OBSERVE
            else:
                target = AuthorityLevel(
                    max(AuthorityLevel.OBSERVE, current.level - 1)
                )
            credential = AuthorityCredential(
                credential_id=(
                    f"authority::{agent_id}::v{current.authority_version + 1}"
                ),
                agent_id=agent_id,
                level=target,
                authority_version=current.authority_version + 1,
                policy_digest=self.policy.ref.digest,
                issued_by=decided_by,
                issued_at=at,
            )
            self.credentials[agent_id] = credential
            self.windows[agent_id] = self._empty_window(credential)
            self.transitions[agent_id].append(
                AuthorityTransition(
                    transition_id=(
                        f"transition::{agent_id}::v{credential.authority_version}"
                    ),
                    agent_id=agent_id,
                    from_level=current.level,
                    to_level=target,
                    from_version=current.authority_version,
                    to_version=credential.authority_version,
                    policy_digest=self.policy.ref.digest,
                    reason_code=reason_code,
                    evidence_refs=(evidence_ref,),
                    decided_by=decided_by,
                    occurred_at=at,
                )
            )
            return credential

    def transition_history(self, agent_id: str) -> tuple[AuthorityTransition, ...]:
        with self._lock:
            self._current(agent_id)
            return tuple(self.transitions[agent_id])

    def _promotion_failures(
        self,
        window: EvidenceWindow,
        *,
        at: str,
    ) -> list[str]:
        now = _instant(at)
        failures: list[str] = []
        if window.runs < self.policy.min_runs:
            failures.append("insufficient_runs")
        if window.success_rate < self.policy.min_success_rate:
            failures.append("success_rate_below_threshold")
        if window.blockers > self.policy.max_blockers:
            failures.append("blocker_budget_exceeded")
        missing_slices = set(self.policy.required_evaluation_slices) - set(
            window.evaluation_slices
        )
        if missing_slices:
            failures.append("evaluation_slice_coverage_missing")
        oldest_allowed = now - timedelta(days=self.policy.evidence_max_age_days)
        if any(_instant(outcome.occurred_at) < oldest_allowed for outcome in window.outcomes):
            failures.append("stale_evidence")
        if any(_instant(outcome.occurred_at) > now for outcome in window.outcomes):
            failures.append("future_dated_evidence")
        return failures

    def _current(self, agent_id: str) -> AuthorityCredential:
        try:
            return self.credentials[agent_id]
        except KeyError as error:
            raise CommitmentError(f"unknown agent {agent_id!r}") from error

    def _empty_window(self, credential: AuthorityCredential) -> EvidenceWindow:
        return EvidenceWindow(
            credential.agent_id,
            self.policy.ref.digest,
            credential.authority_version,
        )

    @staticmethod
    def _finding(code: str, message: str, evidence: str) -> GovernanceFinding:
        return GovernanceFinding(code, message, evidence)
