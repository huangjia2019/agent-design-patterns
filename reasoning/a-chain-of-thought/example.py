"""Runnable demo for the Chain-of-Thought pattern.

Replays the lecture-opening incident. A small-claim auto-insurance
agent upgrades from a non-reasoning model to a reasoning model. The
team adds the well-meaning prompt:

    Please analyze this claim step by step:
    1. Check policy applicability
    2. Check amount against the limit
    ...

Two weeks later the regulator pulls a denial letter from May 3rd and
asks for the agent's reasoning. The thinking field is empty. Root
cause: that request was rate-limited by Opus and silently failed over
to Sonnet, and the Opus-signed thinking blocks were stripped because
Sonnet rejects another model's signatures. The lesson record is
absent because the harness never wrote one.

This example shows the lesson written. With `CoTManager` the harness
records the trace, classifies the effort tier, normalizes tags across
providers, and produces both regulator and customer audit views — so
the next pulled denial letter has a trail.

Run:
    python reasoning/a-chain-of-thought/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    CoTManager,
    ThinkingBlock,
    ThinkingEffort,
)


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    manager = CoTManager(default_effort=ThinkingEffort.MEDIUM)

    # ------------------------------------------------------------------
    # Claim 1: routine — small fender bender, photos clean, amount low.
    # ------------------------------------------------------------------
    _print_section("Claim 1 — routine fender bender")
    task1 = "Approve or deny claim #2603-44781: rear-bumper damage, ¥4,200, clean record"
    auto_effort = manager.estimate_effort(task1)
    print(f"auto-picked effort tier: {auto_effort.name}")

    trace1 = manager.create_trace(task1, effort=auto_effort, model="claude-opus-4-6")
    # Simulate a single Opus thinking block emitted by the reasoning model.
    trace1.thinking_blocks.append(
        ThinkingBlock(
            block_id="opus-001",
            content=(
                "Policy clause 2.1.a covers rear-bumper damage. Amount "
                "¥4,200 is below the auto-approve ceiling of ¥10,000. "
                "Claimant has zero prior claims in the last 24 months. "
                "Approve."
            ),
            signature="sig:opus-4-6-abc123",
            model="claude-opus-4-6",
            tokens=42,
        )
    )
    trace1.final_output = "APPROVED: ¥4,200 to be paid via direct deposit within 3 business days."

    print(f"trace_id        : {trace1.trace_id}")
    print(f"thinking tokens : {trace1.total_thinking_tokens}")
    print(f"reasoning ratio : {trace1.reasoning_token_ratio:.3f}")

    # ------------------------------------------------------------------
    # Claim 2: ambiguous — high-amount, blurred photos, multiple prior
    # claims. The reasoning model emits two blocks. Mid-stream, Opus
    # rate-limits and the harness fails over to Sonnet. Without
    # `strip_for_fallback` the request would fail at the provider edge.
    # ------------------------------------------------------------------
    _print_section("Claim 2 — ambiguous; fallback mid-stream")
    task2 = (
        "Investigate claim #2603-44912: ¥18,900 hood damage, blurry photo, "
        "claimant has 3 prior claims in 18 months. Decide approve / deny / "
        "escalate to human review."
    )
    trace2 = manager.create_trace(task2, effort=ThinkingEffort.HIGH, model="claude-opus-4-6")
    trace2.thinking_blocks.extend([
        ThinkingBlock(
            block_id="opus-002",
            content=(
                "Three prior claims in 18 months is above the policy "
                "threshold for automatic approval. Need to look at the "
                "current incident more carefully — photo is too blurry "
                "to confirm hood damage matches the reported cause."
            ),
            signature="sig:opus-4-6-def456",
            model="claude-opus-4-6",
            tokens=58,
        ),
        ThinkingBlock(
            block_id="opus-003",
            content=(
                "Recommend escalation to human adjuster. Photo evidence "
                "insufficient, prior claim pattern warrants verification."
            ),
            signature="sig:opus-4-6-ghi789",
            model="claude-opus-4-6",
            tokens=28,
        ),
    ])

    print(f"pre-fallback blocks  : {len(trace2.thinking_blocks)}")
    print(f"pre-fallback ratio   : {trace2.reasoning_token_ratio:.3f}")

    # Now Opus rate-limits. Strip incompatible blocks before forwarding
    # to Sonnet, the way Claude Code does.
    fallback_trace = trace2.strip_for_fallback("claude-sonnet-4-6")
    fallback_trace.thinking_blocks.append(
        ThinkingBlock(
            block_id="sonnet-001",
            content=(
                "Photo blurry, claim count pattern unusual. Escalating "
                "to human adjuster."
            ),
            # No signature: this block is portable.
            model="claude-sonnet-4-6",
            tokens=21,
        )
    )
    fallback_trace.final_output = (
        "ESCALATED to human adjuster: photo evidence insufficient and "
        "claimant has 3 prior claims in 18 months."
    )
    manager.traces[fallback_trace.trace_id] = fallback_trace

    print(f"post-fallback blocks : {len(fallback_trace.thinking_blocks)}")
    print(f"fallback chain       : {fallback_trace.fallback_chain}")
    print(f"final decision       : {fallback_trace.final_output}")

    # ------------------------------------------------------------------
    # Tag normalization across providers
    # ------------------------------------------------------------------
    _print_section("Cross-provider tag normalization (Hermes-style)")
    deepseek_raw = (
        "<think>The damage location matches the police-report description. "
        "Amount is within the auto-approve range.</think>\n"
        "Final answer: approve."
    )
    blocks = manager.normalize_tags(deepseek_raw, source_family="deepseek")
    print(f"normalized {len(blocks)} block(s) from DeepSeek output:")
    for b in blocks:
        print(f"  - {b.block_id}: {b.content[:60]}... ({b.tokens} tokens)")

    # ------------------------------------------------------------------
    # Audit views — the two angles the regulator pulled in the lecture story.
    # ------------------------------------------------------------------
    _print_section("Regulator audit view (full trail)")
    reg_view = manager.audit_view(fallback_trace.trace_id, view="regulator")
    print(f"thinking blocks   : {len(reg_view['thinking_blocks'])}")
    print(f"fallback_chain    : {reg_view['fallback_chain']}")
    print(f"reasoning_ratio   : {reg_view['reasoning_token_ratio']}")
    print(f"final_output      : {reg_view['final_output'][:80]}")

    _print_section("Customer audit view (redacted summary)")
    cust_view = manager.audit_view(fallback_trace.trace_id, view="customer")
    print(f"decision_summary : {cust_view['decision_summary'][:120]}")
    print(f"had_fallback     : {cust_view['had_fallback']}")
    # Reasoning content is intentionally absent from the customer view.


if __name__ == "__main__":
    main()
