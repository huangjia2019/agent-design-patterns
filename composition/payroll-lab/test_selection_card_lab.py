"""End-to-end tests for the payroll selection-card lab."""
from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("selection_card_lab", None)

from selection_card_lab import run_independent, run_shared_state  # noqa: E402


def test_independent_sources_earn_fanout_gather() -> None:
    run = run_independent()

    assert run["outcome"]["state"] == "accepted"
    assert run["baseline"]["metrics"]["defect_recall"] == 0.0
    assert run["proposal"]["metrics"]["defect_recall"] == 1.0
    assert run["proposal"]["divergences"][0]["low_sources"] == [
        "social_security"
    ]


def test_shared_state_exposes_false_consensus_and_earns_a_loop() -> None:
    run = run_shared_state()

    assert run["handpicked_card_state"] == "draft"
    assert {
        finding["code"]
        for finding in run["preflight_findings"]
    } == {"precondition_not_evidenced"}
    assert run["baseline"]["metrics"]["false_consensus"] == 1.0
    assert run["proposal"]["confirmed"] == "上月结转写入了错误的社保基数"
    assert run["outcome"]["state"] == "accepted"


def test_every_accepted_outcome_binds_runtime_evidence() -> None:
    for run in (run_independent(), run_shared_state()):
        assert run["outcome"]["evidence_refs"]
        assert len(run["card_digest"]) == 16
