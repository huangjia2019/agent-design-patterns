"""Handoff Chain pattern.

Minimal, framework-agnostic reference implementation of the pattern described in
column lecture 07-05. Work moves down a pipeline of specialist agents, each doing
one stage and passing a baton to the next. Not a tree (that is Hierarchical
Delegation), not parallel copies (that is Fan-out-Gather) — a line.

Scenario: an AI travel assistant turns "I need to be in Shanghai tomorrow
afternoon" into a booked trip by passing a baton down a chain: intent → route
(Amap) → flight → airport taxi (Didi) → hotel (Ctrip). Each stage reads the baton,
does its part, and adds to it. Drop one thing the next stage needs and the whole
downstream chain breaks — often silently, three stages later, where the cause is
already unrecoverable.

Like the sibling patterns this file is small (~140 lines) and is not a framework.
A pluggable ``StageFn`` is the seam LangGraph, the Claude Agent SDK, or a mock plugs
into. The two tutorials wire real agents into the same chain.

Two named tools from the lecture:

* **The Baton Contract** (接力棒规约) — every stage declares what it ``requires`` from
  the baton and what it ``provides``. The chain validates both at each seam, so a
  missing hand-off fails fast, *at the seam that dropped it*, with a name attached —
  not three stages downstream where the cause is lost.
* **Append-only baton** (棒上不回改) — the intent and committed facts are locked once
  set. A later stage may add, never silently overwrite. A handoff passes values, not
  a shared mutable scratchpad, so one stage cannot quietly rewrite what an earlier
  stage committed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


class SeamError(Exception):
    """Raised at the exact handoff that broke — names the stage and what was short.
    Failing here, at the seam, is the whole point: the alternative is a wrong trip
    discovered at the airport."""


@dataclass
class Baton:
    """What travels down the chain. ``intent`` is set once and carried unchanged;
    ``facts`` is append-only (committed facts never silently change); ``legs`` and
    ``trace`` accumulate."""

    intent: str
    facts: dict[str, Any] = field(default_factory=dict)   # committed, append-only
    legs: list[dict] = field(default_factory=list)        # booked legs accumulate
    trace: list[str] = field(default_factory=list)        # stages that have run


@dataclass(frozen=True)
class StageSpec:
    """A stage's half of the Baton Contract: what it needs, what it must deliver."""

    name: str
    requires: tuple[str, ...] = ()     # fact keys that must already be on the baton
    provides: tuple[str, ...] = ()     # fact keys this stage must add


# stage(baton) -> a delta: {"facts": {...新事实...}, "legs": [...新腿...]}.
# The stage returns what it ADDS; it never mutates the baton in place.
StageFn = Callable[[Baton], Awaitable[dict]]


class HandoffChain:
    """Run stages in order, validating the Baton Contract at every seam. A stage
    that is handed a baton missing what it requires fails fast, named; a stage that
    tries to overwrite a committed fact is refused (append-only)."""

    def __init__(self, stages: list[tuple[StageSpec, StageFn]]):
        self.stages = stages

    async def run(self, baton: Baton) -> Baton:
        for spec, fn in self.stages:
            self._check_requires(spec, baton)             # seam check: entry
            delta = await fn(baton) or {}
            self._apply(spec, baton, delta)               # seam check: exit + append-only
            baton.trace.append(spec.name)
        return baton

    @staticmethod
    def _check_requires(spec: StageSpec, baton: Baton) -> None:
        missing = [k for k in spec.requires if k not in baton.facts]
        if missing:
            # The baton reached this stage short. Name the seam and what is missing.
            raise SeamError(f"stage '{spec.name}' requires {missing}; "
                            f"baton only has {sorted(baton.facts)}")

    @staticmethod
    def _apply(spec: StageSpec, baton: Baton, delta: dict) -> None:
        new_facts = delta.get("facts", {})
        # Append-only: a stage may not silently rewrite a committed fact.
        clobbered = [k for k, v in new_facts.items()
                     if k in baton.facts and baton.facts[k] != v]
        if clobbered:
            raise SeamError(f"stage '{spec.name}' tried to overwrite committed "
                            f"fact(s) {clobbered}; the baton is append-only")
        # Postcondition: the stage must deliver what it promised.
        undelivered = [k for k in spec.provides
                       if k not in new_facts and k not in baton.facts]
        if undelivered:
            raise SeamError(f"stage '{spec.name}' promised {list(spec.provides)} "
                            f"but did not provide {undelivered}")
        baton.facts.update(new_facts)
        baton.legs.extend(delta.get("legs", []))


def trip_chain(stages_by_name: dict[str, StageFn]) -> HandoffChain:
    """The travel-assistant chain: intent -> route -> flight -> taxi -> hotel. Each
    stage's contract makes the dependencies explicit, so a dropped handoff is caught
    at the seam instead of at the airport."""

    specs = [
        StageSpec("intent", requires=(), provides=("city", "date")),
        StageSpec("route",  requires=("city", "date"), provides=("depart_by",)),
        StageSpec("flight", requires=("city", "date"), provides=("boarding",)),
        StageSpec("taxi",   requires=("depart_by", "boarding"), provides=("taxi_eta",)),
        StageSpec("hotel",  requires=("city", "date"), provides=("hotel",)),
    ]
    return HandoffChain([(s, stages_by_name[s.name]) for s in specs])
