"""Tests for the Handoff Chain pattern.

Run: pytest collaboration/d-handoff-chain/test_pattern.py -v

No API key needed — mock ``StageFn`` callables stand in for real agents, so every
test is deterministic. The tutorials swap the mocks for LangGraph / the Claude Agent
SDK; the chain and its seam checks never change.
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)   # ensure we pick up THIS folder's pattern.py

from pattern import (   # noqa: E402
    Baton,
    HandoffChain,
    SeamError,
    StageSpec,
    trip_chain,
)


def _stage(facts=None, legs=None):
    async def fn(baton: Baton) -> dict:
        return {"facts": dict(facts or {}), "legs": list(legs or [])}
    return fn


# A full set of well-behaved stages for the trip chain.
def _good_stages():
    return {
        "intent": _stage({"city": "Shanghai", "date": "2026-07-02"}),
        "route":  _stage({"depart_by": "18:00"}),
        "flight": _stage({"boarding": "19:30"}, legs=[{"type": "flight"}]),
        "taxi":   _stage({"taxi_eta": "19:00"}, legs=[{"type": "taxi"}]),
        "hotel":  _stage({"hotel": "ctrip#123"}, legs=[{"type": "hotel"}]),
    }


# ----- The happy path: baton accumulates, in order -----------------------------

def test_full_chain_runs_and_accumulates():
    chain = trip_chain(_good_stages())
    baton = asyncio.run(chain.run(Baton(intent="be in Shanghai tomorrow PM")))
    assert baton.trace == ["intent", "route", "flight", "taxi", "hotel"]
    assert baton.facts["city"] == "Shanghai"
    assert baton.facts["taxi_eta"] == "19:00"
    assert len(baton.legs) == 3                     # flight + taxi + hotel


def test_intent_is_carried_unchanged():
    chain = trip_chain(_good_stages())
    baton = asyncio.run(chain.run(Baton(intent="be in Shanghai tomorrow PM")))
    assert baton.intent == "be in Shanghai tomorrow PM"   # never touched by any stage


# ----- The Baton Contract: a short handoff fails fast, at the seam -------------

def test_missing_requirement_fails_at_the_seam_that_dropped_it():
    stages = _good_stages()
    # Sabotage 'route' so it never provides depart_by. The taxi stage needs it.
    stages["route"] = _stage({})
    chain = HandoffChain([
        (StageSpec("route", requires=(), provides=("depart_by",)), stages["route"]),
    ])
    try:
        asyncio.run(chain.run(Baton(intent="x")))
        assert False, "expected SeamError"
    except SeamError as e:
        assert "route" in str(e) and "depart_by" in str(e)   # named + attributed


def test_taxi_seam_breaks_when_route_is_dropped():
    # Real-chain version: route runs but provides nothing, so taxi's requires fail.
    stages = _good_stages()
    stages["route"] = _stage({})     # forgets depart_by
    try:
        asyncio.run(trip_chain(stages).run(Baton(intent="x")))
        assert False, "expected SeamError"
    except SeamError as e:
        assert "route" in str(e)     # route promised depart_by, didn't deliver


# ----- Append-only: a stage may not silently rewrite a committed fact ----------

def test_overwriting_a_committed_fact_is_refused():
    stages = _good_stages()
    stages["flight"] = _stage({"boarding": "19:30", "city": "Beijing"})  # rewrites city!
    try:
        asyncio.run(trip_chain(stages).run(Baton(intent="x")))
        assert False, "expected SeamError"
    except SeamError as e:
        assert "overwrite" in str(e) and "city" in str(e)


def test_re_providing_the_same_value_is_fine():
    # Writing the SAME value a fact already holds is not a clobber.
    stages = _good_stages()
    stages["flight"] = _stage({"boarding": "19:30", "city": "Shanghai"})  # same city
    baton = asyncio.run(trip_chain(stages).run(Baton(intent="x")))
    assert baton.facts["city"] == "Shanghai"


# ----- Postcondition: a stage must deliver what it promised --------------------

def test_stage_that_underdelivers_is_caught():
    chain = HandoffChain([
        (StageSpec("intent", provides=("city", "date")), _stage({"city": "SH"})),  # no date
    ])
    try:
        asyncio.run(chain.run(Baton(intent="x")))
        assert False, "expected SeamError"
    except SeamError as e:
        assert "date" in str(e)


# ----- trip_chain assembles the canonical sequence ----------------------------

def test_trip_chain_sequence():
    chain = trip_chain(_good_stages())
    assert [spec.name for spec, _ in chain.stages] == \
        ["intent", "route", "flight", "taxi", "hotel"]
