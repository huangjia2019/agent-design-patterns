"""Integration tests for the Payroll Governance Lab."""
from __future__ import annotations

import os
import sqlite3
import sys
from dataclasses import replace

import pytest


sys.path.insert(0, os.path.dirname(__file__))

from governance_payroll_imports import load_local  # noqa: E402


bench = load_local("bench")
governance_lab = load_local("governance_lab")
TIMES = governance_lab.TIMES
approval = governance_lab.approval
run_changed_after_approval = governance_lab.run_changed_after_approval
run_approval_gate = governance_lab.run_approval_gate
run_approval_policy_change = governance_lab.run_approval_policy_change
run_blast_radius = governance_lab.run_blast_radius
run_blast_radius_retry_storm = governance_lab.run_blast_radius_retry_storm
run_governed = governance_lab.run_governed
run_naive = governance_lab.run_naive
run_progressive_commitment = governance_lab.run_progressive_commitment
approval_controller = governance_lab.approval_controller


def test_local_modules_do_not_claim_generic_import_names() -> None:
    assert bench.__name__ == "_adps_governance_payroll_bench"
    assert governance_lab.__name__ == "_adps_governance_payroll_governance_lab"
    assert sys.modules.get("bench") is not bench
    assert sys.modules.get("governance_lab") is not governance_lab


def test_collaboration_artifact_is_real_and_acceptance_grants_no_authority() -> None:
    bench.prepare()
    contract, artifact, acceptance = bench.reviewed_artifact()

    assert acceptance.accepted
    assert artifact.contract_digest == contract.digest
    assert artifact.payload.employee_count == 798
    assert artifact.payload.amount == 13_706_097.0
    assert contract.authority_scope == ("read:payroll", "propose:payment")


def test_proposal_boundary_consumes_the_contract_authority_scope() -> None:
    bench.prepare()
    contract, _artifact, _acceptance = bench.reviewed_artifact()
    read_only = replace(contract, authority_scope=("read:payroll",))

    assert (
        bench.require_contract_proposal_authority(
            contract,
            "payroll.disburse",
        )
        == "propose:payment"
    )
    with pytest.raises(PermissionError, match="requires 'propose:payment'"):
        bench.require_contract_proposal_authority(
            read_only,
            "payroll.disburse",
        )


def test_naive_bridge_pays_with_zero_governance_receipts() -> None:
    result = run_naive()

    assert result["artifact_acceptance"] == "accepted"
    assert result["governance_receipts"] == 0
    assert result["payment"]["amount"] == 13_706_097.0
    assert result["state"]["payment_count"] == 1


def test_governed_bridge_completes_all_controls_and_trace() -> None:
    result = run_governed()

    assert result["approval"]["final"] == "allowed"
    assert result["containment"]["reservation"] == "allowed"
    assert result["authority"]["level"] == "AUTONOMOUS"
    assert result["authority"]["decision"] == "allowed"
    assert result["payment"]["amount"] == 13_706_097.0
    assert result["audit"]["complete"]
    assert result["audit"]["chain_valid"]
    assert result["audit"]["event_count"] == 7
    assert result["state"]["receipt_count"] == 5


def test_changed_proposal_cannot_reuse_old_approval() -> None:
    result = run_changed_after_approval()

    assert result["original_digest"] != result["changed_digest"]
    assert not result["old_approval_authorizes"]
    assert "invalid receipts: approval-gate" in result["adapter_result"]
    assert result["state"]["payment_count"] == 0


def test_retry_storm_is_bounded_by_one_use_effect_permits() -> None:
    result = run_blast_radius_retry_storm()

    assert result["unbounded"] == {
        "approved_amount": 13_706_097.0,
        "payment_count": 1438,
        "money_out": 24_701_937.0,
        "overpay": 10_995_840.0,
    }
    assert result["bounded"]["payment_count"] == 798
    assert result["bounded"]["money_out"] == 13_706_097.0
    assert result["bounded"]["refused_draws"] == 640
    root = result["snapshot"]["payroll-window::2026-06"]
    assert root["reserved_amount"] == 0
    assert root["in_flight_amount"] == 0
    assert root["unknown_amount"] == 0
    assert root["committed_amount"] == 13_706_097.0


