"""End-to-end tests for the lecture 43 capstone."""
from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("capstone_lab", None)

from capstone_lab import run_capstone  # noqa: E402


def test_bound_capstone_accepts_all_eight_modules_and_endpoint() -> None:
    result = run_capstone("bound")

    assert result["acceptance"]["accepted"] is True
    assert result["acceptance"]["local_acceptance_count"] == 8
    assert result["acceptance"]["findings"] == []
    assert result["release_row"]["paid_count"] == 798
    assert result["release_row"]["reversed_count"] == 2
    assert result["module_details"]["memory"]["all_done"] is True
    assert result["module_details"]["governance"]["final_decision"] == "allowed"


def test_local_only_capstone_proves_local_success_is_insufficient() -> None:
    result = run_capstone("local-only")
    codes = {finding["code"] for finding in result["acceptance"]["findings"]}

    assert result["acceptance"]["local_acceptance_count"] == 8
    assert result["acceptance"]["accepted"] is False
    assert "lineage_break" in codes
    assert "endpoint_receipt_mismatch" in codes
    assert "endpoint_artifact_mismatch" in codes


def test_capstone_uses_one_selected_pattern_per_module() -> None:
    result = run_capstone("bound")

    assert len(result["patterns"]) == 8
    assert {item["module"] for item in result["patterns"]} == {
        "composition",
        "perception",
        "collaboration",
        "reasoning",
        "action",
        "reflection",
        "governance",
        "memory",
    }


def test_unknown_capstone_mode_is_rejected() -> None:
    try:
        run_capstone("unknown")
    except KeyError as error:
        assert error.args == ("unknown",)
    else:
        raise AssertionError("unknown capstone mode was accepted")
