"""Lecture 35 hands-on: the settlement-to-payment chain, and what a seam
check does not check.

Runs the pattern from ../d-handoff-chain/pattern.py on the month-end
payroll bench (798 PAID, 2 REVERSED). The baton travels a line of five
specialists: intent -> settle -> fund_check -> pay -> receipt. Every seam
validates the Baton Contract (requires in, provides out, append-only).

    scene 1  the clean run: 798 pay lines settle to 13,706,097, funding
             is checked, payment executes, a receipt closes the chain.
             The trace names every stage that ran.
    scene 2  two seams doing their job: a settle that forgets to deliver
             net_total fails AT ITS OWN SEAM, named, before fund_check
             ever runs; a pay stage that tries to "round down" the
             committed net_total is refused -- the baton is append-only.
    scene 3  run with --wrong-value: settle computes net_total from the
             employees table (the obligation view, the same mistake
             lectures 33 and 34 chased). The key is present, every
             existence seam passes, and pay moves 13,744,541 -- the
             38,444 that lecture 34's review panel kept in the bank goes
             out the door here. This is G4 in stress_collab_gaps.py:
             the seam guaranteed delivery, not correctness. The lab's
             semantic seam layer then binds value contracts to the same
             chain, and the wrong number dies at settle's own seam.

The semantic layer is an adapter, not a pattern change: ValueContract +
guarded() wrap a StageFn and raise the pattern's own SeamError, so a
value violation reads exactly like a missing key -- named at the seam
that produced it. The contracts here (net_total must equal the bank's
PAID sum, funding_ok must be True) are teaching values bound to this
bench; a real chain gets them from the controlling ledger.

Everything is deterministic and reads the bench directly; no API key.
Run `python3 handoff_chain_lab.py` (add --wrong-value for scene 3).
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_hand = _load(HERE.parent / "d-handoff-chain" / "pattern.py", "handoff_pattern")
Baton = _hand.Baton
HandoffChain = _hand.HandoffChain
SeamError = _hand.SeamError
StageSpec = _hand.StageSpec

sys.path.insert(0, str(HERE.parent.parent / "reflection" / "payroll-lab"))
import bench  # noqa: E402

FUNDING_CAP = 14_000_000.0     # teaching value: what the payroll account can cover


def month_end():
    return bench.month_end_state()


def bank_net(con) -> float:
    return float(con.execute(
        "SELECT SUM(e.base_salary) FROM payroll p "
        "JOIN employees e ON e.emp_id = p.emp_id "
        "WHERE p.month = ? AND p.status = 'PAID'", (bench.MONTH,)).fetchone()[0])


# ---- the five specialists ------------------------------------------------------

def make_stages(con, paid: dict):
    async def intent(b):
        return {"facts": {"month": bench.MONTH, "run_id": f"run-{bench.MONTH}"}}

    async def settle(b):
        rows = con.execute(
            "SELECT e.emp_id, e.base_salary FROM payroll p "
            "JOIN employees e ON e.emp_id = p.emp_id "
            "WHERE p.month = ? AND p.status = 'PAID' ORDER BY e.emp_id",
            (b.facts["month"],)).fetchall()
        legs = [{"emp_id": e, "amount": float(s)} for e, s in rows]
        return {"facts": {"net_total": round(sum(l["amount"] for l in legs), 2)},
                "legs": legs}

    async def settle_from_obligation(b):
        # Lectures 33/34's author, one stage further downstream: the run is
        # computed from the employees table, so the total carries the two
        # REVERSED payslips. The KEY it promised is delivered; the value is
        # wrong by 38,444.
        rows = con.execute(
            "SELECT emp_id, base_salary FROM employees ORDER BY emp_id").fetchall()
        legs = [{"emp_id": e, "amount": float(s)} for e, s in rows]
        return {"facts": {"net_total": round(sum(l["amount"] for l in legs), 2)},
                "legs": legs}

    async def fund_check(b):
        return {"facts": {"funding_ok": b.facts["net_total"] <= FUNDING_CAP}}

    async def pay(b):
        # Deliberately trusts the baton: the seam guaranteed net_total and
        # funding_ok EXIST. Nothing here re-derives whether they are right.
        paid["total"] = b.facts["net_total"]
        paid["lines"] = len(b.legs)
        return {"facts": {"paid_total": b.facts["net_total"]}}

    async def receipt(b):
        return {"facts": {"receipt_id": f"rcpt-{b.facts['run_id']}"}}

    return {"intent": intent, "settle": settle,
            "settle_from_obligation": settle_from_obligation,
            "fund_check": fund_check, "pay": pay, "receipt": receipt}


SPECS = [
    StageSpec("intent", provides=("month", "run_id")),
    StageSpec("settle", requires=("month",), provides=("net_total",)),
    StageSpec("fund_check", requires=("net_total",), provides=("funding_ok",)),
    StageSpec("pay", requires=("net_total", "funding_ok"), provides=("paid_total",)),
    StageSpec("receipt", requires=("paid_total",), provides=("receipt_id",)),
]


def payroll_chain(stages: dict, *, settle_key: str = "settle",
                  wrap: Callable | None = None) -> HandoffChain:
    picked = []
    for spec in SPECS:
        fn = stages[settle_key] if spec.name == "settle" else stages[spec.name]
        picked.append((spec, wrap(spec, fn) if wrap else fn))
    return HandoffChain(picked)


# ---- the semantic seam: value contracts on top of existence checks --------------

@dataclass(frozen=True)
class ValueContract:
    """The other half of the Baton Contract: not 'was the key delivered'
    but 'is the value the one the controlling ledger would accept'."""

    key: str
    describe: str
    check: Callable[[Any], str | None]   # a finding, or None when the value holds


def make_contracts(con) -> list[ValueContract]:
    net = bank_net(con)
    return [
        ValueContract(
            key="net_total",
            describe="net_total must equal the bank's PAID sum",
            check=lambda v: None if abs(v - net) <= 0.005
            else f"got {v:,.2f}, bank PAID sum is {net:,.2f}"),
        ValueContract(
            key="funding_ok",
            describe="payment may only run on a positive funding check",
            check=lambda v: None if v is True else f"got {v!r}"),
    ]


def guarded(contracts: list[ValueContract]):
    """Wrap a StageFn so the values it delivers are checked at ITS seam.
    Violations raise the pattern's own SeamError: a wrong value reads
    exactly like a missing key, named where it was produced."""
    by_key = {c.key: c for c in contracts}

    def wrap(spec: StageSpec, fn):
        async def stage(baton):
            delta = await fn(baton) or {}
            for key, value in delta.get("facts", {}).items():
                contract = by_key.get(key)
                if contract is None:
                    continue
                finding = contract.check(value)
                if finding:
                    raise SeamError(f"stage '{spec.name}' delivered '{key}' but the "
                                    f"value fails its contract: {finding} "
                                    f"({contract.describe})")
            return delta
        return stage
    return wrap


# ---- scenes ----------------------------------------------------------------------

def run_chain(con, *, settle_key: str = "settle", wrap=None) -> tuple[Baton, dict]:
    paid: dict = {}
    chain = payroll_chain(make_stages(con, paid), settle_key=settle_key, wrap=wrap)
    baton = asyncio.run(chain.run(Baton(intent=f"disburse {bench.MONTH} salaries")))
    return baton, paid


def main() -> None:
    con = month_end()

    if "--wrong-value" not in sys.argv:
        print("== scene 1: the clean run, intent to receipt ==")
        baton, paid = run_chain(con)
        print(f"   trace: {' -> '.join(baton.trace)}")
        print(f"   paid {paid['lines']} lines, total {paid['total']:,.2f}")
        print(f"   receipt: {baton.facts['receipt_id']}")

        print("\n== scene 2: two seams doing their job ==")
        paid2: dict = {}
        stages = make_stages(con, paid2)

        async def settle_forgets(b):
            return {"legs": [{"emp_id": "E0001", "amount": 8000.0}]}   # no net_total

        stages["settle"] = settle_forgets
        try:
            asyncio.run(payroll_chain(stages).run(Baton(intent="disburse")))
        except SeamError as e:
            print(f"   dropped handoff: {e}")
        print(f"   -> named at settle's own seam; pay never ran "
              f"(paid={paid2 or 'nothing'})")

        paid3: dict = {}
        stages = make_stages(con, paid3)
        real_pay = stages["pay"]

        async def pay_rounds_down(b):
            delta = await real_pay(b)
            delta["facts"]["net_total"] = float(int(b.facts["net_total"]) // 1000 * 1000)
            return delta

        stages["pay"] = pay_rounds_down
        try:
            asyncio.run(payroll_chain(stages).run(Baton(intent="disburse")))
        except SeamError as e:
            print(f"   overwrite refused: {e}")
        print("   -> a later stage may add facts, never rewrite a committed one")

    else:
        print("== scene 3 (--wrong-value): the key is there, the value is wrong ==")
        baton, paid = run_chain(con, settle_key="settle_from_obligation")
        print(f"   trace: {' -> '.join(baton.trace)}  (every seam passed)")
        print(f"   paid {paid['lines']} lines, total {paid['total']:,.2f}")
        print(f"   -> 38,444 more than the bank's PAID sum: the two REVERSED")
        print(f"      payslips lecture 34's panel kept in the bank just went out.")
        print(f"      The seam guaranteed 'net_total was delivered', never that")
        print(f"      it was right. (G4 in stress_collab_gaps.py.)")

        print("\n   same chain, semantic seam bound to the controlling ledger:")
        try:
            run_chain(con, settle_key="settle_from_obligation",
                      wrap=guarded(make_contracts(con)))
        except SeamError as e:
            print(f"   {e}")
        print("   -> the wrong number dies at settle's own seam; pay never ran")


if __name__ == "__main__":
    main()
