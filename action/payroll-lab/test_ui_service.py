"""Focused tests for the Payroll teaching UI service layer."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from ui_service import (  # noqa: E402
    LECTURES,
    database_state,
    parse_output,
    table_rows,
)


def test_all_action_lectures_are_registered() -> None:
    assert set(LECTURES) == {"21", "22", "23", "24", "25"}
    assert all(len(item["stages"]) == 4 for item in LECTURES.values())


def test_parse_output_promotes_evidence_and_blocks() -> None:
    events = parse_output(
        """
        == scene 2 ==
        approval evidence: id=4, amount=999999, status=APPROVED
        -> BLOCKED_PRE
        ledger check: E0099 is still DRAFT
        """
    )
    assert [event["kind"] for event in events] == [
        "phase",
        "evidence",
        "blocked",
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
