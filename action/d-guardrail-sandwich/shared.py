"""Shared hook factories for the Guardrail Sandwich reference implementations.

Both the langgraph/ and langchain/ notebooks import from here, so the hook
definitions — and the runner that executes them — stay in sync between the two
frameworks. Each factory returns a config dict:

    {"name", "fn", "phase", "priority", "blocks", "applies_to"}

- phase       — PRE (before the tool) or POST (after it)
- priority    — lower runs first
- blocks      — False = shadow mode (a BLOCK is downgraded to WARN, tool still runs)
- applies_to  — None = every tool; or a list of tool names this hook guards

Both notebooks honor every field: they filter by `phase` and `applies_to`,
sort by `priority`, and run each hook through `run_single_hook` below.
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


def applicable_hooks(hooks: list[dict[str, Any]], phase: HookPhase, tool_name: str) -> list[dict[str, Any]]:
    """Hooks for this phase that apply to this tool, in priority order.

    `applies_to=None` means the hook guards every tool; otherwise the tool name
    must be listed. Both notebooks select hooks through this one function."""
    selected = [
        h for h in hooks
        if h["phase"] == phase.value
        and (h.get("applies_to") is None or tool_name in h["applies_to"])
    ]
    return sorted(selected, key=lambda h: h.get("priority", 100))


def run_single_hook(hook_cfg: dict[str, Any], tool_name: str, args: dict[str, Any],
                    tool_output: Any) -> dict[str, Any]:
    """Run one hook and return a structured outcome dict.

    Two safety rules, identical on both sides:
    - Fail closed: if the hook fn raises, treat it as BLOCK (never PASS).
    - Shadow mode: if blocks=False, a BLOCK is downgraded to WARN (tool still runs).
    """
    outcome = {"hook_name": hook_cfg["name"], "phase": hook_cfg["phase"]}
    fn = hook_cfg["fn"]
    try:
        result, reason = fn(tool_name, args, tool_output)
    except Exception as e:  # noqa: BLE001 — fail closed: a crashing guard must not open the door
        return {**outcome, "result": HookResult.BLOCK.value,
                "reason": f"hook crashed: {type(e).__name__}: {e}"}

    if result == HookResult.BLOCK.value and not hook_cfg.get("blocks", True):
        return {**outcome, "result": HookResult.WARN.value, "reason": f"[shadow] {reason}"}

    return {**outcome, "result": result, "reason": reason}
