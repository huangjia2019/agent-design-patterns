"""Invariants for the Approval Gate pattern."""
from __future__ import annotations

import os
import sys
from dataclasses import replace

import pytest


HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    ActionProposal,
    ApprovalError,
    ApprovalGate,
    ApprovalPolicy,
    ApprovalRoute,
    ControlDecision,
    Reversibility,
    RiskLevel,
)


NOW = "2026-07-17T10:00:00+00:00"
ROLE_DIRECTORY = {
    "alice": ("payroll-controller",),
    "bob": ("treasury-controller",),
    "carol": ("governance-owner",),
    "dave": ("risk-owner",),
}


def approval_gate(policy: ApprovalPolicy | None = None) -> ApprovalGate:
    return ApprovalGate(
        policy,
        role_resolver=lambda approver_id: ROLE_DIRECTORY.get(approver_id, ()),
    )


def payroll_proposal(**changes) -> ActionProposal:
    values = {
        "proposal_id": "payroll-2026-06",
        "version": 1,
        "contract_digest": "contract-a",
        "artifact_id": "artifact-a",
        "artifact_digest": "artifact-content-a",
        "requested_by": "payroll-agent",
        "action": "payroll.disburse",
        "resource_scope": ("payroll:2026-06", "bank:payroll"),
        "idempotency_key": "payroll-2026-06-v1",
        "risk": RiskLevel.CRITICAL,
        "reversibility": Reversibility.IRREVERSIBLE,
        "amount": 13_706_097.0,
        "subject_count": 798,
        "evidence_refs": ("sqlite://payroll.db/paid",),
    }
    values.update(changes)
    return ActionProposal(**values)


def complete_approval(
    gate: ApprovalGate,
    proposal: ActionProposal,
) -> tuple:
    routed = gate.evaluate(proposal, now=NOW)
    first = gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at="2026-07-17T10:05:00+00:00",
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="bob",
        role="treasury-controller",
        approved=True,
        at="2026-07-17T10:06:00+00:00",
    )
    return routed, first, final


def install_next_policy(gate: ApprovalGate) -> tuple[ApprovalPolicy, ActionProposal]:
    next_policy = replace(gate.policy, version=gate.policy.version + 1)
    proposal = payroll_proposal(
        proposal_id=f"approval-policy-v{next_policy.version}",
        version=next_policy.version,
        artifact_id=next_policy.policy_id,
        artifact_digest=next_policy.ref.content_digest,
        requested_by="governance-agent",
        action="governance.approval-policy.update",
        resource_scope=(f"policy:{next_policy.policy_id}",),
        idempotency_key=f"approval-policy-v{next_policy.version}",
        amount=0,
        subject_count=1,
        evidence_refs=(f"policy://{next_policy.policy_id}/v{next_policy.version}",),
    )
    routed = gate.evaluate(proposal, now=NOW)
    assert routed.ticket.required_roles == ("governance-owner", "risk-owner")
    gate.attest(
        routed.ticket.ticket_id,
        approver_id="carol",
        role="governance-owner",
        approved=True,
        at="2026-07-17T10:02:00+00:00",
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="dave",
        role="risk-owner",
        approved=True,
        at="2026-07-17T10:03:00+00:00",
    )
    gate.install_policy(
        next_policy,
        proposal=proposal,
        receipt=final.receipt,
        at="2026-07-17T10:04:00+00:00",
    )
    return next_policy, proposal


def test_low_risk_small_effect_is_auto_allowed() -> None:
    gate = approval_gate()
    proposal = payroll_proposal(
        proposal_id="preview",
        action="payroll.preview",
        risk=RiskLevel.LOW,
        reversibility=Reversibility.REVERSIBLE,
        amount=0,
        subject_count=1,
    )

    result = gate.evaluate(proposal, now=NOW)

    assert result.route is ApprovalRoute.AUTO_ALLOW
    assert result.receipt.decision is ControlDecision.ALLOWED
    assert gate.authorize(proposal, result.receipt, at=NOW)


