"""Context Triage pattern.

Minimal reference implementation of the four-tier priority scheduling pattern
described in column lecture 02-02. The model is the same as an OS process
scheduler — sort context items by priority, fit as many as possible into the
token budget, and treat error stack traces as un-droppable invariants.

This file is intentionally small (≈ 90 lines). It is not a framework. It is
the smallest amount of code that captures the pattern.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Callable


class Priority(IntEnum):
    """Four-tier priority — higher number = higher priority."""

    CRITICAL = 4    # P0: system prompt, safety rules, current task
    IMPORTANT = 3   # P1: current file, recent tool results, error traces
    SUPPORTING = 2  # P2: past dialogue, background docs
    DEFERRABLE = 1  # P3: addressable but not pre-loaded; pulled via tool


@dataclass
class ContextItem:
    """One candidate item competing for a slot in the context window."""

    name: str
    content: str
    priority: Priority
    token_estimate: int = 0
    is_error: bool = False    # Error traces are invariants — never dropped.

    def __post_init__(self) -> None:
        if self.token_estimate == 0:
            # Rough heuristic — production code should use a real tokenizer
            # (tiktoken for OpenAI, the Anthropic SDK's counter for Claude).
            self.token_estimate = max(1, len(self.content) // 4)


@dataclass
class TriageDecision:
    """One trace record per triage call — required in production."""

    timestamp: str
    budget: int
    selected: list[str]
    deferred: list[str]
    dropped: list[str]
    tokens_used: int


@dataclass
class ContextTriage:
    """Sort, fit, and trace. That's the whole pattern."""

    budget: int = 180_000   # 200K window minus ~20K headroom for output
    error_detector: Callable[[ContextItem], bool] | None = None
    _decisions: list[TriageDecision] = field(default_factory=list)

    def triage(
        self, items: list[ContextItem]
    ) -> tuple[list[ContextItem], list[ContextItem], TriageDecision]:
        """Return (selected, deferred, decision_trace)."""
        # Sort key: priority desc, error trace boost, content length desc.
        sorted_items = sorted(
            items,
            key=lambda x: (
                x.priority.value,
                2.0 if self._is_error(x) else 0.0,
                len(x.content),
            ),
            reverse=True,
        )

        selected: list[ContextItem] = []
        deferred: list[ContextItem] = []
        dropped: list[ContextItem] = []
        tokens_used = 0

        for item in sorted_items:
            if item.priority == Priority.DEFERRABLE:
                deferred.append(item)
                continue
            if tokens_used + item.token_estimate <= self.budget or self._is_error(item):
                selected.append(item)
                tokens_used += item.token_estimate
            else:
                dropped.append(item)

        decision = TriageDecision(
            timestamp=datetime.now(timezone.utc).isoformat(),
            budget=self.budget,
            selected=[i.name for i in selected],
            deferred=[i.name for i in deferred],
            dropped=[i.name for i in dropped],
            tokens_used=tokens_used,
        )
        self._decisions.append(decision)
        return selected, deferred, decision

    def _is_error(self, item: ContextItem) -> bool:
        if item.is_error:
            return True
        if self.error_detector is not None:
            return bool(self.error_detector(item))
        return False

    @property
    def decisions(self) -> list[TriageDecision]:
        """Trace history — for debugging and analytics."""
        return list(self._decisions)
