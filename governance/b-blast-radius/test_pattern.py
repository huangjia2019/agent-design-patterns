"""Invariants for the Blast Radius Control pattern."""
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
    BlastBudget,
    BlastRadiusController,
    ContainmentError,
    ContainmentScope,
    ControlDecision,
    EffectStatus,
    LeaseStatus,
    Reversibility,
    RiskLevel,
)


def proposal(
    proposal_id: str = "engineering",
    *,
    amount: float = 5_000_000.0,
    subjects: int = 300,
    key: str | None = None,
) -> ActionProposal:
    return ActionProposal(
        proposal_id=proposal_id,
        version=1,
        contract_digest="contract",
        artifact_id=f"artifact-{proposal_id}",
        artifact_digest=f"artifact-{proposal_id}-content-v1",
        requested_by="payroll-agent",
        action="payroll.disburse",
        resource_scope=("payroll:2026-06", "bank:payroll"),
        idempotency_key=key or f"{proposal_id}-v1",
        risk=RiskLevel.CRITICAL,
        reversibility=Reversibility.IRREVERSIBLE,
        amount=amount,
        subject_count=subjects,
        evidence_refs=("sqlite://payroll.db/paid",),
    )


def controller() -> BlastRadiusController:
    control = BlastRadiusController()
    control.register_scope(
        ContainmentScope(
            "company",
            BlastBudget(
                15_000_000,
                800,
                4,
                ("payroll.disburse",),
                ("payroll:", "bank:"),
            ),
        )
    )
    for department in ("engineering", "operations", "sales"):
        control.register_scope(
            ContainmentScope(
                department,
                BlastBudget(
                    6_000_000,
                    350,
                    1,
                    ("payroll.disburse",),
                    ("payroll:", "bank:"),
                ),
                parent_id="company",
            )
        )
    return control


def test_child_scope_must_narrow_parent_budget() -> None:
    control = BlastRadiusController()
    control.register_scope(
        ContainmentScope(
            "root",
            BlastBudget(100, 10, 1, ("pay",), ("payroll:",)),
        )
    )

    with pytest.raises(ContainmentError, match="amount"):
        control.register_scope(
            ContainmentScope(
                "child",
                BlastBudget(101, 10, 1, ("pay",), ("payroll:",)),
                parent_id="root",
            )
        )


def test_child_scope_may_narrow_a_parent_resource_prefix() -> None:
    control = BlastRadiusController()
    control.register_scope(
        ContainmentScope(
            "root",
            BlastBudget(100, 10, 2, ("pay",), ("payroll:", "bank:")),
        )
    )
    control.register_scope(
        ContainmentScope(
            "engineering",
            BlastBudget(
                50,
                5,
                1,
                ("pay",),
                ("payroll:2026-06:engineering", "bank:payroll"),
            ),
            parent_id="root",
        )
    )

    assert control.scopes["engineering"].parent_id == "root"


def test_child_scope_cannot_escape_a_parent_resource_prefix() -> None:
    control = BlastRadiusController()
    control.register_scope(
        ContainmentScope(
            "root",
            BlastBudget(100, 10, 2, ("pay",), ("payroll:",)),
        )
    )

    with pytest.raises(ContainmentError, match="resources"):
        control.register_scope(
            ContainmentScope(
                "refunds",
                BlastBudget(50, 5, 1, ("pay",), ("customer:refunds",)),
                parent_id="root",
            )
        )


def test_reservation_consumes_leaf_and_parent_capacity_before_execution() -> None:
    control = controller()
    lease = control.reserve(
        proposal(),
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
    )
    snapshot = control.snapshot()

    assert lease.policy_digest == control.policy_ref.digest
    assert snapshot["engineering"]["reserved_amount"] == 5_000_000
    assert snapshot["company"]["reserved_amount"] == 5_000_000


def test_siblings_cannot_race_past_the_parent_limit() -> None:
    control = controller()
    control.reserve(
        proposal("engineering", amount=6_000_000, subjects=300),
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
    )
    control.reserve(
        proposal("operations", amount=6_000_000, subjects=250),
        scope_id="operations",
        at="2026-07-17T10:00:01+00:00",
    )

    with pytest.raises(ContainmentError, match="company"):
        control.reserve(
            proposal("sales", amount=4_000_000, subjects=200),
            scope_id="sales",
            at="2026-07-17T10:00:02+00:00",
        )


