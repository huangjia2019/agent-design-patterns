"""Service-level tests for the Payroll Governance Lab UI."""

from __future__ import annotations

import os
import sys

import pytest


sys.path.insert(0, os.path.dirname(__file__))

from governance_payroll_imports import load_local  # noqa: E402


bench = load_local("bench")
ui_service = load_local("ui_service")
LECTURES = ui_service.LECTURES
run_lecture = ui_service.run_lecture


def test_all_five_lectures_are_connected() -> None:
    assert tuple(LECTURES) == ("36", "37", "38", "39", "40")


def test_intro_returns_naive_and_governed_comparison() -> None:
    payload = run_lecture("36")

    assert payload["result"]["naive"]["governance_receipts"] == 0
    assert payload["result"]["governed"]["audit"]["complete"]
    assert payload["state"]["payment_count"] == 1


def test_intro_variant_exposes_policy_drift() -> None:
    payload = run_lecture("36", variant=True)

    assert payload["result"]["mode"] == "policy-drift"
    assert payload["result"]["inventory"]["verified"] == 6
    assert payload["result"]["before"]["decision"] == "escalated"
    assert payload["result"]["after"]["decision"] == "accepted"
    assert payload["result"]["after"]["raw_policy_marks"] == ()
    assert (
        payload["result"]["before"]["policy_digest"]
        != payload["result"]["after"]["policy_digest"]
    )
    assert payload["state"]["payment_count"] == 0


def test_approval_variant_rejects_a_changed_proposal() -> None:
    payload = run_lecture("37", variant=True)

    assert not payload["result"]["changed"]["old_approval_authorizes"]
    assert "approval-gate" in payload["result"]["changed"]["adapter_result"]
    assert payload["state"]["payment_count"] == 0


def test_containment_standard_scene_blocks_third_department_before_payment() -> None:
    payload = run_lecture("38")

    assert payload["result"]["mode"] == "blast-radius-overflow"
    assert payload["result"]["batches"][2]["leaf_legal"]
    assert payload["result"]["batches"][2]["decision"] == "blocked"
    assert "payroll-window" in payload["result"]["batches"][2]["blocked_at"]
    assert payload["state"]["payment_count"] == 0


def test_containment_variant_bounds_the_retry_storm_per_effect() -> None:
    payload = run_lecture("38", variant=True)

    result = payload["result"]
    assert result["mode"] == "blast-radius-retry-storm"
    assert result["unbounded"]["money_out"] == 24_701_937
    assert result["unbounded"]["overpay"] == 10_995_840
    assert result["bounded"]["money_out"] == 13_706_097
    assert result["bounded"]["payment_count"] == 798
    assert result["bounded"]["refused_draws"] == 640
    assert result["snapshot"]["payroll-window::2026-06"]["unknown_amount"] == 0


def test_progressive_variant_demotes_and_clears_evidence() -> None:
    payload = run_lecture("39", variant=True)

    incident = payload["result"]["incident"]
    assert incident["before"]["level"] == "LIMITED"
    assert incident["after"]["level"] == "OBSERVE"
    assert incident["old_credential_decision"] == "denied"
    assert incident["fresh_evidence_runs"] == 0


def test_progressive_standard_scene_earns_limited_authority() -> None:
    payload = run_lecture("39")
    result = payload["result"]

    assert [window["runs"] for window in result["evidence_windows"]] == [5, 5, 5]
    assert all(len(window["evaluation_slices"]) == 5 for window in result["evidence_windows"])
    assert result["shadow"] == {
        "credential_version": 3,
        "simulation_decision": "allowed",
        "live_decision": "denied",
        "live_findings": ("live_effect_not_authorized",),
    }
    assert result["limited"]["canary_decision"] == "allowed"
    assert result["limited"]["full_decision"] == "denied"
    assert result["state"]["payment_count"] == 0


def test_observability_variant_reports_missing_controls() -> None:
    payload = run_lecture("40", variant=True)

    assert not payload["result"]["audit"]["complete"]
    assert payload["result"]["audit"]["chain_valid"]
    assert payload["result"]["audit"]["missing_controls"] == (
        "approval-gate",
        "blast-radius",
        "progressive-commitment",
    )
    assert len(payload["result"]["events"]) == 2
    assert payload["result"]["payment"]["amount"] == 13_706_097.0
    assert payload["state"]["payment_count"] == 1


def test_table_endpoint_source_rejects_unknown_names() -> None:
    bench.prepare()

    with pytest.raises(KeyError):
        bench.table_rows("drop table")
