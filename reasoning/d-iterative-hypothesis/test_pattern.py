"""Invariants for the Iterative Hypothesis Testing pattern."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    Evidence,
    Hypothesis,
    HypothesisStatus,
    HypothesisTree,
    IterativeHypothesisLoop,
)


# ---- Hypothesis: evidence accumulation -------------------------------------


def test_recording_refuting_evidence_marks_falsified() -> None:
    h = Hypothesis(h_id="a", description="x", prior=0.5, posterior=0.5)
    ev = Evidence(description="contradicts", source="log", effect="refutes", target_hypothesis_id="a")
    h.record_evidence(ev, posterior_delta=-1.0)
    assert h.status == HypothesisStatus.FALSIFIED
    assert h.falsified_by == "contradicts"
    assert h.posterior == 0.0   # clamped


def test_recording_strong_supporting_evidence_marks_confirmed() -> None:
    h = Hypothesis(h_id="a", description="x", prior=0.4, posterior=0.4)
    ev = Evidence(description="matches", source="log", effect="supports", target_hypothesis_id="a")
    h.record_evidence(ev, posterior_delta=0.55)
    assert h.status == HypothesisStatus.CONFIRMED
    assert h.posterior == pytest.approx(0.95)


def test_weak_supporting_evidence_keeps_status_testing() -> None:
    h = Hypothesis(h_id="a", description="x", prior=0.4, posterior=0.4)
    ev = Evidence(description="minor", source="log", effect="supports", target_hypothesis_id="a")
    h.record_evidence(ev, posterior_delta=0.2)
    assert h.status == HypothesisStatus.TESTING
    assert h.posterior == pytest.approx(0.6)


def test_posterior_clamped_to_unit_interval() -> None:
    h = Hypothesis(h_id="a", description="x", prior=0.5, posterior=0.5)
    h.record_evidence(
        Evidence("more", "log", "supports", "a"),
        posterior_delta=5.0,
    )
    assert h.posterior == 1.0


# ---- HypothesisTree -------------------------------------------------------


def test_tree_add_returns_existing_on_duplicate_description() -> None:
    tree = HypothesisTree()
    h1 = tree.add("pump failed", prior=0.8, iteration=1)
    h2 = tree.add("pump failed", prior=0.7, iteration=2)
    assert h1.h_id == h2.h_id
    assert tree.hypotheses[h1.h_id].prior == 0.8, "duplicate add should not overwrite"


def test_tree_active_excludes_falsified_and_confirmed() -> None:
    tree = HypothesisTree()
    a = tree.add("A", 0.5, 1)
    b = tree.add("B", 0.5, 1)
    c = tree.add("C", 0.5, 1)
    a.status = HypothesisStatus.FALSIFIED
    b.status = HypothesisStatus.CONFIRMED
    active = tree.active()
    assert len(active) == 1
    assert active[0].h_id == c.h_id


def test_survivor_count_counts_unfalsified() -> None:
    tree = HypothesisTree()
    a = tree.add("A", 0.5, 1)
    b = tree.add("B", 0.5, 1)
    c = tree.add("C", 0.5, 1)
    a.status = HypothesisStatus.FALSIFIED
    b.status = HypothesisStatus.CONFIRMED   # confirmed counts as survivor
    assert tree.survivor_count() == 2
    c.status = HypothesisStatus.FALSIFIED
    assert tree.survivor_count() == 1


# ---- IterativeHypothesisLoop ---------------------------------------------


def _scripted_loop(
    planner_outputs: list,
    generator_outputs: dict[str, list],
    evaluator_decisions: dict[tuple[str, str], tuple[str, float]],
    max_iterations: int = 5,
) -> IterativeHypothesisLoop:
    """Build a loop where each role behaves deterministically per script."""
    iteration_index = {"i": 0}

    def planner(_problem, _existing, iteration):
        idx = iteration - 1
        return planner_outputs[idx] if idx < len(planner_outputs) else []

    def generator(h):
        return generator_outputs.get(h.description, [])

    def evaluator(h, evidence_desc, _source):
        return evaluator_decisions.get((h.description, evidence_desc), ("neutral", 0.0))

    return IterativeHypothesisLoop(
        planner=planner,
        generator=generator,
        evaluator=evaluator,
        max_iterations=max_iterations,
    )


def test_loop_converges_when_single_survivor_confirmed() -> None:
    loop = _scripted_loop(
        planner_outputs=[
            [("real cause", 0.5), ("noise", 0.5)],
        ],
        generator_outputs={
            "real cause": [("matches exactly", "tool:a")],
            "noise": [("does not match", "tool:b")],
        },
        evaluator_decisions={
            ("real cause", "matches exactly"): ("supports", 0.55),
            ("noise", "does not match"): ("refutes", -1.0),
        },
    )
    tree, outcome = loop.run("problem")
    assert outcome.converged is True
    assert outcome.needs_hitl is False
    confirmed = tree.by_id(outcome.confirmed_id)
    assert confirmed and confirmed.description == "real cause"


def test_loop_handles_context_reset_when_all_falsified_then_new_proposal() -> None:
    loop = _scripted_loop(
        planner_outputs=[
            [("h1", 0.5), ("h2", 0.5)],         # iter 1
            [("h3 reset cause", 0.95)],          # iter 2 — context-reset
        ],
        generator_outputs={
            "h1": [("contradicts h1", "tool:x")],
            "h2": [("contradicts h2", "tool:y")],
            "h3 reset cause": [("matches new evidence", "tool:z")],
        },
        evaluator_decisions={
            ("h1", "contradicts h1"): ("refutes", -1.0),
            ("h2", "contradicts h2"): ("refutes", -1.0),
            ("h3 reset cause", "matches new evidence"): ("supports", 0.55),
        },
    )
    tree, outcome = loop.run("problem")
    assert outcome.converged is True
    confirmed = tree.by_id(outcome.confirmed_id)
    assert confirmed and confirmed.description == "h3 reset cause"


def test_loop_hits_cap_with_multiple_survivors_triggers_hitl() -> None:
    loop = _scripted_loop(
        planner_outputs=[
            [("h1", 0.5), ("h2", 0.5)],
        ],
        generator_outputs={
            "h1": [("inconclusive", "tool:x")],
            "h2": [("inconclusive", "tool:y")],
        },
        evaluator_decisions={
            ("h1", "inconclusive"): ("neutral", 0.0),
            ("h2", "inconclusive"): ("neutral", 0.0),
        },
        max_iterations=3,
    )
    _tree, outcome = loop.run("problem")
    assert outcome.converged is False
    assert outcome.needs_hitl is True
    assert outcome.iterations_used == 3


def test_loop_cap_with_single_survivor_does_not_trigger_hitl() -> None:
    loop = _scripted_loop(
        planner_outputs=[
            [("h1", 0.5), ("h2", 0.5)],
        ],
        generator_outputs={
            "h1": [("matches a bit", "tool:x")],
            "h2": [("contradicts h2", "tool:y")],
        },
        evaluator_decisions={
            ("h1", "matches a bit"): ("supports", 0.1),   # not enough to confirm
            ("h2", "contradicts h2"): ("refutes", -1.0),
        },
        max_iterations=2,
    )
    _tree, outcome = loop.run("problem")
    assert outcome.converged is False
    assert outcome.needs_hitl is False
    assert outcome.confirmed_id is not None


def test_loop_max_iterations_validated() -> None:
    with pytest.raises(ValueError):
        IterativeHypothesisLoop(
            planner=lambda *a: [],
            generator=lambda h: [],
            evaluator=lambda h, d, s: ("neutral", 0.0),
            max_iterations=0,
        )


def test_loop_records_iteration_in_hypothesis() -> None:
    loop = _scripted_loop(
        planner_outputs=[
            [("h1", 0.5)],
            [("h2 added later", 0.5)],
        ],
        generator_outputs={
            "h1": [("contradicts h1", "tool:x")],
            "h2 added later": [],
        },
        evaluator_decisions={
            ("h1", "contradicts h1"): ("refutes", -1.0),
        },
        max_iterations=3,
    )
    tree, _ = loop.run("problem")
    h2 = next(h for h in tree.hypotheses.values() if h.description == "h2 added later")
    assert h2.created_iteration == 2
