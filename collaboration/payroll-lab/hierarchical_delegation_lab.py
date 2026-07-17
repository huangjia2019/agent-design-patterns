"""Lecture 32 lab: contract-bound hierarchical delegation.

The real C1 pattern runs on the month-end payroll bench. Four deterministic
scenes expose the topology and its two admission levels:

1. child contracts, artifacts, and receipts line up;
2. one worker failure becomes one evidenced failure artifact;
3. a worker that drops rows is caught by contract-owned roster evidence;
4. every batch passes locally, while a portfolio gate catches the combined sum.

Workers are deterministic test doubles. The lab measures interface behavior,
not model capability.

Run:
    python3 hierarchical_delegation_lab.py
    python3 hierarchical_delegation_lab.py --sum-blind
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "a-hierarchical-delegation"))
sys.path.insert(0, str(HERE.parent.parent / "reflection" / "payroll-lab"))

import bench  # noqa: E402
from pattern import (  # noqa: E402
    AcceptanceDecision,
    PortfolioBoundary,
    SafetyBoundary,
    SalaryBatchResult,
    SettlementSupervisor,
    Verdict,
    batch_fingerprint,
    bind_salary_result,
)


SUM_BLIND = "--sum-blind" in sys.argv
con = bench.month_end_state()
REVERSED_IDS = set(bench.REVERSED_IDS)
roster = [
    {"id": employee_id, "client": department, "base": base_salary}
    for employee_id, department, base_salary in con.execute(
        "SELECT emp_id, dept, base_salary FROM employees ORDER BY emp_id"
    )
]


def build_result(
    handoff,
    rows,
    *,
    verdict: Verdict = Verdict.SUCCESS,
    needs_review: tuple[str, ...] = (),
    confidence: float = 0.98,
) -> SalaryBatchResult:
    employee_ids = tuple(str(row["id"]) for row in rows)
    return SalaryBatchResult(
        batch_id=handoff.contract.contract_id,
        verdict=verdict,
        employee_count=len(rows),
        total_amount=float(sum(float(row["base"]) for row in rows)),
        input_fingerprint=batch_fingerprint(employee_ids),
        needs_review=needs_review,
        confidence=confidence,
    )


async def worker(handoff, rows):
    """A diligent worker behind the dispatch seam."""
    flagged = tuple(str(row["id"]) for row in rows if row["id"] in REVERSED_IDS)
    verdict = Verdict.PARTIAL if flagged else Verdict.SUCCESS
    return bind_salary_result(
        handoff,
        build_result(
            handoff,
            rows,
            verdict=verdict,
            needs_review=flagged,
        ),
        evidence_refs=(
            f"sqlite://payroll.db/employees?batch={handoff.contract.contract_id}",
        ),
    )


def show_batch_receipts(summary) -> None:
    for artifact, receipt in zip(
        summary.batch_artifacts,
        summary.batch_receipts,
        strict=True,
    ):
        codes = ",".join(finding.code for finding in receipt.findings) or "clean"
        print(
            f"   {artifact.payload.batch_id:<20} "
            f"{receipt.decision.value:<10} [{codes}]"
        )


def show_summary(summary) -> None:
    payload = summary.portfolio_artifact.payload
    root_codes = (
        ",".join(finding.code for finding in summary.portfolio_receipt.findings)
        or "clean"
    )
    print(f"   admitted total: {payload.admitted_total_amount:,.0f}")
    print(f"   claimed total:  {payload.claimed_total_amount:,.0f}")
    print(f"   employee_count: {payload.employee_count}")
    print(f"   auto_approved:  {list(payload.auto_approved)}")
    print(f"   human_review:   {list(payload.human_review)}")
    print(
        f"   portfolio:      {summary.portfolio_receipt.decision.value} "
        f"[{root_codes}]"
    )


BOUNDARY = SafetyBoundary(amount_threshold=3_000_000, min_confidence=0.85)


if not SUM_BLIND:
    print("== scene 1: one root contract, five child receipts ==")
    supervisor = SettlementSupervisor(
        worker,
        BOUNDARY,
        PortfolioBoundary(max_total_amount=20_000_000),
    )
    assignments = supervisor.decompose(roster)
    print(
        f"   decomposed: {len(roster)} employees -> "
        f"{len(assignments)} non-overlapping child contracts"
    )
    print(
        "   chain: TaskContract -> HandoffEnvelope -> "
        "ArtifactEnvelope -> AcceptanceReceipt"
    )
    summary = asyncio.run(supervisor.run(roster))
    show_batch_receipts(summary)
    show_summary(summary)

    print("\n== scene 2: one worker dies; one batch escalates ==")

    async def flaky(handoff, rows):
        if handoff.contract.contract_id == "batch::Ops":
            raise RuntimeError("worker context crashed")
        return await worker(handoff, rows)

    summary = asyncio.run(
        SettlementSupervisor(
            flaky,
            BOUNDARY,
            PortfolioBoundary(max_total_amount=20_000_000),
        ).run(roster)
    )
    failed = next(
        artifact.payload
        for artifact in summary.batch_artifacts
        if artifact.payload.batch_id == "batch::Ops"
    )
    print(f"   batch::Ops failure_code: {failed.failure_code}")
    print(f"   batch::Ops retryable:    {failed.retryable}")
    show_summary(summary)

    print("\n== scene 3: contract evidence catches a silent row drop ==")

    async def dropper(handoff, rows):
        if handoff.contract.contract_id == "batch::Engineering":
            kept = rows[:-12]
            return bind_salary_result(
                handoff,
                build_result(handoff, kept),
                evidence_refs=("sqlite://payroll.db/dropper",),
            )
        return await worker(handoff, rows)

    summary = asyncio.run(
        SettlementSupervisor(
            dropper,
            BOUNDARY,
            PortfolioBoundary(max_total_amount=20_000_000),
        ).run(roster)
    )
    engineering = next(
        receipt
        for artifact, receipt in zip(
            summary.batch_artifacts,
            summary.batch_receipts,
            strict=True,
        )
        if artifact.payload.batch_id == "batch::Engineering"
    )
    print(
        "   batch::Engineering: "
        + ",".join(finding.code for finding in engineering.findings)
    )
    print(
        "   portfolio: "
        + ",".join(
            finding.code for finding in summary.portfolio_receipt.findings
        )
    )
    print("   -> the worker cannot approve its own incomplete roster slice")

else:
    print("== scene 4: local admission versus portfolio admission ==")

    async def clean_worker(handoff, rows):
        return bind_salary_result(
            handoff,
            build_result(handoff, rows),
            evidence_refs=("sqlite://payroll.db/clean",),
        )

    blind = asyncio.run(
        SettlementSupervisor(
            clean_worker,
            BOUNDARY,
            PortfolioBoundary(max_total_amount=None),
        ).run(roster)
    )
    guarded = asyncio.run(
        SettlementSupervisor(
            clean_worker,
            BOUNDARY,
            PortfolioBoundary(max_total_amount=13_000_000),
        ).run(roster)
    )
    assert all(
        receipt.decision is AcceptanceDecision.ACCEPTED
        for receipt in guarded.batch_receipts
    )
    print(f"   every batch decision: {AcceptanceDecision.ACCEPTED.value}")
    print(f"   combined claim:       {guarded.portfolio_artifact.payload.claimed_total_amount:,.0f}")
    print(f"   no portfolio limit:   {blind.portfolio_receipt.decision.value}")
    print(f"   13,000,000 limit:     {guarded.portfolio_receipt.decision.value}")
    print(
        "   finding:              "
        + ",".join(
            finding.code for finding in guarded.portfolio_receipt.findings
        )
    )
