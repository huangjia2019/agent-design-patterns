"""Runnable demo for the Parallel Exploration pattern.

Replays the medical-imaging incident from the lecture opening. A CT
agent reads a 12mm lung nodule and reports BI-RADS 3 (low concern).
Three months later the patient comes back; the nodule is now 18mm and
the biopsy comes back malignant. Tracing the agent's chain shows the
reasoning was internally consistent — it just missed the spiculation
on that one sample.

Rewriting to N=5 parallel reads: 3 branches still see BI-RADS 3, but
two branches catch faint spiculation and pleural retraction and flag
BI-RADS 4a. Under majority vote the verdict is still 3. Under
**ANY_ALARM** the trace escalates to human review — and the catch
moves three months earlier.

This example shows all five aggregation strategies on the same set of
branches so you can see why the choice matters.

Run:
    python reasoning/c-parallel-exploration/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    AggregationStrategy,
    BranchResult,
    ParallelExploration,
)


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def _ct_sampler(query: str, branch_id: int) -> BranchResult:
    """Stand-in for an LLM call. Returns five different reads of the
    same CT image, mirroring the lecture's described distribution:
    three call BI-RADS 3, two catch additional features and flag 4a.
    """
    reads = [
        BranchResult(branch_id=0, answer="BI-RADS 3", confidence=0.89, tokens=180),
        BranchResult(branch_id=1, answer="BI-RADS 3", confidence=0.84, tokens=175),
        BranchResult(
            branch_id=2, answer="BI-RADS 4a", confidence=0.76, tokens=210,
            alarm=True,
            metadata={"features": ["faint spiculation"]},
        ),
        BranchResult(branch_id=3, answer="BI-RADS 3", confidence=0.87, tokens=185),
        BranchResult(
            branch_id=4, answer="BI-RADS 4a", confidence=0.72, tokens=220,
            alarm=True,
            metadata={"features": ["mild pleural retraction"]},
        ),
    ]
    return reads[branch_id]


def _radiology_verifier(_query: str, branch: BranchResult) -> float:
    """Toy verifier: prefer branches that note additional features."""
    score = branch.confidence
    if branch.metadata.get("features"):
        score += 0.1
    return score


def _accept_if_explicit(_query: str, answer: str) -> bool:
    """First-correct gate: accept answers that include the grade."""
    return "BI-RADS" in answer


def main() -> None:
    query = "Read CT scan #45821: right-upper-lobe 12mm nodule. Provide BI-RADS grade."

    _print_section("Branches (5 independent reads)")
    for i in range(5):
        b = _ct_sampler(query, i)
        flag = " ALARM" if b.alarm else ""
        print(f"  branch {b.branch_id}: {b.answer:11s} confidence={b.confidence:.2f}{flag}")

    # ------------------------------------------------------------------
    # Try all five aggregators on the same set of branches.
    # ------------------------------------------------------------------
    strategies = [
        (AggregationStrategy.MAJORITY, {}),
        (AggregationStrategy.WEIGHTED, {}),
        (AggregationStrategy.VERIFIER, {"verifier": _radiology_verifier}),
        (AggregationStrategy.FIRST_CORRECT, {"correctness_check": _accept_if_explicit}),
        (AggregationStrategy.ANY_ALARM, {}),
    ]

    _print_section("Aggregation comparison")
    for strat, extra in strategies:
        runner = ParallelExploration(sampler=_ct_sampler, n=5, strategy=strat, **extra)
        trace = runner.run(query)
        flag = " (ALARM)" if trace.triggered_alarm else ""
        print(
            f"  {strat.value:14s} → {trace.final_answer:11s}"
            f"  agreement={trace.branch_agreement_rate:.2f}  effectiveN={trace.effective_n}"
            f"  tokens={trace.total_tokens}{flag}"
        )

    # ------------------------------------------------------------------
    # The lesson: majority votes BI-RADS 3, any-alarm escalates to 4a.
    # In medical imaging that's a three-month-earlier catch.
    # ------------------------------------------------------------------
    _print_section("Why ANY_ALARM matters here")
    print("  MAJORITY                : BI-RADS 3 (3 vs 2)")
    print("  ANY_ALARM               : BI-RADS 4a + escalate to human review")
    print("  expected catch shift    : ~3 months earlier (lecture-opening case)")
    print("  cost trade              : ~5× tokens for ~7pp accuracy")


if __name__ == "__main__":
    main()
