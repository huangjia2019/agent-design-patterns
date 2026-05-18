"""Invariants for the Complexity-Based Routing pattern."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    ComplexityRouter,
    ComplexityTier,
    FallbackChain,
    FallbackStep,
    FallbackTriggeredError,
    causal_keyword_signal,
    length_signal,
    template_query_signal,
)


# ---- Signal functions ------------------------------------------------------


def test_length_signal_capped_at_one() -> None:
    assert length_signal("a") < 0.01
    assert length_signal("x" * 5000) == 1.0


def test_causal_keyword_signal_detects_why() -> None:
    assert causal_keyword_signal("Why did revenue drop") > 0
    assert causal_keyword_signal("count users") == 0.0


def test_template_query_signal_detects_template() -> None:
    assert template_query_signal("Show me the top 10 products") == 1.0
    assert template_query_signal("本周注册用户数") == 1.0
    assert template_query_signal("Explain why retention dropped") == 0.0


# ---- ComplexityRouter ------------------------------------------------------


def test_router_picks_simple_for_template_query() -> None:
    router = ComplexityRouter()
    decision = router.route("本周注册用户数")
    assert decision.tier == ComplexityTier.SIMPLE


def test_router_picks_complex_for_causal_question() -> None:
    router = ComplexityRouter()
    decision = router.route(
        "Why did GMV drop 8% week-over-week and what if we had price elasticity of -1.2"
    )
    assert decision.tier == ComplexityTier.COMPLEX


def test_router_returns_reason_string() -> None:
    router = ComplexityRouter()
    decision = router.route("Why did churn rise")
    assert isinstance(decision.reason, str) and decision.reason


def test_router_supports_custom_tier_models() -> None:
    custom = {
        ComplexityTier.SIMPLE: "gpt-4o-mini",
        ComplexityTier.MEDIUM: "gpt-4o",
        ComplexityTier.COMPLEX: "o1",
    }
    router = ComplexityRouter(tier_models=custom)
    decision = router.route("Why did sales fall counterfactual analysis")
    assert decision.model == "o1"


def test_router_score_is_bounded() -> None:
    router = ComplexityRouter()
    for q in ["Why?", "x" * 2000 + " prove that", "Show me users", ""]:
        decision = router.route(q)
        assert 0.0 <= decision.score <= 1.0


# ---- FallbackChain ---------------------------------------------------------


def _always_valid(_output: str) -> None:
    return None


def _reject_haiku(output: str) -> None:
    if "haiku" in output.lower():
        raise FallbackTriggeredError("haiku output not trustworthy")


def test_chain_returns_first_tier_when_validator_passes() -> None:
    chain = FallbackChain(
        llm_call=lambda task, model: f"answer from {model}",
        validator=_always_valid,
    )
    output, steps = chain.run("show me weekly signups")  # routes SIMPLE
    assert len(steps) == 1
    assert steps[0].validated is True
    assert "haiku" in output


def test_chain_escalates_when_validator_rejects() -> None:
    chain = FallbackChain(
        llm_call=lambda task, model: f"answer from {model}",
        validator=_reject_haiku,
    )
    output, steps = chain.run("show me weekly signups")
    assert len(steps) == 2, "first tier should be rejected then succeed at next tier"
    assert steps[0].validated is False
    assert steps[1].validated is True
    assert "haiku" not in output


def test_chain_records_fail_reason_on_escalation() -> None:
    chain = FallbackChain(
        llm_call=lambda task, model: f"answer from {model}",
        validator=_reject_haiku,
    )
    _, steps = chain.run("show me weekly signups")
    assert steps[0].fail_reason == "haiku output not trustworthy"


def test_chain_starts_at_complex_skips_lower_tiers() -> None:
    chain = FallbackChain(
        llm_call=lambda task, model: f"answer from {model}",
        validator=_always_valid,
    )
    _, steps = chain.run(
        "prove that the system converges under counterfactual price shock why explain"
    )
    assert steps[0].tier == ComplexityTier.COMPLEX
    assert len(steps) == 1


def test_chain_raises_when_cascade_exhausted() -> None:
    def reject_all(_output: str) -> None:
        raise FallbackTriggeredError("nothing is good enough")

    chain = FallbackChain(
        llm_call=lambda task, model: "anything",
        validator=reject_all,
    )
    with pytest.raises(FallbackTriggeredError) as exc:
        chain.run("show me weekly signups")
    assert "exhausted" in str(exc.value)


def test_chain_step_order_is_cheapest_first() -> None:
    chain = FallbackChain(
        llm_call=lambda task, model: f"answer from {model}",
        validator=_reject_haiku,
    )
    _, steps = chain.run("show me weekly signups")
    assert steps[0].tier.value < steps[1].tier.value


def test_fallback_step_records_timestamp() -> None:
    step = FallbackStep(
        tier=ComplexityTier.SIMPLE,
        model="haiku",
        output="x",
        validated=True,
    )
    assert step.timestamp  # ISO string present
