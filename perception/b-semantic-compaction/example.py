"""Runnable demo for the Semantic Compaction pattern.

Simulates a 30-turn debugging session where the agent eventually rules out
three approaches (cache warming, retry-with-backoff, query rewriting). With
no anchor, the compactor would silently drop those exclusions and the agent
would retry them. With the anchor, exclusions persist across compaction.

Uses a fake LLM so the demo runs without API keys. To wire to a real LLM,
replace ``fake_llm`` with a function that calls Anthropic / OpenAI / etc.

Run:
    python perception/b-semantic-compaction/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import CompactionAnchor, SemanticCompactor, Turn   # noqa: E402


def fake_llm(prompt: str) -> str:
    """Deterministic stub. Returns a well-formed anchor based on the prompt."""
    return (
        "INTENT: diagnose intermittent 503s on /api/checkout\n"
        "CHANGES: added connection-pool metrics | enabled slow-query logging | "
        "rolled back hotfix-2026-05-12\n"
        "DECIDED: focus on database connection pool, not Redis cache\n"
        "EXCLUDED: cache warming | retry-with-backoff | query rewriting\n"
        "NEXT: instrument pool.acquire timing | check max_connections setting"
    )


def build_session() -> list[Turn]:
    """A long-ish debugging session with three error traces and 27 normal turns."""
    turns: list[Turn] = [
        Turn(role="user", content="Our checkout endpoint returns 503 ~5% of the time.", tokens=20),
        Turn(role="assistant", content="Let me check recent deployments and pool metrics.", tokens=15),
    ]
    for i in range(12):
        turns.append(Turn(
            role="tool_result",
            content="x" * 4000,    # long tool output, ~1000 tokens
            tokens=1000,
        ))
        turns.append(Turn(
            role="assistant",
            content=f"Hypothesis {i}: explored.",
            tokens=20,
        ))
    turns.append(Turn(
        role="tool_result",
        content="Traceback: TimeoutError: pool exhausted after 30 retries (max=10)",
        tokens=60,
        is_error=True,
    ))
    turns.append(Turn(
        role="assistant",
        content="Confirmed pool exhaustion. Excluding cache-warming and retry-backoff hypotheses.",
        tokens=30,
    ))
    turns.append(Turn(
        role="tool_result",
        content="Traceback: ConnectionError: too many open file descriptors",
        tokens=50,
        is_error=True,
    ))
    turns.append(Turn(
        role="user",
        content="What have we ruled out so far?",
        tokens=10,
    ))
    return turns


def main() -> None:
    compactor = SemanticCompactor(
        llm=fake_llm,
        anchor=CompactionAnchor(intent="diagnose intermittent 503s"),
        preserve_recent=4,
        trigger_at_ratio=0.55,
    )

    turns = build_session()
    before_tokens = sum(t.tokens for t in turns)
    before_errors = sum(1 for t in turns if t.is_error)

    budget = 16_000
    target = 400          # tight enough to force L2 (fold to anchor)
    print(f"Budget: {budget:,}    Total before: {before_tokens:,} ({len(turns)} turns)")
    print(f"Compaction target: {target:,} tokens")
    print(f"Triggers compaction? {compactor.should_compact(before_tokens, budget)}")
    print()

    compacted = compactor.compact(turns, target_tokens=target)

    after_tokens = sum(t.tokens for t in compacted)
    after_errors = sum(1 for t in compacted if t.is_error)

    print(f"After: {after_tokens:,} tokens ({len(compacted)} turns)")
    print(f"Events: {[(e.level, e.turns_before, '->',  e.turns_after) for e in compactor.events]}")
    print()
    print("Anchor state after compaction:")
    print(compactor.anchor.to_summary())
    print()
    print("Invariants:")
    print(f"  Error traces in input  : {before_errors}")
    print(f"  Error traces preserved : {after_errors}")
    print(f"  All errors kept?       : {after_errors >= before_errors}")
    print(f"  Excluded approaches recovered? : "
          f"{len(compactor.anchor.excluded_approaches) >= 3}")
    print()
    print("Health check:")
    print(f"  {compactor.health_check()}")


if __name__ == "__main__":
    main()
