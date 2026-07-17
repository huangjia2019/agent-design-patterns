"""Runnable example: delegate an 800-employee payroll run.

    python collaboration/a-hierarchical-delegation/example.py

No API key is needed. A deterministic worker fills the same dispatch seam that
LangGraph or an agent SDK would use.
"""
from __future__ import annotations

import asyncio
import random

from pattern import (
    PortfolioBoundary,
    SafetyBoundary,
    SalaryBatchResult,
    SettlementSupervisor,
    Verdict,
    batch_fingerprint,
    bind_salary_result,
)


CLIENTS = ["acme", "globex", "initech", "umbrella", "wayne", "stark"]


def build_roster(n: int = 800) -> list[dict]:
    rng = random.Random(42)
    return [
        {"id": f"e{i}", "client": rng.choice(CLIENTS), "base": rng.randint(5000, 20000)}
        for i in range(n)
    ]


async def mock_worker(handoff, rows):
    """Return one compact, contract-bound artifact and no raw worker trace."""
    await asyncio.sleep(0.01)
    total = float(sum(float(row["base"]) * 1.3 for row in rows))
    flagged = (
        (str(rows[0]["id"]),)
        if handoff.contract.contract_id == "batch::stark" and rows
        else ()
    )
    employee_ids = tuple(str(row["id"]) for row in rows)
    result = SalaryBatchResult(
        batch_id=handoff.contract.contract_id,
        verdict=Verdict.PARTIAL if flagged else Verdict.SUCCESS,
        employee_count=len(rows),
        total_amount=round(total, 2),
        input_fingerprint=batch_fingerprint(employee_ids),
        anomalies=("commission exceeds department mean",) if flagged else (),
        needs_review=flagged,
        confidence=0.6 if flagged else 1.0,
    )
    return bind_salary_result(
        handoff,
        result,
        evidence_refs=(f"roster://{handoff.contract.contract_id}",),
    )


async def main() -> None:
    roster = build_roster()
    supervisor = SettlementSupervisor(
        dispatch=mock_worker,
        boundary=SafetyBoundary(
            amount_threshold=5_000_000,
            min_confidence=0.85,
        ),
        portfolio_boundary=PortfolioBoundary(max_total_amount=20_000_000),
        max_concurrent=5,
    )
    summary = await supervisor.run(roster)

    print(f"Supervisor: 1 · Workers: {len(summary.batch_artifacts)}")
    print(f"Total (auto-admitted):  {summary.total:,.2f}")
    print(f"Employees represented:  {summary.employee_count}")
    print(f"Auto-admitted batches:  {list(summary.auto_approved)}")
    print(f"Held for human review:  {list(summary.human_review)}")
    print(f"Portfolio decision:     {summary.portfolio_receipt.decision.value}")


if __name__ == "__main__":
    asyncio.run(main())