def test_payroll_release_routes_to_two_role_human_review() -> None:
    result = approval_gate().evaluate(payroll_proposal(), now=NOW)

    assert result.route is ApprovalRoute.HUMAN_REVIEW
    assert result.receipt.decision is ControlDecision.PENDING
    assert result.ticket.required_roles == (
        "payroll-controller",
        "treasury-controller",
    )
    assert {
        "amount_requires_review",
        "subject_count_requires_review",
        "risk_requires_review",
        "irreversible_effect",
    } <= set(result.ticket.reason_codes)


@pytest.mark.parametrize(
    ("amount", "roles"),
    (
        (9_800.0, ("payroll-operator",)),
        (2_400_000.0, ("payroll-supervisor",)),
        (12_500_000.0, ("finance-controller",)),
        (13_706_097.0, ("payroll-controller", "treasury-controller")),
    ),
)
def test_human_review_routes_amount_to_the_required_signers(
    amount: float,
    roles: tuple[str, ...],
) -> None:
    result = approval_gate().evaluate(payroll_proposal(amount=amount), now=NOW)

    assert result.route is ApprovalRoute.HUMAN_REVIEW
    assert result.ticket.required_roles == roles


def test_all_required_roles_produce_an_authorizing_receipt() -> None:
    gate = approval_gate()
    proposal = payroll_proposal()
    _routed, first, final = complete_approval(gate, proposal)

    assert first.receipt.decision is ControlDecision.PENDING
    assert final.receipt.decision is ControlDecision.ALLOWED
    assert gate.authorize(
        proposal,
        final.receipt,
        at="2026-07-17T10:10:00+00:00",
    )


def test_maker_cannot_approve_its_own_proposal() -> None:
    gate = approval_gate()
    result = gate.evaluate(payroll_proposal(), now=NOW)

    with pytest.raises(ApprovalError, match="maker"):
        gate.attest(
            result.ticket.ticket_id,
            approver_id="payroll-agent",
            role="payroll-controller",
            approved=True,
            at="2026-07-17T10:05:00+00:00",
        )


def test_one_person_cannot_fill_two_required_roles() -> None:
    gate = ApprovalGate(
        role_resolver=lambda approver_id: (
            ("payroll-controller", "treasury-controller")
            if approver_id == "alice"
            else ()
        )
    )
    result = gate.evaluate(payroll_proposal(), now=NOW)
    gate.attest(
        result.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at="2026-07-17T10:05:00+00:00",
    )

    with pytest.raises(ApprovalError, match="multiple"):
        gate.attest(
            result.ticket.ticket_id,
            approver_id="alice",
            role="treasury-controller",
            approved=True,
            at="2026-07-17T10:06:00+00:00",
        )


def test_human_rejection_is_fail_closed() -> None:
    gate = approval_gate()
    result = gate.evaluate(payroll_proposal(), now=NOW)

    denied = gate.attest(
        result.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=False,
        at="2026-07-17T10:05:00+00:00",
    )

    assert denied.route is ApprovalRoute.DENY
    assert denied.receipt.decision is ControlDecision.DENIED


def test_expired_ticket_is_denied() -> None:
    gate = approval_gate(ApprovalPolicy(ticket_ttl_minutes=5))
    result = gate.evaluate(payroll_proposal(), now=NOW)

    expired = gate.attest(
        result.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at="2026-07-17T10:06:00+00:00",
    )

    assert expired.receipt.decision is ControlDecision.DENIED
    assert {finding.code for finding in expired.receipt.findings} == {
        "approval_expired"
    }


def test_hard_limit_is_denied_without_creating_a_ticket() -> None:
    gate = approval_gate()

    result = gate.evaluate(
        payroll_proposal(amount=20_000_001.0),
        now=NOW,
    )

    assert result.route is ApprovalRoute.DENY
    assert result.ticket is None
    assert "amount_above_hard_limit" in {
        finding.code for finding in result.receipt.findings
    }


def test_approval_cannot_move_to_a_changed_proposal() -> None:
    gate = approval_gate()
    proposal = payroll_proposal()
    _routed, _first, final = complete_approval(gate, proposal)

    assert not gate.authorize(
        replace(proposal, artifact_digest="artifact-content-changed"),
        final.receipt,
        at="2026-07-17T10:10:00+00:00",
    )


