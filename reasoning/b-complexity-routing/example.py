"""Runnable demo for the Complexity-Based Routing pattern.

Replays the data-analysis Agent scenario from the lecture opening:
the team defaulted everything to Opus and got a ¥480k month-one
bill. Tracing the traffic revealed 41% of queries were SQL template
fills ("last week's signups"), 22% were GROUP-BYs, only 23% needed
real reasoning. Three-tier routing pushed the bill to ~¥120k.

This example shows the routing logic in isolation. The `_fake_llm`
function stands in for the provider: it returns short canned
answers for cheap models and longer reasoned answers for the
expensive tier. A toy validator rejects suspiciously short answers
from cheap tiers — that's where the FallbackTriggeredError lives.

Run:
    python reasoning/b-complexity-routing/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    ComplexityRouter,
    ComplexityTier,
    FallbackChain,
    FallbackTriggeredError,
)


# ----------------------------------------------------------------------------
# Fake LLM and validator — stand-ins so the demo runs without API keys.
# ----------------------------------------------------------------------------

def _fake_llm(task: str, model: str) -> str:
    """Pretends to call a model. Quality scales with model tier."""
    if "haiku" in model:
        # The cheap tier nails simple queries but produces shallow
        # output for the harder ones.
        if "show me" in task.lower() or "本周" in task:
            return f"SELECT count(*) FROM users WHERE signup_at > now() - interval '7 days';  -- via {model}"
        return f"[short answer from {model}]"
    if "sonnet" in model:
        return f"[mid-tier reasoning from {model}: groups by region, joins users on cohorts]"
    # opus
    return (
        f"[deep reasoning from {model}: decomposes the question into "
        "drivers, runs counterfactual on price elasticity, joins with "
        "retention curve, returns final attribution]"
    )


def _validate_or_escalate(output: str) -> None:
    """Toy validator: cheap-tier outputs that are too short escalate.

    Production validators check schema, confidence, refusal patterns,
    or run a cheap correctness check (e.g. dry-run a SQL plan)."""
    if output.startswith("[short answer"):
        raise FallbackTriggeredError("cheap-tier output too shallow to trust")


def _print_section(title: str) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    router = ComplexityRouter()
    chain = FallbackChain(llm_call=_fake_llm, router=router, validator=_validate_or_escalate)

    queries = [
        "本周注册用户数",
        "Show me the top 10 products by revenue last week",
        "Group churn rate by region and cohort for Q3",
        "Why did GMV drop 8% week-over-week",
        "If we raise price by 10%, what will the churn elasticity be?",
        "Tell me a joke",   # off-track; will route SIMPLE
    ]

    # ------------------------------------------------------------------
    # Section 1: routing alone (no escalation)
    # ------------------------------------------------------------------
    _print_section("Routing-only view (no escalation)")
    for q in queries:
        decision = router.route(q)
        print(f"  {decision.tier.name:8s} ({decision.score:.2f})  {decision.reason}")
        print(f"            → {decision.model}   '{q[:60]}'")

    # ------------------------------------------------------------------
    # Section 2: full cascade with validation
    # ------------------------------------------------------------------
    _print_section("Full cascade (validate → escalate on shallow output)")
    total_steps = 0
    total_escalations = 0
    for q in queries:
        try:
            output, steps = chain.run(q)
            total_steps += len(steps)
            total_escalations += sum(1 for s in steps if not s.validated)
            print(f"  query: {q[:60]}")
            print(f"    final tier: {steps[-1].tier.name} ({steps[-1].model})")
            if len(steps) > 1:
                fail_reasons = " → ".join(s.fail_reason or "ok" for s in steps[:-1])
                print(f"    escalation trail: {fail_reasons}")
            print(f"    output: {output[:80]}")
        except FallbackTriggeredError as e:
            print(f"  query: {q[:60]}\n    GIVE UP: {e.reason}")

    _print_section("Aggregate routing health")
    print(f"total queries        : {len(queries)}")
    print(f"total cascade steps  : {total_steps}")
    print(f"escalations          : {total_escalations}")
    print(f"escalation rate      : {total_escalations / max(total_steps, 1):.2f}")

    # ------------------------------------------------------------------
    # Section 3: showing the audit shape on a single escalating case
    # ------------------------------------------------------------------
    _print_section("Audit shape for one escalating case")
    output, steps = chain.run("Cluster these support tickets by intent")
    for i, step in enumerate(steps, start=1):
        status = "✓" if step.validated else "✗"
        print(f"  step {i} {status}  tier={step.tier.name:8s} model={step.model}")
        if step.fail_reason:
            print(f"            reason: {step.fail_reason}")


if __name__ == "__main__":
    main()
