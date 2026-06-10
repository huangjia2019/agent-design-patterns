"""Shared hook factories for Guardrail Sandwich tutorials.

Both the langgraph/ and langchain/ notebooks import from here so the hook
definitions stay in sync. Each factory returns a config dict:

    {"name", "fn", "phase" (langgraph only), "priority", "blocks", "applies_to"}

The langchain/ notebook ignores the "phase" key since it uses separate
pre_hooks/post_hooks lists.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class HookResult(str, Enum):
    PASS = "pass"
    BLOCK = "block"
    WARN = "warn"


class HookPhase(str, Enum):
    PRE = "pre"
    POST = "post"


def amount_threshold_hook(field_name: str, max_amount: float, *,
                          name: str = "amount_threshold", priority: int = 100,
                          blocks: bool = True, applies_to: list[str] | None = None) -> dict[str, Any]:
    """PRE: blocks when args[field_name] exceeds max_amount."""
    def fn(_tool_name, args, _output):
        amount = args.get(field_name)
        if amount is None:
            return HookResult.PASS.value, f"field {field_name!r} absent"
        if amount > max_amount:
            return HookResult.BLOCK.value, f"{field_name}={amount} exceeds {max_amount}"
        return HookResult.PASS.value, f"{field_name}={amount} within limit"
    return {"name": name, "fn": fn, "phase": HookPhase.PRE.value,
            "priority": priority, "blocks": blocks, "applies_to": applies_to}


def blocklist_hook(field_name: str, blocklist: set[str], *,
                   name: str = "blocklist", priority: int = 100,
                   blocks: bool = True, applies_to: list[str] | None = None) -> dict[str, Any]:
    """PRE: blocks when args[field_name] matches a deny-list entry."""
    def fn(_tool_name, args, _output):
        value = str(args.get(field_name, ""))
        if value in blocklist:
            return HookResult.BLOCK.value, f"{field_name}={value!r} on blocklist"
        return HookResult.PASS.value, f"{field_name} clear"
    return {"name": name, "fn": fn, "phase": HookPhase.PRE.value,
            "priority": priority, "blocks": blocks, "applies_to": applies_to}


def output_schema_hook(required_keys: list[str], *,
                       name: str = "output_schema", priority: int = 100,
                       blocks: bool = True, applies_to: list[str] | None = None) -> dict[str, Any]:
    """POST: blocks when tool output is missing required keys."""
    def fn(_tool_name, _args, output):
        if not isinstance(output, dict):
            return HookResult.BLOCK.value, f"output is {type(output).__name__}, expected dict"
        missing = [key for key in required_keys if key not in output]
        if missing:
            return HookResult.BLOCK.value, f"output missing keys: {missing}"
        return HookResult.PASS.value, "output schema valid"
    return {"name": name, "fn": fn, "phase": HookPhase.POST.value,
            "priority": priority, "blocks": blocks, "applies_to": applies_to}
