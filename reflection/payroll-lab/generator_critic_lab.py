"""Lecture 27: review a payroll report with one-pass Generator-Critic chains.

The standard scene makes the interface boundary visible:

1. pass 1 reviews the original report and drafts a revision;
2. the revision remains unreviewed;
3. pass 2 is an explicit new review and may accept it.

The --rubber-stamp contrast removes the ledger and schema evidence. The wrong
report then receives a high score and is accepted, which demonstrates that a
polished critic cannot recover facts it was never allowed to observe.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


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
connection = bench.month_end_state()
PAID_DB = connection.execute(
    "SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'", (MONTH,)
).fetchone()[0]
REVERSED_DB = [
    row[0]
    for row in connection.execute(
        "SELECT emp_id FROM payroll WHERE month=? AND status='REVERSED' ORDER BY emp_id",
        (MONTH,),
    )
]


def generate_report(_brief: str) -> Artifact:
    return Artifact(
        content=(
            f"MONTHLY-REPORT month={MONTH} paid=800 reversed=0 "
            "conclusion=all-clear"
        ),
        metadata={"month": MONTH, "source": "report-agent"},
    )


def grounded_critic(artifact: Artifact) -> Critique:
    draft = artifact.content
    issues: list[Issue] = []

    if "exceptions=" not in draft:
        issues.append(
            Issue(
                Severity.BLOCKER,
                "required field exceptions is missing",
                "report schema",
                "report schema v2 requires paid/reversed/exceptions",
                "schema",
            )
        )
    if f"paid={PAID_DB}" not in draft:
        issues.append(
            Issue(
                Severity.BLOCKER,
                "paid count disagrees with the ledger",
                "paid",
                f"ledger COUNT(status='PAID') = {PAID_DB}",
                "reconcile_paid",
            )
        )
    if f"reversed={len(REVERSED_DB)}" not in draft:
        issues.append(
            Issue(
                Severity.BLOCKER,
                "reversed count disagrees with the ledger",
                "reversed",
                f"ledger REVERSED rows: {', '.join(REVERSED_DB)}",
                "reconcile_reversed",
            )
        )
    if "all-clear" in draft:
        issues.append(
            Issue(
                Severity.INFO,
                "state the residual exception explicitly",
                "conclusion",
                "reporting guideline R-7",
                "wording",
            )
        )

    # This opinion stays auditable, but cannot trigger an automatic revision
    # because it carries no external evidence.
    issues.append(
        Issue(
            Severity.WARNING,
            "the report feels thin; make it longer",
            "body",
            check="vibe",
        )
    )

    grounded_blockers = [issue for issue in issues if issue.severity is Severity.BLOCKER]
    return Critique(
        score=0.42 if grounded_blockers else 0.94,
        issues=issues,
        summary=f"{len(grounded_blockers)} grounded blocker(s)",
        score_evidence=(
            f"{len(grounded_blockers)} grounded blocker(s)"
            if grounded_blockers
            else ""
        ),
    )


def revise_report(artifact: Artifact, critique: Critique) -> Artifact:
    checks = {issue.check for issue in critique.blockers()}
    paid = PAID_DB if "reconcile_paid" in checks else 800
    reversed_ids = REVERSED_DB if "reconcile_reversed" in checks else []
    exceptions = ",".join(reversed_ids) or "none"
    conclusion = "exceptions-pending" if reversed_ids else "all-clear"
    content = (
        f"MONTHLY-REPORT month={MONTH} paid={paid} reversed={len(reversed_ids)} "
        f"exceptions={exceptions} conclusion={conclusion}"
    )
    return artifact.revise(content, note="applied grounded critique findings")


def rubber_stamp_critic(_artifact: Artifact) -> Critique:
    return Critique(
        score=0.96,
        issues=[
            Issue(
                Severity.INFO,
                "format and tone are consistent",
                "whole report",
                "the report contains a heading and a conclusion",
                "surface_format",
            )
        ],
        summary="polished and internally consistent",
    )


def show_pass(pass_no: int, result: ChainResult) -> None:
    print(
        f"[PASS {pass_no}] decision={result.decision.value} "
        f"reviewed_revision={result.reviewed_artifact.revision}"
    )
    print(f"   reviewed: {result.reviewed_artifact.content}")
    print(f"   trace: {' -> '.join(result.trace)}")
    for issue in result.critique.issues:
        print(
            f"   [ISSUE {issue.severity.value.upper()}] check={issue.check} "
            f"message={issue.message} evidence={issue.evidence}"
        )
    for issue in result.critique.dropped_issues:
        print(
            f"   [DROPPED] check={issue.check or 'unnamed'} "
            f"message={issue.message} evidence=NONE"
        )
    if result.revision_draft is not None:
        print(
            f"[REVISION_DRAFT] revision={result.revision_draft.revision} "
            f"review_status=UNREVIEWED content={result.revision_draft.content}"
        )


def run_standard() -> None:
    print(f"== ledger truth: paid={PAID_DB}, reversed={REVERSED_DB} ==")
    print("== scene 1: one pass drafts a revision; a second pass reviews it ==")
    chain = GeneratorCriticChain(
        generator=generate_report,
        critic=grounded_critic,
        reviser=revise_report,
        policy=AcceptancePolicy(min_score=0.8, require_evidence=True),
    )

    first = chain.run(f"monthly report {MONTH}")
    show_pass(1, first)
    if first.revision_draft is None:
        raise RuntimeError("the broken fixture should produce a revision draft")

    print("[BOUNDARY] revision draft is not accepted by pass 1; submit it again")
    second = chain.review(first.revision_draft)
    show_pass(2, second)
    print(f"[VERDICT] {second.decision.value.upper()} after explicit re-review")


def run_rubber_stamp() -> None:
    print(f"== ledger truth: paid={PAID_DB}, reversed={REVERSED_DB} ==")
    print("== contrast: rubber-stamp critic without ledger or schema evidence ==")
    chain = GeneratorCriticChain(
        generator=generate_report,
        critic=rubber_stamp_critic,
        policy=AcceptancePolicy(min_score=0.8),
    )
    result = chain.run(f"monthly report {MONTH}")
    show_pass(1, result)
    print(
        f"[VERDICT] {result.decision.value.upper()} wrong_report=true "
        f"report_paid=800 ledger_paid={PAID_DB}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the lecture 27 payroll lab.")
    parser.add_argument(
        "--rubber-stamp",
        action="store_true",
        help="Run the critic without ledger and schema evidence.",
    )
    args = parser.parse_args()
    if args.rubber_stamp:
        run_rubber_stamp()
    else:
        run_standard()


if __name__ == "__main__":
    main()
