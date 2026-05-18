"""Invariants for the Parallel Exploration pattern."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    AggregationStrategy,
    BranchResult,
    ParallelExploration,
    ParallelTrace,
)


def _seed_branches() -> list[BranchResult]:
    """Five branches, 3 agree on 'A', 2 dissent on 'B' (one alarms)."""
    return [
        BranchResult(branch_id=0, answer="A", confidence=0.9, tokens=10),
        BranchResult(branch_id=1, answer="A", confidence=0.8, tokens=10),
        BranchResult(branch_id=2, answer="B", confidence=0.6, tokens=10, alarm=True),
        BranchResult(branch_id=3, answer="A", confidence=0.85, tokens=10),
        BranchResult(branch_id=4, answer="B", confidence=0.55, tokens=10),
    ]


def _make_sampler(branches: list[BranchResult]):
    def sampler(_query: str, i: int) -> BranchResult:
        return branches[i]
    return sampler


# ---- ParallelTrace metrics ------------------------------------------------


def test_branch_agreement_rate_with_majority_a() -> None:
    trace = ParallelTrace(
        query="q", n=5, strategy=AggregationStrategy.MAJORITY,
        branches=_seed_branches(),
    )
    assert trace.branch_agreement_rate == pytest.approx(3 / 5)


def test_effective_n_reflects_distinct_answers() -> None:
    trace = ParallelTrace(
        query="q", n=5, strategy=AggregationStrategy.MAJORITY,
        branches=_seed_branches(),
    )
    assert trace.effective_n == 2


def test_total_tokens_sums_across_branches() -> None:
    trace = ParallelTrace(
        query="q", n=5, strategy=AggregationStrategy.MAJORITY,
        branches=_seed_branches(),
    )
    assert trace.total_tokens == 50


def test_metrics_safe_on_empty_branches() -> None:
    trace = ParallelTrace(query="q", n=0, strategy=AggregationStrategy.MAJORITY)
    assert trace.branch_agreement_rate == 0.0
    assert trace.effective_n == 0
    assert trace.total_tokens == 0


# ---- Constructor guards ---------------------------------------------------


def test_n_below_two_raises() -> None:
    with pytest.raises(ValueError):
        ParallelExploration(sampler=lambda q, i: BranchResult(i, "x"), n=1)


# ---- Aggregation strategies ----------------------------------------------


def test_majority_picks_most_common() -> None:
    branches = _seed_branches()
    runner = ParallelExploration(
        sampler=_make_sampler(branches), n=5, strategy=AggregationStrategy.MAJORITY,
    )
    trace = runner.run("q")
    assert trace.final_answer == "A"
    assert trace.triggered_alarm is False


def test_weighted_picks_highest_cumulative_confidence() -> None:
    # Two branches with high confidence on B beat three with low on A.
    branches = [
        BranchResult(branch_id=0, answer="A", confidence=0.2, tokens=10),
        BranchResult(branch_id=1, answer="A", confidence=0.2, tokens=10),
        BranchResult(branch_id=2, answer="A", confidence=0.2, tokens=10),
        BranchResult(branch_id=3, answer="B", confidence=0.9, tokens=10),
        BranchResult(branch_id=4, answer="B", confidence=0.9, tokens=10),
    ]
    runner = ParallelExploration(
        sampler=_make_sampler(branches), n=5, strategy=AggregationStrategy.WEIGHTED,
    )
    assert runner.run("q").final_answer == "B"


def test_verifier_strategy_uses_judge_score() -> None:
    branches = _seed_branches()

    def verifier(_query: str, b: BranchResult) -> float:
        # Heavily favor B regardless of how many branches voted A.
        return 10.0 if b.answer == "B" else 0.1

    runner = ParallelExploration(
        sampler=_make_sampler(branches), n=5, strategy=AggregationStrategy.VERIFIER,
        verifier=verifier,
    )
    assert runner.run("q").final_answer == "B"


def test_verifier_strategy_requires_function() -> None:
    runner = ParallelExploration(
        sampler=_make_sampler(_seed_branches()), n=5,
        strategy=AggregationStrategy.VERIFIER,
    )
    with pytest.raises(ValueError):
        runner.run("q")


def test_first_correct_returns_first_accepted_answer() -> None:
    branches = _seed_branches()
    runner = ParallelExploration(
        sampler=_make_sampler(branches), n=5,
        strategy=AggregationStrategy.FIRST_CORRECT,
        correctness_check=lambda _q, ans: ans == "B",
    )
    trace = runner.run("q")
    assert trace.final_answer == "B"


def test_first_correct_falls_back_to_majority_when_no_branch_passes() -> None:
    branches = _seed_branches()
    runner = ParallelExploration(
        sampler=_make_sampler(branches), n=5,
        strategy=AggregationStrategy.FIRST_CORRECT,
        correctness_check=lambda _q, _ans: False,
    )
    trace = runner.run("q")
    assert trace.final_answer == "A"   # majority A


def test_first_correct_requires_function() -> None:
    runner = ParallelExploration(
        sampler=_make_sampler(_seed_branches()), n=5,
        strategy=AggregationStrategy.FIRST_CORRECT,
    )
    with pytest.raises(ValueError):
        runner.run("q")


def test_any_alarm_escalates_on_any_branch_alarm() -> None:
    branches = _seed_branches()
    runner = ParallelExploration(
        sampler=_make_sampler(branches), n=5,
        strategy=AggregationStrategy.ANY_ALARM,
    )
    trace = runner.run("q")
    assert trace.triggered_alarm is True
    assert trace.final_answer == "B"   # alarming branch's answer


def test_any_alarm_majority_when_no_branch_alarms() -> None:
    branches = [BranchResult(i, "A", confidence=0.9) for i in range(5)]
    runner = ParallelExploration(
        sampler=_make_sampler(branches), n=5,
        strategy=AggregationStrategy.ANY_ALARM,
    )
    trace = runner.run("q")
    assert trace.triggered_alarm is False
    assert trace.final_answer == "A"


def test_any_alarm_picks_highest_confidence_alarming_branch() -> None:
    branches = [
        BranchResult(0, "A", confidence=0.9),
        BranchResult(1, "B", confidence=0.5, alarm=True),
        BranchResult(2, "C", confidence=0.8, alarm=True),
        BranchResult(3, "A", confidence=0.9),
        BranchResult(4, "A", confidence=0.9),
    ]
    runner = ParallelExploration(
        sampler=_make_sampler(branches), n=5,
        strategy=AggregationStrategy.ANY_ALARM,
    )
    trace = runner.run("q")
    assert trace.final_answer == "C"   # higher-confidence alarming branch wins


def test_run_records_completed_at_timestamp() -> None:
    runner = ParallelExploration(
        sampler=_make_sampler(_seed_branches()), n=5,
        strategy=AggregationStrategy.MAJORITY,
    )
    trace = runner.run("q")
    assert trace.completed_at is not None
