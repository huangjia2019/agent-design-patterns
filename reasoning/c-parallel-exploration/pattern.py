"""Parallel Exploration pattern.

Reference implementation from column lecture 04-04. The claim: **a
single chain has lucky-seed bias.** Same prompt, same model, different
samples can give different answers. For most agents that's noise to
ignore — but for high-stakes work (medical reads, fraud calls,
production root-cause diagnosis) the noise is the *signal you need*.
Run N branches, aggregate them with the right policy, and you trade
~5× cost for ~5-15 points of accuracy.

The pattern is one class:

* `ParallelExploration` runs N branches with optional prompt variation
  per branch, then aggregates with one of five strategies. Each branch
  reports a `BranchResult`; the trace keeps all of them so the audit
  can replay the disagreement, not just the winner.

Five aggregators:

* `MAJORITY` — classical Wang 2022 self-consistency vote.
* `WEIGHTED` — weight by branch confidence (trust the surer branches).
* `VERIFIER` — a judge function picks the best (Universal SC).
* `FIRST_CORRECT` — first branch a checker accepts wins (test-driven).
* `ANY_ALARM` — *any* branch flagging escalation wins. This is the
  medical-imaging lesson: missing a 4a is worse than a false alarm.

The default aggregation is `MAJORITY`. The aggregation choice is a
business decision about asymmetric error cost, not an engineering
preference.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable


class AggregationStrategy(Enum):
    MAJORITY = "majority"
    WEIGHTED = "weighted"
    VERIFIER = "verifier"
    FIRST_CORRECT = "first_correct"
    ANY_ALARM = "any_alarm"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BranchResult:
    """One branch's output, with enough metadata for honest aggregation."""

    branch_id: int
    answer: str
    confidence: float = 1.0   # 0.0–1.0; set lower if the branch self-estimates uncertainty
    tokens: int = 0
    latency_ms: float = 0.0
    alarm: bool = False       # raised when this branch wants escalation
    metadata: dict = field(default_factory=dict)


@dataclass
class ParallelTrace:
    """The full audit record of a parallel run."""

    query: str
    n: int
    strategy: AggregationStrategy
    branches: list[BranchResult] = field(default_factory=list)
    final_answer: str = ""
    triggered_alarm: bool = False
    started_at: str = field(default_factory=_now_iso)
    completed_at: str | None = None

    @property
    def total_tokens(self) -> int:
        return sum(b.tokens for b in self.branches)

    @property
    def branch_agreement_rate(self) -> float:
        """How aligned the branches are — health-line 0.60-0.80.
        Too low = task really is complex; too high = N is overkill."""
        if not self.branches:
            return 0.0
        counts = Counter(b.answer for b in self.branches)
        most_common = counts.most_common(1)[0][1]
        return most_common / len(self.branches)

    @property
    def effective_n(self) -> int:
        """Number of *distinct* answers — production health metric.
        Effective N close to N means the prompt variation is doing
        its job; close to 1 means the branches are wasted."""
        return len({b.answer for b in self.branches})


# Branch sampler: takes (query, branch_id) and returns a BranchResult.
# In production this wraps an async LLM call with per-branch
# temperature / seed / prompt variation; the test suite uses a
# deterministic stand-in.
BranchSamplerFn = Callable[[str, int], BranchResult]
# Verifier judge: scores a BranchResult against the query, returns a float.
VerifierFn = Callable[[str, BranchResult], float]
# Correctness check: takes a query and answer, returns True if accepted.
CorrectnessFn = Callable[[str, str], bool]


class ParallelExploration:
    """Run N branches, aggregate with the configured strategy."""

    def __init__(
        self,
        sampler: BranchSamplerFn,
        n: int = 5,
        strategy: AggregationStrategy = AggregationStrategy.MAJORITY,
        verifier: VerifierFn | None = None,
        correctness_check: CorrectnessFn | None = None,
    ) -> None:
        if n < 2:
            raise ValueError("parallel exploration requires n >= 2")
        self.sampler = sampler
        self.n = n
        self.strategy = strategy
        self.verifier = verifier
        self.correctness_check = correctness_check

    def run(self, query: str) -> ParallelTrace:
        """Run the branches synchronously and aggregate.

        Production deployments swap this for an async fan-out (asyncio /
        threadpool) with isolated event loops per branch — DeerFlow's
        pattern — so a slow branch doesn't block fast ones. The
        aggregation logic stays identical.
        """
        trace = ParallelTrace(query=query, n=self.n, strategy=self.strategy)
        for i in range(self.n):
            trace.branches.append(self.sampler(query, i))

        if self.strategy == AggregationStrategy.MAJORITY:
            trace.final_answer = self._majority(trace.branches)
        elif self.strategy == AggregationStrategy.WEIGHTED:
            trace.final_answer = self._weighted(trace.branches)
        elif self.strategy == AggregationStrategy.VERIFIER:
            trace.final_answer = self._verifier_judge(query, trace.branches)
        elif self.strategy == AggregationStrategy.FIRST_CORRECT:
            trace.final_answer = self._first_correct(query, trace.branches)
        elif self.strategy == AggregationStrategy.ANY_ALARM:
            trace.final_answer, trace.triggered_alarm = self._any_alarm(trace.branches)

        trace.completed_at = _now_iso()
        return trace

    # --- aggregators -----------------------------------------------------

    @staticmethod
    def _majority(branches: list[BranchResult]) -> str:
        counts = Counter(b.answer for b in branches)
        return counts.most_common(1)[0][0]

    @staticmethod
    def _weighted(branches: list[BranchResult]) -> str:
        scores: dict[str, float] = {}
        for b in branches:
            scores[b.answer] = scores.get(b.answer, 0.0) + b.confidence
        # Return the answer with the highest cumulative confidence.
        return max(scores.items(), key=lambda kv: kv[1])[0]

    def _verifier_judge(self, query: str, branches: list[BranchResult]) -> str:
        if self.verifier is None:
            raise ValueError("VERIFIER strategy requires a verifier function")
        scored = [(b, self.verifier(query, b)) for b in branches]
        return max(scored, key=lambda pair: pair[1])[0].answer

    def _first_correct(self, query: str, branches: list[BranchResult]) -> str:
        if self.correctness_check is None:
            raise ValueError("FIRST_CORRECT strategy requires a correctness_check function")
        for b in branches:
            if self.correctness_check(query, b.answer):
                return b.answer
        # No branch passed — fall back to majority so the trace has
        # *something* to record. The caller inspects the trace to see
        # that no branch passed.
        return self._majority(branches)

    @staticmethod
    def _any_alarm(branches: list[BranchResult]) -> tuple[str, bool]:
        """If any branch raised alarm, escalate; otherwise majority answer.

        The medical-imaging lesson: missing a real alarm costs more
        than handling a false one. Use this when error cost is
        asymmetric in the *raise-alarm* direction."""
        alarmers = [b for b in branches if b.alarm]
        if alarmers:
            # Pick the highest-confidence alarming answer.
            top = max(alarmers, key=lambda b: b.confidence)
            return top.answer, True
        counts = Counter(b.answer for b in branches)
        return counts.most_common(1)[0][0], False
