"""Invariants the Semantic Compaction pattern must preserve."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)   # ensure we pick up THIS folder's pattern.py

from pattern import CompactionAnchor, SemanticCompactor, Turn   # noqa: E402


def _stub_llm(prompt: str) -> str:
    return (
        "INTENT: diagnose flaky test\n"
        "CHANGES: pinned numpy | added retry\n"
        "DECIDED: it's not a network issue\n"
        "EXCLUDED: GPU driver | thread-pool size\n"
        "NEXT: profile the failing test"
    )


def _turns_n(n: int, tokens_each: int = 100, *, role: str = "tool_result") -> list[Turn]:
    return [Turn(role=role, content="x" * tokens_each * 4, tokens=tokens_each) for _ in range(n)]


def test_compact_returns_input_if_already_under_budget() -> None:
    turns = _turns_n(3, tokens_each=50)
    c = SemanticCompactor(llm=_stub_llm)
    out = c.compact(turns, target_tokens=10_000)
    assert out == turns
    assert not c.events


def test_should_compact_threshold_is_inclusive() -> None:
    c = SemanticCompactor(llm=_stub_llm, trigger_at_ratio=0.60)
    assert c.should_compact(total_tokens=6_000, budget=10_000) is True
    assert c.should_compact(total_tokens=5_999, budget=10_000) is False


def test_error_traces_survive_level_1() -> None:
    turns = [
        Turn(role="tool_result", content="huge log " * 1000, tokens=2_000),
        Turn(role="tool_result", content="Traceback: boom", tokens=50, is_error=True),
        *_turns_n(4, tokens_each=20, role="assistant"),
    ]
    c = SemanticCompactor(llm=_stub_llm, preserve_recent=2)
    out = c.compact(turns, target_tokens=200)
    errors_in = sum(1 for t in turns if t.is_error)
    errors_out = sum(1 for t in out if t.is_error)
    assert errors_out >= errors_in


def test_anchor_excluded_approaches_persist_across_compaction() -> None:
    turns = _turns_n(20, tokens_each=200)
    anchor = CompactionAnchor(
        intent="debug flaky test",
        excluded_approaches=["GPU driver hypothesis"],
    )
    c = SemanticCompactor(llm=_stub_llm, anchor=anchor, preserve_recent=2)
    c.compact(turns, target_tokens=300)
    assert "GPU driver hypothesis" in c.anchor.excluded_approaches


def test_anchor_to_summary_renders_only_non_empty_slots() -> None:
    a = CompactionAnchor(intent="hello")
    s = a.to_summary()
    assert "INTENT: hello" in s
    assert "CHANGES" not in s
    assert "EXCLUDED" not in s


def test_compaction_event_records_token_deltas() -> None:
    turns = _turns_n(15, tokens_each=1_500)
    c = SemanticCompactor(llm=_stub_llm, preserve_recent=2)
    c.compact(turns, target_tokens=2_000)
    assert c.events
    e = c.events[-1]
    assert e.tokens_after < e.tokens_before
    assert 0 < e.compression_ratio < 1


def test_health_check_flags_error_loss_violations() -> None:
    # Inject an error that we expect to survive; we'll force a fake L3 by
    # constructing an event that drops it.
    c = SemanticCompactor(llm=_stub_llm, preserve_recent=2)
    fake_input = [
        Turn(role="user", content="ok", tokens=10),
        Turn(role="tool_result", content="Error: boom", tokens=10, is_error=True),
    ]
    # Manually log an "error-dropping" event to verify health_check catches it
    c._log(3, before_n=2, result=fake_input[:1], before_t=20, errors_in=1)
    report = c.health_check()
    assert "error_loss_violation" in report


def test_level_3_fires_only_when_l1_and_l2_insufficient() -> None:
    # Make every turn an error trace so L1 (clear tools) and L2 (fold to anchor)
    # cannot drop enough tokens.
    turns = [Turn(role="tool_result", content="Error " + "x" * 400, tokens=200, is_error=True)
             for _ in range(20)]
    c = SemanticCompactor(llm=_stub_llm, preserve_recent=2)
    c.compact(turns, target_tokens=500)
    assert c.events[-1].level == 3


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
