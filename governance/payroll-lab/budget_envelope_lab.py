"""Lecture 38 hands-on: how much can one bug spend before anything stops it?

Three scenes on the month-end payroll world, no API key, no database
damage (payments are simulated in memory). Every import here is
committed code; the b-blast-radius pattern industrializes what scene 2
sketches.

    scene 1  the unbounded rerun: the CFO ticket from lecture 37
             approved 13,706,097. Then a retry bug re-executes the Ops
             batch four extra times. Every admission gate this course
             shipped -- the 3,000,000 batch line, the 13,000,000 cash
             line, the funding cap, the approval ticket -- stays green,
             because every one of them reads CLAIMED amounts before
             execution. Actual money out: 24,701,937. The blast radius
             of one bug is the whole ledger.
    scene 2  the envelope tree: the approved amount becomes the root
             BudgetEnvelope; each department reserves a child envelope
             (amount, payment count, allowed employee ids). A child can
             only narrow its parent. Execution draws from the envelope
             BEFORE money moves. The same retry bug now dies on its
             first extra draw: paid stays 13,706,097, and the damage
             shows up as refusals naming the envelope, not as money.
    scene 3  the three axes: amount, count, and object scope refuse
             independently. A sixth 5,000,000 "retro" reservation dies
             at reserve time because the root is fully partitioned --
             the sum-blind gap from lecture 32 becomes structurally
             impossible. A contractor outside the root roster cannot
             even be reserved for; a Sales employee cannot be paid
             through the Ops envelope.

Totals are computed from the bench ledger, not typed in. The envelope
book is a teaching minimum: no persistence, no concurrent draws, no
release/return of unused reservation, no exclusive-partition check
between siblings. Those belong to the pattern, not the intro lab.

Run `python3 budget_envelope_lab.py` from the repo root.
"""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Lecture 37's lab already chains to lecture 36's, the committed
# delegation pattern and the bench. Build on it with one import.
_lab37 = load_module(HERE / "approval_ticket_lab.py", "lab37_dep")
month_end = _lab37.month_end
settle_rows = _lab37.settle_rows
settle_total = _lab37.settle_total
MONTH = _lab37.MONTH

_bc = sys.modules["collaboration.boundary_contract"]
Finding = _bc.Finding
FindingSeverity = _bc.FindingSeverity

RETRY_STORM = ("Ops", 4)  # the buggy executor re-runs Ops four extra times


# ---- the settlement, grouped the way execution runs it --------------------------

def dept_batches(con) -> tuple[tuple[str, tuple[tuple[str, float], ...]], ...]:
    """PAID slips grouped by department: (dept, ((emp_id, amount), ...))."""
    batches: dict[str, list[tuple[str, float]]] = {}
    for dept, emp, amount in con.execute(
        "SELECT e.dept, p.emp_id, p.base + p.bonus + p.adjustment "
        "FROM payroll p JOIN employees e ON e.emp_id = p.emp_id "
        "WHERE p.month = ? AND p.status = 'PAID' "
        "ORDER BY e.dept, p.emp_id", (MONTH,)):
        batches.setdefault(dept, []).append((emp, float(amount)))
    return tuple((dept, tuple(rows)) for dept, rows in batches.items())


# ---- scene 2: the envelope tree -------------------------------------------------

@dataclass(frozen=True)
class BudgetEnvelope:
    """A pre-authorized spending boundary on three axes: how much money,
    how many payments, and exactly which employees."""

    envelope_id: str
    holder: str
    max_amount: float
    max_payments: int
    allowed_refs: frozenset


@dataclass
class EnvelopeState:
    envelope: BudgetEnvelope
    spent: float = 0.0
    payments: int = 0


@dataclass(frozen=True)
class DrawDecision:
    envelope_id: str
    ref: str
    amount: float
    admitted: bool
    findings: tuple


class BudgetBook:
    """Root envelope plus child reservations. A child can only narrow
    its parent; a draw must fit its envelope before money moves."""

    def __init__(self, root: BudgetEnvelope) -> None:
        self.root = root
        self._children: dict[str, EnvelopeState] = {}

    def reserved_amount(self) -> float:
        return sum(s.envelope.max_amount for s in self._children.values())

    def reserved_payments(self) -> int:
        return sum(s.envelope.max_payments for s in self._children.values())

    def reserve(self, child: BudgetEnvelope) -> tuple:
        findings = []
        remaining = self.root.max_amount - self.reserved_amount()
        if child.max_amount > remaining:
            findings.append(Finding(
                code="reservation_over_parent", field="max_amount",
                message="the child envelope does not fit the parent",
                evidence=f"child={child.max_amount:,.0f} "
                         f"parent_remaining={remaining:,.0f}"))
        if child.max_payments > self.root.max_payments - self.reserved_payments():
            findings.append(Finding(
                code="reservation_over_parent", field="max_payments",
                message="the child payment count does not fit the parent",
                evidence=f"child={child.max_payments} parent_remaining="
                         f"{self.root.max_payments - self.reserved_payments()}"))
        outside = child.allowed_refs - self.root.allowed_refs
        if outside:
            findings.append(Finding(
                code="reservation_out_of_scope", field="allowed_refs",
                message="a child may only narrow the parent scope",
                evidence=f"refs_outside_parent={sorted(outside)}"))
        if not findings:
            self._children[child.envelope_id] = EnvelopeState(child)
        return tuple(findings)

    def draw(self, envelope_id: str, ref: str, amount: float) -> DrawDecision:
        state = self._children.get(envelope_id)
        if state is None:
            return DrawDecision(envelope_id, ref, amount, False, (Finding(
                code="envelope_unknown", field="envelope_id",
                message="no reservation exists for this envelope",
                evidence=f"envelope_id={envelope_id}"),))
        findings = []
        env = state.envelope
        if ref not in env.allowed_refs:
            findings.append(Finding(
                code="envelope_object_out_of_scope", field="ref",
                message="this employee is outside the envelope scope",
                evidence=f"envelope={envelope_id} ref={ref}"))
        if state.spent + amount > env.max_amount:
            findings.append(Finding(
                code="envelope_amount_exceeded", field="amount",
                message="the draw does not fit the envelope",
                evidence=f"draw={amount:,.0f} "
                         f"remaining={env.max_amount - state.spent:,.0f}"))
        if state.payments + 1 > env.max_payments:
            findings.append(Finding(
                code="envelope_count_exceeded", field="payments",
                message="the envelope has no payments left",
                evidence=f"max_payments={env.max_payments}"))
        if findings:
            return DrawDecision(envelope_id, ref, amount, False,
                                tuple(findings))
        state.spent += amount
        state.payments += 1
        return DrawDecision(envelope_id, ref, amount, True, ())


