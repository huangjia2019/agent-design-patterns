"""Invariant tests for the composition capstone discipline lab."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab = _load(HERE / "handpick_discipline_lab.py", "handpick_discipline_lab")


def test_the_lookup_task_stops_and_the_diagnosis_task_proceeds():
    lookup = lab.payslip_lookup_vector()
    assert lookup.heavy_functions() == ()
    assert lookup.verdict().startswith("STOP")
    diag = lab.reconciliation_vector()
    assert diag.heavy_functions() == ("reasoning",)
    assert diag.verdict().startswith("PROCEED")


def test_fanout_locates_the_divergence_when_sources_are_independent():
    run = lab.run_fanout(shared_carryover=False)
    assert run["recall"] == 1.0
    assert run["false_consensus"] == 0.0
    assert "social_security" in run["divergences"]


def test_fanout_produces_a_false_consensus_on_the_shared_carryover_twin():
    run = lab.run_fanout(shared_carryover=True)
    assert run["recall"] == 0.0
    assert run["false_consensus"] == 1.0
    assert run["divergences"] == []


def test_iterative_hypothesis_recovers_the_carryover_root_cause():
    run = lab.run_hypothesis(max_iterations=2)
    assert run["recall"] == 1.0
    assert run["converged"] is True
    assert "上月结转" in run["confirmed"]


def test_the_two_twins_get_the_same_pattern_from_naive_hand_picking():
    # The whole point: by label both tasks are "reconcile four ledgers",
    # so hand-picking by label gives both Fan-out -- and one then fails.
    independent = lab.run_fanout(shared_carryover=False)
    shared = lab.run_fanout(shared_carryover=True)
    assert independent["pattern"] == shared["pattern"] == "扇出聚合"
    assert independent["recall"] == 1.0 and shared["recall"] == 0.0


def test_the_same_right_pattern_stalls_at_one_iteration_and_confirms_at_two():
    stalled = lab.run_hypothesis(max_iterations=1)
    solved = lab.run_hypothesis(max_iterations=2)
    # Same pattern, one parameter changed.
    assert stalled["pattern"] == solved["pattern"] == "迭代假设验证"
    assert stalled["converged"] is False
    assert solved["converged"] is True
    # At the low cap it still points at the survivor but cannot confirm it.
    assert stalled["confirmed"] == solved["confirmed"]


def test_only_committed_patterns_are_imported():
    # The lab must not depend on Codex's uncommitted composition/pattern.py;
    # its two engines are the committed Fan-out and Iterative Hypothesis.
    assert hasattr(lab._FANOUT, "Reconciler")
    assert hasattr(lab._HYP, "IterativeHypothesisLoop")
