"""Complexity-Based Routing pattern.

Reference implementation from column lecture 04-03. The claim:
**not every query needs Opus.** With GPT-4o ~16× the price of
GPT-4o-mini and similar gaps across Claude tiers, routing 40-70% of
traffic to a cheaper tier typically halves the bill at no measurable
quality loss — provided the routing is done with a real signal and
provided the fallback path is honest about when the cheap tier was
wrong.

Two classes carry the pattern:

* `ComplexityRouter` — picks an initial tier from the task shape using
  pluggable signals (length, keyword cues, intent tags). Returns a
  `RoutingDecision` with reason; *never* a bare model id, because the
  reason is what an audit asks for first.
* `FallbackChain` — runs the chosen tier, validates the output, and
  on failure escalates to the next tier with a `FallbackTriggeredError`.
  Three iron rules: validators are pluggable, escalation has a hard
  ceiling, and the chain records *why* each step failed so the audit
  log isn't just "tier=2 was used; nobody knows why."

The whole point: routing is product economics, not infra plumbing.
Make the policy explicit and inspectable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable


class ComplexityTier(Enum):
    """Three tiers covers most production needs.

    Hermes runs six tiers of effort. Most teams find that three model
    tiers (cheap / medium / expensive) plus an off switch is the
    sweet spot — more tiers add ops cost without quality lift.
    """

    SIMPLE = 1     # cheapest model, lowest latency
    MEDIUM = 2     # mid-tier model
    COMPLEX = 3    # most expensive model, highest quality


# Default tier → model assignment. Swap this dict at construction time.
DEFAULT_TIER_MODELS: dict[ComplexityTier, str] = {
    ComplexityTier.SIMPLE: "claude-haiku-4-5",
    ComplexityTier.MEDIUM: "claude-sonnet-4-6",
    ComplexityTier.COMPLEX: "claude-opus-4-6",
}


@dataclass
class RoutingDecision:
    """The output of `ComplexityRouter.route`.

    Carries the reason so the audit log has more than just a model id.
    """

    tier: ComplexityTier
    model: str
    reason: str               # human-readable single sentence
    score: float              # 0.0–1.0, internal use


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# Signal functions take the task string and return a score in [0, 1].
SignalFn = Callable[[str], float]


def length_signal(task: str) -> float:
    """Longer tasks tend to need more reasoning. Capped at 800 chars."""
    return min(len(task) / 800.0, 1.0)


def causal_keyword_signal(task: str) -> float:
    """Causal / counterfactual / proof tasks need the expensive tier."""
    cues = (
        "why", "explain", "prove", "derive", "counterfactual", "what if",
        "因果", "证明", "推导", "归因", "为什么",
    )
    t = task.lower()
    hits = sum(1 for kw in cues if kw in t)
    return min(hits / 2.0, 1.0)


def template_query_signal(task: str) -> float:
    """Negative signal — recognizes lookup / template patterns that
    don't need reasoning. Returns the *anti*-score (1.0 = obvious template,
    so subtract from total)."""
    patterns = (
        r"^\s*(how many|count|list|show me)\b",
        r"^\s*(上周|本周|本月|今天|昨天).{0,20}(几|数|总)",
    )
    return 1.0 if any(re.search(p, task.lower()) for p in patterns) else 0.0


class ComplexityRouter:
    """Maps a task to a complexity tier with an explicit reason."""

    def __init__(
        self,
        tier_models: dict[ComplexityTier, str] | None = None,
        positive_signals: list[SignalFn] | None = None,
        negative_signals: list[SignalFn] | None = None,
        tier_thresholds: tuple[float, float] = (0.35, 0.70),
    ) -> None:
        self.tier_models = tier_models or dict(DEFAULT_TIER_MODELS)
        self.positive_signals = positive_signals or [length_signal, causal_keyword_signal]
        self.negative_signals = negative_signals or [template_query_signal]
        self.simple_threshold, self.complex_threshold = tier_thresholds

    def route(self, task: str) -> RoutingDecision:
        # Take the strongest positive signal — a single strong indicator
        # (e.g. "prove", "why") is enough to escalate, no need to average
        # it down against a weak length score. Subtract the average
        # negative score so a single template signal can pull a borderline
        # task back down to SIMPLE.
        positive = max((fn(task) for fn in self.positive_signals), default=0.0)
        negative = sum(fn(task) for fn in self.negative_signals) / max(len(self.negative_signals), 1)
        score = max(0.0, positive - negative)

        if score < self.simple_threshold:
            tier = ComplexityTier.SIMPLE
            reason = "task shape looks like a lookup / template query"
        elif score < self.complex_threshold:
            tier = ComplexityTier.MEDIUM
            reason = "task has moderate length or one reasoning cue"
        else:
            tier = ComplexityTier.COMPLEX
            reason = "task carries causal / counterfactual / proof cues"

        return RoutingDecision(
            tier=tier,
            model=self.tier_models[tier],
            reason=reason,
            score=round(score, 3),
        )


# ----------------------------------------------------------------------------
# Fallback chain
# ----------------------------------------------------------------------------


class FallbackTriggeredError(Exception):
    """Raised by a validator when the cheap tier's output is not trustworthy.

    Carries the reason so the audit log can show why the chain escalated.
    Inspired by Claude Code's `FallbackTriggeredError`: the *semantic*
    failure ("quality not good enough"), distinct from ordinary
    exceptions like network or auth errors.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


