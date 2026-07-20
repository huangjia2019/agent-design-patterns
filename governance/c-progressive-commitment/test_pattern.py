"""Invariants for the Progressive Commitment pattern."""
from __future__ import annotations

import os
import sys
from dataclasses import replace
from datetime import datetime, timedelta

import pytest


HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    ActionProposal,
    AuthorityLevel,
    DEFAULT_PROFILES,
    CommitmentError,
    ControlDecision,
    GovernanceReceipt,
    IncidentSeverity,
    ProgressiveCommitment,
    ProgressivePolicy,
    Reversibility,
    RiskLevel,
    RunOutcome,
)


def progressive_control(
    policy: ProgressivePolicy | None = None,
) -> ProgressiveCommitment:
    return ProgressiveCommitment(
        policy,
        role_resolver=lambda identity: (
            ("governance-owner",)
            if identity == "governance-admin"
            else (
                ("incident-responder",)
                if identity == "incident-monitor"
                else ()
            )
        ),
        outcome_verifier=lambda outcome: (
            outcome.recorded_by == "payroll-evaluator"
            and outcome.evidence_ref.startswith("eval://")
        ),
    )


def proposal(
    *,
    mode: str = "live",
    amount: float = 500_000,
    subjects: int = 20,
) -> ActionProposal:
    return ActionProposal(
        proposal_id="payroll-batch",
        version=1,
        contract_digest="contract",
        artifact_id="artifact",
        artifact_digest="artifact-content-v1",
        requested_by="payroll-agent",
        action="payroll.disburse",
        resource_scope=("payroll:2026-06", "bank:payroll"),
        idempotency_key="payroll-batch-v1",
        risk=RiskLevel.CRITICAL,
        reversibility=Reversibility.IRREVERSIBLE,
        amount=amount,
        subject_count=subjects,
        evidence_refs=("sqlite://payroll.db/paid",),
        attributes=(("execution_mode", mode),),
    )


def allowed_parent(control: str, item: ActionProposal) -> GovernanceReceipt:
    return GovernanceReceipt(
        receipt_id=f"{control}-receipt",
        control=control,
        proposal_digest=item.digest,
        policy_digest=f"{control}-policy",
        decided_by=control,
        decision=ControlDecision.ALLOWED,
        issued_at="2026-07-17T10:00:00+00:00",
        evidence_refs=(f"{control}://evidence",),
    )


def record_successes(
    progressive: ProgressiveCommitment,
    agent_id: str,
) -> None:
    issued_at = datetime.fromisoformat(
        progressive.credentials[agent_id].issued_at
    )
    for index in range(progressive.policy.min_runs):
        progressive.record_outcome(
            agent_id,
            RunOutcome(
                f"run-{index}",
                success=True,
                blocker=False,
                evidence_ref=f"eval://run-{index}",
                evaluation_slice=f"slice-{index}",
                occurred_at=(
                    issued_at + timedelta(minutes=index + 1)
                ).isoformat(),
                recorded_by="payroll-evaluator",
            ),
        )


def promote_once(
    progressive: ProgressiveCommitment,
    agent_id: str = "payroll-agent",
):
    record_successes(progressive, agent_id)
    issued_at = datetime.fromisoformat(
        progressive.credentials[agent_id].issued_at
    )
    request = progressive.request_promotion(
        agent_id,
        at=(issued_at + timedelta(minutes=10)).isoformat(),
    )
    return progressive.approve_promotion(
        request,
        approver_id="governance-admin",
        role="governance-owner",
        at=(issued_at + timedelta(minutes=11)).isoformat(),
    )


def reach_level(
    target: AuthorityLevel,
) -> tuple[ProgressiveCommitment, object]:
    progressive = progressive_control()
    credential = progressive.enroll(
        "payroll-agent",
        at="2026-07-17T09:00:00+00:00",
    )
    while credential.level < target:
        credential = promote_once(progressive)
    return progressive, credential


def test_new_agent_starts_at_observe() -> None:
    progressive = progressive_control()

    credential = progressive.enroll(
        "payroll-agent",
        at="2026-07-17T09:00:00+00:00",
    )

    assert credential.level is AuthorityLevel.OBSERVE
    assert progressive.windows["payroll-agent"].runs == 0


