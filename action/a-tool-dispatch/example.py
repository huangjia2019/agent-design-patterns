"""Runnable demo for the Tool Dispatch pattern.

Replays the city-logistics incident from the lecture opening. An
agent with 17 tools is told to dispatch 80 backed-up orders during
morning rush hour. The first version of the dispatcher routes every
order to `driver_007` — the agent saw the highest-rated driver,
called `assign_driver`, told itself "looks good, keep going," and
ran `assign_driver(order_N, driver_007)` 80 times without refreshing
state.

This example shows the fixed dispatcher catching the same mistake:

* `assign_driver` is marked `requires_fresh_state` + destructive +
  `quota_per_session=5` per driver.
* The agent's first 5 calls succeed.
* The 6th call to driver_007 is rejected with `quota_exceeded`.
* A stale-state call (no refresh in >60s) is rejected with
  `stale_state_must_refresh`.
* A halluciated tool name is rejected with `tool_hallucination`.
* Saga rollback unwinds the destructive calls in reverse.

Run:
    python action/a-tool-dispatch/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    RiskLevel,
    ToolDispatcher,
    ToolMetadata,
)


# --- Toy tool handlers — stand-ins for the real backend ---------------------

_drivers_state: dict[str, dict] = {
    "driver_007": {"available": True, "assigned": 0},
    "driver_012": {"available": True, "assigned": 0},
    "driver_021": {"available": True, "assigned": 0},
}


def query_drivers(city: str) -> list[dict]:
    return [
        {"driver_id": did, **info}
        for did, info in _drivers_state.items()
        if info["available"]
    ]


def assign_driver(driver_id: str, order_id: str) -> dict:
    _drivers_state[driver_id]["assigned"] += 1
    return {"driver_id": driver_id, "order_id": order_id, "status": "assigned"}


def unassign_driver(driver_id: str, order_id: str) -> dict:
    _drivers_state[driver_id]["assigned"] -= 1
    return {"driver_id": driver_id, "order_id": order_id, "status": "unassigned"}


# --- Build the dispatcher ---------------------------------------------------


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    dispatcher = ToolDispatcher()
    dispatcher.register(
        ToolMetadata(
            name="query_drivers",
            description="Return the current list of available drivers in a city.",
            when_to_use="Before any assign_driver call",
            is_read_only=True,
            is_concurrency_safe=True,
            risk_level=RiskLevel.LOW,
        ),
        query_drivers,
    )
    dispatcher.register(
        ToolMetadata(
            name="assign_driver",
            description="Assign order_id to driver_id.",
            when_to_use="After confirming driver is available and within quota",
            when_not_to_use="When the driver already has 5 assignments this session",
            is_destructive=True,
            requires_fresh_state=True,
            quota_per_session=5,         # max 5 per driver per session
            rollback_action="unassign_driver",
            risk_level=RiskLevel.HIGH,
        ),
        assign_driver,
    )
    dispatcher.register(
        ToolMetadata(
            name="unassign_driver",
            description="Inverse of assign_driver. Saga inverse.",
            when_to_use="Called by saga rollback, not by the agent directly",
            is_destructive=True,
            rollback_action="assign_driver",   # technically inverse-of-inverse
        ),
        unassign_driver,
    )

    session = "demo-session-2026-05-19"

    # ------------------------------------------------------------------
    # Phase 1: refresh state (read) so writes are unblocked.
    # ------------------------------------------------------------------
    _print_section("Phase 1: query_drivers (refreshes state)")
    t = dispatcher.dispatch("query_drivers", {"city": "Shanghai"}, session_id=session)
    print(f"  status={t.status}  drivers_seen={len(t.output)}")

    # ------------------------------------------------------------------
    # Phase 2: try to route 8 orders all to driver_007.
    # ------------------------------------------------------------------
    _print_section("Phase 2: 8 assign_driver calls — all to driver_007")
    print("  expected: first 5 succeed, then quota_exceeded × 3")
    for i in range(1, 9):
        t = dispatcher.dispatch(
            "assign_driver",
            {"driver_id": "driver_007", "order_id": f"order_{i:03d}"},
            session_id=session,
        )
        marker = "✓" if t.status == "success" else "✗"
        reason = f" ({t.rejected_reason})" if t.status != "success" else ""
        print(f"  {marker} order_{i:03d} → driver_007: {t.status}{reason}")

    # ------------------------------------------------------------------
    # Phase 3: a halluciated tool the agent invented.
    # ------------------------------------------------------------------
    _print_section("Phase 3: halluciated tool name")
    t = dispatcher.dispatch(
        "magically_optimize_routes",
        {"city": "Shanghai"},
        session_id=session,
    )
    print(f"  status={t.status}  reason={t.rejected_reason}")

    # ------------------------------------------------------------------
    # Phase 4: simulate state going stale; next write rejects.
    # ------------------------------------------------------------------
    _print_section("Phase 4: stale state on a new driver")
    dispatcher.last_state_refresh[session] = 0   # pretend it's been forever
    t = dispatcher.dispatch(
        "assign_driver",
        {"driver_id": "driver_012", "order_id": "order_100"},
        session_id=session,
    )
    print(f"  status={t.status}  reason={t.rejected_reason}")

    # ------------------------------------------------------------------
    # Phase 5: saga rollback unwinds all successful destructive calls.
    # ------------------------------------------------------------------
    _print_section("Phase 5: saga rollback")
    results = dispatcher.rollback_session(session)
    print(f"  rolled back {len(results)} destructive action(s):")
    for r in results[:3]:
        print(f"    {r['tool']} → {r['status']}")
    if len(results) > 3:
        print(f"    ... and {len(results) - 3} more")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    _print_section("Summary")
    total = len(dispatcher.traces)
    successes = sum(1 for t in dispatcher.traces if t.status == "success")
    rejections = sum(1 for t in dispatcher.traces if t.status == "rejected")
    print(f"  total dispatch attempts : {total}")
    print(f"  successes               : {successes}")
    print(f"  rejections              : {rejections}")
    print(f"  reject breakdown        :")
    by_reason: dict[str, int] = {}
    for t in dispatcher.traces:
        if t.status == "rejected" and t.rejected_reason:
            key = t.rejected_reason.split(":")[0]
            by_reason[key] = by_reason.get(key, 0) + 1
    for reason, count in by_reason.items():
        print(f"    {reason:30s} {count}")


if __name__ == "__main__":
    main()
