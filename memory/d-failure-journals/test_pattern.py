"""Invariants for the Failure Journals pattern."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    FailureCategory,
    FailureEntry,
    FailureJournal,
)


# ---- Stable failure_id -----------------------------------------------------


def test_failure_id_is_stable_for_same_inputs() -> None:
    exc = RuntimeError("boundary leak: test client_id in prod/oauth.yaml")
    e1 = FailureEntry.from_exception(exc, FailureCategory.BOUNDARY_LEAK, "task-X")
    e2 = FailureEntry.from_exception(exc, FailureCategory.BOUNDARY_LEAK, "task-X")
    assert e1.failure_id == e2.failure_id


def test_failure_id_differs_when_category_differs() -> None:
    exc = RuntimeError("same message")
    a = FailureEntry.from_exception(exc, FailureCategory.BOUNDARY_LEAK, "task-X")
    b = FailureEntry.from_exception(exc, FailureCategory.TOOL_ERROR, "task-X")
    assert a.failure_id != b.failure_id


# ---- Recording -------------------------------------------------------------


def test_recording_same_failure_twice_increments_access_count() -> None:
    j = FailureJournal()
    exc = RuntimeError("repeated mistake")
    e1 = FailureEntry.from_exception(exc, FailureCategory.TOOL_ERROR, "task-Y")
    j.record(e1)
    e2 = FailureEntry.from_exception(exc, FailureCategory.TOOL_ERROR, "task-Y")
    j.record(e2)
    assert len(j.entries) == 1
    assert j.entries[e1.failure_id].access_count == 1


def test_different_signatures_create_different_entries() -> None:
    j = FailureJournal()
    e1 = FailureEntry.from_exception(
        RuntimeError("same exc"), FailureCategory.TOOL_ERROR, "task-A",
    )
    e2 = FailureEntry.from_exception(
        RuntimeError("same exc"), FailureCategory.TOOL_ERROR, "task-B",
    )
    j.record(e1)
    j.record(e2)
    assert len(j.entries) == 2


# ---- Classification --------------------------------------------------------


def test_by_category_filters_correctly() -> None:
    j = FailureJournal()
    for category, msg in [
        (FailureCategory.BOUNDARY_LEAK, "leak 1"),
        (FailureCategory.BOUNDARY_LEAK, "leak 2"),
        (FailureCategory.TOOL_ERROR, "tool 1"),
        (FailureCategory.API_TRANSIENT, "api 1"),
    ]:
        j.record(FailureEntry.from_exception(
            RuntimeError(msg), category, f"task-{msg}",
        ))
    assert len(j.by_category(FailureCategory.BOUNDARY_LEAK)) == 2
    assert len(j.by_category(FailureCategory.TOOL_ERROR)) == 1
    assert len(j.by_category(FailureCategory.CONTEXT_OVERFLOW)) == 0


def test_high_risk_entries_returns_only_boundary_and_permission() -> None:
    j = FailureJournal()
    for cat in [
        FailureCategory.BOUNDARY_LEAK,
        FailureCategory.PERMISSION_DENY,
        FailureCategory.TOOL_ERROR,
        FailureCategory.API_TRANSIENT,
    ]:
        j.record(FailureEntry.from_exception(
            RuntimeError(cat.value), cat, f"task-{cat.value}",
        ))
    high_risk = j.high_risk_entries()
    assert len(high_risk) == 2
    assert {e.category for e in high_risk} == {
        FailureCategory.BOUNDARY_LEAK,
        FailureCategory.PERMISSION_DENY,
    }


# ---- Recall ----------------------------------------------------------------


def test_recall_returns_entries_above_similarity_threshold() -> None:
    j = FailureJournal()
    j.record(FailureEntry.from_exception(
        RuntimeError("oauth token refresh failed"),
        FailureCategory.TOOL_ERROR,
        "fix oauth refresh in billing-service config/oauth.yaml",
    ))
    j.record(FailureEntry.from_exception(
        RuntimeError("unrelated billing webhook bug"),
        FailureCategory.API_TRANSIENT,
        "stripe webhook retry storm in payments-service",
    ))

    results = j.recall_for_task(
        "fix oauth token refresh in billing-service oauth.yaml config",
        threshold=0.25,
        force_include_high_risk=False,
    )
    assert len(results) >= 1
    assert any("oauth" in r.task_signature for r in results)


def test_recall_updates_access_count_and_last_recalled_at() -> None:
    j = FailureJournal()
    entry = FailureEntry.from_exception(
        RuntimeError("typo in regex"),
        FailureCategory.TOOL_ERROR,
        "regex fix in parser module",
    )
    j.record(entry)
    assert entry.access_count == 0
    assert entry.last_recalled_at is None

    j.recall_for_task("regex fix in parser module", threshold=0.5, force_include_high_risk=False)
    assert entry.access_count == 1
    assert entry.last_recalled_at is not None


def test_recall_high_risk_override_surfaces_even_when_similarity_is_zero() -> None:
    j = FailureJournal()
    j.record(FailureEntry.from_exception(
        RuntimeError("test client_id in prod config"),
        FailureCategory.BOUNDARY_LEAK,
        "auth-service config oauth.yaml edit",
        lessons=["always re-read env header"],
    ))

    # Task signature with no word overlap with the recorded entry.
    results = j.recall_for_task(
        "render quarterly revenue chart for sales dashboard",
        threshold=0.95,
        force_include_high_risk=True,
    )
    assert len(results) == 1
    assert results[0].category == FailureCategory.BOUNDARY_LEAK


def test_recall_can_be_disabled_for_high_risk_override() -> None:
    j = FailureJournal()
    j.record(FailureEntry.from_exception(
        RuntimeError("test client_id in prod config"),
        FailureCategory.BOUNDARY_LEAK,
        "auth-service config edit",
    ))
    results = j.recall_for_task(
        "render quarterly revenue chart",
        threshold=0.95,
        force_include_high_risk=False,
    )
    assert results == []


def test_recall_respects_top_k() -> None:
    j = FailureJournal()
    for i in range(5):
        j.record(FailureEntry.from_exception(
            RuntimeError(f"shared token error {i}"),
            FailureCategory.TOOL_ERROR,
            f"shared task signature with token {i}",
        ))
    results = j.recall_for_task(
        "shared task signature with token query",
        top_k=2,
        threshold=0.2,
        force_include_high_risk=False,
    )
    assert len(results) == 2


# ---- Render ---------------------------------------------------------------


def test_render_for_prompt_includes_category_summary_and_lessons() -> None:
    j = FailureJournal()
    entry = FailureEntry.from_exception(
        RuntimeError("test client_id leaked to prod config"),
        FailureCategory.BOUNDARY_LEAK,
        "auth-service config edit",
        lessons=["re-read env header", "diff unrelated config changes"],
    )
    j.record(entry)
    text = j.render_for_prompt([entry])
    assert "boundary_leak" in text
    assert "test client_id leaked to prod config" in text
    assert "re-read env header" in text
    assert "diff unrelated config changes" in text


def test_render_for_prompt_empty_returns_empty_string() -> None:
    j = FailureJournal()
    assert j.render_for_prompt([]) == ""


# ---- Lifecycle ------------------------------------------------------------


def test_eviction_protects_high_risk_entries() -> None:
    """High-risk failures (boundary_leak / permission_deny) must not be evicted
    even when the journal is over capacity."""
    j = FailureJournal(max_entries=3)

    # A high-risk entry that has never been recalled.
    high_risk = FailureEntry.from_exception(
        RuntimeError("test client_id in prod"),
        FailureCategory.BOUNDARY_LEAK,
        "auth boundary leak",
    )
    j.record(high_risk)

    # Fill the journal with five low-risk entries (some recalled, some not).
    for i in range(5):
        e = FailureEntry.from_exception(
            RuntimeError(f"low-risk {i}"),
            FailureCategory.TOOL_ERROR,
            f"low-risk task {i}",
        )
        j.record(e)

    assert high_risk.failure_id in j.entries
    assert len(j.entries) <= 3


def test_health_report_includes_recall_rate_and_categories() -> None:
    j = FailureJournal()
    j.record(FailureEntry.from_exception(
        RuntimeError("first"),
        FailureCategory.TOOL_ERROR,
        "task-first",
    ))
    j.record(FailureEntry.from_exception(
        RuntimeError("second"),
        FailureCategory.BOUNDARY_LEAK,
        "task-second",
    ))
    # Trigger recall on the first entry so recall_rate > 0.
    j.recall_for_task("task-first", threshold=0.5, force_include_high_risk=False)
    report = j.health_report()
    assert report["total_entries"] == 2
    assert report["recall_rate"] > 0
    assert report["high_risk_entries"] == 1
    assert report["by_category"][FailureCategory.TOOL_ERROR.value] == 1
    assert report["by_category"][FailureCategory.BOUNDARY_LEAK.value] == 1
