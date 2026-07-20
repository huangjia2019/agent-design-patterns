"""Invariant tests for the lecture-38 budget-envelope lab."""
from __future__ import annotations

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


lab = load_module(HERE / "budget_envelope_lab.py", "budget_envelope_lab")
_bc = sys.modules["collaboration.boundary_contract"]

APPROVED = 13_706_097.0
OPS_TOTAL = 2_748_960.0
OPS_COUNT = 160


def test_department_reservations_partition_the_approved_root():
    con = lab.month_end()
    book = lab.build_book(con)
    assert book.reserved_amount() == APPROVED == book.root.max_amount
    assert book.reserved_payments() == 798 == book.root.max_payments
    assert len(book.root.allowed_refs) == 798


def test_the_retry_storm_without_envelopes_overpays_the_ops_total_four_times():
    con = lab.month_end()
    payments, refusals = lab.execute_settlement(lab.dept_batches(con),
                                                book=None)
    assert refusals == []
    assert lab.paid_total(payments) == APPROVED + 4 * OPS_TOTAL
    assert lab.paid_total(payments) == 24_701_937.0


def test_the_same_storm_with_envelopes_pays_the_approved_amount_exactly():
    con = lab.month_end()
    book = lab.build_book(con)
    payments, refusals = lab.execute_settlement(lab.dept_batches(con),
                                                book=book)
    assert lab.paid_total(payments) == APPROVED
    assert len(refusals) == 4 * OPS_COUNT
    codes = {f.code for d in refusals for f in d.findings}
    assert codes == {"envelope_amount_exceeded", "envelope_count_exceeded"}


def test_a_reservation_beyond_the_full_root_is_refused_at_reserve_time():
    con = lab.month_end()
    book = lab.build_book(con)
    findings = book.reserve(lab.BudgetEnvelope(
        envelope_id="env::retro", holder="payroll-agent",
        max_amount=5_000_000, max_payments=2,
        allowed_refs=frozenset({"E0007", "E0012"})))
    codes = {f.code for f in findings}
    assert "reservation_over_parent" in codes
    assert "reservation_out_of_scope" in codes  # reversed slips not in root
    amount = next(f for f in findings
                  if f.code == "reservation_over_parent"
                  and f.field == "max_amount")
    assert "parent_remaining=0" in amount.evidence


def test_a_child_may_only_narrow_the_parent_scope():
    con = lab.month_end()
    book = lab.build_book(con)
    findings = book.reserve(lab.BudgetEnvelope(
        envelope_id="env::contractor", holder="payroll-agent",
        max_amount=0.0, max_payments=0,
        allowed_refs=frozenset({"X9999"})))
    scope = next(f for f in findings
                 if f.code == "reservation_out_of_scope")
    assert "X9999" in scope.evidence


def test_a_draw_outside_the_envelope_scope_is_refused():
    con = lab.month_end()
    book = lab.build_book(con)
    sales_emp = dict(lab.dept_batches(con))["Sales"][0][0]
    decision = book.draw("env::Ops", sales_emp, 1.0)
    assert not decision.admitted
    (finding,) = decision.findings
    assert finding.code == "envelope_object_out_of_scope"
    assert "env::Ops" in finding.evidence and sales_emp in finding.evidence


def test_the_amount_and_count_axes_refuse_independently():
    root = lab.BudgetEnvelope("env::r", "t", 1_000.0, 10,
                              frozenset({"A", "B"}))
    book = lab.BudgetBook(root)
    assert book.reserve(lab.BudgetEnvelope(
        "env::c", "t", 100.0, 1, frozenset({"A"}))) == ()
    first = book.draw("env::c", "A", 40.0)
    assert first.admitted
    second = book.draw("env::c", "A", 40.0)  # amount fits, count is spent
    assert {f.code for f in second.findings} == {"envelope_count_exceeded"}
    assert book.reserve(lab.BudgetEnvelope(
        "env::d", "t", 100.0, 5, frozenset({"B"}))) == ()
    book.draw("env::d", "B", 60.0)
    over = book.draw("env::d", "B", 50.0)  # count fits, amount does not
    assert {f.code for f in over.findings} == {"envelope_amount_exceeded"}
    assert "remaining=40" in over.findings[0].evidence


def test_a_draw_on_an_unreserved_envelope_is_refused():
    con = lab.month_end()
    book = lab.build_book(con)
    decision = book.draw("env::ghost", "E0001", 1.0)
    assert not decision.admitted
    assert decision.findings[0].code == "envelope_unknown"


def test_every_refusal_is_a_blocker_with_evidence():
    con = lab.month_end()
    book = lab.build_book(con)
    _, refusals = lab.execute_settlement(lab.dept_batches(con), book=book)
    assert refusals
    for decision in refusals:
        for finding in decision.findings:
            assert finding.severity is _bc.FindingSeverity.BLOCKER
            assert finding.evidence.strip()
