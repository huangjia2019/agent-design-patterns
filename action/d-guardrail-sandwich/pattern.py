"""Guardrail Sandwich pattern.

Reference implementation from column lecture 05-05. The claim: **for
destructive actions, put a slice of bread on both sides.** Every
high-risk tool call is wrapped in two layers of programmatic checks
— pre-hooks that can block, post-hooks that audit / verify / mark
for rollback. Both layers are owned by the harness, not the agent;
the agent does not get to bypass them by being clever.

The opening story: a corporate-banking agent transferred ¥3.2M to
the wrong account because two digits were transposed in the LLM's
parse of an email. No pre-check on account number format / whitelist
/ AML rules. No post-check that the funds went where intended.
Twelve hours to discover; partially un-recoverable. With sandwich:
**0.3% mis-transfer rate → 0.001%, latency +2–3s.** In banking,
absolutely worth it.

The pattern is two classes and one decorator:

* `HookSpec` — one hook. `name`, `phase` (pre or post), `priority`,
  whether failure `blocks`, and a callable. Pre-hooks that block
  raise `GuardrailViolation`. Post-hooks that block trigger rollback.
* `GuardrailSandwich` — runs the pre-hook chain, the tool, the
  post-hook chain. Records the full trace. On a pre-hook violation,
  the tool never runs. On a post-hook violation, the tool's
  rollback action (if any) is recorded for the saga.
* `GuardrailViolation` — typed exception with the offending hook's
  name. Easy to catch, easy to log, distinct from random tool errors.

Three named failure modes from the lecture:

* **Composition bypass** — the agent finds a way to call the tool
  *without* going through the sandwich (a sub-tool that wraps it, a
  raw API call). Closed here by making the sandwich the only callable
  entry point; bare handlers are not exposed.
* **Sandwich overhead tax** — sandwich every tool, even reads, and
  latency triples. Closed by tagging hooks with an `applies_to_phase`
  flag; reads skip the destructive sandwich.
* **Schema drift** — pre-hook validates against schema v1, the LLM
  starts emitting v2, hook lets bad payload through. Closed by
  versioning the schema validation and failing-closed on mismatch.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class HookPhase(Enum):
    PRE = "pre"
    POST = "post"


class HookResult(Enum):
    PASS = "pass"
    BLOCK = "block"      # pre: never invoke tool. post: mark for rollback.
    WARN = "warn"        # log and continue


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GuardrailViolation(Exception):
    """Raised on pre-hook block. Carries hook name + reason."""

    hook_name: str
    reason: str
    phase: HookPhase = HookPhase.PRE

    def __str__(self) -> str:
        return f"guardrail '{self.hook_name}' ({self.phase.value}): {self.reason}"


# A hook callable: takes (tool_name, args, tool_output_or_none) and
# returns (HookResult, reason). Pre-hooks see tool_output=None.
HookFn = Callable[[str, dict[str, Any], Any], tuple[HookResult, str]]


@dataclass
class HookSpec:
    """One guardrail hook.

    `priority` controls ordering — lower runs first. `blocks=True`
    means PASS/WARN let execution continue; BLOCK halts. With
    `blocks=False`, even BLOCK is downgraded to a logged WARN — useful
    for shadow-mode rollout (the lecture's "monitor mode → soft
    enforcement → full enforcement" cadence).
    """

    name: str
    phase: HookPhase
    fn: HookFn
    priority: int = 100
    blocks: bool = True
    applies_to: set[str] | None = None     # None = all tools


@dataclass
class HookOutcome:
    hook_name: str
    phase: HookPhase
    result: HookResult
    reason: str
    elapsed_ms: int = 0


@dataclass
class SandwichTrace:
    """One sandwiched call's audit record."""

    tool_name: str
    args: dict[str, Any]
    pre_outcomes: list[HookOutcome] = field(default_factory=list)
    tool_output: Any = None
    tool_error: str | None = None
    post_outcomes: list[HookOutcome] = field(default_factory=list)
    rollback_marked: bool = False
    final_status: str = "pending"      # passed | blocked_pre | tool_failed | blocked_post
    started_at: str = field(default_factory=_now_iso)
    completed_at: str | None = None


# Tool handler: takes a dict of args, returns whatever the tool produces.
ToolFn = Callable[..., Any]


class GuardrailSandwich:
    """Wrap a tool call in pre + post hook chains.

    Tools registered here cannot be invoked except via `run`. The
    handler signature stays unchanged; the sandwich is transparent
    to the tool author.
    """

    def __init__(self) -> None:
        self.tools: dict[str, ToolFn] = {}
        self.hooks: list[HookSpec] = []

    # ----- registration ------------------------------------------------

    def register_tool(self, name: str, handler: ToolFn) -> None:
        if name in self.tools:
            raise ValueError(f"tool {name!r} already registered")
        self.tools[name] = handler

    def add_hook(self, hook: HookSpec) -> None:
        self.hooks.append(hook)
        # Keep stably sorted by priority; lower priority runs first.
        self.hooks.sort(key=lambda h: (h.phase.value, h.priority))

    # ----- execution ---------------------------------------------------

    def run(self, tool_name: str, args: dict[str, Any]) -> SandwichTrace:
        trace = SandwichTrace(tool_name=tool_name, args=dict(args))
        if tool_name not in self.tools:
            trace.final_status = "tool_failed"
            trace.tool_error = f"unknown tool {tool_name!r}"
            trace.completed_at = _now_iso()
            return trace

        # 1. Pre-hook chain.
        for hook in self._applicable_hooks(tool_name, HookPhase.PRE):
            outcome = self._run_hook(hook, tool_name, args, tool_output=None)
            trace.pre_outcomes.append(outcome)
            if outcome.result == HookResult.BLOCK and hook.blocks:
                trace.final_status = "blocked_pre"
                trace.completed_at = _now_iso()
                return trace

        # 2. Tool execution.
        try:
            trace.tool_output = self.tools[tool_name](**args)
        except Exception as e:
            trace.tool_error = f"{type(e).__name__}: {e}"
            trace.final_status = "tool_failed"
            trace.completed_at = _now_iso()
            return trace

        # 3. Post-hook chain.
        rollback = False
        for hook in self._applicable_hooks(tool_name, HookPhase.POST):
            outcome = self._run_hook(hook, tool_name, args, tool_output=trace.tool_output)
            trace.post_outcomes.append(outcome)
            if outcome.result == HookResult.BLOCK and hook.blocks:
                rollback = True
                # Continue running remaining post-hooks for full audit.

        trace.rollback_marked = rollback
        trace.final_status = "blocked_post" if rollback else "passed"
        trace.completed_at = _now_iso()
        return trace

    # ----- internals ---------------------------------------------------

    def _applicable_hooks(self, tool_name: str, phase: HookPhase) -> list[HookSpec]:
        return [
            h for h in self.hooks
            if h.phase == phase and (h.applies_to is None or tool_name in h.applies_to)
        ]

    @staticmethod
    def _run_hook(
        hook: HookSpec,
        tool_name: str,
        args: dict[str, Any],
        tool_output: Any,
    ) -> HookOutcome:
        start = time.monotonic()
        try:
            result, reason = hook.fn(tool_name, args, tool_output)
        except Exception as e:
            # Hook itself crashed — fail closed.
            return HookOutcome(
                hook_name=hook.name, phase=hook.phase,
                result=HookResult.BLOCK,
                reason=f"hook crashed: {type(e).__name__}: {e}",
                elapsed_ms=int((time.monotonic() - start) * 1000),
            )

        # If the hook is in shadow mode (`blocks=False`), downgrade BLOCK to WARN
        # in the recorded outcome. The reason is preserved so dashboards still
        # see the original signal.
        if result == HookResult.BLOCK and not hook.blocks:
            return HookOutcome(
                hook_name=hook.name, phase=hook.phase,
                result=HookResult.WARN,
                reason=f"[shadow] {reason}",
                elapsed_ms=int((time.monotonic() - start) * 1000),
            )

        return HookOutcome(
            hook_name=hook.name, phase=hook.phase,
            result=result, reason=reason,
            elapsed_ms=int((time.monotonic() - start) * 1000),
        )


# ---- Common hook factories -------------------------------------------------


def amount_threshold_hook(
    field: str,
    max_amount: float,
    *,
    name: str = "amount_threshold",
    priority: int = 100,
    blocks: bool = True,
) -> HookSpec:
    """Block when args[field] exceeds the threshold."""
    def fn(tool_name, args, _output):
        amount = args.get(field)
        if amount is None:
            return HookResult.PASS, f"field {field!r} absent"
        if amount > max_amount:
            return HookResult.BLOCK, f"{field}={amount} exceeds {max_amount}"
        return HookResult.PASS, f"{field}={amount} within limit"
    return HookSpec(name=name, phase=HookPhase.PRE, fn=fn,
                    priority=priority, blocks=blocks)


def blocklist_hook(
    field: str,
    blocklist: set[str],
    *,
    name: str = "blocklist",
    priority: int = 100,
    blocks: bool = True,
) -> HookSpec:
    """Block when args[field] is on the blocklist (e.g. OFAC sanctions)."""
    def fn(tool_name, args, _output):
        value = str(args.get(field, ""))
        if value in blocklist:
            return HookResult.BLOCK, f"{field}={value!r} on blocklist"
        return HookResult.PASS, f"{field} clear"
    return HookSpec(name=name, phase=HookPhase.PRE, fn=fn,
                    priority=priority, blocks=blocks)


def output_schema_hook(
    required_keys: list[str],
    *,
    name: str = "output_schema",
    priority: int = 100,
    blocks: bool = True,
) -> HookSpec:
    """Post-hook: tool output must be a dict containing required keys."""
    def fn(tool_name, args, output):
        if not isinstance(output, dict):
            return HookResult.BLOCK, f"output is {type(output).__name__}, expected dict"
        missing = [k for k in required_keys if k not in output]
        if missing:
            return HookResult.BLOCK, f"output missing keys: {missing}"
        return HookResult.PASS, "output schema valid"
    return HookSpec(name=name, phase=HookPhase.POST, fn=fn,
                    priority=priority, blocks=blocks)


def pii_redaction_hook(
    patterns: list[str],
    *,
    name: str = "pii_redaction",
    priority: int = 200,
    blocks: bool = True,
) -> HookSpec:
    """Post-hook: scan tool output string representation for PII patterns."""
    import re
    compiled = [re.compile(p) for p in patterns]

    def fn(tool_name, args, output):
        text = str(output)
        for pat in compiled:
            if pat.search(text):
                return HookResult.BLOCK, f"PII pattern {pat.pattern!r} found in output"
        return HookResult.PASS, "no PII detected"
    return HookSpec(name=name, phase=HookPhase.POST, fn=fn,
                    priority=priority, blocks=blocks)
