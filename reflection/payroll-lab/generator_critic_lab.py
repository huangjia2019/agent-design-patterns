"""Lecture 27 hands-on: the monthly report through Generator-Critic passes.

Uses the pattern from ../a-generator-critic/pattern.py on the payroll bench
(month-end: 798 PAID, 2 REVERSED). Three scenes:

    scene 1  explicit runner calls the one-pass primitive up to three times;
             round 1 carries ledger errors plus a missing field; wired checks
             find them all, while one evidence-free "vibe" finding is dropped
    scene 2  a rubber-stamp critic: same wrong draft, no external checks,
             accepted in one pass -- lecture 26's lesson at pattern level
    scene 3  run with --stubborn: the generator ignores one fix, the runner
             exhausts its pass budget and hands the draft to a human

The primitive remains generate -> critique -> gate -> optional revision draft.
Repeated repair is owned by this runner, not by the F1 Generator-Critic pattern.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "a-generator-critic"))
from pattern import (  # noqa: E402
    AcceptancePolicy,
    Artifact,
    ChainResult,
    Critique,
    GeneratorCriticChain,
    Issue,
    Severity,
)
import bench  # noqa: E402

MONTH = bench.MONTH
STUBBORN = "--stubborn" in sys.argv

con = bench.month_end_state()
PAID_DB = con.execute(
    "SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
    (MONTH,),
).fetchone()[0]
REVERSED_DB = [
    r[0]
    for r in con.execute(
        "SELECT emp_id FROM payroll WHERE month=? AND status='REVERSED'",
        (MONTH,),
    )
]


@dataclass
class DemoTrace:
    results: list[ChainResult] = field(default_factory=list)
    status: str = "pending"  # clean | pass_budget_exhausted


CheckFn = Callable[[Artifact], list[Issue]]


# ---- the generator: drafts from a belief, revises from prior pass evidence ---

belief = {"paid": 800, "reversed": [], "exceptions_field": False}


def reset_belief() -> None:
    belief.update({"paid": 800, "reversed": [], "exceptions_field": False})


def apply_blocking_evidence(blocking_issues: list[Issue]) -> None:
    for issue in blocking_issues:
        if issue.source == "reconcile_paid":
            belief["paid"] = PAID_DB
        if issue.source == "reconcile_reversed" and not STUBBORN:
            belief["reversed"] = REVERSED_DB
        if issue.source == "schema":
            belief["exceptions_field"] = True


def draft_report(brief: str, blocking_issues: list[Issue]) -> Artifact:
    apply_blocking_evidence(blocking_issues)
    parts = [
        f"MONTHLY-REPORT month={MONTH}",
        f"paid={belief['paid']}",
        f"reversed={len(belief['reversed'])}",
    ]
    if belief["exceptions_field"]:
        parts.append("exceptions=" + (",".join(belief["reversed"]) or "none"))
    parts.append(
        "conclusion=all-clear"
        if not belief["reversed"]
        else "conclusion=exceptions-pending"
    )
    return Artifact(content=" ".join(parts), metadata={"brief": brief})


# ---- the critic: wired checks plus one sloppy opinion ------------------------

def schema_check(artifact: Artifact) -> list[Issue]:
    missing = [key for key in ("paid=", "reversed=", "exceptions=") if key not in artifact.content]
    if missing:
        return [
            Issue(
                Severity.BLOCKER,
                f"required fields missing: {missing}",
                "report",
                "schema",
                "report schema v2 requires paid/reversed/exceptions",
            )
        ]
    return []


def reconcile_paid(artifact: Artifact) -> list[Issue]:
    if f"paid={PAID_DB}" not in artifact.content:
        return [
            Issue(
                Severity.BLOCKER,
                "paid count disagrees with the ledger",
                "paid",
                "reconcile_paid",
                f"ledger COUNT(status='PAID') = {PAID_DB}",
            )
        ]
    return []


def reconcile_reversed(artifact: Artifact) -> list[Issue]:
    if f"reversed={len(REVERSED_DB)}" not in artifact.content:
        return [
            Issue(
                Severity.BLOCKER,
                "reversed count disagrees with the ledger",
                "reversed",
                "reconcile_reversed",
                f"ledger REVERSED rows: {', '.join(REVERSED_DB)}",
            )
        ]
    return []


def style_check(artifact: Artifact) -> list[Issue]:
    if "all-clear" in artifact.content:
        return [
            Issue(
                Severity.INFO,
                "prefer explicit residual-risk wording over 'all-clear'",
                "conclusion",
                "style",
                "reporting guideline R-7",
            )
        ]
    return []


def vibe_check(_artifact: Artifact) -> list[Issue]:
    return [
        Issue(
            Severity.BLOCKER,
            "report feels thin, expand it",
            "report",
            "vibe",
            "",
        )
    ]


def make_critic(checks: dict[str, CheckFn]) -> Callable[[Artifact], Critique]:
    def critic(artifact: Artifact) -> Critique:
        issues: list[Issue] = []
        for check in checks.values():
            issues.extend(check(artifact))
        score = 0.55 if any(
            issue.severity is Severity.BLOCKER and issue.is_evidence_backed()
            for issue in issues
        ) else 0.92
        return Critique(
            score=score,
            issues=issues,
            summary=f"{len(issues)} finding(s) before evidence gate",
        )

    return critic


def run_explicit_passes(
    brief: str,
    checks: dict[str, CheckFn],
    *,
    max_passes: int = 3,
) -> DemoTrace:
    trace = DemoTrace()
    blocking: list[Issue] = []
    for _pass_no in range(1, max_passes + 1):
        chain = GeneratorCriticChain(
            generator=lambda prompt, blocking=blocking: draft_report(prompt, blocking),
            critic=make_critic(checks),
            policy=AcceptancePolicy(min_score=0.8),
        )
        result = chain.run(brief)
        trace.results.append(result)
        if result.decision.value == "accepted":
            trace.status = "clean"
            return trace
        blocking = result.critique.blockers()
    trace.status = "pass_budget_exhausted"
    return trace


def show(trace: DemoTrace) -> None:
    for idx, result in enumerate(trace.results, start=1):
        print(f"   pass {idx}: {result.artifact.content}")
        print(f"      decision: {result.decision.value}  trace={' -> '.join(result.trace)}")
        for issue in result.critique.issues:
            print(
                f"      [{issue.severity.value:7s}] {issue.source}: {issue.message}"
                f"  (evidence: {issue.evidence})"
            )
        for issue in result.critique.dropped_issues:
            print(
                f"      [DROPPED] {issue.source or 'unknown'}: {issue.message}"
                "  (no evidence -- logged, not acted on)"
            )
    print(f"   status: {trace.status.upper()} after {len(trace.results)} pass(es)")


print(f"== ledger truth: paid={PAID_DB}, reversed={REVERSED_DB} ==")

print(f"\n== scene 1: the wired critic (stubborn={STUBBORN}) ==")
reset_belief()
wired_checks = {
    "schema": schema_check,
    "reconcile_paid": reconcile_paid,
    "reconcile_reversed": reconcile_reversed,
    "style": style_check,
    "vibe": vibe_check,
}
trace = run_explicit_passes(f"monthly report {MONTH}", wired_checks)
show(trace)
if trace.status == "pass_budget_exhausted":
    print(
        "   -> handed to a human with the full findings history. "
        "The last draft is not shipped."
    )

print("\n== scene 2: the rubber-stamp critic (no external checks) ==")
reset_belief()
trace2 = run_explicit_passes(f"monthly report {MONTH}", {"vibe": vibe_check})
show(trace2)
print(
    f"   -> ACCEPTED a report that says paid=800 while the ledger says {PAID_DB}. "
    "No external signal, no actionable findings, wrong report ships."
)
