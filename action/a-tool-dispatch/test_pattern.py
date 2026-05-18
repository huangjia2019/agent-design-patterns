"""Invariants for the Tool Dispatch pattern."""
from __future__ import annotations

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    DispatchTrace,
    RiskLevel,
    ToolDispatchError,
    ToolDispatcher,
    ToolMetadata,
)


# ---- Registration guards ---------------------------------------------------


def test_destructive_tool_without_rollback_action_raises() -> None:
    d = ToolDispatcher()
    meta = ToolMetadata(name="zap", description="zap", when_to_use="when",
                        is_destructive=True, rollback_action=None)
    with pytest.raises(ToolDispatchError):
        d.register(meta, lambda: None)


def test_tool_cannot_be_both_read_only_and_destructive() -> None:
    d = ToolDispatcher()
    meta = ToolMetadata(name="x", description="x", when_to_use="when",
                        is_read_only=True, is_destructive=True,
                        rollback_action="undo")
    with pytest.raises(ToolDispatchError):
        d.register(meta, lambda: None)


def test_registered_tool_is_findable() -> None:
    d = ToolDispatcher()
    d.register(
        ToolMetadata(name="ping", description="ping", when_to_use="health"),
        lambda: "pong",
    )
    assert "ping" in d.tools


# ---- Hallucination & unknown tools ----------------------------------------


def test_hallucinated_tool_is_rejected() -> None:
    d = ToolDispatcher()
    trace = d.dispatch("nonexistent", {}, "s1")
    assert trace.status == "rejected"
    assert trace.rejected_reason == "tool_hallucination"


# ---- Read-only path -------------------------------------------------------


def test_read_only_call_succeeds_and_refreshes_state() -> None:
    d = ToolDispatcher()
    d.register(
        ToolMetadata(name="q", description="q", when_to_use="x", is_read_only=True),
        lambda: [1, 2, 3],
    )
    trace = d.dispatch("q", {}, "s1")
    assert trace.status == "success"
    assert trace.output == [1, 2, 3]
    assert "s1" in d.last_state_refresh


# ---- Quota enforcement ----------------------------------------------------


def _build_dispatcher_with_assign(quota: int) -> ToolDispatcher:
    d = ToolDispatcher()
    d.register(
        ToolMetadata(name="refresh", description="r", when_to_use="x",
                     is_read_only=True),
        lambda: True,
    )
    d.register(
        ToolMetadata(
            name="assign", description="a", when_to_use="x",
            is_destructive=True, requires_fresh_state=False,   # off for these tests
            quota_per_session=quota, rollback_action="undo",
        ),
        lambda driver_id, order_id: {"driver_id": driver_id, "order_id": order_id},
    )
    d.register(
        ToolMetadata(name="undo", description="u", when_to_use="x"),
        lambda driver_id, order_id: True,
    )
    return d


def test_quota_per_session_blocks_after_n_calls() -> None:
    d = _build_dispatcher_with_assign(quota=3)
    for i in range(3):
        t = d.dispatch("assign",
                       {"driver_id": "d1", "order_id": f"o{i}"}, "s1")
        assert t.status == "success", f"call {i} should succeed"
    blocked = d.dispatch("assign", {"driver_id": "d1", "order_id": "o4"}, "s1")
    assert blocked.status == "rejected"
    assert "quota_exceeded" in blocked.rejected_reason


def test_quota_is_scoped_per_primary_arg() -> None:
    d = _build_dispatcher_with_assign(quota=2)
    # Two calls to driver d1 exhaust its quota; d2 is independent.
    for i in range(2):
        d.dispatch("assign", {"driver_id": "d1", "order_id": f"o{i}"}, "s1")
    t = d.dispatch("assign", {"driver_id": "d2", "order_id": "o-d2"}, "s1")
    assert t.status == "success"


def test_quota_is_scoped_per_session() -> None:
    d = _build_dispatcher_with_assign(quota=1)
    d.dispatch("assign", {"driver_id": "d1", "order_id": "o1"}, "session-A")
    t = d.dispatch("assign", {"driver_id": "d1", "order_id": "o2"}, "session-B")
    assert t.status == "success", "different session should not share quota"


def test_unlimited_quota_minus_one() -> None:
    d = _build_dispatcher_with_assign(quota=-1)
    for i in range(20):
        t = d.dispatch("assign", {"driver_id": "d1", "order_id": f"o{i}"}, "s1")
        assert t.status == "success"


# ---- State freshness ------------------------------------------------------


def test_requires_fresh_state_blocks_without_refresh() -> None:
    d = ToolDispatcher()
    d.register(
        ToolMetadata(
            name="write", description="w", when_to_use="x",
            is_destructive=True, requires_fresh_state=True,
            rollback_action="undo",
        ),
        lambda key, value: {"key": key, "value": value},
    )
    d.register(ToolMetadata(name="undo", description="u", when_to_use="x"),
               lambda key, value: True)

    t = d.dispatch("write", {"key": "k", "value": "v"}, "s1")
    assert t.status == "rejected"
    assert t.rejected_reason == "stale_state_must_refresh"


