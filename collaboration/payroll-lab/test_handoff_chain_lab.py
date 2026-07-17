"""Invariant tests for the lecture-35 handoff-chain lab."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


lab = _load(HERE / "handoff_chain_lab.py", "handoff_lab")
_hand = sys.modules["handoff_pattern"]

NET = 13_706_097.0
GROSS = 13_744_541.0


def test_clean_chain_pays_the_bank_sum_and_traces_every_stage():
    con = lab.month_end()
    baton, paid = lab.run_chain(con)
    assert baton.trace == ["intent", "settle", "fund_check", "pay", "receipt"]
    assert paid == {"total": NET, "lines": 798}
    assert baton.facts["paid_total"] == NET
    assert baton.facts["receipt_id"] == "rcpt-run-2026-06"


def test_dropped_handoff_fails_at_the_seam_that_dropped_it():
    con = lab.month_end()
    paid: dict = {}
    stages = lab.make_stages(con, paid)

    async def settle_forgets(b):
        return {"legs": [{"emp_id": "E0001", "amount": 8000.0}]}

    stages["settle"] = settle_forgets
    with pytest.raises(_hand.SeamError) as err:
        asyncio.run(lab.payroll_chain(stages).run(_hand.Baton(intent="disburse")))
    assert "stage 'settle'" in str(err.value) and "net_total" in str(err.value)
    assert paid == {}                       # pay never ran


def test_append_only_refuses_a_rewrite_of_a_committed_fact():
    con = lab.month_end()
    paid: dict = {}
    stages = lab.make_stages(con, paid)
    real_pay = stages["pay"]

    async def pay_rounds_down(b):
        delta = await real_pay(b)
        delta["facts"]["net_total"] = 13_706_000.0
        return delta

    stages["pay"] = pay_rounds_down
    with pytest.raises(_hand.SeamError) as err:
        asyncio.run(lab.payroll_chain(stages).run(_hand.Baton(intent="disburse")))
    assert "append-only" in str(err.value) and "net_total" in str(err.value)


def test_rewriting_the_same_value_is_not_flagged():
    """Documented subtlety: append-only compares values, so re-delivering an
    identical value passes. Provenance of a fact is therefore ambiguous when
    two stages deliver the same number."""
    con = lab.month_end()
    paid: dict = {}
    stages = lab.make_stages(con, paid)
    real_pay = stages["pay"]

    async def pay_restates(b):
        delta = await real_pay(b)
        delta["facts"]["net_total"] = b.facts["net_total"]   # same value again
        return delta

    stages["pay"] = pay_restates
    baton = asyncio.run(lab.payroll_chain(stages).run(_hand.Baton(intent="disburse")))
    assert baton.facts["paid_total"] == NET


def test_provides_can_be_satisfied_by_an_upstream_fact():
    """Documented pattern boundary: the exit seam accepts a promised key that
    is ALREADY on the baton, so a stage can 'deliver' without producing."""
    spec = _hand.StageSpec("noop", provides=("net_total",))
    baton = _hand.Baton(intent="x", facts={"net_total": 1.0})
    _hand.HandoffChain._apply(spec, baton, {})     # no delta, no SeamError
    assert baton.facts["net_total"] == 1.0


def test_wrong_value_sails_through_every_existence_seam():
    con = lab.month_end()
    baton, paid = lab.run_chain(con, settle_key="settle_from_obligation")
    assert baton.trace == ["intent", "settle", "fund_check", "pay", "receipt"]
    assert paid["total"] == GROSS
    assert paid["total"] - NET == 38_444.0     # lecture 34's money went out here


def test_semantic_seam_kills_the_wrong_value_at_settle():
    con = lab.month_end()
    with pytest.raises(_hand.SeamError) as err:
        lab.run_chain(con, settle_key="settle_from_obligation",
                      wrap=lab.guarded(lab.make_contracts(con)))
    msg = str(err.value)
    assert "stage 'settle'" in msg and "net_total" in msg
    assert "13,744,541.00" in msg and "13,706,097.00" in msg


def test_semantic_seam_passes_the_clean_chain_untouched():
    con = lab.month_end()
    baton, paid = lab.run_chain(con, wrap=lab.guarded(lab.make_contracts(con)))
    assert paid == {"total": NET, "lines": 798}
    assert baton.facts["receipt_id"] == "rcpt-run-2026-06"
