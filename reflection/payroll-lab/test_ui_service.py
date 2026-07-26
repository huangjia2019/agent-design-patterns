"""Focused tests for the Payroll Reflection Lab teaching UI."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.modules.pop("ui_service", None)

from ui_service import (  # noqa: E402
    LAB_LOCK,
    LECTURES,
    LabBusy,
    database_state,
    parse_output,
    prepare_month_end_state,
    reset_database,
    run_lecture,
    table_rows,
)


@pytest.fixture(autouse=True)
def month_end_bench() -> None:
    prepare_month_end_state()
    yield
    reset_database()


def test_reflection_lectures_are_registered_with_repo_status() -> None:
    assert set(LECTURES) == {"26", "27", "28", "29", "30"}
    assert all(len(item["stages"]) == 4 for item in LECTURES.values())
    assert LECTURES["26"]["available"] is True
    assert LECTURES["30"]["available"] is True


def test_month_end_state_exposes_the_report_ledger_mismatch() -> None:
    state = database_state()
    assert state["employees"] == 800
    assert state["ledger_truth"] == {"paid": 798, "reversed": 2}
    assert state["report_claim"] == {
        "paid": 800,
        "reversed": 0,
        "conclusion": "all-clear",
    }
    assert state["mismatch_findings"] == 2


def test_parse_output_separates_introspection_from_external_evidence() -> None:
    events = parse_output(
        """
        == run 1: introspective critic ==
        attempt 1: APPROVED, score 96/100
        == run 2: reconciliation against the ledger ==
        REJECTED: report says paid=800, ledger counts 798
        [VERDICT] external evidence forced the revision
        """
    )
    assert [event["kind"] for event in events] == [
        "phase",
        "introspection",
        "phase",
        "blocked",
        "evidence",
    ]


def test_lecture_26_runs_both_standard_and_strict_variants() -> None:
    standard = run_lecture("26")
    strict = run_lecture("26", variant=True)

    assert standard["return_code"] == 0
    assert standard["analysis"]["self_scores"] == [96, 96]
    assert standard["analysis"]["external_findings"] == 2
    assert standard["analysis"]["revision"]["conclusion"] == "exceptions-pending"
    assert strict["analysis"]["self_scores"] == [88, 88]
    assert strict["analysis"]["external_findings"] == 2


def test_lecture_27_keeps_revision_and_acceptance_in_separate_passes() -> None:
    standard = run_lecture("27")
    rubber_stamp = run_lecture("27", variant=True)

    assert standard["analysis"]["decisions"] == ["needs_revision", "accepted"]
    assert standard["analysis"]["grounded_blockers"] == 3
    assert standard["analysis"]["wrong_report_accepted"] is False
    assert rubber_stamp["analysis"]["decisions"] == ["accepted"]
    assert rubber_stamp["analysis"]["wrong_report_accepted"] is True


def test_lecture_28_routes_only_after_verification() -> None:
    standard = run_lecture("28")
    no_gate = run_lecture("28", variant=True)

    assert standard["analysis"]["failed_goldens"] == [
        "over-cap clamp",
        "under-floor clamp",
    ]
    assert standard["analysis"]["promoted"] is True
    assert standard["analysis"]["matched"] == "social-base-adjust"
    assert standard["analysis"]["wrong_bases"] == 0
    assert no_gate["analysis"]["gate_skipped"] is True
    assert no_gate["analysis"]["wrong_bases"] == 209


def test_lecture_29_separates_recall_from_reuse_feedback() -> None:
    standard = run_lecture("29")
    no_feedback = run_lecture("29", variant=True)

    assert standard["analysis"]["misbound_before"] == 1
    assert standard["analysis"]["misbound_after"] == 0
    assert standard["analysis"]["ritual_archived"] is True
    assert standard["analysis"]["graduation_candidates"] == [
        "2026-06-batch-fail"
    ]
    assert no_feedback["analysis"]["feedback_connected"] is False
    assert no_feedback["analysis"]["ritual_effectiveness"] == 0.5
    assert no_feedback["analysis"]["ritual_archived"] is False
    assert no_feedback["analysis"]["membership_reuses"] == 0


def test_lecture_30_runs_fixed_and_rollback_paths() -> None:
    standard = run_lecture("30")
    meltdown = run_lecture("30", variant=True)

    assert standard["analysis"]["statuses"] == ["FIXED", "BLOCKED_BY_CRITIC"]
    assert standard["analysis"]["controlled_rounds"] == 2
    assert standard["analysis"]["naive_rounds"] == 0
    assert "ROLLED_BACK_REGRESSION" in meltdown["analysis"]["statuses"]
    assert meltdown["analysis"]["naive_rounds"] == 9
    assert meltdown["analysis"]["controlled_rounds"] == 2
    assert meltdown["analysis"]["failure_classes"] == 7
    assert "c2" in meltdown["analysis"]["rolled_back"]
    assert any(
        event["kind"] == "evidence" and "baseline_restored: true" in event["text"]
        for event in meltdown["events"]
    )


def test_shared_bench_rejects_a_concurrent_run() -> None:
    LAB_LOCK.acquire()
    try:
        with pytest.raises(LabBusy):
            prepare_month_end_state()
    finally:
        LAB_LOCK.release()


def test_table_rows_can_find_the_two_reversed_payslips() -> None:
    result = table_rows("payroll", page=1, page_size=5, search="REVERSED")
    assert result["total"] == 2
    assert {row["emp_id"] for row in result["rows"]} == {"E0007", "E0012"}


def test_unknown_table_is_rejected() -> None:
    with pytest.raises(KeyError):
        table_rows("sqlite_master")
