"""Runnable example: "I need to be in Shanghai tomorrow afternoon" → a booked trip.

    python collaboration/d-handoff-chain/example.py

No API key needed. Five mock stages pass a baton down the chain — intent → route →
flight → taxi → hotel — each adding its part. Then we break it on purpose: a route
stage that forgets to hand off ``depart_by``, and watch the chain fail fast at the
taxi seam instead of booking a taxi that can't make the flight. Swap the mocks for
LangGraph nodes or Claude Agent SDK subagents (see the tutorials) and the chain and
its seam checks never change.
"""
from __future__ import annotations

import asyncio

from pattern import Baton, SeamError, trip_chain


def stages(drop_depart_by: bool = False) -> dict:
    async def intent(b: Baton) -> dict:
        return {"facts": {"city": "Shanghai", "date": "2026-07-02"}}

    async def route(b: Baton) -> dict:
        # The Amap stage. If drop_depart_by, it "forgets" to hand off the deadline.
        return {"facts": {} if drop_depart_by else {"depart_by": "18:00"}}

    async def flight(b: Baton) -> dict:
        return {"facts": {"boarding": "19:30"},
                "legs": [{"type": "flight", "code": "MU5102", "boarding": "19:30"}]}

    async def taxi(b: Baton) -> dict:
        # Needs depart_by AND boarding — both come from upstream stages.
        return {"facts": {"taxi_eta": "19:00"},
                "legs": [{"type": "taxi", "provider": "didi", "eta": "19:00"}]}

    async def hotel(b: Baton) -> dict:
        return {"facts": {"hotel": "ctrip#88"},
                "legs": [{"type": "hotel", "provider": "ctrip"}]}

    return {"intent": intent, "route": route, "flight": flight, "taxi": taxi, "hotel": hotel}


async def main() -> None:
    print("=== A clean run: the baton makes it down the chain ===\n")
    baton = await trip_chain(stages()).run(Baton(intent="be in Shanghai tomorrow PM"))
    print(f"intent (carried unchanged): {baton.intent}")
    print(f"trace: {' -> '.join(baton.trace)}")
    print(f"committed facts: {baton.facts}")
    print(f"booked legs: {[leg['type'] for leg in baton.legs]}")

    print("\n=== A dropped handoff: route forgets depart_by ===\n")
    try:
        await trip_chain(stages(drop_depart_by=True)).run(Baton(intent="be in Shanghai"))
    except SeamError as e:
        print(f"SeamError (fail fast, named): {e}")
        print("\nThe chain stopped at the route seam — the exact stage that dropped "
              "the handoff, not three stages later at the airport. The culprit is "
              "named, so the fix is one place, not a hunt.")


if __name__ == "__main__":
    asyncio.run(main())