def test_promotion_requires_a_fresh_evidence_window() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")

    with pytest.raises(CommitmentError, match="insufficient_runs"):
        progressive.request_promotion(
            "payroll-agent",
            at="2026-07-17T10:00:00+00:00",
        )


def test_promotion_advances_one_level_and_resets_evidence() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")

    credential = promote_once(progressive)

    assert credential.level is AuthorityLevel.RECOMMEND
    assert credential.authority_version == 2
    assert progressive.windows["payroll-agent"].runs == 0


def test_blocker_prevents_promotion_even_with_enough_runs() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")
    record_successes(progressive, "payroll-agent")
    progressive.record_outcome(
        "payroll-agent",
        RunOutcome(
            "blocked",
            success=False,
            blocker=True,
            evidence_ref="eval://blocked",
            evaluation_slice="adversarial",
            occurred_at="2026-07-17T09:00:00+00:00",
            recorded_by="payroll-evaluator",
        ),
    )

    with pytest.raises(CommitmentError, match="blocker"):
        progressive.request_promotion(
            "payroll-agent",
            at="2026-07-17T10:00:00+00:00",
        )


def test_agent_cannot_promote_itself() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")
    record_successes(progressive, "payroll-agent")
    request = progressive.request_promotion(
        "payroll-agent",
        at="2026-07-17T10:00:00+00:00",
    )

    with pytest.raises(CommitmentError, match="itself"):
        progressive.approve_promotion(
            request,
            approver_id="payroll-agent",
            role="governance-owner",
            at="2026-07-17T10:01:00+00:00",
        )


def test_shadow_level_allows_simulation_but_denies_live_effect() -> None:
    progressive, credential = reach_level(AuthorityLevel.SHADOW)

    shadow = progressive.authorize(
        proposal(mode="shadow", amount=13_706_097, subjects=798),
        credential,
        at="2026-07-17T10:00:00+00:00",
    )
    live = progressive.authorize(
        proposal(mode="live", amount=13_706_097, subjects=798),
        credential,
        at="2026-07-17T10:00:00+00:00",
    )

    assert shadow.decision is ControlDecision.ALLOWED
    assert live.decision is ControlDecision.DENIED
    assert "live_effect_not_authorized" in {
        finding.code for finding in live.findings
    }


def test_limited_live_effect_requires_approval_and_containment() -> None:
    progressive, credential = reach_level(AuthorityLevel.LIMITED)
    item = proposal()

    missing = progressive.authorize(
        item,
        credential,
        at="2026-07-17T10:00:00+00:00",
    )
    allowed = progressive.authorize(
        item,
        credential,
        at="2026-07-17T10:00:00+00:00",
        parent_receipts=(
            allowed_parent("approval-gate", item),
            allowed_parent("blast-radius", item),
        ),
    )

    assert missing.decision is ControlDecision.DENIED
    assert allowed.decision is ControlDecision.ALLOWED


def test_limited_profile_enforces_amount_and_subject_caps() -> None:
    progressive, credential = reach_level(AuthorityLevel.LIMITED)
    item = proposal(amount=1_000_001, subjects=51)

    receipt = progressive.authorize(
        item,
        credential,
        at="2026-07-17T10:00:00+00:00",
        parent_receipts=(
            allowed_parent("approval-gate", item),
            allowed_parent("blast-radius", item),
        ),
    )

    assert receipt.decision is ControlDecision.DENIED
    assert {"amount_above_authority", "subjects_above_authority"} <= {
        finding.code for finding in receipt.findings
    }


def test_old_credential_is_invalid_after_promotion() -> None:
    progressive = progressive_control()
    old = progressive.enroll(
        "payroll-agent",
        at="2026-07-17T09:00:00+00:00",
    )
    promote_once(progressive)

    receipt = progressive.authorize(
        proposal(),
        old,
        at="2026-07-17T10:00:00+00:00",
    )

    assert receipt.decision is ControlDecision.DENIED
    assert "stale_credential" in {finding.code for finding in receipt.findings}


