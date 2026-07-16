"""Focused tests for the Payroll teaching UI service layer."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import ui_service  # noqa: E402
from ui_service import (  # noqa: E402
    LECTURES,
    database_state,
    parse_output,
    table_rows,
)


def test_all_action_lectures_are_registered() -> None:
    assert set(LECTURES) == {"21", "22", "23", "24", "25"}
    assert all(len(item["stages"]) == 4 for item in LECTURES.values())


def test_single_engine_no_legacy_runners() -> None:
    # The console runs one engine: the stress workbench. The old 独立故障实验 /
    # per-lecture runners (naked_loop / run_action_module / SCENARIOS) are gone.
    for gone in ("SCENARIOS", "run_scenario", "run_lecture"):
        assert not hasattr(ui_service, gone), f"legacy runner {gone} should be removed"


def test_console_copy_does_not_reference_retired_labs() -> None:
    console_copy = json.dumps(LECTURES, ensure_ascii=False) + (HERE / "ui" / "index.html").read_text()
    for retired in ("ScriptedModelAdapter", "naked_loop", "run_action_module", "原始实验"):
        assert retired not in console_copy


def test_parse_output_promotes_evidence_and_blocks() -> None:
    events = parse_output(
        """
        [DEMO] prompt fault is injected at the model boundary; scenario=scope-creep
        [NORTH STAR] preserve payroll notes
        [PROMPT INJECTION] untrusted operator note
        [AGENT PROPOSAL] clear_payroll_note
        == scene 2 ==
        approval evidence: id=4, amount=999999, status=APPROVED
        -> BLOCKED_PRE
        [RECOVERY] route to exception review
        ledger check: E0099 is still DRAFT
        """
    )
    assert [event["kind"] for event in events] == [
        "experiment",
        "north-star",
        "injection",
        "proposal",
        "phase",
        "evidence",
        "blocked",
        "recovery",
        "evidence",
    ]


def test_database_state_exposes_tables_and_baseline_metrics() -> None:
    state = database_state()
    assert state["employees"] == 800
    assert {table["name"] for table in state["tables"]} == {
        "employees",
        "payroll",
        "approvals",
        "policies",
    }


def test_table_rows_supports_search_and_pagination() -> None:
    result = table_rows("employees", page=1, page_size=5, search="E0007")
    assert result["total"] == 1
    assert result["rows"][0]["emp_id"] == "E0007"


def test_unknown_table_is_rejected() -> None:
    with pytest.raises(KeyError):
        table_rows("sqlite_master")
