"""Invariants for the Guardrail Sandwich pattern."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    GuardrailSandwich,
    GuardrailViolation,
    HookOutcome,
    HookPhase,
    HookResult,
    HookSpec,
    amount_threshold_hook,
    blocklist_hook,
    output_schema_hook,
    pii_redaction_hook,
)


# ---- Hook factories ------------------------------------------------------


def test_amount_threshold_passes_under_limit() -> None:
    hook = amount_threshold_hook("amount", max_amount=1000)
    result, _ = hook.fn("t", {"amount": 500}, None)
    assert result == HookResult.PASS


def test_amount_threshold_blocks_over_limit() -> None:
    hook = amount_threshold_hook("amount", max_amount=1000)
    result, reason = hook.fn("t", {"amount": 5000}, None)
    assert result == HookResult.BLOCK
    assert "exceeds" in reason


def test_amount_threshold_passes_when_field_missing() -> None:
    hook = amount_threshold_hook("amount", max_amount=1000)
    result, _ = hook.fn("t", {}, None)
    assert result == HookResult.PASS


def test_blocklist_blocks_listed_value() -> None:
    hook = blocklist_hook("account", {"BAD-1", "BAD-2"})
    result, _ = hook.fn("t", {"account": "BAD-1"}, None)
    assert result == HookResult.BLOCK


def test_blocklist_passes_clean_value() -> None:
    hook = blocklist_hook("account", {"BAD-1"})
    result, _ = hook.fn("t", {"account": "GOOD-1"}, None)
    assert result == HookResult.PASS


def test_output_schema_blocks_missing_keys() -> None:
    hook = output_schema_hook(["a", "b"])
    result, reason = hook.fn("t", {}, {"a": 1})
    assert result == HookResult.BLOCK
    assert "b" in reason


def test_output_schema_blocks_non_dict() -> None:
    hook = output_schema_hook(["a"])
    result, _ = hook.fn("t", {}, "not a dict")
    assert result == HookResult.BLOCK


def test_output_schema_passes_complete_dict() -> None:
    hook = output_schema_hook(["a", "b"])
    result, _ = hook.fn("t", {}, {"a": 1, "b": 2, "c": 3})
    assert result == HookResult.PASS


def test_pii_redaction_blocks_matching_pattern() -> None:
    hook = pii_redaction_hook([r"\d{3}-\d{2}-\d{4}"])
    result, _ = hook.fn("t", {}, "ssn: 123-45-6789 found")
    assert result == HookResult.BLOCK


def test_pii_redaction_passes_clean_output() -> None:
    hook = pii_redaction_hook([r"\d{3}-\d{2}-\d{4}"])
    result, _ = hook.fn("t", {}, "all clear")
    assert result == HookResult.PASS


# ---- Sandwich basics -----------------------------------------------------


def _make_sandwich_with_simple_tool():
    s = GuardrailSandwich()
    s.register_tool("echo", lambda **kwargs: {"echoed": kwargs})
    return s


def test_duplicate_tool_registration_raises() -> None:
    s = _make_sandwich_with_simple_tool()
    with pytest.raises(ValueError):
        s.register_tool("echo", lambda: None)


def test_unknown_tool_returns_tool_failed_trace() -> None:
    s = GuardrailSandwich()
    trace = s.run("missing", {})
    assert trace.final_status == "tool_failed"
    assert "unknown" in trace.tool_error.lower()


def test_no_hooks_means_tool_runs_unchanged() -> None:
    s = _make_sandwich_with_simple_tool()
    trace = s.run("echo", {"hello": "world"})
    assert trace.final_status == "passed"
    assert trace.tool_output == {"echoed": {"hello": "world"}}
    assert trace.pre_outcomes == []
    assert trace.post_outcomes == []


# ---- Pre-hook behavior ---------------------------------------------------


def test_pre_hook_block_prevents_tool_invocation() -> None:
    s = _make_sandwich_with_simple_tool()
    called = [False]

    def block_everything(name, args, output):
        return HookResult.BLOCK, "nope"

    s.add_hook(HookSpec(name="block_all", phase=HookPhase.PRE, fn=block_everything))

    # Replace tool to assert it's not called.
    def explode(**kwargs):
        called[0] = True
        return None
    s.tools["echo"] = explode

    trace = s.run("echo", {})
    assert trace.final_status == "blocked_pre"
    assert called[0] is False


def test_pre_hooks_run_in_priority_order() -> None:
    s = _make_sandwich_with_simple_tool()
    order: list[str] = []

    def make_hook(name, priority):
        def fn(t, a, o):
            order.append(name)
            return HookResult.PASS, "ok"
        return HookSpec(name=name, phase=HookPhase.PRE, fn=fn, priority=priority)

    s.add_hook(make_hook("third", 300))
    s.add_hook(make_hook("first", 100))
    s.add_hook(make_hook("second", 200))
    s.run("echo", {})
    assert order == ["first", "second", "third"]


def test_shadow_mode_downgrades_block_to_warn() -> None:
    s = _make_sandwich_with_simple_tool()

    def shadow_block(name, args, output):
        return HookResult.BLOCK, "would block in enforcement mode"

    s.add_hook(HookSpec(
        name="shadow", phase=HookPhase.PRE, fn=shadow_block, blocks=False,
    ))
    trace = s.run("echo", {})
    assert trace.final_status == "passed"
    assert trace.pre_outcomes[0].result == HookResult.WARN
    assert "[shadow]" in trace.pre_outcomes[0].reason


def test_pre_hook_crash_fails_closed() -> None:
    s = _make_sandwich_with_simple_tool()

    def buggy_hook(name, args, output):
        raise ValueError("hook author goofed")

    s.add_hook(HookSpec(name="buggy", phase=HookPhase.PRE, fn=buggy_hook))
    trace = s.run("echo", {})
    assert trace.final_status == "blocked_pre"
    assert "hook crashed" in trace.pre_outcomes[0].reason


# ---- Post-hook behavior --------------------------------------------------


def test_post_hook_block_marks_rollback_but_tool_already_ran() -> None:
    s = _make_sandwich_with_simple_tool()
    called = [False]

    def tool_run(**kwargs):
        called[0] = True
        return {"out": 1}
    s.tools["echo"] = tool_run

    def post_block(name, args, output):
        return HookResult.BLOCK, "schema mismatch"

    s.add_hook(HookSpec(name="post_block", phase=HookPhase.POST, fn=post_block))
    trace = s.run("echo", {})
    assert called[0] is True       # tool DID run
    assert trace.rollback_marked is True
    assert trace.final_status == "blocked_post"


def test_post_hooks_all_run_even_after_block() -> None:
    """Audit completeness: post-hooks form a chain that all execute,
    so the operator sees every issue, not just the first."""
    s = _make_sandwich_with_simple_tool()

    def block_hook(name, args, output):
        return HookResult.BLOCK, "issue 1"
    def warn_hook(name, args, output):
        return HookResult.WARN, "issue 2"

    s.add_hook(HookSpec(name="block", phase=HookPhase.POST, fn=block_hook, priority=10))
    s.add_hook(HookSpec(name="warn", phase=HookPhase.POST, fn=warn_hook, priority=20))
    trace = s.run("echo", {})
    assert len(trace.post_outcomes) == 2


# ---- Tool errors ---------------------------------------------------------


def test_tool_exception_skips_post_hooks_and_records_error() -> None:
    s = GuardrailSandwich()

    def explode(**kwargs):
        raise RuntimeError("downstream failure")
    s.register_tool("ex", explode)

    post_calls = [0]
    def post(name, args, output):
        post_calls[0] += 1
        return HookResult.PASS, "ok"

    s.add_hook(HookSpec(name="post", phase=HookPhase.POST, fn=post))
    trace = s.run("ex", {})
    assert trace.final_status == "tool_failed"
    assert "RuntimeError" in trace.tool_error
    assert post_calls[0] == 0


# ---- Tool scoping --------------------------------------------------------


def test_applies_to_scopes_hook_to_specific_tools() -> None:
    s = GuardrailSandwich()
    s.register_tool("a", lambda: "out-a")
    s.register_tool("b", lambda: "out-b")

    seen: list[str] = []
    def watcher(name, args, output):
        seen.append(name)
        return HookResult.PASS, "ok"

    s.add_hook(HookSpec(
        name="scoped", phase=HookPhase.PRE, fn=watcher,
        applies_to={"a"},
    ))
    s.run("a", {})
    s.run("b", {})
    assert seen == ["a"]


# ---- Trace bookkeeping --------------------------------------------------


def test_trace_records_started_and_completed_timestamps() -> None:
    s = _make_sandwich_with_simple_tool()
    trace = s.run("echo", {})
    assert trace.started_at
    assert trace.completed_at


def test_guardrail_violation_carries_hook_name_and_reason() -> None:
    err = GuardrailViolation(hook_name="x", reason="y", phase=HookPhase.PRE)
    assert err.hook_name == "x"
    assert err.reason == "y"
    assert "x" in str(err) and "y" in str(err)
