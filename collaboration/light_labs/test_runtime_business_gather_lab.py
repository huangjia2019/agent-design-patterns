"""Checks for the Harness/runtime versus business/gather bonus lab."""

from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import runtime_business_gather_lab as lab  # noqa: E402


def test_healthy_run_is_concurrent_and_business_ready() -> None:
    result = lab.run_scenario_sync("healthy")

    assert result.runtime.status is lab.RuntimeStatus.COMPLETE
    assert result.runtime.peak_concurrency == 3
    assert len(result.runtime.successful_cards) == 3
    assert result.business.status is lab.BusinessStatus.READY
    assert result.business.release_allowed is True
    assert all(check.passed for check in result.business.checks)


def test_timeout_is_runtime_fact_and_missing_bank_is_business_fact() -> None:
    result = lab.run_scenario_sync("bank-timeout")

    assert result.runtime.status is lab.RuntimeStatus.PARTIAL
    bank = next(
        outcome for outcome in result.runtime.outcomes if outcome.source_id == "bank_ledger"
    )
    assert bank.status is lab.WorkerStatus.TIMED_OUT
    assert result.business.status is lab.BusinessStatus.INSUFFICIENT_EVIDENCE
    assert result.business.missing_sources == ("bank_ledger",)
    assert result.business.release_allowed is False


def test_duplicate_worker_does_not_create_independent_evidence() -> None:
    result = lab.run_scenario_sync("duplicate-lineage")

    assert len(result.runtime.successful_cards) == 4
    assert result.business.status is lab.BusinessStatus.READY
    assert result.business.duplicate_lineages == ("hr_roster_copy",)
    assert result.business.admitted_sources == (
        "bank_ledger",
        "hr_roster",
        "payroll_batch",
    )


def test_wrong_unit_is_quarantined_before_arithmetic() -> None:
    result = lab.run_scenario_sync("unit-mismatch")

    assert result.runtime.status is lab.RuntimeStatus.COMPLETE
    assert result.business.status is lab.BusinessStatus.INSUFFICIENT_EVIDENCE
    assert result.business.missing_sources == ("bank_ledger",)
    assert result.business.quarantined == ("bank_ledger:unit=CNY_CENTS",)


def test_all_workers_can_succeed_while_business_invariant_fails() -> None:
    result = lab.run_scenario_sync("unexplained-gap")

    assert result.runtime.status is lab.RuntimeStatus.COMPLETE
    assert all(
        outcome.status is lab.WorkerStatus.SUCCEEDED
        for outcome in result.runtime.outcomes
    )
    assert result.business.status is lab.BusinessStatus.CONFLICT
    assert result.business.release_allowed is False
    amount_check = next(
        check for check in result.business.checks if check.name == "ledger_explains_amount"
    )
    assert amount_check.passed is False
