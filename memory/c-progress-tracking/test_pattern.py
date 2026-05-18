"""Invariants the Progress Tracking pattern must preserve."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import ProgressTracker, TodoList, TodoStatus   # noqa: E402


# ───────────────────── invariants ─────────────────────

def test_add_creates_pending_item_with_stable_id() -> None:
    lst = TodoList(owner_id="a")
    a = lst.add("fix bug", "Fixing bug")
    b = lst.add("fix bug", "Fixing bug")
    assert a.status == TodoStatus.PENDING
    # Same content → same id (so retries don't duplicate)
    assert a.todo_id == b.todo_id


def test_only_one_item_can_be_in_progress_at_a_time() -> None:
    lst = TodoList(owner_id="a")
    a = lst.add("task A", "Doing A")
    b = lst.add("task B", "Doing B")
    lst.start(a.todo_id)
    assert a.status == TodoStatus.IN_PROGRESS
    lst.start(b.todo_id)
    assert b.status == TodoStatus.IN_PROGRESS
    assert a.status == TodoStatus.PENDING   # bumped back


def test_completing_item_sets_timestamp() -> None:
    lst = TodoList(owner_id="a")
    a = lst.add("task", "Doing task")
    lst.start(a.todo_id)
    lst.complete(a.todo_id)
    assert a.status == TodoStatus.COMPLETED
    assert a.completed_at is not None
    assert a.started_at is not None


def test_render_uses_active_form_for_in_progress_items() -> None:
    lst = TodoList(owner_id="a")
    a = lst.add("write tests", "Writing tests")
    lst.start(a.todo_id)
    rendered = lst.render()
    assert "Writing tests" in rendered
    assert "[~]" in rendered


def test_render_uses_content_for_non_in_progress_items() -> None:
    lst = TodoList(owner_id="a")
    lst.add("write tests", "Writing tests")
    rendered = lst.render()
    assert "write tests" in rendered
    assert "Writing tests" not in rendered


def test_all_done_returns_false_when_any_item_pending() -> None:
    lst = TodoList(owner_id="a")
    a = lst.add("a", "A")
    lst.add("b", "B")
    lst.complete(a.todo_id)
    assert lst.all_done() is False


def test_all_done_returns_true_when_every_item_completed() -> None:
    lst = TodoList(owner_id="a")
    a = lst.add("a", "A")
    b = lst.add("b", "B")
    lst.complete(a.todo_id)
    lst.complete(b.todo_id)
    assert lst.all_done() is True


def test_request_review_status_is_distinct_from_completed() -> None:
    lst = TodoList(owner_id="a")
    a = lst.add("a", "A")
    lst.request_review(a.todo_id)
    assert a.status == TodoStatus.NEEDS_REVIEW
    assert lst.all_done() is False   # needs_review isn't done


def test_evict_if_all_done_clears_list_when_complete() -> None:
    tracker = ProgressTracker()
    lst = tracker.get_list("agent1")
    a = lst.add("a", "A")
    lst.complete(a.todo_id)
    assert tracker.evict_if_all_done("agent1") is True
    fresh = tracker.get_list("agent1")
    assert fresh.items == []


def test_evict_does_not_fire_when_anything_still_pending() -> None:
    tracker = ProgressTracker()
    lst = tracker.get_list("agent1")
    lst.add("a", "A")
    assert tracker.evict_if_all_done("agent1") is False
    assert len(tracker.get_list("agent1").items) == 1


def test_context_loss_detection_fires_on_complex_task_with_no_todos() -> None:
    tracker = ProgressTracker()
    busy = [
        "let me refactor the parsers",
        "then implement the validators",
        "and then test the migration",
    ] * 3
    assert tracker.context_loss_detected("agent1", busy) is True


def test_context_loss_detection_silent_when_todos_exist() -> None:
    tracker = ProgressTracker()
    tracker.get_list("agent1").add("x", "X")
    busy = ["refactor then implement then test"] * 5
    assert tracker.context_loss_detected("agent1", busy) is False


def test_nudge_messages_escalate_across_calls() -> None:
    tracker = ProgressTracker()
    tracker.get_list("a").add("x", "X")
    m1 = tracker.nudge_message("a")
    m2 = tracker.nudge_message("a")
    m3 = tracker.nudge_message("a")
    assert "reminder" in m1.lower()
    assert "drifting" in m2.lower() or "drift" in m2.lower()
    assert "STOP" in m3


def test_per_owner_lists_are_isolated() -> None:
    tracker = ProgressTracker()
    tracker.get_list("agent-a").add("task A", "A")
    tracker.get_list("agent-b").add("task B", "B")
    assert len(tracker.get_list("agent-a").items) == 1
    assert len(tracker.get_list("agent-b").items) == 1
    assert (
        tracker.get_list("agent-a").items[0].content
        != tracker.get_list("agent-b").items[0].content
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