def test_approval_scene_exposes_route_roles_and_bound_receipt() -> None:
    result = run_approval_gate()

    assert result["route"]["name"] == "human_review"
    assert set(result["route"]["reason_codes"]) == {
        "amount_requires_review",
        "subject_count_requires_review",
        "risk_requires_review",
        "irreversible_effect",
    }
    assert result["attestations"][0]["decision"] == "pending"
    assert result["attestations"][1]["decision"] == "allowed"
    assert result["final_receipt"]["proposal_digest"] == result["proposal"]["digest"]
    assert result["state"]["receipt_count"] == 2


def test_approval_scene_changed_variant_fails_at_approval_binding() -> None:
    result = run_approval_gate(changed_after_approval=True)

    assert result["changed"]["restored_ids"] == ("E0007", "E0012")
    assert result["changed"]["delta_amount"] == 38_444.0
    assert result["changed"]["changed_subject_count"] == 800
    assert (
        result["changed"]["original_artifact_digest"]
        != result["changed"]["changed_artifact_digest"]
    )
    assert not result["changed"]["old_approval_authorizes"]
    assert "invalid receipts: approval-gate" in result["changed"]["adapter_result"]
    assert result["state"]["payment_count"] == 0


def test_approval_policy_change_is_approved_under_the_old_policy() -> None:
    result = run_approval_policy_change()

    assert result["route"] == "human_review"
    assert result["required_roles"] == ("governance-owner", "risk-owner")
    assert result["first_decision"] == "pending"
    assert result["final_decision"] == "allowed"
    assert result["installed_policy_version"] == 2
    assert result["approved_under_policy"] != result["installed_policy_digest"]


def test_equal_total_artifact_drift_changes_the_proposal_binding() -> None:
    bench.prepare()
    original = bench.release_proposal()
    with sqlite3.connect(bench.ACTION_LAB / "payroll.db") as con:
        con.execute(
            "UPDATE employees SET bank_account=? WHERE emp_id='E0042'",
            ("6222-0042-REVIEW",),
        )
        con.commit()
    changed = bench.release_proposal()

    assert changed.amount == original.amount
    assert changed.subject_count == original.subject_count
    assert changed.contract_digest == original.contract_digest
    assert changed.artifact_id == original.artifact_id
    assert changed.artifact_digest != original.artifact_digest
    assert changed.digest != original.digest


def test_sibling_batches_are_locally_legal_but_share_the_parent_window() -> None:
    result = run_blast_radius(include_third=True)

    engineering, finance, operations = result["batches"]
    assert engineering["amount"] == 2_738_800
    assert finance["amount"] == 2_726_337
    assert operations["amount"] == 2_748_960
    assert all(item["leaf_legal"] for item in result["batches"])
    assert finance["root_after"] == 5_465_137
    assert operations["root_after"] == 5_465_137
    assert operations["decision"] == "blocked"
    assert "payroll-window" in operations["blocked_at"]
    assert result["state"]["payment_count"] == 0


def test_progressive_commitment_uses_real_slices_and_a_real_canary() -> None:
    result = run_progressive_commitment()

    assert result["evidence_windows"][0]["evaluation_slices"] == (
        "Engineering",
        "Finance",
        "Ops",
        "Sales",
        "Support",
    )
    assert result["limited"]["canary_amount"] == 168_658
    assert result["limited"]["canary_subjects"] == 20
    assert result["limited"]["canary_decision"] == "allowed"
    assert set(result["limited"]["full_findings"]) == {
        "amount_above_authority",
        "subjects_above_authority",
    }
    assert len(bench.table_rows("authority_transitions")) == 4
    assert bench.table_rows("authority_transitions")[-1]["to_level"] == "LIMITED"
    assert result["timeline"][1]["summary"].startswith("OBSERVE -> RECOMMEND")
    assert result["state"]["payment_count"] == 0


