"""Invariants the Context Triage pattern must preserve."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)   # ensure we pick up THIS folder's pattern.py

from pattern import ContextItem, ContextTriage, Priority   # noqa: E402


def _items(*specs: tuple[str, Priority, int, bool]) -> list[ContextItem]:
    return [
        ContextItem(name=n, content="x" * (toks * 4), priority=p, is_error=err)
        for (n, p, toks, err) in specs
    ]


def test_p3_items_are_always_deferred_not_loaded() -> None:
    items = _items(
        ("a", Priority.CRITICAL, 10, False),
        ("b", Priority.DEFERRABLE, 10, False),
    )
    selected, deferred, _ = ContextTriage(budget=1000).triage(items)
    assert [i.name for i in selected] == ["a"]
    assert [i.name for i in deferred] == ["b"]


def test_priority_order_selected_first() -> None:
    items = _items(
        ("low", Priority.SUPPORTING, 5, False),
        ("high", Priority.CRITICAL, 5, False),
    )
    selected, _, _ = ContextTriage(budget=1000).triage(items)
    assert selected[0].name == "high"


def test_error_items_are_preserved_even_when_budget_exhausted() -> None:
    items = _items(
        ("bulk", Priority.CRITICAL, 990, False),
        ("err", Priority.IMPORTANT, 100, True),     # would overflow budget
    )
    selected, _, _ = ContextTriage(budget=1000).triage(items)
    names = [i.name for i in selected]
    assert "err" in names, "error trace must never be dropped"


def test_low_priority_items_dropped_when_budget_overflows() -> None:
    items = _items(
        ("must", Priority.CRITICAL, 800, False),
        ("nice", Priority.SUPPORTING, 800, False),
    )
    selected, _, decision = ContextTriage(budget=1000).triage(items)
    assert [i.name for i in selected] == ["must"]
    assert decision.dropped == ["nice"]


def test_decision_trace_records_every_call() -> None:
    triage = ContextTriage(budget=1000)
    items = _items(("a", Priority.CRITICAL, 10, False))
    triage.triage(items)
    triage.triage(items)
    assert len(triage.decisions) == 2
    for d in triage.decisions:
        assert d.timestamp and d.budget == 1000


def test_custom_error_detector_protects_inferred_errors() -> None:
    items = _items(
        ("bulk", Priority.CRITICAL, 990, False),
        ("trace", Priority.IMPORTANT, 100, False),  # no is_error flag
    )
    items[1].content = "Traceback (most recent call last): boom"
    triage = ContextTriage(
        budget=1000,
        error_detector=lambda i: "Traceback" in i.content,
    )
    selected, _, _ = triage.triage(items)
    assert "trace" in [i.name for i in selected]


def test_tokens_used_never_exceeds_budget_except_for_error_invariant() -> None:
    items = _items(
        ("a", Priority.CRITICAL, 400, False),
        ("b", Priority.CRITICAL, 400, False),
        ("c", Priority.CRITICAL, 400, False),
    )
    _, _, decision = ContextTriage(budget=1000).triage(items)
    assert decision.tokens_used <= 1000


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