def test_critical_incident_demotes_to_observe_and_invalidates_old_credential() -> None:
    progressive, old = reach_level(AuthorityLevel.LIMITED)

    current = progressive.demote(
        "payroll-agent",
        severity=IncidentSeverity.CRITICAL,
        reason_code="duplicate_payment",
        evidence_ref="incident://duplicate-payment",
        decided_by="incident-monitor",
        role="incident-responder",
        at="2026-07-17T11:00:00+00:00",
    )

    assert current.level is AuthorityLevel.OBSERVE
    assert current.authority_version == old.authority_version + 1
    assert progressive.windows["payroll-agent"].runs == 0


def test_untrusted_actor_cannot_demote_an_agent() -> None:
    progressive, _ = reach_level(AuthorityLevel.LIMITED)

    with pytest.raises(CommitmentError, match="identity provider"):
        progressive.demote(
            "payroll-agent",
            severity=IncidentSeverity.CRITICAL,
            reason_code="authority_boundary_violation",
            evidence_ref="authority-receipt://denied",
            decided_by="unknown-monitor",
            role="incident-responder",
            at="2026-07-17T11:00:00+00:00",
        )


def test_policy_change_invalidates_existing_evidence() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")
    record_successes(progressive, "payroll-agent")
    progressive.policy = replace(progressive.policy, version=2)

    with pytest.raises(CommitmentError, match="another policy"):
        progressive.record_outcome(
            "payroll-agent",
            RunOutcome(
                "new-run",
                success=True,
                blocker=False,
                evidence_ref="eval://new-run",
                evaluation_slice="new-policy",
                occurred_at="2026-07-17T09:00:00+00:00",
                recorded_by="payroll-evaluator",
            ),
        )


def test_duplicate_run_or_evidence_cannot_be_counted_twice() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")
    first = RunOutcome(
        "run-1",
        True,
        False,
        "eval://run-1",
        "engineering",
        "2026-07-17T09:01:00+00:00",
        "payroll-evaluator",
    )
    progressive.record_outcome("payroll-agent", first)

    with pytest.raises(CommitmentError, match="identity"):
        progressive.record_outcome(
            "payroll-agent",
            replace(first, evidence_ref="eval://run-1-copy"),
        )
    with pytest.raises(CommitmentError, match="evidence"):
        progressive.record_outcome(
            "payroll-agent",
            replace(first, run_id="run-2"),
        )


def test_previous_level_evidence_cannot_enter_a_new_window() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")
    credential = promote_once(progressive)

    with pytest.raises(CommitmentError, match="predates"):
        progressive.record_outcome(
            "payroll-agent",
            RunOutcome(
                "old-level-run",
                True,
                False,
                "eval://old-level-run",
                "engineering",
                "2026-07-17T09:05:00+00:00",
                "payroll-evaluator",
            ),
        )
    assert credential.level is AuthorityLevel.RECOMMEND


def test_promotion_request_is_bound_to_the_exact_evidence_window() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")
    record_successes(progressive, "payroll-agent")
    request = progressive.request_promotion(
        "payroll-agent",
        at="2026-07-17T10:00:00+00:00",
    )
    progressive.record_outcome(
        "payroll-agent",
        RunOutcome(
            "late-blocker",
            False,
            True,
            "eval://late-blocker",
            "adversarial",
            "2026-07-17T10:00:30+00:00",
            "payroll-evaluator",
        ),
    )

    with pytest.raises(CommitmentError, match="stale evidence window"):
        progressive.approve_promotion(
            request,
            approver_id="governance-admin",
            role="governance-owner",
            at="2026-07-17T10:01:00+00:00",
        )


def test_promotion_can_require_evaluation_slice_coverage() -> None:
    policy = ProgressivePolicy(
        required_evaluation_slices=("slice-0", "adversarial"),
    )
    progressive = progressive_control(policy)
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")
    record_successes(progressive, "payroll-agent")

    with pytest.raises(CommitmentError, match="slice"):
        progressive.request_promotion(
            "payroll-agent",
            at="2026-07-17T10:00:00+00:00",
        )


def test_stale_evidence_cannot_support_a_new_promotion() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-05-01T09:00:00+00:00")
    for index in range(progressive.policy.min_runs):
        progressive.record_outcome(
            "payroll-agent",
            RunOutcome(
                f"old-{index}",
                True,
                False,
                f"eval://old-{index}",
                f"slice-{index}",
                f"2026-05-{10 + index:02d}T09:00:00+00:00",
                "payroll-evaluator",
            ),
        )

    with pytest.raises(CommitmentError, match="stale_evidence"):
        progressive.request_promotion(
            "payroll-agent",
            at="2026-07-17T10:00:00+00:00",
        )


