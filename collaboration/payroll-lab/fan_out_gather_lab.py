"""Lecture 33 lab: three contract-bound ledgers answer one question.

Three deterministic source workers read the month-end payroll bench through
different attributable boundaries. The gather preserves agreement, divergence,
single-source items, source failure, and the final root receipt.

Run:
    python3 fan_out_gather_lab.py
    python3 fan_out_gather_lab.py --additive
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path


HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


fan = load_module(
    HERE.parent / "b-fan-out-gather" / "pattern.py",
    "fanout_pattern",
)
AcceptanceDecision = fan.AcceptanceDecision
AggregatorPolicy = fan.AggregatorPolicy
ContributionRule = fan.ContributionRule
FanOutGather = fan.FanOutGather
Reconciler = fan.Reconciler
SourceAdmissionPolicy = fan.SourceAdmissionPolicy
SourceResult = fan.SourceResult
SourceSpec = fan.SourceSpec
Strategy = fan.Strategy
TaskContract = fan.TaskContract
Tolerance = fan.Tolerance
bind_source_result = fan.bind_source_result

sys.path.insert(0, str(HERE.parent.parent / "reflection" / "payroll-lab"))
import bench  # noqa: E402


SIGN_OFF_THRESHOLD = 10_000.0
CONTRACTOR_POOL = 184_000.0
DEPARTMENTS = ("Engineering", "Finance", "Ops", "Sales", "Support")
TASK_ROWS = ({"question": f"total pay per department, {bench.MONTH}"},)


def month_end():
    return bench.month_end_state()


def root_contract() -> TaskContract:
    return TaskContract(
        contract_id=f"payroll-reconciliation::{bench.MONTH}",
        version=1,
        objective=f"reconcile total pay per department for {bench.MONTH}",
        output_schema="ReconciliationReport",
        accountable_owner="payroll-controller",
        input_refs=(f"payroll://month/{bench.MONTH}",),
        constraints=("competing sources must preserve divergence",),
        allowed_tools=("fan_out_sources",),
        authority_scope=("read:source-artifacts", "propose:reconciliation"),
        boundary="controller may reconcile; it may not rewrite source readings",
    )


def gross_by_dept(con) -> dict[str, float]:
    return {
        department: float(total)
        for department, total in con.execute(
            "SELECT dept, SUM(base_salary) FROM employees GROUP BY dept"
        )
    }


def net_by_dept(con) -> dict[str, float]:
    return {
        department: float(total)
        for department, total in con.execute(
            "SELECT e.dept, SUM(e.base_salary) FROM payroll p "
            "JOIN employees e ON e.emp_id = p.emp_id "
            "WHERE p.month = ? AND p.status = 'PAID' GROUP BY e.dept",
            (bench.MONTH,),
        )
    }


def reversed_by_dept(con) -> dict[str, float]:
    return {
        department: float(total)
        for department, total in con.execute(
            "SELECT e.dept, SUM(e.base_salary) FROM payroll p "
            "JOIN employees e ON e.emp_id = p.emp_id "
            "WHERE p.month = ? AND p.status = 'REVERSED' GROUP BY e.dept",
            (bench.MONTH,),
        )
    }


def source_specs() -> tuple[SourceSpec, ...]:
    return (
        SourceSpec(
            source_id="hr_payroll",
            snapshot_ref=f"sqlite://payroll.db/employees?month={bench.MONTH}",
            period=bench.MONTH,
            unit="CNY",
            boundary="obligation view from the employee roster",
            expected_items=DEPARTMENTS + ("Contractors",),
            allowed_tools=("read_employees",),
            authority_scope=("read:employees",),
        ),
        SourceSpec(
            source_id="bank_ledger",
            snapshot_ref=f"sqlite://payroll.db/paid-payslips?month={bench.MONTH}",
            period=bench.MONTH,
            unit="CNY",
            boundary="money-out view from PAID payslips only",
            expected_items=DEPARTMENTS,
            allowed_tools=("read_paid_payslips",),
            authority_scope=("read:payroll-ledger",),
        ),
        SourceSpec(
            source_id="batch_artifacts",
            snapshot_ref=f"artifact://lecture-32/batches?month={bench.MONTH}",
            period=bench.MONTH,
            unit="CNY",
            boundary="department totals reported by delegated batch workers",
            expected_items=DEPARTMENTS,
            allowed_tools=("read_batch_artifacts",),
            authority_scope=("read:batch-artifacts",),
        ),
    )


def make_sources(con):
    specs = {source.source_id: source for source in source_specs()}

    async def hr_payroll(handoff, rows):
        items = gross_by_dept(con)
        items["Contractors"] = CONTRACTOR_POOL
        source = specs["hr_payroll"]
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

    async def bank_ledger(handoff, rows):
        source = specs["bank_ledger"]
        result = SourceResult.from_mapping(
            source_id=source.source_id,
            snapshot_ref=source.snapshot_ref,
            period=source.period,
            unit=source.unit,
            line_items=net_by_dept(con),
        )
        return bind_source_result(
            handoff,
            result,
            evidence_refs=(source.snapshot_ref,),
        )

    async def batch_artifacts(handoff, rows):
        source = specs["batch_artifacts"]
        result = SourceResult.from_mapping(
            source_id=source.source_id,
            snapshot_ref=source.snapshot_ref,
            period=source.period,
            unit=source.unit,
            line_items=gross_by_dept(con),
        )
        return bind_source_result(
            handoff,
            result,
            evidence_refs=(source.snapshot_ref,),
        )

    workers = {
        "hr_payroll": hr_payroll,
        "bank_ledger": bank_ledger,
        "batch_artifacts": batch_artifacts,
    }
    return tuple((source, workers[source.source_id]) for source in source_specs())


def sign_off_reviewer(report) -> tuple[str, ...]:
    findings = []
    for verdict in report.attributable_divergences:
        if abs(verdict.gap) > SIGN_OFF_THRESHOLD:
            findings.append(
                f"divergence on '{verdict.item}' (gap {verdict.gap:,.0f}) "
                "exceeds sign-off threshold; route to controller"
            )
    return tuple(findings)


def competing_gather(con, sources=None) -> FanOutGather:
    policy = AggregatorPolicy(
        strategy=Strategy.COMPETING,
        seam_reviewer=sign_off_reviewer,
        tolerance=Tolerance(absolute=1.0),
    )
    return FanOutGather(
        sources or make_sources(con),
        Reconciler(policy),
        SourceAdmissionPolicy(min_confidence=0.8),
        min_success_rate=0.95,
    )


def additive_gather(con) -> FanOutGather:
    policy = AggregatorPolicy(
        strategy=Strategy.ADDITIVE,
        contribution_rule=ContributionRule.SUM,
    )
    return FanOutGather(
        make_sources(con),
        Reconciler(policy),
        SourceAdmissionPolicy(min_confidence=0.8),
        min_success_rate=0.95,
    )


def run_competing(con):
    return asyncio.run(competing_gather(con).run(root_contract(), TASK_ROWS))


def run_with_dead_bank(con):
    sources = list(make_sources(con))

    async def dead(handoff, rows):
        raise RuntimeError("bank API down")

    sources = [
        (source, dead if source.source_id == "bank_ledger" else worker)
        for source, worker in sources
    ]
    return asyncio.run(
        competing_gather(con, tuple(sources)).run(root_contract(), TASK_ROWS)
    )


def run_additive(con):
    return asyncio.run(additive_gather(con).run(root_contract(), TASK_ROWS))


def main() -> None:
    con = month_end()

    if "--additive" not in sys.argv:
        print("== scene 1: three source contracts, one typed gather ==")
        run = run_competing(con)
        report = run.report
        print(
            "   source receipts: "
            + ", ".join(
                f"{artifact.payload.source_id}={receipt.decision.value}"
                for artifact, receipt in zip(
                    run.source_artifacts,
                    run.source_receipts,
                    strict=True,
                )
            )
        )
        print(f"   agreed ({len(report.agreed_items)}): {list(report.agreed_items)}")
        for verdict in report.attributable_divergences:
            print(
                f"   attributable divergence: '{verdict.item}' "
                f"gap={verdict.gap:,.0f}"
            )
            print(
                f"      low  {list(verdict.low_sources)} -> "
                f"{min(verdict.values.values()):,.0f}"
            )
            print(
                f"      high {list(verdict.high_sources)} -> "
                f"{max(verdict.values.values()):,.0f}"
            )
        for verdict in report.to_human:
            if verdict.layer.value == "unexplained":
                print(f"   to human: '{verdict.item}' ({verdict.reason})")
        for finding in report.seam_findings:
            print(f"   seam reviewer: {finding}")
        print(f"   root receipt: {run.report_receipt.decision.value}")
        reversed_finance = reversed_by_dept(con)["Finance"]
        print(
            f"   ledger confirmation: REVERSED Finance={reversed_finance:,.0f}"
        )
        print("   -> the gather located the source boundary; an independent")
        print("      ledger query confirmed what produced the 38,444 gap.")

        print("\n== scene 2: the bank source dies; the floor holds ==")
        run = run_with_dead_bank(con)
        failed = next(
            artifact.payload
            for artifact in run.source_artifacts
            if artifact.payload.source_id == "bank_ledger"
        )
        print(f"   status: {run.report.status.value}")
        print(f"   missing required: {list(run.report.missing_required_sources)}")
        print(f"   bank failure: {failed.failure_code}")
        print(f"   root receipt: {run.report_receipt.decision.value}")

    else:
        print("== scene 3: competing answers declared additive ==")
        run = run_additive(con)
        report = run.report
        print(f"   merged['Finance']: {report.merged['Finance']:,.0f}")
        print(f"   total:             {report.total:,.0f}")
        print(f"   divergence items:  {len(report.verdicts)}")
        print(f"   root receipt:      {run.report_receipt.decision.value}")
        print("   -> the contract declared SUM, so every component behaved")
        print("      correctly while the disagreement channel disappeared.")


if __name__ == "__main__":
    main()
