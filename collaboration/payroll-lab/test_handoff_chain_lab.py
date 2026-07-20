"""End-to-end checks for the lecture 35 handoff-chain lab."""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest


HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab = load_module(HERE / "handoff_chain_lab.py", "handoff_lab")
handoff = sys.modules["handoff_pattern"]

NET = 13_706_097.0
GROSS = 13_744_541.0


def test_clean_chain_pays_the_controlling_ledger_and_seals_receipts() -> None:
    con = lab.month_end()
    result, paid = lab.run_chain(con)
    payment = lab.payment_record(paid)

    assert result.baton.trace == (
        "intent",
        "settle",
        "fund_check",
        "pay",
        "receipt",
    )
    assert result.baton.revision == 5
    assert len(result.receipts) == 5
    assert result.baton.stage_receipts == result.receipts
    assert payment == {
        "total": NET,
        "lines": 798,
        "payment_id": "payment-2026-06",
    }
    assert result.baton.facts["paid_total"] == NET
    assert result.baton.facts["receipt_id"] == "rcpt-run-2026-06"
    assert result.acceptance_receipt.accepted
    assert result.acceptance_receipt.artifact_id == result.baton.snapshot_id


def test_settlement_receipt_binds_owned_facts_and_evidence() -> None:
    con = lab.month_end()
    result, _ = lab.run_chain(con)
    receipt = result.receipts[1]

    assert receipt.stage_name == "settle"
    assert receipt.consumed_keys == ("month",)
    assert receipt.produced_keys == ("net_total", "pay_lines")
    assert receipt.evidence_refs == (
        "sqlite://payroll.db/paid-ledger?month=2026-06",
    )
    assert result.baton.fact_record("net_total").producer_stage == "settle"


def test_dropped_handoff_fails_at_settlement_checkpoint() -> None:
    con = lab.month_end()

    async def settle_forgets_total(view):
        return handoff.StageDelta(
            facts=(
                handoff.FactValue(
                    "pay_lines",
                    lab.paid_lines(con),
                    ("sqlite://paid-lines",),
                ),
            )
        )

    with pytest.raises(handoff.SeamError) as err:
        lab.run_chain(
            con,
            replacements={"settle": settle_forgets_total},
        )

    assert err.value.stage_name == "settle"
    assert err.value.code == "promised_fact_missing"
    assert err.value.checkpoint.trace == ("intent",)
    assert "net_total" in err.value.detail


def test_later_stage_cannot_restate_an_owned_upstream_fact() -> None:
    con = lab.month_end()

    async def pay_restates_total(view):
        return handoff.StageDelta(
            facts=(
                handoff.FactValue(
                    "paid_total",
                    view.facts["net_total"],
                    ("payment://attempt",),
                ),
                handoff.FactValue(
                    "payment_id",
                    "payment-2026-06",
                    ("payment://attempt",),
                ),
                handoff.FactValue(
                    "net_total",
                    view.facts["net_total"],
                    ("payment://attempt",),
                ),
            )
        )

    with pytest.raises(handoff.SeamError) as err:
        lab.run_chain(con, replacements={"pay": pay_restates_total})

    assert err.value.stage_name == "pay"
    assert err.value.code == "undeclared_fact"
    assert "net_total" in err.value.detail


def test_thin_contract_can_accept_the_wrong_obligation_total() -> None:
    con = lab.month_end()
    result, paid = lab.run_chain(
        con,
        semantic=False,
        settlement="obligation",
    )
    payment = lab.payment_record(paid)

    assert result.acceptance_receipt.accepted
    assert payment["total"] == GROSS
    assert payment["lines"] == 800
    assert payment["total"] - NET == 38_444.0


def test_release_contract_rejects_wrong_value_before_payment() -> None:
    con = lab.month_end()
    paid: dict = {}
    chain = lab.payroll_chain(
        con,
        paid,
        semantic=True,
        settlement="obligation",
    )

    with pytest.raises(handoff.SeamError) as err:
        asyncio.run(
            chain.run(
                lab.new_baton(
                    lab.payroll_contract(),
                    baton_id="strict-payroll",
                    intent="disburse salaries",
                )
            )
        )

    assert err.value.stage_name == "settle"
    assert err.value.code == "fact_semantic_violation"
    assert "13,744,541.00" in err.value.detail
    assert "13,706,097.00" in err.value.detail
    assert err.value.checkpoint.trace == ("intent",)
    assert paid == {}


def test_payment_uses_stage_run_id_as_the_idempotency_key() -> None:
    con = lab.month_end()
    result, paid = lab.run_chain(con)
    pay_receipt = result.receipts[3]

    assert list(paid) == [pay_receipt.stage_run_id]
    assert paid[pay_receipt.stage_run_id]["payment_id"] == "payment-2026-06"


def test_nested_stage_view_mutation_cannot_change_committed_pay_lines() -> None:
    con = lab.month_end()

    async def fund_check_mutates_copy(view):
        lines = view.facts["pay_lines"]
        local = list(lines)
        local.clear()
        return handoff.StageDelta(
            facts=(
                handoff.FactValue(
                    "funding_ok",
                    True,
                    ("treasury://available",),
                ),
            )
        )

    result, paid = lab.run_chain(
        con,
        replacements={"fund_check": fund_check_mutates_copy},
    )

    assert len(result.baton.facts["pay_lines"]) == 798
    assert lab.payment_record(paid)["lines"] == 798
