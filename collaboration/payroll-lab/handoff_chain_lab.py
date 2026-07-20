"""Lecture 35 lab: a contract-bound payroll handoff chain.

Five specialists move one immutable baton from intent to receipt:

``intent -> settle -> fund_check -> pay -> receipt``

The normal run commits 798 pay lines and 13,706,097. Scene 2 demonstrates exact
delivery and field ownership. ``--wrong-value`` compares a thin existence contract
with the release contract: the thin contract accepts 13,744,541, while the release
contract rejects the same value at the settlement seam before payment runs.
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path


HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


handoff = load_module(
    HERE.parent / "d-handoff-chain" / "pattern.py",
    "handoff_pattern",
)
FactRule = handoff.FactRule
FactValue = handoff.FactValue
HandoffChain = handoff.HandoffChain
SeamError = handoff.SeamError
StageBinding = handoff.StageBinding
StageDelta = handoff.StageDelta
StageSpec = handoff.StageSpec
TaskContract = handoff.TaskContract
new_baton = handoff.new_baton

sys.path.insert(0, str(HERE.parent.parent / "reflection" / "payroll-lab"))
import bench  # noqa: E402


FUNDING_CAP = 14_000_000.0


@dataclass(frozen=True)
class PayLine:
    emp_id: str
    amount: float


def month_end():
    return bench.month_end_state()


def payroll_contract() -> TaskContract:
    return TaskContract(
        contract_id=f"payroll-handoff-{bench.MONTH}",
        version=1,
        objective="move one reviewed salary run from intent to receipt",
        output_schema="PayrollBaton",
        accountable_owner="payroll-controller",
        input_refs=(f"sqlite://payroll.db?month={bench.MONTH}",),
        constraints=(
            "settlement must match the PAID ledger",
            "payment requires a positive funding check",
            "each fact has one owning stage",
        ),
        authority_scope=("read:payroll", "propose:payment"),
        boundary="each specialist commits only its declared facts",
    )


def bank_net(con) -> float:
    return float(
        con.execute(
            "SELECT SUM(e.base_salary) FROM payroll p "
            "JOIN employees e ON e.emp_id = p.emp_id "
            "WHERE p.month = ? AND p.status = 'PAID'",
            (bench.MONTH,),
        ).fetchone()[0]
    )


def paid_lines(con) -> tuple[PayLine, ...]:
    return tuple(
        PayLine(emp_id, float(amount))
        for emp_id, amount in con.execute(
            "SELECT e.emp_id, e.base_salary FROM payroll p "
            "JOIN employees e ON e.emp_id = p.emp_id "
            "WHERE p.month = ? AND p.status = 'PAID' ORDER BY e.emp_id",
            (bench.MONTH,),
        )
    )


def obligation_lines(con) -> tuple[PayLine, ...]:
    return tuple(
        PayLine(emp_id, float(amount))
        for emp_id, amount in con.execute(
            "SELECT emp_id, base_salary FROM employees ORDER BY emp_id"
        )
    )


SPECS = (
    StageSpec("intent", provides=("month", "run_id")),
    StageSpec(
        "settle",
        requires=("month",),
        provides=("net_total", "pay_lines"),
    ),
    StageSpec(
        "fund_check",
        requires=("net_total",),
        provides=("funding_ok",),
    ),
    StageSpec(
        "pay",
        requires=("net_total", "pay_lines", "funding_ok"),
        provides=("paid_total", "payment_id"),
    ),
    StageSpec(
        "receipt",
        requires=("run_id", "paid_total", "payment_id"),
        provides=("receipt_id",),
    ),
)


def make_stages(con, paid: dict, *, settlement: str = "paid"):
    async def intent(view):
        return StageDelta(
            facts=(
                FactValue(
                    "month",
                    bench.MONTH,
                    (f"request://payroll/{bench.MONTH}",),
                ),
                FactValue(
                    "run_id",
                    f"run-{bench.MONTH}",
                    (f"request://payroll/{bench.MONTH}",),
                ),
            )
        )

    async def settle(view):
        lines = (
            paid_lines(con)
            if settlement == "paid"
            else obligation_lines(con)
        )
        total = round(sum(line.amount for line in lines), 2)
        source = (
            "paid-ledger"
            if settlement == "paid"
            else "employee-obligation"
        )
        evidence = (f"sqlite://payroll.db/{source}?month={bench.MONTH}",)
        return StageDelta(
            facts=(
                FactValue("net_total", total, evidence),
                FactValue("pay_lines", lines, evidence),
            ),
            artifact_refs=(f"artifact://payrun/{bench.MONTH}/{source}",),
        )

    async def fund_check(view):
        total = view.facts["net_total"]
        return StageDelta(
            facts=(
                FactValue(
                    "funding_ok",
                    total <= FUNDING_CAP,
                    ("treasury://payroll-account/available",),
                ),
            )
        )

    async def pay(view):
        payment_id = f"payment-{bench.MONTH}"
        paid.setdefault(
            view.stage_run_id,
            {
                "total": view.facts["net_total"],
                "lines": len(view.facts["pay_lines"]),
                "payment_id": payment_id,
            },
        )
        return StageDelta(
            facts=(
                FactValue(
                    "paid_total",
                    view.facts["net_total"],
                    (f"payment://{payment_id}",),
                ),
                FactValue(
                    "payment_id",
                    payment_id,
                    (f"payment://{payment_id}",),
                ),
            )
        )

    async def receipt(view):
        receipt_id = f"rcpt-{view.facts['run_id']}"
        return StageDelta(
            facts=(
                FactValue(
                    "receipt_id",
                    receipt_id,
                    (f"receipt://{receipt_id}",),
                ),
            )
        )

    return {
        "intent": intent,
        "settle": settle,
        "fund_check": fund_check,
        "pay": pay,
        "receipt": receipt,
    }


def payroll_rules(con, *, semantic: bool) -> tuple[FactRule, ...]:
    expected_total = bank_net(con)

    def net_total_rule(value, view):
        if not semantic or abs(value - expected_total) <= 0.005:
            return None
        return (
            f"got {value:,.2f}, bank PAID sum is "
            f"{expected_total:,.2f}"
        )

    def funding_rule(value, view):
        if not semantic or value is True:
            return None
        return f"funding_ok must be True, got {value!r}"

    def paid_total_rule(value, view):
        expected = view.facts["net_total"]
        if not semantic or abs(value - expected) <= 0.005:
            return None
        return f"paid_total={value:,.2f}, net_total={expected:,.2f}"

    return (
        FactRule("month", "intent", str),
        FactRule("run_id", "intent", str),
        FactRule(
            "net_total",
            "settle",
            float,
            validator=net_total_rule,
        ),
        FactRule("pay_lines", "settle", tuple),
        FactRule(
            "funding_ok",
            "fund_check",
            bool,
            validator=funding_rule,
        ),
        FactRule(
            "paid_total",
            "pay",
            float,
            validator=paid_total_rule,
        ),
        FactRule("payment_id", "pay", str),
        FactRule("receipt_id", "receipt", str),
    )


def payroll_chain(
    con,
    paid: dict,
    *,
    semantic: bool,
    settlement: str = "paid",
    replacements: dict | None = None,
) -> HandoffChain:
    stages = make_stages(con, paid, settlement=settlement)
    stages.update(replacements or {})
    return HandoffChain(
        payroll_contract(),
        tuple(
            StageBinding(spec, stages[spec.name])
            for spec in SPECS
        ),
        payroll_rules(con, semantic=semantic),
        chain_id="payroll-handoff-chain",
    )


def run_chain(
    con,
    *,
    semantic: bool = True,
    settlement: str = "paid",
    replacements: dict | None = None,
):
    paid: dict = {}
    chain = payroll_chain(
        con,
        paid,
        semantic=semantic,
        settlement=settlement,
        replacements=replacements,
    )
    result = asyncio.run(
        chain.run(
            new_baton(
                payroll_contract(),
                baton_id=f"payroll-{bench.MONTH}",
                intent=f"disburse {bench.MONTH} salaries",
            )
        )
    )
    return result, paid


def payment_record(paid: dict) -> dict:
    return next(iter(paid.values()))


def main() -> None:
    con = month_end()

    if "--wrong-value" not in sys.argv:
        print("== scene 1: the clean run, intent to receipt ==")
        result, paid = run_chain(con)
        payment = payment_record(paid)
        print(f"   trace: {' -> '.join(result.baton.trace)}")
        print(
            f"   revisions: 0 -> {result.baton.revision}, "
            f"stage receipts={len(result.receipts)}"
        )
        print(
            f"   paid {payment['lines']} lines, "
            f"total {payment['total']:,.2f}"
        )
        print(f"   receipt: {result.baton.facts['receipt_id']}")
        print(
            f"   acceptance={result.acceptance_receipt.decision.value} "
            f"artifact={result.acceptance_receipt.artifact_id}"
        )

        print("\n== scene 2: exact delivery and ownership ==")

        async def settle_forgets_total(view):
            lines = paid_lines(con)
            return StageDelta(
                facts=(
                    FactValue(
                        "pay_lines",
                        lines,
                        (f"sqlite://payroll.db/paid?month={bench.MONTH}",),
                    ),
                )
            )

        try:
            run_chain(
                con,
                replacements={"settle": settle_forgets_total},
            )
        except SeamError as exc:
            print(f"   dropped handoff: {exc}")
            print(
                f"   checkpoint={exc.checkpoint.snapshot_id} "
                f"trace={list(exc.checkpoint.trace)}"
            )

        async def pay_restates_total(view):
            return StageDelta(
                facts=(
                    FactValue(
                        "paid_total",
                        view.facts["net_total"],
                        ("payment://attempt",),
                    ),
                    FactValue(
                        "payment_id",
                        f"payment-{bench.MONTH}",
                        ("payment://attempt",),
                    ),
                    FactValue(
                        "net_total",
                        view.facts["net_total"],
                        ("payment://attempt",),
                    ),
                )
            )

        try:
            run_chain(
                con,
                replacements={"pay": pay_restates_total},
            )
        except SeamError as exc:
            print(f"   ownership refused: {exc}")
    else:
        print("== scene 3: the key exists, the contract is too thin ==")
        result, paid = run_chain(
            con,
            semantic=False,
            settlement="obligation",
        )
        payment = payment_record(paid)
        print(
            f"   thin contract: acceptance="
            f"{result.acceptance_receipt.decision.value}"
        )
        print(
            f"   paid {payment['lines']} lines, "
            f"total {payment['total']:,.2f}"
        )
        print(
            "   -> every stage delivered the declared key and type; "
            "the contract omitted the controlling-ledger rule."
        )

        print("\n   same stages under payroll-release semantics:")
        strict_paid: dict = {}
        strict_chain = payroll_chain(
            con,
            strict_paid,
            semantic=True,
            settlement="obligation",
        )
        try:
            asyncio.run(
                strict_chain.run(
                    new_baton(
                        payroll_contract(),
                        baton_id=f"payroll-{bench.MONTH}-strict",
                        intent=f"disburse {bench.MONTH} salaries",
                    )
                )
            )
        except SeamError as exc:
            print(f"   {exc}")
            print(
                f"   checkpoint revision={exc.checkpoint.revision} "
                f"trace={list(exc.checkpoint.trace)}"
            )
        print(f"   payment side effects={strict_paid or 'none'}")


if __name__ == "__main__":
    main()