def test_re_evaluating_a_pending_binding_preserves_signatures_and_expiry() -> None:
    gate = approval_gate()
    proposal = payroll_proposal()
    routed = gate.evaluate(proposal, now=NOW)
    first = gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at="2026-07-17T10:05:00+00:00",
    )

    repeated = gate.evaluate(proposal, now="2026-07-17T10:20:00+00:00")

    assert repeated.ticket.ticket_id == routed.ticket.ticket_id
    assert repeated.ticket.expires_at == routed.ticket.expires_at
    assert repeated.ticket.attestations == first.ticket.attestations
    assert repeated.receipt.digest == first.receipt.digest


def test_re_evaluating_a_final_binding_returns_the_final_receipt() -> None:
    gate = approval_gate()
    proposal = payroll_proposal()
    _routed, _first, final = complete_approval(gate, proposal)

    repeated = gate.evaluate(proposal, now="2026-07-17T10:20:00+00:00")

    assert repeated.route is ApprovalRoute.HUMAN_REVIEW
    assert repeated.receipt.digest == final.receipt.digest
    assert repeated.receipt.decision is ControlDecision.ALLOWED


def test_a_new_policy_version_gets_a_distinct_ticket_binding() -> None:
    gate = approval_gate()
    proposal = payroll_proposal()
    old = gate.evaluate(proposal, now=NOW)
    install_next_policy(gate)

    new = gate.evaluate(proposal, now="2026-07-17T10:01:00+00:00")

    assert new.ticket.ticket_id != old.ticket.ticket_id
    assert new.ticket.policy_digest != old.ticket.policy_digest


def test_ticket_does_not_survive_a_policy_change() -> None:
    gate = approval_gate()
    result = gate.evaluate(payroll_proposal(), now=NOW)
    install_next_policy(gate)

    with pytest.raises(ApprovalError, match="policy version"):
        gate.attest(
            result.ticket.ticket_id,
            approver_id="alice",
            role="payroll-controller",
            approved=True,
            at="2026-07-17T10:05:00+00:00",
        )


def test_policy_installation_rejects_a_proposal_for_other_content() -> None:
    gate = approval_gate()
    next_policy = replace(gate.policy, version=2)
    proposal = payroll_proposal(
        proposal_id="approval-policy-v2",
        version=2,
        artifact_id=next_policy.policy_id,
        artifact_digest="different-policy-content",
        requested_by="governance-agent",
        action="governance.approval-policy.update",
        resource_scope=(f"policy:{next_policy.policy_id}",),
        idempotency_key="approval-policy-v2",
        amount=0,
        subject_count=1,
    )
    routed = gate.evaluate(proposal, now=NOW)
    gate.attest(
        routed.ticket.ticket_id,
        approver_id="carol",
        role="governance-owner",
        approved=True,
        at="2026-07-17T10:02:00+00:00",
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="dave",
        role="risk-owner",
        approved=True,
        at="2026-07-17T10:03:00+00:00",
    )

    with pytest.raises(ApprovalError, match="new policy content"):
        gate.install_policy(
            next_policy,
            proposal=proposal,
            receipt=final.receipt,
            at="2026-07-17T10:04:00+00:00",
        )


def test_policy_validates_threshold_order() -> None:
    with pytest.raises(ValueError, match="exceed"):
        ApprovalPolicy(
            auto_allow_max_amount=100,
            deny_above_amount=100,
        )


def test_claimed_role_must_come_from_a_trusted_identity_provider() -> None:
    gate = ApprovalGate(role_resolver=lambda _approver_id: ())
    result = gate.evaluate(payroll_proposal(), now=NOW)

    with pytest.raises(ApprovalError, match="identity provider"):
        gate.attest(
            result.ticket.ticket_id,
            approver_id="mallory",
            role="payroll-controller",
            approved=True,
            at="2026-07-17T10:05:00+00:00",
        )


def test_rejected_ticket_is_terminal() -> None:
    gate = approval_gate()
    result = gate.evaluate(payroll_proposal(), now=NOW)
    gate.attest(
        result.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=False,
        at="2026-07-17T10:05:00+00:00",
    )

    with pytest.raises(ApprovalError, match="already closed"):
        gate.attest(
            result.ticket.ticket_id,
            approver_id="bob",
            role="treasury-controller",
            approved=True,
            at="2026-07-17T10:06:00+00:00",
        )
