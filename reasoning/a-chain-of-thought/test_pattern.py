"""Invariants for the Chain-of-Thought pattern."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    CoTManager,
    CoTTrace,
    ThinkingBlock,
    ThinkingEffort,
)


# ---- ThinkingBlock compatibility -------------------------------------------


def test_unsigned_block_is_portable_across_models() -> None:
    b = ThinkingBlock(block_id="x", content="...", signature=None, model="claude-sonnet")
    assert b.is_compatible_with("deepseek-r1") is True


def test_signed_block_binds_to_origin_model() -> None:
    b = ThinkingBlock(block_id="x", content="...", signature="sig:abc", model="claude-opus")
    assert b.is_compatible_with("claude-opus") is True
    assert b.is_compatible_with("claude-sonnet") is False


# ---- CoTTrace strip_for_fallback ------------------------------------------


def _trace_with_mixed_blocks() -> CoTTrace:
    return CoTTrace(
        trace_id="t1",
        task="decide",
        effort=ThinkingEffort.MEDIUM,
        thinking_blocks=[
            ThinkingBlock("a", "opus-1", signature="sig:opus", model="opus", tokens=20),
            ThinkingBlock("b", "opus-2", signature="sig:opus", model="opus", tokens=30),
            ThinkingBlock("c", "portable", signature=None, model="any", tokens=10),
        ],
        final_output="decision",
        model_used="opus",
    )


def test_strip_for_fallback_drops_incompatible_blocks() -> None:
    trace = _trace_with_mixed_blocks()
    stripped = trace.strip_for_fallback("sonnet")
    assert len(stripped.thinking_blocks) == 1
    assert stripped.thinking_blocks[0].block_id == "c"
    assert stripped.model_used == "sonnet"
    assert stripped.fallback_chain == ["sonnet"]


def test_strip_for_fallback_preserves_original() -> None:
    trace = _trace_with_mixed_blocks()
    _ = trace.strip_for_fallback("sonnet")
    assert len(trace.thinking_blocks) == 3, "original trace must not be mutated"


def test_strip_for_fallback_to_same_model_keeps_all_blocks() -> None:
    trace = _trace_with_mixed_blocks()
    stripped = trace.strip_for_fallback("opus")
    assert len(stripped.thinking_blocks) == 3


# ---- Token ratio metric ---------------------------------------------------


def test_reasoning_token_ratio_grows_with_thinking() -> None:
    trace = CoTTrace(
        trace_id="t",
        task="x",
        effort=ThinkingEffort.MEDIUM,
        thinking_blocks=[
            ThinkingBlock("a", "...", tokens=100),
            ThinkingBlock("b", "...", tokens=200),
        ],
        final_output="hi",   # very short output
    )
    assert trace.reasoning_token_ratio > 0.9


def test_reasoning_token_ratio_zero_when_no_thinking() -> None:
    trace = CoTTrace(
        trace_id="t",
        task="x",
        effort=ThinkingEffort.OFF,
        thinking_blocks=[],
        final_output="hi",
    )
    assert trace.reasoning_token_ratio == 0.0


# ---- CoTManager: create_trace ---------------------------------------------


def test_create_trace_assigns_stable_id_per_task() -> None:
    m = CoTManager()
    t1 = m.create_trace("task-A")
    t2 = m.create_trace("task-A")
    assert t1.trace_id != t2.trace_id, "trace ids include timestamp; same task at different moments should differ"


def test_create_trace_uses_default_effort_when_omitted() -> None:
    m = CoTManager(default_effort=ThinkingEffort.HIGH)
    trace = m.create_trace("anything")
    assert trace.effort == ThinkingEffort.HIGH


# ---- Tag normalization ----------------------------------------------------


def test_normalize_tags_deepseek_think() -> None:
    m = CoTManager()
    raw = "<think>step one.</think><think>step two.</think>after"
    blocks = m.normalize_tags(raw, source_family="deepseek")
    assert len(blocks) == 2
    assert blocks[0].model == "deepseek"
    assert "step one" in blocks[0].content


def test_normalize_tags_openai_reasoning() -> None:
    m = CoTManager()
    raw = "<reasoning>consider clause 2.1</reasoning>final: approve"
    blocks = m.normalize_tags(raw, source_family="openai")
    assert len(blocks) == 1
    assert blocks[0].content.startswith("consider")


def test_normalize_tags_unknown_family_returns_empty() -> None:
    m = CoTManager()
    blocks = m.normalize_tags("<unknown>x</unknown>", source_family="mistral")
    assert blocks == []


def test_normalize_tags_skips_empty_content() -> None:
    m = CoTManager()
    raw = "<think>   </think>real text"
    blocks = m.normalize_tags(raw, source_family="deepseek")
    assert blocks == []


# ---- Effort estimator -----------------------------------------------------


def test_estimate_effort_short_task_returns_off() -> None:
    m = CoTManager()
    assert m.estimate_effort("today's date") == ThinkingEffort.OFF


def test_estimate_effort_proof_keyword_returns_high() -> None:
    m = CoTManager()
    assert m.estimate_effort("Please prove that the sum is associative") == ThinkingEffort.HIGH


def test_estimate_effort_medium_length_returns_medium() -> None:
    m = CoTManager()
    task = " ".join(["word"] * 50)
    assert m.estimate_effort(task) == ThinkingEffort.MEDIUM


# ---- Audit views ----------------------------------------------------------


def test_regulator_view_includes_blocks_and_chain() -> None:
    m = CoTManager()
    trace = m.create_trace("decide on claim X", model="opus")
    trace.thinking_blocks.append(ThinkingBlock("a", "consider clause", model="opus", tokens=10))
    trace.final_output = "approved."
    view = m.audit_view(trace.trace_id, view="regulator")
    assert view["thinking_blocks"]
    assert view["thinking_blocks"][0]["content"] == "consider clause"
    assert view["model_used"] == "opus"
    assert "reasoning_token_ratio" in view


def test_customer_view_omits_reasoning_content() -> None:
    m = CoTManager()
    trace = m.create_trace("decide on claim X", model="opus")
    trace.thinking_blocks.append(
        ThinkingBlock("a", "internal trade-secret reasoning here", model="opus", tokens=10)
    )
    trace.final_output = "approved."
    view = m.audit_view(trace.trace_id, view="customer")
    assert "thinking_blocks" not in view
    assert "decision_summary" in view
    assert "internal trade-secret" not in str(view), "reasoning content must not leak to customer view"


def test_audit_view_returns_empty_for_unknown_trace() -> None:
    m = CoTManager()
    assert m.audit_view("nonexistent") == {}