def test_requires_fresh_state_passes_after_recent_read() -> None:
    d = ToolDispatcher()
    d.register(
        ToolMetadata(name="read", description="r", when_to_use="x",
                     is_read_only=True),
        lambda: [],
    )
    d.register(
        ToolMetadata(name="write", description="w", when_to_use="x",
                     is_destructive=True, requires_fresh_state=True,
                     rollback_action="undo"),
        lambda key, value: {"k": key, "v": value},
    )
    d.register(ToolMetadata(name="undo", description="u", when_to_use="x"),
               lambda key, value: True)

    d.dispatch("read", {}, "s1")
    t = d.dispatch("write", {"key": "k", "value": "v"}, "s1")
    assert t.status == "success"


def test_requires_fresh_state_blocks_after_freshness_window() -> None:
    d = ToolDispatcher()
    d.STATE_FRESHNESS_SECONDS = 0   # any read is immediately "stale"
    d.register(
        ToolMetadata(name="read", description="r", when_to_use="x",
                     is_read_only=True),
        lambda: [],
    )
    d.register(
        ToolMetadata(name="write", description="w", when_to_use="x",
                     is_destructive=True, requires_fresh_state=True,
                     rollback_action="undo"),
        lambda key, value: True,
    )
    d.register(ToolMetadata(name="undo", description="u", when_to_use="x"),
               lambda key, value: True)
    d.dispatch("read", {}, "s1")
    time.sleep(0.01)
    t = d.dispatch("write", {"key": "k", "value": "v"}, "s1")
    assert t.status == "rejected"
    assert t.rejected_reason == "stale_state_must_refresh"


# ---- Approval gate --------------------------------------------------------


def test_requires_approval_short_circuits_with_pending_reason() -> None:
    d = ToolDispatcher()
    d.register(
        ToolMetadata(name="approve_op", description="a", when_to_use="x",
                     requires_approval=True),
        lambda: "should not run",
    )
    t = d.dispatch("approve_op", {}, "s1")
    assert t.status == "rejected"
    assert t.rejected_reason == "awaiting_approval"


# ---- Execution failures ---------------------------------------------------


def test_handler_exception_becomes_failed_trace() -> None:
    d = ToolDispatcher()
    def explode() -> None:
        raise ValueError("boom")
    d.register(
        ToolMetadata(name="x", description="x", when_to_use="x", is_read_only=True),
        explode,
    )
    t = d.dispatch("x", {}, "s1")
    assert t.status == "failed"
    assert "ValueError" in (t.rejected_reason or "")


# ---- Saga rollback --------------------------------------------------------


def test_destructive_success_appends_to_saga_log() -> None:
    d = _build_dispatcher_with_assign(quota=5)
    d.dispatch("assign", {"driver_id": "d1", "order_id": "o1"}, "s1")
    assert len(d.saga_log) == 1
    assert d.saga_log[0]["tool"] == "assign"
    assert d.saga_log[0]["rollback"] == "undo"


def test_rollback_session_unwinds_in_reverse() -> None:
    d = _build_dispatcher_with_assign(quota=5)
    call_log: list[tuple] = []

    def tracked_undo(driver_id: str, order_id: str) -> bool:
        call_log.append((driver_id, order_id))
        return True

    d.handlers["undo"] = tracked_undo
    for i in range(3):
        d.dispatch("assign",
                   {"driver_id": "d1", "order_id": f"o{i}"}, "s1")
    d.rollback_session("s1")
    assert call_log == [("d1", "o2"), ("d1", "o1"), ("d1", "o0")]


def test_rollback_session_leaves_other_sessions_intact() -> None:
    d = _build_dispatcher_with_assign(quota=5)
    d.dispatch("assign", {"driver_id": "d1", "order_id": "oA"}, "session-A")
    d.dispatch("assign", {"driver_id": "d1", "order_id": "oB"}, "session-B")
    d.rollback_session("session-A")
    remaining_sessions = {entry["session_id"] for entry in d.saga_log}
    assert remaining_sessions == {"session-B"}


# ---- Trace history --------------------------------------------------------


def test_every_dispatch_is_recorded() -> None:
    d = ToolDispatcher()
    d.register(
        ToolMetadata(name="r", description="r", when_to_use="x", is_read_only=True),
        lambda: 1,
    )
    for _ in range(5):
        d.dispatch("r", {}, "s1")
    d.dispatch("nope", {}, "s1")
    assert len(d.traces) == 6
    assert isinstance(d.traces[0], DispatchTrace)