def test_payment_adapter_rechecks_proposal_binding() -> None:
    bench.prepare()
    item = bench.release_proposal()
    gate = approval_controller()
    routed = gate.evaluate(item, now=TIMES["proposal"])
    gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at=TIMES["approval_1"],
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="bob",
        role="treasury-controller",
        approved=True,
        at=TIMES["approval_2"],
    )
    changed = replace(item, amount=item.amount + 1)

    with pytest.raises(PermissionError, match="missing governance receipts"):
        bench.execute_payment(
            changed,
            receipts=(final.receipt,),
            active_policies={"approval-gate": gate.policy.ref},
            at=TIMES["effect"],
        )


def test_payment_adapter_rechecks_active_policy_binding() -> None:
    bench.prepare()
    item = bench.release_proposal()
    gate = approval_controller()
    routed = gate.evaluate(item, now=TIMES["proposal"])
    gate.attest(
        routed.ticket.ticket_id,
        approver_id="alice",
        role="payroll-controller",
        approved=True,
        at=TIMES["approval_1"],
    )
    final = gate.attest(
        routed.ticket.ticket_id,
        approver_id="bob",
        role="treasury-controller",
        approved=True,
        at=TIMES["approval_2"],
    )
    containment = governance_lab._supporting_control("blast-radius", item)
    authority = governance_lab._supporting_control("progressive-commitment", item)
    changed_policy = approval.ApprovalPolicy(version=2)

    with pytest.raises(PermissionError, match="invalid receipts: approval-gate"):
        bench.execute_payment(
            item,
            receipts=(final.receipt, containment[0], authority[0]),
            active_policies={
                "approval-gate": changed_policy.ref,
                "blast-radius": containment[1],
                "progressive-commitment": authority[1],
            },
            at=TIMES["effect"],
        )


def test_payment_adapter_rechecks_live_containment_after_kill_switch() -> None:
    bench.prepare()
    item = bench.release_department_proposal("Engineering")
    control = governance_lab.department_containment_controller(("Engineering",))
    lease = control.reserve(
        item,
        scope_id="department::engineering",
        allowed_refs=(item.artifact_id,),
        at=TIMES["reserve"],
    )
    reservation = control.reservation_receipt(
        lease,
        item,
        at=TIMES["reserve"],
    )
    permit = control.begin_effect(
        lease,
        item,
        effect_ref=item.artifact_id,
        amount=item.amount,
        subject_count=item.subject_count,
        idempotency_key=f"{item.idempotency_key}::effect",
        at=TIMES["effect"],
    )
    approval_receipt, approval_policy = governance_lab._supporting_control(
        "approval-gate",
        item,
    )
    authority_receipt, authority_policy = governance_lab._supporting_control(
        "progressive-commitment",
        item,
    )
    control.trip_kill_switch(
        "payroll-window::2026-06",
        at=TIMES["effect"],
    )

    with pytest.raises(PermissionError, match="live containment permit"):
        bench.execute_payment(
            item,
            receipts=(approval_receipt, reservation, authority_receipt),
            active_policies={
                "approval-gate": approval_policy,
                "blast-radius": control.policy_ref,
                "progressive-commitment": authority_policy,
            },
            at=TIMES["effect"],
            live_containment=(control, permit),
        )


def test_database_exposes_structured_control_evidence() -> None:
    result = run_governed()

    assert result["state"]["tables"] == {
        "proposals": 1,
        "control_receipts": 5,
        "authority_credentials": 1,
        "authority_transitions": 5,
        "budget_usage": 2,
        "governance_events": 7,
        "payment_effects": 1,
    }
    assert len(bench.table_rows("governance_events")) == 7
    assert bench.table_rows("payment_effects")[0]["mode"] == "governed"


def test_unknown_control_table_is_rejected() -> None:
    bench.prepare()

    with pytest.raises(KeyError):
        bench.table_rows("sqlite_master")