# A validator takes an output and returns None if OK, or raises
# FallbackTriggeredError to escalate.
ValidatorFn = Callable[[str], None]
# An LLM call: takes (task, model_id) and returns the answer.
LLMCallFn = Callable[[str, str], str]


@dataclass
class FallbackStep:
    """One step in the fallback chain audit record."""

    tier: ComplexityTier
    model: str
    output: str
    validated: bool
    fail_reason: str | None = None
    timestamp: str = field(default_factory=_now_iso)


class FallbackChain:
    """Cascade through tiers until validation passes or the chain is exhausted.

    The chain is a small interpreter for "try cheap, escalate on
    quality failure." It never escalates on transport errors — those
    belong to a different retry loop. Maximum 3 tiers; nobody runs a
    four-tier cascade in production (the Opus → Opus is no good).
    """

    def __init__(
        self,
        llm_call: LLMCallFn,
        router: ComplexityRouter | None = None,
        validator: ValidatorFn | None = None,
        max_escalations: int = 2,
    ) -> None:
        self.llm_call = llm_call
        self.router = router or ComplexityRouter()
        self.validator = validator or (lambda _output: None)
        self.max_escalations = max_escalations

    def run(self, task: str) -> tuple[str, list[FallbackStep]]:
        """Run the chain. Returns (final_output, audit_steps).

        Each escalation appends a `FallbackStep` so the audit log can
        show the whole path, not just the winning tier.
        """
        initial = self.router.route(task)
        tier_order = self._tier_order_from(initial.tier)
        steps: list[FallbackStep] = []

        for tier in tier_order:
            model = self.router.tier_models[tier]
            output = self.llm_call(task, model)
            try:
                self.validator(output)
            except FallbackTriggeredError as e:
                steps.append(FallbackStep(
                    tier=tier, model=model, output=output,
                    validated=False, fail_reason=e.reason,
                ))
                if len(steps) > self.max_escalations:
                    raise FallbackTriggeredError(
                        f"cascade exhausted after {len(steps)} tiers; last fail: {e.reason}"
                    )
                continue
            steps.append(FallbackStep(
                tier=tier, model=model, output=output, validated=True,
            ))
            return output, steps

        # If the loop completes without returning, we ran out of tiers.
        raise FallbackTriggeredError("cascade exhausted with no validated output")

    @staticmethod
    def _tier_order_from(start: ComplexityTier) -> list[ComplexityTier]:
        """Escalation order. If we start at SIMPLE we may go all the way
        up; if we start at COMPLEX, there's no cheaper tier to fall
        back to, so the chain is one step."""
        all_tiers = [ComplexityTier.SIMPLE, ComplexityTier.MEDIUM, ComplexityTier.COMPLEX]
        return [t for t in all_tiers if t.value >= start.value]
