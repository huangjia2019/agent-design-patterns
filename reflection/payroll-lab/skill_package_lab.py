"""Lecture 28 hands-on: June's settlement workflow becomes a routable skill.

Uses the pattern from ../b-skill-package/pattern.py on the payroll bench.
June's social-base settlement took three critic rounds to get right
(lecture 27); this lab freezes that workflow into a skill for July.
Three scenes:

    scene 1  verify before store: the distilled skill froze the OLD policy
             year into its steps; two golden questions fail, it stays
             TRIAL; fix one step, re-verify, promoted to VERIFIED
    scene 2  the router only sees VERIFIED: July's task routes to the
             promoted skill; a trigger-matching TRIAL skill is invisible;
             an unmatched task falls back to from-scratch, explicitly
    scene 3  run with --no-gate: the wrong-year skill is stored as
             trusted without verification, July routes to it, and the
             800-person database shows how many contribution bases go
             wrong -- silently, every step reporting success

Run `python3 skill_package_lab.py` (add --no-gate for scene 3).
"""
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "b-skill-package"))
from pattern import (  # noqa: E402
    GoldenQuestion, Skill, SkillLibrary, SkillStatus, distill_from_trace)
import bench  # noqa: E402

NO_GATE = "--no-gate" in sys.argv

# Social-insurance contribution-base bounds (mock policy table).
# The policy year rolls over in July -- June's run used 2025 bounds,
# July must use 2026 bounds. This is the classic gotcha: never compute
# this year's bases with last year's bounds.
POLICY = {"2025": (4462, 22311), "2026": (4880, 24402)}


def run_skill(skill: Skill, payload: dict) -> int:
    """Deterministic runner: walks the skill's steps, returns the
    contribution base it computes for one employee payload."""
    lo, hi = None, None
    base = None
    for step in skill.steps:
        op, _, arg = step.partition(":")
        if op == "fetch_policy":
            lo, hi = POLICY[arg]
        elif op == "clamp_base":
            declared = payload["declared"]
            base = max(lo, min(hi, declared))
        # verify_group / reconcile / report steps: no-op on one payload
    return base


# Golden questions for the JULY settlement: boundary cases with the
# 2026 bounds, worked out by hand once. This is the external signal --
# the skill's answer is compared to a known-correct expectation, not to
# the agent's own opinion of how the run went.
GOLDENS = [
    GoldenQuestion("over-cap clamp", {"declared": 30000}, 24402),
    GoldenQuestion("under-floor clamp", {"declared": 4000}, 4880),
    GoldenQuestion("mid-band passthrough", {"declared": 12000}, 12000),
]

# June's successful trace, as the distiller sees it: six tool calls,
# four distinct tools -- enough to be worth freezing. Note the literal
# policy year baked into the first call.
JUNE_TRACE = [
    {"tool": "fetch_policy", "args": "2025"},
    {"tool": "clamp_base", "args": "batch"},
    {"tool": "verify_group", "args": "batch"},
    {"tool": "clamp_base", "args": "exceptions"},
    {"tool": "reconcile", "args": "2026-06"},
    {"tool": "report", "args": "2026-06"},
]

library = SkillLibrary()
skill = distill_from_trace(
    task="2026-06 settlement under social-base adjustment",
    tool_calls=JUNE_TRACE,
    name="social-base-adjust",
    description="monthly settlement when contribution-base bounds change",
    triggers=["settlement", "social", "base", "adjust", "contribution"],
)
library.add(skill)


def show_report(report):
    for name in report.passed:
        print(f"      [PASS] {name}")
    for name, expect, got in report.failed:
        print(f"      [FAIL] {name}: expected {expect}, skill computed {got}")
    verdict = "PROMOTED to VERIFIED" if report.promoted else "stays TRIAL, not routable"
    print(f"   -> {verdict}")


if not NO_GATE:
    print("== scene 1: verify before store ==")
    print(f"   distilled from June's trace: steps[0] = {skill.steps[0]}")
    report = library.verify("social-base-adjust", GOLDENS, run_skill)
    show_report(report)

    print("\n   fix one step: fetch_policy:2025 -> fetch_policy:2026, re-verify")
    skill.steps[0] = "fetch_policy:2026"
    skill.version += 1
    report = library.verify("social-base-adjust", GOLDENS, run_skill)
    show_report(report)

    print("\n== scene 2: the router only sees VERIFIED ==")
    # A half-baked distilled skill whose triggers also match July's task.
    library.add(Skill(
        name="settlement-hotfix",
        description="unreviewed leftovers from a June incident",
        triggers=["settlement", "social", "base", "adjust", "contribution", "july"],
        steps=["fetch_policy:2025", "clamp_base:batch"],
        source="distilled"))
    for s in library.skills.values():
        print(f"   library: {s.name:22s} status={s.status.value}")

    task = "2026-07 settlement social base adjust contribution recalc"
    decision = library.route(task)
    print(f"   route({task!r})")
    print(f"      considered: {decision.considered}")
    print(f"      matched: {decision.matched}")
    print("      settlement-hotfix's triggers also match this task, but it is")
    print("      TRIAL -- the router never saw it.")

    other = library.route("year-end bonus special payout")
    print("   route('year-end bonus special payout')")
    print(f"      matched: {other.matched}, fallback: {other.fallback}")
    print("      no verified skill fits: fall back to from-scratch, visibly.")

else:
    print("== scene 3 (--no-gate): stored as trusted, never verified ==")
    skill.status = SkillStatus.VERIFIED          # "it worked in June, ship it"
    decision = library.route(
        "2026-07 settlement social base adjust contribution recalc")
    print(f"   route matched: {decision.matched} (steps[0] = {skill.steps[0]})")

    con = bench.month_end_state()
    lo26, hi26 = POLICY["2026"]
    wrong = 0
    for (declared,) in con.execute("SELECT base_salary FROM employees"):
        right = max(lo26, min(hi26, declared))
        got = run_skill(skill, {"declared": declared})
        if got != right:
            wrong += 1
    total = con.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    print(f"   applied to all {total} employees with 2025 bounds:")
    print(f"   {wrong} contribution bases computed wrong. Every step reported")
    print("   success; nothing in the run knows the policy year rolled over.")
    print("   The three golden questions cost three comparisons. This costs")
    print(f"   {wrong} wrong social-insurance payments and a July of corrections.")
