"""Skill Package pattern.

Reference implementation from column lecture 06-03 (28). The claim:
**a skill enters the library only after it passes external verification,
and the router only ever routes to verified skills.** The agent saying
"that run worked, save it" is introspection; a golden question comparing
the skill's output against a known-correct expectation is a signal.
Without that gate, one bad distilled skill gets recalled month after
month, and the library makes the agent worse instead of better.

Router topology, not a chain: at runtime the pattern's core act is one
routing decision — match the incoming task against the library's
triggers and load the winning skill. Distillation and verification
happen between tasks; routing happens inside one.

Three roles:

* `Skill` — a named, loadable, reusable workflow: triggers for routing,
  steps for execution, plus lifecycle state. Every skill enters the
  library as TRIAL, regardless of who wrote it.
* `SkillLibrary.verify` — the admission gate. Runs the skill against a
  set of golden questions (input -> expected output, deterministic).
  All must pass before the skill is promoted to VERIFIED. Failures keep
  it in TRIAL, invisible to the router.
* `SkillLibrary.route` — trigger matching over VERIFIED skills only.
  No match returns an explicit from-scratch fallback; the router never
  silently picks a TRIAL skill because it "looks close".

Post-reuse outcomes feed back: a verified skill whose success rate
drops is demoted to TRIAL and must re-verify. That is the staleness
guard — policy years change, and last year's skill must not keep its
badge on this year's numbers.

Named failure modes:

* **Library pollution** — unverified skills stored as trusted; recall
  spreads the error. Closed by the admission gate.
* **Skill staleness** — the world changed, the skill did not. Closed by
  post-reuse tracking + demotion.
* **Discovery mismatch** — triggers too vague, router picks the wrong
  skill or none. Surfaced by the explicit RouteDecision record.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class SkillStatus(str, Enum):
    TRIAL = "TRIAL"          # stored, not routable
    VERIFIED = "VERIFIED"    # passed all golden questions, routable
    RETIRED = "RETIRED"      # evicted, kept for audit


@dataclass
class GoldenQuestion:
    """One admission check: feed `payload` to the skill, expect `expect`.

    Golden questions are deterministic by design — boundary cases,
    reconciliation counts, known worked examples. They are the external
    signal that separates "the agent believes the skill works" from
    "the skill demonstrably works"."""

    name: str
    payload: dict[str, Any]
    expect: Any


@dataclass
class Skill:
    name: str
    description: str
    triggers: list[str]
    steps: list[str]
    source: str = "human"            # human | distilled
    source_task: str = ""
    status: SkillStatus = SkillStatus.TRIAL
    version: int = 1
    verified_against: list[str] = field(default_factory=list)
    use_count: int = 0
    success_count: int = 0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.use_count if self.use_count else 0.0


@dataclass
class VerificationReport:
    skill: str
    passed: list[str] = field(default_factory=list)
    failed: list[tuple[str, Any, Any]] = field(default_factory=list)  # (name, expect, got)
    promoted: bool = False
    at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class RouteDecision:
    """The routing act, recorded. `considered` keeps every verified
    skill's score so a mismatch can be diagnosed instead of guessed."""

    task: str
    matched: str | None
    considered: list[tuple[str, float]] = field(default_factory=list)
    fallback: str | None = None      # "from_scratch" when nothing matched


# A runner executes a skill's steps on one payload and returns the result
# the golden question will compare. Deterministic in the labs.
RunnerFn = Callable[[Skill, dict[str, Any]], Any]


class SkillLibrary:
    def __init__(self, demote_below: float = 0.8, min_uses: int = 5) -> None:
        self.skills: dict[str, Skill] = {}
        self.demote_below = demote_below
        self.min_uses = min_uses

    def add(self, skill: Skill) -> Skill:
        """Every skill enters as TRIAL — human-written or distilled.
        The badge comes from verification, not from authorship."""
        skill.status = SkillStatus.TRIAL
        self.skills[skill.name] = skill
        return skill

    # ── admission gate ────────────────────────────────────────────────
    def verify(self, name: str, goldens: list[GoldenQuestion],
               runner: RunnerFn) -> VerificationReport:
        skill = self.skills[name]
        # A verification run replaces the old badge. Policy updates and new
        # boundary cases must be able to remove a previously earned approval.
        skill.status = SkillStatus.TRIAL
        skill.verified_against = []
        report = VerificationReport(skill=name)
        for g in goldens:
            got = runner(skill, g.payload)
            if got == g.expect:
                report.passed.append(g.name)
            else:
                report.failed.append((g.name, g.expect, got))
        if goldens and not report.failed:
            skill.status = SkillStatus.VERIFIED
            skill.verified_against = [g.name for g in goldens]
            # Reuse outcomes belong to this verification credential. A new
            # credential starts a fresh observation window.
            skill.use_count = 0
            skill.success_count = 0
            report.promoted = True
        return report

    # ── the routing act ───────────────────────────────────────────────
    def route(self, task: str) -> RouteDecision:
        decision = RouteDecision(task=task, matched=None)
        words = set(task.lower().split())
        best, best_score = None, 0.0
        for skill in self.skills.values():
            if skill.status is not SkillStatus.VERIFIED:
                continue
            triggers = {t.lower() for t in skill.triggers}
            score = len(words & triggers) / len(triggers) if triggers else 0.0
            decision.considered.append((skill.name, round(score, 2)))
            if score > best_score:
                best, best_score = skill, score
        if best and best_score > 0.3:
            decision.matched = best.name
        else:
            decision.fallback = "from_scratch"
        return decision

    # ── post-reuse signal ─────────────────────────────────────────────
    def record_use(self, name: str, success: bool) -> Skill:
        skill = self.skills[name]
        if skill.status is not SkillStatus.VERIFIED:
            raise ValueError("only VERIFIED skills can record routed outcomes")
        skill.use_count += 1
        if success:
            skill.success_count += 1
        if (skill.use_count >= self.min_uses
                and skill.success_rate < self.demote_below):
            skill.status = SkillStatus.TRIAL     # must re-verify
        return skill

    def retire(self, name: str) -> None:
        self.skills[name].status = SkillStatus.RETIRED


def distill_from_trace(task: str, tool_calls: list[dict[str, Any]],
                       name: str, description: str, triggers: list[str],
                       *, succeeded: bool,
                       min_calls: int = 5, min_unique: int = 3) -> Skill | None:
    """Hermes-inspired distillation trigger: only a successful trace with
    enough distinct tool calls is worth freezing into a skill. The
    returned skill is TRIAL — distillation earns storage, never trust."""
    if not succeeded:
        return None
    if len(tool_calls) < min_calls:
        return None
    if len({c.get("tool") for c in tool_calls}) < min_unique:
        return None
    steps = [f"{c['tool']}:{c.get('args', '')}" for c in tool_calls]
    return Skill(
        name=name,
        description=description,
        triggers=triggers,
        steps=steps,
        source="distilled",
        source_task=task,
    )
