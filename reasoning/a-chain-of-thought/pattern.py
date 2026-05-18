"""Chain-of-Thought pattern.

Reference implementation of the *new* Chain-of-Thought from column
lecture 04-02. The 2022 prompt trick ("Let's think step by step") is
not what this pattern is anymore. In 2026 every frontier model emits
reasoning on its own — including hidden reasoning tokens you pay for
without seeing. The job moved from the model layer to the harness:

    emit  →  store  →  audit  →  migrate  →  control

This file ships the bones of the harness side. `CoTManager` keeps
trace records as first-class structured data, can `strip_for_fallback`
when the chain has to cross a model boundary (Claude Code's "thinking
signatures are model-bound" rule), supports four effort tiers
(low / medium / high / max — Anthropic's standard), and offers two
audit views (regulator sees everything, customer sees the redacted
decision summary).

The pattern is one of two things in the same file:

* `CoTTrace` — the durable trace object with a list of `ThinkingBlock`s,
  fallback chain, final output, token totals, and a serialization
  contract that survives crossing process boundaries.
* `CoTManager` — the runtime entry point. Hands out traces, picks an
  effort tier from task shape, normalizes reasoning tags coming back
  from heterogeneous model families (OpenAI `<reasoning>`, DeepSeek
  `<think>`, Google `<thought>`, Anthropic structured blocks), and
  produces the two audit views.

The pattern's claim, stated as one sentence: **CoT in 2026 is not a
prompt trick; it's the audit log of the agent's reasoning trajectory,
treated as first-class structured data with lifecycle invariants you
enforce in the harness, not in the prompt.**
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ThinkingEffort(Enum):
    """Anthropic-standard 4 effort tiers + OFF.

    OFF / LOW / MEDIUM / HIGH / MAX. The values are ordered, so you can
    compare with `<` and `>`. Hermes uses 6 tiers (adds MINIMAL); 4 is
    the more common production choice.
    """

    OFF = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    MAX = 4


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ThinkingBlock:
    """One contiguous block of reasoning emitted by a model.

    `signature` and `model` together carry the cross-model compatibility
    contract: an Anthropic-signed block cannot be replayed against
    DeepSeek and vice versa. `is_compatible_with` is the predicate the
    fallback path calls before forwarding the block.
    """

    block_id: str
    content: str
    signature: str | None = None     # provider-issued binding to the producing model
    model: str = ""                  # the model id that emitted this block
    tokens: int = 0
    timestamp: str = field(default_factory=_now_iso)

    def is_compatible_with(self, target_model: str) -> bool:
        """Whether this block survives a fallback to `target_model`.

        The rule: an unsigned block is always portable. A signed block
        binds to its origin model; sending it on to a different model
        will get the request rejected at the provider edge, which is
        the lecture-opening incident.
        """
        if self.signature is None:
            return True
        return self.model == target_model


@dataclass
class CoTTrace:
    """One task's complete reasoning trajectory.

    Persistent. Serializable. Survives crashes, fallbacks, and replays.
    The body of this object is the audit answer to "why did the agent
    do that?"
    """

    trace_id: str
    task: str
    effort: ThinkingEffort
    thinking_blocks: list[ThinkingBlock] = field(default_factory=list)
    final_output: str = ""
    model_used: str = ""
    fallback_chain: list[str] = field(default_factory=list)
    started_at: str = field(default_factory=_now_iso)
    completed_at: str | None = None

    @property
    def total_thinking_tokens(self) -> int:
        return sum(b.tokens for b in self.thinking_blocks)

    @property
    def reasoning_token_ratio(self) -> float:
        """thinking_tokens / (thinking_tokens + output_tokens).

        Production deployments alert when the p99 of this metric drifts
        outside 0.30 – 0.60: too low and the agent is under-thinking,
        too high and it's burning tokens to think about simple things.
        """
        # ~4 chars per token as a coarse output estimate; production
        # uses the provider's tokenizer.
        output_tokens = max(len(self.final_output) // 4, 1)
        total = self.total_thinking_tokens + output_tokens
        return self.total_thinking_tokens / total if total else 0.0

    def strip_for_fallback(self, target_model: str) -> "CoTTrace":
        """Return a sibling trace with model-incompatible blocks removed.

        This is Claude Code's first iron rule. The original trace stays
        intact for audit; the stripped sibling is what gets forwarded
        to the fallback provider. The fallback model id is appended to
        `fallback_chain` so the audit view can show the trail.
        """
        compatible = [
            b for b in self.thinking_blocks if b.is_compatible_with(target_model)
        ]
        return CoTTrace(
            trace_id=self.trace_id,
            task=self.task,
            effort=self.effort,
            thinking_blocks=compatible,
            final_output=self.final_output,
            model_used=target_model,
            fallback_chain=self.fallback_chain + [target_model],
            started_at=self.started_at,
        )


_TAG_PATTERNS_BY_FAMILY = {
    "openai": [r"<reasoning>(.*?)</reasoning>"],
    "deepseek": [r"<think>(.*?)</think>"],
    "google": [r"<thought>(.*?)</thought>"],
    # anthropic emits structured blocks via the SDK, not embedded tags
}


class CoTManager:
    """Runtime entry point for CoT-as-infrastructure.

    Holds traces in memory by default. Production deployments swap the
    `traces` dict for sqlite / postgres / Kafka with the same interface;
    the audit view + token ratio metric stay identical.
    """

    def __init__(self, default_effort: ThinkingEffort = ThinkingEffort.MEDIUM) -> None:
        self.default_effort = default_effort
        self.traces: dict[str, CoTTrace] = {}

    def create_trace(
        self,
        task: str,
        effort: ThinkingEffort | None = None,
        model: str = "",
    ) -> CoTTrace:
        digest_source = f"{task}|{_now_iso()}"
        trace = CoTTrace(
            trace_id=hashlib.sha256(digest_source.encode()).hexdigest()[:12],
            task=task,
            effort=effort or self.default_effort,
            model_used=model,
        )
        self.traces[trace.trace_id] = trace
        return trace

    def normalize_tags(self, raw_text: str, source_family: str) -> list[ThinkingBlock]:
        """Hermes-style cross-provider tag normalization.

        OpenAI emits `<reasoning>`, DeepSeek `<think>`, Google
        `<thought>`. The harness sees them all as `ThinkingBlock`s with
        the family recorded, so downstream code never branches on the
        provider identity again.
        """
        patterns = _TAG_PATTERNS_BY_FAMILY.get(source_family, [])
        blocks: list[ThinkingBlock] = []
        for pattern in patterns:
            for content in re.findall(pattern, raw_text, flags=re.DOTALL):
                stripped = content.strip()
                if not stripped:
                    continue
                blocks.append(
                    ThinkingBlock(
                        block_id=hashlib.sha256(stripped.encode()).hexdigest()[:12],
                        content=stripped,
                        model=source_family,
                        tokens=max(len(stripped) // 4, 1),
                    )
                )
        return blocks

    def estimate_effort(self, task: str) -> ThinkingEffort:
        """A small heuristic so callers don't have to pick a tier by hand.

        Production deployments replace this with a learned classifier
        or a cheap pre-LLM call. The contract is the same.
        """
        if any(kw in task.lower() for kw in ("prove", "derive", "证明", "推导", "因果")):
            return ThinkingEffort.HIGH
        words = len(task.split())
        if words < 8:
            return ThinkingEffort.OFF
        if words < 25:
            return ThinkingEffort.LOW
        if words < 100:
            return ThinkingEffort.MEDIUM
        return ThinkingEffort.HIGH

    def audit_view(self, trace_id: str, view: str = "regulator") -> dict:
        """Two-view audit. Regulators see the full trail; customers see
        the redacted decision summary."""
        trace = self.traces.get(trace_id)
        if trace is None:
            return {}
        if view == "regulator":
            return {
                "trace_id": trace.trace_id,
                "task": trace.task,
                "effort": trace.effort.name,
                "model_used": trace.model_used,
                "fallback_chain": trace.fallback_chain,
                "thinking_blocks": [
                    {
                        "id": b.block_id,
                        "content": b.content,
                        "model": b.model,
                        "tokens": b.tokens,
                    }
                    for b in trace.thinking_blocks
                ],
                "final_output": trace.final_output,
                "total_thinking_tokens": trace.total_thinking_tokens,
                "reasoning_token_ratio": round(trace.reasoning_token_ratio, 3),
            }
        # customer view: decision summary only, no reasoning content
        return {
            "trace_id": trace.trace_id,
            "decision_summary": trace.final_output[:500],
            "had_fallback": len(trace.fallback_chain) > 0,
            "model_used": trace.model_used,
        }
