"""Progress Tracking pattern.

Reference implementation of the structured-todo pattern from column
lecture 03-04. The pattern's claim: **LLMs have no working memory**.
Their entire "memory" lives inside the context window, and the window
has a U-shaped attention curve — the middle of a long task gets buried.

When an agent goes on a 30-turn debug detour mid-task, the original
plan's remaining items often get forgotten. The fix is dumb-engineering
robust: force the agent to maintain a structured, externalised todo
list, and nudge it back to that list whenever the conversation drifts.

Core data model (matches Claude Code's three-field TodoWrite):

* `content` — what needs doing ("Fix cache invalidation bug")
* `active_form` — present-continuous phrasing for in-progress display
  ("Fixing cache invalidation bug")
* `status` — one of pending / in_progress / completed / needs_review

Invariants enforced by `TodoList`:

* At most one item is `in_progress` at a time. Starting a new item
  bumps any existing in-progress item back to pending.
* The list is per-owner (per agent, per session, per sub-agent), so
  sub-agents don't pollute the parent's todos.
* When all items complete, the list auto-evicts — Claude Code's
  counter-intuitive but necessary "clear when done" behaviour.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class TodoStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"     # optional: human review gate before completion


_STATUS_MARK = {
    "pending": "[ ]",
    "in_progress": "[~]",
    "completed": "[x]",
    "needs_review": "[?]",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TodoItem:
    content: str                                  # imperative form
    active_form: str                              # present-continuous, for in-progress display
    status: TodoStatus = TodoStatus.PENDING
    created_at: str = field(default_factory=_now_iso)
    started_at: str | None = None
    completed_at: str | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def todo_id(self) -> str:
        """Stable id — content hash, so retries don't duplicate the item."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:12]


@dataclass
class TodoList:
    """Per-owner todo list with invariant enforcement."""

    owner_id: str
    items: list[TodoItem] = field(default_factory=list)

    def add(
        self,
        content: str,
        active_form: str,
        tags: list[str] | None = None,
    ) -> TodoItem:
        item = TodoItem(
            content=content, active_form=active_form, tags=tags or [],
        )
        self.items.append(item)
        return item

    def start(self, todo_id: str) -> None:
        """Mark in_progress. Bump any other in-progress item back to pending."""
        for it in self.items:
            if it.status == TodoStatus.IN_PROGRESS and it.todo_id != todo_id:
                it.status = TodoStatus.PENDING
        for it in self.items:
            if it.todo_id == todo_id:
                it.status = TodoStatus.IN_PROGRESS
                it.started_at = _now_iso()
                return

    def complete(self, todo_id: str) -> None:
        for it in self.items:
            if it.todo_id == todo_id:
                it.status = TodoStatus.COMPLETED
                it.completed_at = _now_iso()
                return

    def request_review(self, todo_id: str) -> None:
        """Mark needs_review. The gate before declaring done."""
        for it in self.items:
            if it.todo_id == todo_id:
                it.status = TodoStatus.NEEDS_REVIEW
                return

    def in_progress_item(self) -> TodoItem | None:
        for it in self.items:
            if it.status == TodoStatus.IN_PROGRESS:
                return it
        return None

    def all_done(self) -> bool:
        return bool(self.items) and all(
            it.status == TodoStatus.COMPLETED for it in self.items
        )

    def pending_count(self) -> int:
        return sum(1 for it in self.items if it.status == TodoStatus.PENDING)

    def render(self) -> str:
        """Markdown render for injection back into the agent's context."""
        if not self.items:
            return "(no todos)"
        lines = []
        for it in self.items:
            mark = _STATUS_MARK[it.status.value]
            label = it.active_form if it.status == TodoStatus.IN_PROGRESS else it.content
            lines.append(f"{mark} {label}")
        return "\n".join(lines)


# Complexity estimator: takes recent message strings, returns an int score
ComplexityFn = Callable[[list[str]], int]


def _default_complexity(messages: list[str]) -> int:
    """Coarse: count action verbs + sequencing words across recent messages."""
    text = " ".join(messages).lower()
    verbs = ["refactor", "implement", "fix", "build", "migrate", "test", "deploy"]
    sequencers = ["then", "after", "next", "and then", "first", "finally", "步骤", "然后"]
    return sum(text.count(v) for v in verbs) + sum(text.count(s) for s in sequencers)


class ProgressTracker:
    """Manage per-owner todo lists + escalating nudges for context-loss recovery."""

    def __init__(self, complexity_estimator: ComplexityFn | None = None) -> None:
        self.lists: dict[str, TodoList] = {}
        self.complexity_estimator = complexity_estimator or _default_complexity
        self.nudge_count: dict[str, int] = {}

    def get_list(self, owner_id: str) -> TodoList:
        if owner_id not in self.lists:
            self.lists[owner_id] = TodoList(owner_id=owner_id)
        return self.lists[owner_id]

    def evict_if_all_done(self, owner_id: str) -> bool:
        """Clear the list if every item is completed. Returns True if evicted."""
        lst = self.lists.get(owner_id)
        if lst is not None and lst.all_done():
            self.lists[owner_id] = TodoList(owner_id=owner_id)
            self.nudge_count.pop(owner_id, None)
            return True
        return False

    def context_loss_detected(
        self, owner_id: str, recent_messages: list[str], threshold: int = 3,
    ) -> bool:
        """DeerFlow-style detection: complex task running, no todos = drift risk."""
        complexity = self.complexity_estimator(recent_messages)
        has_todos = bool(self.lists.get(owner_id, TodoList(owner_id=owner_id)).items)
        return complexity >= threshold and not has_todos

    def nudge_message(self, owner_id: str) -> str:
        """Escalating system-injected reminder — louder each time."""
        n = self.nudge_count.get(owner_id, 0)
        self.nudge_count[owner_id] = n + 1
        list_render = self.get_list(owner_id).render()
        if n == 0:
            return f"[reminder] Your current todos:\n{list_render}"
        if n == 1:
            return (
                "[reminder] You appear to be drifting from your plan. "
                f"Re-read your todos and pick the next item:\n{list_render}"
            )
        return (
            "[reminder] STOP. You have not updated todos in several turns. "
            "Update the list before taking any further action:\n" + list_render
        )