def test_transition_history_keeps_promotion_and_incident_evidence() -> None:
    progressive, limited = reach_level(AuthorityLevel.LIMITED)
    progressive.demote(
        "payroll-agent",
        severity=IncidentSeverity.CRITICAL,
        reason_code="authority_boundary_violation",
        evidence_ref="authority-receipt://denied",
        decided_by="incident-monitor",
        role="incident-responder",
        at="2026-07-17T11:00:00+00:00",
    )

    history = progressive.transition_history("payroll-agent")
    assert history[0].reason_code == "enrolled"
    assert history[-1].from_level is limited.level
    assert history[-1].to_level is AuthorityLevel.OBSERVE
    assert history[-1].evidence_refs == ("authority-receipt://denied",)


def test_policy_profiles_must_cover_the_complete_chain() -> None:
    with pytest.raises(ValueError, match="every authority level"):
        ProgressivePolicy(profiles=())


def test_live_authority_profiles_must_expand_monotonically() -> None:
    profiles = list(DEFAULT_PROFILES)
    profiles[int(AuthorityLevel.AUTONOMOUS)] = replace(
        profiles[int(AuthorityLevel.AUTONOMOUS)],
        max_amount=500_000,
    )

    with pytest.raises(ValueError, match="grow monotonically"):
        ProgressivePolicy(profiles=tuple(profiles))


def test_higher_live_authority_must_retain_upstream_controls() -> None:
    profiles = list(DEFAULT_PROFILES)
    profiles[int(AuthorityLevel.AUTONOMOUS)] = replace(
        profiles[int(AuthorityLevel.AUTONOMOUS)],
        required_controls=("blast-radius",),
    )

    with pytest.raises(ValueError, match="retain upstream controls"):
        ProgressivePolicy(profiles=tuple(profiles))


def test_promotion_approval_rejects_backdating_and_summary_tampering() -> None:
    progressive = progressive_control()
    progressive.enroll("payroll-agent", at="2026-07-17T09:00:00+00:00")
    record_successes(progressive, "payroll-agent")
    request = progressive.request_promotion(
        "payroll-agent",
        at="2026-07-17T10:00:00+00:00",
    )

    with pytest.raises(CommitmentError, match="predates its request"):
        progressive.approve_promotion(
            request,
            approver_id="governance-admin",
            role="governance-owner",
            at="2026-07-17T09:30:00+00:00",
        )

    with pytest.raises(CommitmentError, match="summary"):
        progressive.approve_promotion(
            replace(request, evidence_refs=("eval://substituted",)),
            approver_id="governance-admin",
            role="governance-owner",
            at="2026-07-17T10:01:00+00:00",
        )


def test_demotion_cannot_precede_the_current_credential() -> None:
    progressive, _credential = reach_level(AuthorityLevel.LIMITED)

    with pytest.raises(CommitmentError, match="predates"):
        progressive.demote(
            "payroll-agent",
            severity=IncidentSeverity.CRITICAL,
            reason_code="duplicate_payment",
            evidence_ref="incident://duplicate-payment",
            decided_by="incident-monitor",
            role="incident-responder",
            at="2026-07-17T09:00:00+00:00",
        )


def test_authorization_rejects_expired_or_duplicate_parent_controls() -> None:
    progressive, credential = reach_level(AuthorityLevel.LIMITED)
    item = proposal()
    approval = replace(
        allowed_parent("approval-gate", item),
        expires_at="2026-07-17T09:59:00+00:00",
    )
    containment = allowed_parent("blast-radius", item)

    expired = progressive.authorize(
        item,
        credential,
        at="2026-07-17T10:00:00+00:00",
        parent_receipts=(approval, containment),
    )
    duplicated = progressive.authorize(
        item,
        credential,
        at="2026-07-17T10:00:00+00:00",
        parent_receipts=(containment, containment),
    )

    assert expired.decision is ControlDecision.DENIED
    assert "required_control_missing" in {
        finding.code for finding in expired.findings
    }
    assert duplicated.decision is ControlDecision.DENIED
    assert "duplicate_parent_control" in {
        finding.code for finding in duplicated.findings
    }