def test_commit_moves_reserved_usage_to_committed_usage() -> None:
    control = controller()
    item = proposal()
    lease = control.reserve(
        item,
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
    )

    receipt = control.commit(
        lease.lease_id,
        at="2026-07-17T10:01:00+00:00",
    )
    snapshot = control.snapshot()

    assert receipt.decision is ControlDecision.ALLOWED
    assert control.lease_status[lease.lease_id] is LeaseStatus.COMMITTED
    assert snapshot["company"]["reserved_amount"] == 0
    assert snapshot["company"]["committed_amount"] == item.amount


def test_reserved_lease_produces_a_pre_execution_control_receipt() -> None:
    control = controller()
    item = proposal()
    lease = control.reserve(
        item,
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
        parent_receipts=("approval-receipt",),
    )

    receipt = control.reservation_receipt(
        lease,
        item,
        at="2026-07-17T10:00:01+00:00",
    )

    assert receipt.decision is ControlDecision.ALLOWED
    assert receipt.control == "blast-radius"
    assert receipt.parent_receipts == ("approval-receipt",)
    assert receipt.proposal_digest == item.digest


def test_cancel_releases_capacity() -> None:
    control = controller()
    lease = control.reserve(
        proposal(),
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
    )

    receipt = control.cancel(
        lease.lease_id,
        at="2026-07-17T10:01:00+00:00",
    )

    assert receipt.decision is ControlDecision.REVOKED
    assert control.snapshot()["company"]["reserved_amount"] == 0


def test_kill_switch_revokes_existing_leases_and_blocks_new_ones() -> None:
    control = controller()
    item = proposal()
    lease = control.reserve(
        item,
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
    )

    receipts = control.trip_kill_switch(
        "company",
        at="2026-07-17T10:00:30+00:00",
    )

    assert receipts[0].decision is ControlDecision.REVOKED
    assert not control.authorizes(lease, item)
    with pytest.raises(ContainmentError, match="kill switch"):
        control.reserve(
            proposal("operations"),
            scope_id="operations",
            at="2026-07-17T10:01:00+00:00",
        )


def test_each_external_effect_consumes_a_one_use_live_permit() -> None:
    control = controller()
    item = proposal()
    lease = control.reserve(
        item,
        scope_id="engineering",
        allowed_refs=("E0001",),
        at="2026-07-17T10:00:00+00:00",
    )

    permit = control.begin_effect(
        lease,
        item,
        effect_ref="E0001",
        amount=1_000_000,
        idempotency_key="pay-E0001",
        at="2026-07-17T10:00:01+00:00",
    )
    snapshot = control.snapshot()["company"]

    assert control.effect_authorizes(permit, item)
    assert snapshot["reserved_amount"] == 4_000_000
    assert snapshot["in_flight_amount"] == 1_000_000
    with pytest.raises(ContainmentError, match="idempotency"):
        control.begin_effect(
            lease,
            item,
            effect_ref="E0001",
            amount=1_000_000,
            idempotency_key="pay-E0001",
            at="2026-07-17T10:00:02+00:00",
        )
    with pytest.raises(ContainmentError, match="reference"):
        control.begin_effect(
            lease,
            item,
            effect_ref="E0001",
            amount=1_000_000,
            idempotency_key="retry-E0001",
            at="2026-07-17T10:00:03+00:00",
        )


def test_kill_switch_quarantines_in_flight_effect_without_releasing_its_budget() -> None:
    control = controller()
    item = proposal()
    lease = control.reserve(
        item,
        scope_id="engineering",
        allowed_refs=("E0001",),
        at="2026-07-17T10:00:00+00:00",
    )
    permit = control.begin_effect(
        lease,
        item,
        effect_ref="E0001",
        amount=1_000_000,
        idempotency_key="pay-E0001",
        at="2026-07-17T10:00:01+00:00",
    )

    control.trip_kill_switch(
        "company",
        at="2026-07-17T10:00:02+00:00",
    )
    snapshot = control.snapshot()["company"]

    assert not control.effect_authorizes(permit, item)
    assert control.effect_status[permit.permit_id] is EffectStatus.UNKNOWN
    assert control.lease_status[lease.lease_id] is LeaseStatus.RECONCILING
    assert snapshot["reserved_amount"] == 0
    assert snapshot["unknown_amount"] == 1_000_000

    receipt = control.confirm_effect(
        permit.permit_id,
        succeeded=True,
        at="2026-07-17T10:01:00+00:00",
    )
    snapshot = control.snapshot()["company"]

    assert receipt.decision is ControlDecision.ALLOWED
    assert snapshot["unknown_amount"] == 0
    assert snapshot["committed_amount"] == 1_000_000