# ---- the executor, with and without envelopes -----------------------------------

def execute_settlement(batches, *, book: BudgetBook | None = None,
                       retry_storm=RETRY_STORM):
    """Simulate the bank executor. The bug: one department's batch is
    re-executed `extra` more times. Returns (payments, refusals)."""
    storm_dept, extra = retry_storm
    payments: list[tuple[str, str, float]] = []
    refusals: list[DrawDecision] = []
    for dept, rows in batches:
        runs = 1 + (extra if dept == storm_dept else 0)
        for _ in range(runs):
            for emp, amount in rows:
                if book is None:
                    payments.append((dept, emp, amount))
                    continue
                decision = book.draw(f"env::{dept}", emp, amount)
                if decision.admitted:
                    payments.append((dept, emp, amount))
                else:
                    refusals.append(decision)
    return payments, refusals


def paid_total(payments) -> float:
    return sum(amount for _, _, amount in payments)


def build_book(con) -> BudgetBook:
    """The approved settlement becomes the root; departments reserve."""
    rows = settle_rows(con)
    root = BudgetEnvelope(
        envelope_id=f"env::root::{MONTH}", holder="cfo",
        max_amount=settle_total(con), max_payments=len(rows),
        allowed_refs=frozenset(emp for emp, _ in rows))
    book = BudgetBook(root)
    for dept, batch in dept_batches(con):
        findings = book.reserve(BudgetEnvelope(
            envelope_id=f"env::{dept}", holder=f"supervisor::{dept}",
            max_amount=sum(a for _, a in batch), max_payments=len(batch),
            allowed_refs=frozenset(emp for emp, _ in batch)))
        assert findings == (), findings
    return book


# ---- scenes ---------------------------------------------------------------------

def main() -> None:
    con = month_end()
    batches = dept_batches(con)
    approved = settle_total(con)
    print(f"== scene 1: the unbounded rerun "
          f"(approved {approved:,.0f}, retry storm on Ops x4) ==")
    payments, _ = execute_settlement(batches, book=None)
    print(f"   money out without envelopes: {paid_total(payments):,.0f}")
    print(f"   overpay: {paid_total(payments) - approved:,.0f}")
    print("   -> 37 讲的票据批的是 13,706,097 这个数。执行中把 Ops 批次多跑了")
    print("      四遍，没有任何一道已提交的闸响：批次线、现金线、资金帽、票据，")
    print("      读的全是执行前的申报数。一个重试 bug 的半径是整本台账。")

    print("\n== scene 2: the envelope tree, same bug ==")
    book = build_book(con)
    for dept, batch in dept_batches(con):
        total = sum(a for _, a in batch)
        print(f"   env::{dept:<12} {len(batch):>3} refs  {total:>12,.0f}")
    payments, refusals = execute_settlement(batches, book=book)
    print(f"   money out with envelopes: {paid_total(payments):,.0f}")
    print(f"   refused draws: {len(refusals)}")
    first = refusals[0]
    print(f"      first refusal: {first.findings[0].code} :: "
          f"{first.findings[0].evidence}")
    print("   -> 同一个 bug。钱只出去了批准过的那个数，多出来的四遍全部变成")
    print("      拒绝记录。爆炸半径从整本台账缩成了零，损失换了形态：从钱")
    print("      变成了 finding。")

    print("\n== scene 3: three axes, and the root is full ==")
    retro = book.reserve(BudgetEnvelope(
        envelope_id="env::retro", holder="payroll-agent",
        max_amount=5_000_000, max_payments=2,
        allowed_refs=frozenset(bench_reversed())))
    print(f"   reserve env::retro 5,000,000 -> {retro[0].code} :: "
          f"{retro[0].evidence}")
    contractor = book.reserve(BudgetEnvelope(
        envelope_id="env::contractor", holder="payroll-agent",
        max_amount=0.0, max_payments=1, allowed_refs=frozenset({"X9999"})))
    codes = ",".join(f.code for f in contractor)
    print(f"   reserve env::contractor for X9999 -> {codes}")
    sales_emp = dept_batches(con)[3][1][0][0]
    cross = book.draw("env::Ops", sales_emp, 1.0)
    print(f"   draw {sales_emp} through env::Ops -> "
          f"{cross.findings[0].code}")
    print("   -> 32 讲那个盲区：五个批各自合规、总和越线。在信封树里它到不了")
    print("      执行，预留的时候父信封就满了。金额、次数、对象三个维度各自")
    print("      把门，谁被破就报谁的名字。")


def bench_reversed():
    return _lab37.bench.REVERSED_IDS


if __name__ == "__main__":
    main()
