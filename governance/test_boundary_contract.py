"""Invariants for the shared governance boundary contract."""
from __future__ import annotations

import os
import sys
from dataclasses import replace

import pytest


sys.path.insert(0, os.path.dirname(__file__))

from boundary_contract import (  # noqa: E402
    ActionProposal,
    ControlDecision,
    FindingSeverity,
    GovernanceFinding,
    GovernanceReceipt,
    PolicyRef,
    Reversibility,
    RiskLevel,
)


def proposal() -> ActionProposal:
    return ActionProposal(
        proposal_id="payroll-2026-06",
        version=1,
        contract_digest="contract-a",
        artifact_id="artifact-a",
        artifact_digest="artifact-content-a",
        requested_by="payroll-controller",
        action="payroll.disburse",
        resource_scope=("payroll:2026-06", "bank:payroll"),
        idempotency_key="payroll-2026-06-v1",
        risk=RiskLevel.CRITICAL,
        reversibility=Reversibility.IRREVERSIBLE,
        amount=13_706_097.0,
        subject_count=798,
        evidence_refs=("sqlite://payroll.db/paid",),
    )


def policy() -> PolicyRef:
    return PolicyRef.from_content(
        "governance",
        1,
        {"max_amount": 15_000_000, "roles": ["payroll", "treasury"]},
    )


def receipt(
    item: ActionProposal | None = None,
    ref: PolicyRef | None = None,
) -> GovernanceReceipt:
    item = item or proposal()
    ref = ref or policy()
    return GovernanceReceipt(
        receipt_id="receipt-a",
        control="approval-gate",
        proposal_digest=item.digest,
        policy_digest=ref.digest,
        decided_by="payroll-controller",
        decision=ControlDecision.ALLOWED,
        issued_at="2026-07-17T10:00:00+00:00",
        expires_at="2026-07-17T11:00:00+00:00",
        evidence_refs=("approval://ticket-a",),
    )


def test_proposal_digest_changes_with_the_requested_effect() -> None:
    item = proposal()

    assert item.digest != replace(item, amount=item.amount + 1).digest
    assert item.digest != replace(item, artifact_id="artifact-b").digest
    assert item.digest != replace(item, artifact_digest="artifact-content-b").digest
    assert item.digest != replace(item, version=2).digest


def test_policy_ref_is_content_addressed() -> None:
    first = policy()
    same = policy()
    changed = PolicyRef.from_content(
        "governance",
        1,
        {"max_amount": 10_000_000, "roles": ["payroll", "treasury"]},
    )

    assert first.digest == same.digest
    assert first.digest != changed.digest


def test_receipt_authorizes_only_the_bound_proposal_and_policy() -> None:
    item = proposal()
    ref = policy()
    approval = receipt(item, ref)

    assert approval.authorizes(item, ref, at="2026-07-17T10:30:00+00:00")
    assert not approval.authorizes(
        replace(item, amount=item.amount + 1),
        ref,
        at="2026-07-17T10:30:00+00:00",
    )
    assert not approval.authorizes(
        item,
        PolicyRef.from_content("governance", 2, {"max_amount": 15_000_000}),
        at="2026-07-17T10:30:00+00:00",
    )
    assert not approval.authorizes(item, ref, at="2026-07-17T12:00:00+00:00")


def test_pending_receipt_must_expire() -> None:
    with pytest.raises(ValueError, match="pending receipt must expire"):
        GovernanceReceipt(
            receipt_id="pending",
            control="approval-gate",
            proposal_digest=proposal().digest,
            policy_digest=policy().digest,
            decided_by="approval-router",
            decision=ControlDecision.PENDING,
            issued_at="2026-07-17T10:00:00+00:00",
        )


def test_receipt_expiry_compares_instants_across_timezones() -> None:
    item = proposal()
    ref = policy()
    approval = receipt(item, ref)

    assert approval.authorizes(
        item,
        ref,
        at="2026-07-17T11:30:00+02:00",
    )


def test_allowed_receipt_cannot_hide_a_blocker() -> None:
    with pytest.raises(ValueError, match="allowed receipt"):
        replace(
            receipt(),
            findings=(
                GovernanceFinding(
                    "policy_violation",
                    "amount exceeds policy",
                    "policy://governance/v1",
                    FindingSeverity.BLOCKER,
                ),
            ),
        )


@pytest.mark.parametrize("amount", [-1.0])
def test_proposal_rejects_invalid_effect_dimensions(amount: float) -> None:
    with pytest.raises(ValueError, match="amount"):
        replace(proposal(), amount=amount)
