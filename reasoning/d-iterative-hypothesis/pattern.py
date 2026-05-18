"""Iterative Hypothesis Testing pattern.

Reference implementation from column lecture 04-05. The claim:
**single-pass reasoning is fine for short problems; root-cause work
needs loops.** When the agent has to converge on a diagnosis under
incomplete evidence — production incident triage, medical workup,
fraud forensics, complex code debugging — the right shape is:

    hypothesize → test → falsify → refine → (loop)

Karl Popper, ported to agent runtimes: the loop's exit condition is
**"all strong alternatives have been falsified,"** not "we found
something that fits." That single reframe pushes the agent toward
collecting disconfirming evidence rather than confirming its prior.

The pattern is three classes:

* `Hypothesis` — one candidate, with a prior probability, a list of
  recorded `Evidence`, and a status (`PROPOSED` / `TESTING` /
  `CONFIRMED` / `FALSIFIED` / `INCONCLUSIVE`).
* `HypothesisTree` — the working set. Knows how to add new hypotheses
  mid-loop (Anthropic's "context reset" rule when fresh evidence
  arrives), prune falsified branches, and report when one survives
  alone or none survive at all.
* `IterativeHypothesisLoop` — the runner. Calls a planner to propose
  hypotheses, a generator to fetch evidence, and an evaluator to
  decide what each piece of evidence does to each hypothesis. Hard
  cap on iterations; HITL when the cap hits and >1 hypothesis is
  still standing.

The Anthropic three-agent harness shape (Planner / Generator /
Evaluator) is what the runner expects. In practice you wire each role
to its own model tier — that's why this pattern composes naturally
with [Complexity-Based Routing](../b-complexity-routing/).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable


class HypothesisStatus(Enum):
    PROPOSED = "proposed"
    TESTING = "testing"
    CONFIRMED = "confirmed"
    FALSIFIED = "falsified"
    INCONCLUSIVE = "inconclusive"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Evidence:
    """One piece of evidence collected by the Generator.

    `effect` records what the Evaluator decided this evidence does to
    the named hypothesis: "supports" / "refutes" / "neutral". Storing
    the effect inline (rather than recomputing it) makes the audit
    trail explicit — "this log line falsified H2" is the audit answer.
    """

    description: str
    source: str                   # which tool / query produced it
    effect: str                   # "supports" | "refutes" | "neutral"
    target_hypothesis_id: str
    timestamp: str = field(default_factory=_now_iso)


@dataclass
class Hypothesis:
    """One candidate explanation."""

    h_id: str
    description: str
    prior: float                  # 0.0–1.0, set by the Planner
    posterior: float = 0.0        # 0.0–1.0, updated by the Evaluator
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    evidence: list[Evidence] = field(default_factory=list)
    falsified_by: str | None = None    # description of the killer piece of evidence
    created_iteration: int = 0

    def record_evidence(self, e: Evidence, posterior_delta: float) -> None:
        self.evidence.append(e)
        self.posterior = max(0.0, min(1.0, self.posterior + posterior_delta))
        if e.effect == "refutes":
            self.status = HypothesisStatus.FALSIFIED
            self.falsified_by = e.description
        elif e.effect == "supports" and self.posterior >= 0.9:
            self.status = HypothesisStatus.CONFIRMED
        elif self.status == HypothesisStatus.PROPOSED:
            self.status = HypothesisStatus.TESTING


def _hypothesis_id(description: str) -> str:
    return hashlib.sha256(description.encode()).hexdigest()[:10]


class HypothesisTree:
    """The working set of hypotheses across loop iterations."""

    def __init__(self) -> None:
        self.hypotheses: dict[str, Hypothesis] = {}

    def add(self, description: str, prior: float, iteration: int) -> Hypothesis:
        h_id = _hypothesis_id(description)
        if h_id in self.hypotheses:
            return self.hypotheses[h_id]
        h = Hypothesis(
            h_id=h_id,
            description=description,
            prior=prior,
            posterior=prior,
            created_iteration=iteration,
        )
        self.hypotheses[h_id] = h
        return h

    def active(self) -> list[Hypothesis]:
        """Hypotheses not yet falsified or confirmed."""
        return [h for h in self.hypotheses.values()
                if h.status not in (HypothesisStatus.FALSIFIED, HypothesisStatus.CONFIRMED)]

    def confirmed(self) -> list[Hypothesis]:
        return [h for h in self.hypotheses.values()
                if h.status == HypothesisStatus.CONFIRMED]

    def survivor_count(self) -> int:
        """Hypotheses not yet falsified — the Popperian quantity."""
        return sum(1 for h in self.hypotheses.values()
                   if h.status != HypothesisStatus.FALSIFIED)

    def by_id(self, h_id: str) -> Hypothesis | None:
        return self.hypotheses.get(h_id)


# Planner: takes (problem, existing_hypotheses, iteration), returns a
# list of (description, prior) tuples — new hypotheses to add.
PlannerFn = Callable[[str, list[Hypothesis], int], list[tuple[str, float]]]
# Generator: takes a hypothesis and returns 0+ evidence descriptions/sources.
GeneratorFn = Callable[[Hypothesis], list[tuple[str, str]]]
# Evaluator: takes (hypothesis, evidence_description, evidence_source) and
# returns (effect, posterior_delta).
EvaluatorFn = Callable[[Hypothesis, str, str], tuple[str, float]]


@dataclass
class LoopOutcome:
    converged: bool
    needs_hitl: bool
    confirmed_id: str | None
    iterations_used: int
    reason: str


class IterativeHypothesisLoop:
    """Run the Plan → Generate → Evaluate loop until convergence or cap.

    Production deployments wire each role to its own model tier
    (Opus / Sonnet / Haiku) — Planner needs the most reasoning,
    Generator is mostly tool-dispatch, Evaluator does the Popperian
    decision and benefits from a calmer mid-tier model. This file
    keeps the wiring pluggable.
    """

    def __init__(
        self,
        planner: PlannerFn,
        generator: GeneratorFn,
        evaluator: EvaluatorFn,
        max_iterations: int = 5,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        self.planner = planner
        self.generator = generator
        self.evaluator = evaluator
        self.max_iterations = max_iterations

    def run(self, problem: str) -> tuple[HypothesisTree, LoopOutcome]:
        tree = HypothesisTree()
        for iteration in range(1, self.max_iterations + 1):
            # 1. Planner proposes hypotheses (initial set on iteration 1,
            #    new alternatives later if evidence opens up the space).
            proposals = self.planner(problem, list(tree.hypotheses.values()), iteration)
            for description, prior in proposals:
                tree.add(description, prior, iteration)

            # 2. Generator fetches evidence for each still-active hypothesis.
            for h in tree.active():
                for desc, source in self.generator(h):
                    effect, delta = self.evaluator(h, desc, source)
                    h.record_evidence(
                        Evidence(
                            description=desc,
                            source=source,
                            effect=effect,
                            target_hypothesis_id=h.h_id,
                        ),
                        posterior_delta=delta,
                    )

            # 3. Convergence check — Popperian: if exactly one hypothesis
            #    remains un-falsified and it's been confirmed, we're done.
            confirmed = tree.confirmed()
            if len(confirmed) == 1 and tree.survivor_count() == 1:
                return tree, LoopOutcome(
                    converged=True,
                    needs_hitl=False,
                    confirmed_id=confirmed[0].h_id,
                    iterations_used=iteration,
                    reason="single confirmed survivor",
                )

            # Or: all hypotheses falsified → planner gets a chance to
            # propose a fresh set on the next iteration.
            if tree.survivor_count() == 0 and iteration < self.max_iterations:
                continue

        # Cap reached. If more than one survivor remains, hand off.
        survivors = tree.active()
        if len(survivors) == 1:
            return tree, LoopOutcome(
                converged=False,
                needs_hitl=False,
                confirmed_id=survivors[0].h_id,
                iterations_used=self.max_iterations,
                reason="cap reached, one active hypothesis remaining",
            )
        return tree, LoopOutcome(
            converged=False,
            needs_hitl=True,
            confirmed_id=None,
            iterations_used=self.max_iterations,
            reason=f"cap reached with {len(survivors)} hypothesis/hypotheses still active",
        )
