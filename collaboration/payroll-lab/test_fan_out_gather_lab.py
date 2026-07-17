"""Invariant tests for the lecture-33 fan-out-gather lab."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


lab = _load(HERE / "fan_out_gather_lab.py", "fanout_lab")
_fan = sys.modules["fanout_pattern"]


def test_finance_divergence_is_located_and_gap_is_the_reversed_amount():
    con = lab.month_end()
    report = lab.run_competing(con)
    assert report["status"] == "reconciled"
    assert sorted(report["agreed_items"]) == ["Engineering", "Ops", "Sales", "Support"]
    (rc,) = report["root_causes"]
    assert rc["item"] == "Finance"
    assert rc["gap"] == 38444.0                      # E0007 30,000 + E0012 8,444
    assert rc["low_sources"] == ["bank_ledger"]
    assert sorted(rc["high_sources"]) == ["batch_artifacts", "hr_payroll"]


def test_single_source_item_routes_to_human_not_into_the_answer():
    con = lab.month_end()
    report = lab.run_competing(con)
    (h,) = report["to_human"]
    assert h["item"] == "Contractors"
    assert h["reason"] == "single-source"


def test_seam_reviewer_flags_the_big_root_cause():
    con = lab.month_end()
    report = lab.run_competing(con)
    assert any("Finance" in f and "sign-off" in f for f in report["seam_findings"])


def test_dead_source_hits_the_floor_instead_of_a_survivor_verdict():
    con = lab.month_end()
    report = lab.run_with_dead_bank(con)
    assert report == {"status": "insufficient_sources", "got": 2, "total": 3}


def test_additive_merge_of_competing_answers_swallows_the_conflict():
    con = lab.month_end()
    report = lab.run_additive(con)
    # The disagreement is summed into a bigger number ...
    assert report["merged"]["Finance"] == 2764781.0 + 2764781.0 + 2726337.0
    # ... and every channel that could have carried the conflict is gone.
    assert "root_causes" not in report
    assert "to_human" not in report
    assert "seam_findings" not in report


def test_unexplained_three_way_divergence_goes_to_human():
    """Divergence that does not cluster two ways is layer 3: no root cause
    is claimed, a human gets it. (Exercised here rather than in a scene.)"""
    policy = _fan.AggregatorPolicy(strategy=_fan.Strategy.COMPETING)
    reconciler = _fan.Reconciler(policy, tol=1.0)
    results = [
        _fan.SourceResult(source="a", line_items={"Ops": 100.0}),
        _fan.SourceResult(source="b", line_items={"Ops": 200.0}),
        _fan.SourceResult(source="c", line_items={"Ops": 300.0}),
    ]
    report = reconciler.reconcile(results)
    assert report["root_causes"] == []
    (h,) = report["to_human"]
    assert h["reason"] == "unexplained-divergence"
