"""Small runnable example for the contract-bound Handoff Chain pattern."""
from __future__ import annotations

import asyncio

from pattern import (
    FactRule,
    FactValue,
    HandoffChain,
    SeamError,
    StageBinding,
    StageDelta,
    StageSpec,
    TaskContract,
    new_baton,
)


CONTRACT = TaskContract(
    contract_id="book-trip",
    version=1,
    objective="book one trip through specialist stages",
    output_schema="TravelBaton",
    accountable_owner="travel-controller",
    boundary="each specialist owns declared facts",
)


async def intent(view):
    return StageDelta(
        facts=(
            FactValue("city", "Shanghai", ("request://trip-42",)),
            FactValue("date", "2026-07-18", ("request://trip-42",)),
        )
    )


async def route(view):
    return StageDelta(
        facts=(
            FactValue("depart_by", "18:00", ("map://route-42",)),
        )
    )


async def booking(view):
    return StageDelta(
        facts=(
            FactValue(
                "booking_id",
                "booking-42",
                ("booking://booking-42",),
            ),
        ),
        artifact_refs=("artifact://ticket-42",),
    )


def chain(route_stage=route) -> HandoffChain:
    return HandoffChain(
        CONTRACT,
        (
            StageBinding(
                StageSpec("intent", provides=("city", "date")),
                intent,
            ),
            StageBinding(
                StageSpec(
                    "route",
                    requires=("city", "date"),
                    provides=("depart_by",),
                ),
                route_stage,
            ),
            StageBinding(
                StageSpec(
                    "booking",
                    requires=("depart_by",),
                    provides=("booking_id",),
                ),
                booking,
            ),
        ),
        (
            FactRule("city", "intent", str),
            FactRule("date", "intent", str),
            FactRule("depart_by", "route", str),
            FactRule("booking_id", "booking", str),
        ),
        chain_id="travel-handoff",
    )


async def main() -> None:
    baton = new_baton(
        CONTRACT,
        baton_id="trip-42",
        intent="be in Shanghai tomorrow afternoon",
    )
    result = await chain().run(baton)
    print(f"Trace: {' -> '.join(result.baton.trace)}")
    print(f"Revision: {result.baton.revision}")
    print(f"Facts: {dict(result.baton.facts)}")
    print(f"Stage receipts: {len(result.receipts)}")
    print(f"Acceptance: {result.acceptance_receipt.decision.value}")

    async def route_forgets_departure(view):
        return StageDelta()

    try:
        await chain(route_forgets_departure).run(baton)
    except SeamError as exc:
        print(f"\nSeamError: {exc}")
        print(f"Checkpoint: {exc.checkpoint.snapshot_id}")


if __name__ == "__main__":
    asyncio.run(main())