def test_confirmed_failure_returns_capacity_to_a_live_lease() -> None:
    control = controller()
    item = proposal()
    lease = control.reserve(
        item,
        scope_id="engineering",
        allowed_refs=("E0001",),
        at="2026-07-17T10:00:00+00:00",
    )
    permit = control.begin_effect(
        lease,
        item,
        effect_ref="E0001",
        amount=1_000_000,
        idempotency_key="pay-E0001-attempt-1",
        at="2026-07-17T10:00:01+00:00",
    )

    control.confirm_effect(
        permit.permit_id,
        succeeded=False,
        at="2026-07-17T10:00:02+00:00",
    )
    retry = control.begin_effect(
        lease,
        item,
        effect_ref="E0001",
        amount=1_000_000,
        idempotency_key="pay-E0001-attempt-2",
        at="2026-07-17T10:00:03+00:00",
    )

    assert control.effect_authorizes(retry, item)
    assert control.effect_status[permit.permit_id] is EffectStatus.RELEASED


def test_last_permit_releases_unused_amount_instead_of_leaking_reservation() -> None:
    control = controller()
    item = proposal()
    lease = control.reserve(
        item,
        scope_id="engineering",
        allowed_refs=("E0001",),
        at="2026-07-17T10:00:00+00:00",
    )
    permit = control.begin_effect(
        lease,
        item,
        effect_ref="E0001",
        amount=1_000_000,
        idempotency_key="pay-E0001",
        at="2026-07-17T10:00:01+00:00",
    )

    control.confirm_effect(
        permit.permit_id,
        succeeded=True,
        at="2026-07-17T10:00:02+00:00",
    )
    snapshot = control.snapshot()["company"]

    assert control.lease_status[lease.lease_id] is LeaseStatus.COMMITTED
    assert snapshot["reserved_amount"] == 0
    assert snapshot["committed_amount"] == 1_000_000


def test_idempotency_returns_the_same_lease_for_the_same_proposal() -> None:
    control = controller()
    item = proposal()

    first = control.reserve(
        item,
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
    )
    second = control.reserve(
        item,
        scope_id="engineering",
        at="2026-07-17T10:00:01+00:00",
    )

    assert first == second
    assert control.snapshot()["company"]["reserved_effects"] == 1


def test_idempotency_key_cannot_move_to_a_changed_effect() -> None:
    control = controller()
    item = proposal()
    control.reserve(
        item,
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
    )

    with pytest.raises(ContainmentError, match="another proposal"):
        control.reserve(
            replace(item, amount=item.amount + 1),
            scope_id="engineering",
            at="2026-07-17T10:00:01+00:00",
        )


def test_changed_proposals_with_the_same_business_id_get_distinct_lease_ids() -> None:
    control = BlastRadiusController()
    control.register_scope(
        ContainmentScope(
            "root",
            BlastBudget(
                100,
                10,
                2,
                ("payroll.disburse",),
                ("payroll:", "bank:"),
            ),
        )
    )
    first_proposal = proposal("same-business-id", amount=10, subjects=1, key="first")
    second_proposal = replace(first_proposal, amount=11, idempotency_key="second")

    first = control.reserve(
        first_proposal,
        scope_id="root",
        at="2026-07-17T10:00:00+00:00",
    )
    second = control.reserve(
        second_proposal,
        scope_id="root",
        at="2026-07-17T10:00:01+00:00",
    )

    assert first.lease_id != second.lease_id
    assert len(control.leases) == 2


def test_leaf_rejects_an_out_of_scope_resource() -> None:
    control = controller()

    with pytest.raises(ContainmentError, match="resources"):
        control.reserve(
            replace(proposal(), resource_scope=("customer:refunds",)),
            scope_id="engineering",
            at="2026-07-17T10:00:00+00:00",
        )


def test_policy_is_sealed_on_first_reservation() -> None:
    control = controller()
    control.reserve(
        proposal(),
        scope_id="engineering",
        at="2026-07-17T10:00:00+00:00",
    )

    with pytest.raises(ContainmentError, match="sealed"):
        control.register_scope(
            ContainmentScope(
                "finance",
                BlastBudget(
                    1,
                    1,
                    1,
                    ("payroll.disburse",),
                    ("payroll:",),
                ),
                parent_id="company",
            )
        )
