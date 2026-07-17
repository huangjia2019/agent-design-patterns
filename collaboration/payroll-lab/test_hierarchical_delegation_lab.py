"""End-to-end checks for the lecture 32 delegation lab."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


LAB = Path(__file__).with_name("hierarchical_delegation_lab.py")


def run_lab(*args: str) -> str:
    completed = subprocess.run(
        [sys.executable, str(LAB), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def test_standard_lab_exposes_contract_and_evidence_boundaries() -> None:
    output = run_lab()

    assert (
        "TaskContract -> HandoffEnvelope -> "
        "ArtifactEnvelope -> AcceptanceReceipt"
    ) in output
    assert (
        "roster_count_mismatch,roster_fingerprint_mismatch"
    ) in output
    assert "portfolio_coverage_mismatch,child_batches_unresolved" in output


def test_portfolio_ablation_changes_only_the_root_decision() -> None:
    output = run_lab("--sum-blind")

    assert "every batch decision: accepted" in output
    assert "no portfolio limit:   accepted" in output
    assert "13,000,000 limit:     escalated" in output
    assert "portfolio_amount_exceeded" in output
