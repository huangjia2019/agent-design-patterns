"""Tool Dispatch pattern.

Reference implementation from column lecture 05-02. The claim:
**LLMs are good at using tools, bad at picking tools.** Parameter
filling and result interpretation play to the model's strengths.
Selecting which tool to invoke out of seventeen candidates does not.
Production agents that hand the model a bare tool list and hope for
the best end up with the dispatcher's worst case: every order routed
to the same driver because the agent doesn't refresh state between
calls.

The pattern lifts selection into a typed contract — `ToolMetadata`
— and routes every call through a `ToolDispatcher` that enforces
the contract. Five non-negotiable enforcement points, lifted from
Claude Code's `Tool.ts`:

* `is_read_only` and `is_concurrency_safe` default to **False**.
  Forget to declare a tool safe and the dispatcher treats it as
  destructive. The iron rule: silence means unsafe.
* `quota_per_session` caps how many times the same tool can run
  with the same primary arg in one session — the "80 orders to one
  driver" guard.
* `requires_fresh_state` forces a read-tool refresh before any
  write that touches state older than `STATE_FRESHNESS_SECONDS`.
* `requires_approval` short-circuits execution and returns an
  awaiting-approval trace — wires into the Approval Gate (Ch9).
* `rollback_action` records the inverse for the Saga log. Destructive
  tools without rollback simply cannot be registered.

The shape is intentionally synchronous. Production deployments wrap
each call in async and add the policy engine as an out-of-process
binary (Codex CLI's `execpolicy` crate), but the contract is the
same. Async is plumbing; the contract is the pattern.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ToolMetadata:
    """Typed contract for one tool.

    The Claude Code 14-field schema in trimmed-for-clarity form. Every
    field matters: omit `quota_per_session` and the dispatcher will
    happily route 80 orders to one driver; omit `rollback_action` and
    a failed bulk operation leaves orphaned state.
    """

    name: str
    description: str
    when_to_use: str
    when_not_to_use: str = ""
    exclusive_with: list[str] = field(default_factory=list)
    # Five enforcement flags — defaults all assume "unsafe".
    is_read_only: bool = False
    is_concurrency_safe: bool = False
    is_destructive: bool = False
    requires_fresh_state: bool = False
    requires_approval: bool = False
    # Quotas and inverses.
    quota_per_session: int = -1     # -1 = unlimited
    rollback_action: str | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    is_mcp: bool = False            # external MCP source → extra audit


@dataclass
class DispatchTrace:
    """One dispatch attempt's audit record.

    Status is `success` / `failed` / `rejected`. `rejected` is the
    interesting category — it captures *why the dispatcher refused*,
    distinct from why the tool itself errored.
    """

    tool: str
    args: dict[str, Any]
    session_id: str
    triggered_by: str = "llm"           # "llm" | "programmatic"
    status: str = "pending"
    rejected_reason: str | None = None
    output: Any = None
    elapsed_ms: int = 0
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Tool handler signature: takes the args dict, returns whatever the
# tool produces. Sync; production wraps async.
Handler = Callable[..., Any]


class ToolDispatchError(Exception):
    """Raised on bad registration only — runtime rejections come back
    on the `DispatchTrace`, not as exceptions."""


class ToolDispatcher:
    """Quota + state-refresh + saga dispatcher.

    Stores everything in memory. Production swaps the dicts for
    sqlite / Redis / DynamoDB without touching the dispatch loop;
    the audit trace shape is identical.
    """

    STATE_FRESHNESS_SECONDS = 60

    def __init__(self) -> None:
        self.tools: dict[str, ToolMetadata] = {}
        self.handlers: dict[str, Handler] = {}
        # Quota counted per (session, tool, primary-arg) triple so
        # "assign_driver to driver_007" counts separately from
        # "assign_driver to driver_012".
        self.quota: dict[str, int] = {}
        self.last_state_refresh: dict[str, float] = {}    # by session_id
        self.saga_log: list[dict[str, Any]] = []
        self.traces: list[DispatchTrace] = []

    # ----- registration ------------------------------------------------

    def register(self, meta: ToolMetadata, handler: Handler) -> None:
        if meta.is_destructive and meta.rollback_action is None:
            raise ToolDispatchError(
                f"destructive tool {meta.name!r} must declare rollback_action"
            )
        if meta.is_destructive and meta.is_read_only:
            raise ToolDispatchError(
                f"tool {meta.name!r} cannot be both read_only and destructive"
            )
        self.tools[meta.name] = meta
        self.handlers[meta.name] = handler

    # ----- dispatch ----------------------------------------------------

    def dispatch(
        self,
        tool_name: str,
        args: dict[str, Any],
        session_id: str,
        triggered_by: str = "llm",
    ) -> DispatchTrace:
        trace = DispatchTrace(
            tool=tool_name, args=dict(args),
            session_id=session_id, triggered_by=triggered_by,
        )
        start = time.monotonic()

        meta = self.tools.get(tool_name)
        if meta is None:
            trace.status = "rejected"
            trace.rejected_reason = "tool_hallucination"
            return self._finalize(trace, start)

        # Quota check (per session × tool × primary arg).
        key = self._quota_key(session_id, tool_name, args)
        used = self.quota.get(key, 0)
        if meta.quota_per_session != -1 and used >= meta.quota_per_session:
            trace.status = "rejected"
            trace.rejected_reason = f"quota_exceeded:{used}/{meta.quota_per_session}"
            return self._finalize(trace, start)

        # State freshness — only matters for tools that mutate state.
        if meta.requires_fresh_state:
            last = self.last_state_refresh.get(session_id, 0.0)
            if time.time() - last > self.STATE_FRESHNESS_SECONDS:
                trace.status = "rejected"
                trace.rejected_reason = "stale_state_must_refresh"
                return self._finalize(trace, start)

        # Approval gate — handed off to the human-in-loop pattern.
        if meta.requires_approval:
            trace.status = "rejected"
            trace.rejected_reason = "awaiting_approval"
            return self._finalize(trace, start)

        # Execute.
        try:
            trace.output = self.handlers[tool_name](**args)
            trace.status = "success"
        except Exception as e:
            trace.status = "failed"
            trace.rejected_reason = f"{type(e).__name__}: {e}"
            return self._finalize(trace, start)

        # Post-success bookkeeping: quota, saga, freshness stamp.
        self.quota[key] = used + 1
        if meta.is_destructive and meta.rollback_action:
            self.saga_log.append({
                "tool": tool_name,
                "args": dict(args),
                "rollback": meta.rollback_action,
                "session_id": session_id,
            })
        if meta.is_read_only:
            # A successful read counts as a state refresh for this session.
            self.last_state_refresh[session_id] = time.time()

        return self._finalize(trace, start)

    def rollback_session(self, session_id: str) -> list[dict[str, Any]]:
        """Run the saga inverses in reverse order. Returns the rollback log."""
        results: list[dict[str, Any]] = []
        keep: list[dict[str, Any]] = []
        for entry in reversed(self.saga_log):
            if entry["session_id"] != session_id:
                keep.append(entry)
                continue
            inverse = self.handlers.get(entry["rollback"])
            if inverse is None:
                results.append({
                    "tool": entry["tool"],
                    "status": "rollback_unavailable",
                })
                continue
            try:
                output = inverse(**entry["args"])
                results.append({"tool": entry["tool"], "status": "rolled_back", "output": output})
            except Exception as e:
                results.append({"tool": entry["tool"], "status": "rollback_failed", "error": str(e)})
        # Saga log keeps non-target sessions intact.
        self.saga_log = list(reversed(keep))
        return results

    # ----- helpers -----------------------------------------------------

    def _finalize(self, trace: DispatchTrace, start: float) -> DispatchTrace:
        trace.elapsed_ms = int((time.monotonic() - start) * 1000)
        self.traces.append(trace)
        return trace

    @staticmethod
    def _quota_key(session_id: str, tool: str, args: dict[str, Any]) -> str:
        # Primary arg = first value; lets quota be scoped per-resource.
        primary = next(iter(args.values()), "")
        return f"{session_id}|{tool}|{primary}"
