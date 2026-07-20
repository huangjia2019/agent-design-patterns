"""Runnable Fan-out / Gather example with four deterministic ledgers."""
from __future__ import annotations

import asyncio

from pattern import (
    AggregatorPolicy,
    FanOutGather,
    Reconciler,
    SourceResult,
    SourceSpec,
    Strategy,
    TaskContract,
    bind_source_result,
)


ROWS = ({"id": f"e{i}"} for i in range(800))
LEDGER = {
    "payroll": {"基本工资": 3_100_000.0, "社保代扣": 120_000.0, "加班费": 100_000.0},
    "gl": {"基本工资": 3_100_000.0, "社保代扣": 120_000.0, "加班费": 100_000.0},
    "social_security": {
        "基本工资": 3_100_000.0,
        "社保代扣": 108_000.0,
        "加班费": 100_000.0,
    },
    "attendance": {
        "基本工资": 3_100_000.0,
        "社保代扣": 120_000.0,
        "加班费": 250_000.0,
    },
}


def root_contract() -> TaskContract:
    return TaskContract(
        contract_id="june-ledger-reconciliation",
        version=1,
        objective="reconcile the June payroll ledger",
        output_schema="ReconciliationReport",
        accountable_owner="payroll-controller",
        input_refs=("ledger://2026-06",),
    )


def build_source(source_id: str, items: dict[str, float]):
    source = SourceSpec(
        source_id=source_id,
        snapshot_ref=f"snapshot://{source_id}/2026-06",
        period="2026-06",
        unit="CNY",
        boundary=f"read only from {source_id}",
        expected_items=tuple(items),
        allowed_tools=(f"read_{source_id}",),
        authority_scope=(f"read:{source_id}",),
    )

    async def worker(handoff, rows):
        await asyncio.sleep(0.01)
        result = SourceResult.from_mapping(
            source_id=source.source_id,
            snapshot_ref=source.snapshot_ref,
            period=source.period,
            unit=source.unit,
            line_items=items,
        )
        return bind_source_result(
            handoff,
            result,
            evidence_refs=(source.snapshot_ref,),
        )

    return source, worker


async def main() -> None:
    sources = tuple(
        build_source(source_id, items)
        for source_id, items in LEDGER.items()
    )
    gather = FanOutGather(
        sources,
        Reconciler(AggregatorPolicy(strategy=Strategy.COMPETING), tol=1.0),
        min_success_rate=1.0,
    )
    run = await gather.run(root_contract(), tuple(ROWS))

    print(f"status: {run.report.status.value}")
    print(f"agreed: {list(run.report.agreed_items)}")
    print("attributable divergences:")
    for verdict in run.report.attributable_divergences:
        print(
            f"  {verdict.item}: gap={verdict.gap:,.0f} "
            f"low={list(verdict.low_sources)} "
            f"high={list(verdict.high_sources)}"
        )
    print(f"root receipt: {run.report_receipt.decision.value}")


if __name__ == "__main__":
    asyncio.run(main())
