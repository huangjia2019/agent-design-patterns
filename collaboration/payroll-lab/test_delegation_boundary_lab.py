"""Invariant tests for the lecture 31 delegation boundary lab."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import pytest


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import delegation_boundary_lab as lab  # noqa: E402

from collaboration.boundary_contract import (  # noqa: E402
    AcceptanceDecision,
    ArtifactEnvelope,
    HandoffEnvelope,
)


@pytest.fixture(scope="module")
def fixture():
    connection = lab.bench.month_end_state()
    contract = lab.monthly_report_contract(lab.bench.MONTH)
    truth = lab.ledger_truth(connection, lab.bench.MONTH)
    yield connection, contract, truth
    connection.close()


def test_legacy_packet_is_unbound_and_fails_exact_acceptance(fixture) -> None:
    connection, contract, truth = fixture

    output = lab.worker_write_report(
        lab.LegacyPacket(contract.objective),
        connection,
        lab.bench.MONTH,
    )
    receipt = lab.acceptance(
        output,
        contract,
        truth,
        receipt_id="receipt-test-1",
    )
    codes = {finding.code for finding in receipt.findings}

    assert isinstance(output, lab.LegacyReport)
    assert output.payload.paid == 800
    assert output.payload.exception_ids == ()
    assert receipt.decision is AcceptanceDecision.REJECTED
    assert codes == {
        lab.ReportFindingCode.CONTRACT_BINDING_MISSING.value,
        lab.ReportFindingCode.SCHEMA_MISMATCH.value,
        lab.ReportFindingCode.PAID_COUNT_MISMATCH.value,
        lab.ReportFindingCode.REVERSED_MISMATCH.value,
        lab.ReportFindingCode.CONCLUSION_MISMATCH.value,
    }


def test_rejected_legacy_result_must_be_reissued_as_a_full_contract(fixture) -> None:
    connection, contract, truth = fixture
    legacy = lab.worker_write_report(
        lab.LegacyPacket(contract.objective),
        connection,
        lab.bench.MONTH,
    )
    rejected = lab.acceptance(
        legacy,
        contract,
        truth,
        receipt_id="receipt-test-legacy",
    )
    retry = HandoffEnvelope(
        handoff_id="handoff-test-a2",
        sender="payroll-supervisor",
        receiver="report-worker",
        contract=contract,
        attempt=2,
        prior_receipt=rejected,
    )

    repaired = lab.worker_write_report(retry, connection, lab.bench.MONTH)
    accepted = lab.acceptance(
        repaired,
        contract,
        truth,
        receipt_id="receipt-test-a2",
    )

    assert isinstance(repaired, ArtifactEnvelope)
    assert accepted.decision is AcceptanceDecision.ACCEPTED
    assert repaired.contract_digest == contract.digest
    assert repaired.payload.exception_ids == ("E0007", "E0012")


def test_complete_contract_passes_on_the_first_attempt(fixture) -> None:
    connection, contract, truth = fixture
    handoff = HandoffEnvelope(
        handoff_id="handoff-test-b1",
        sender="payroll-supervisor",
        receiver="report-worker",
        contract=contract,
    )

    output = lab.worker_write_report(handoff, connection, lab.bench.MONTH)
    receipt = lab.acceptance(
        output,
        contract,
        truth,
        receipt_id="receipt-test-b1",
    )

    assert isinstance(output, ArtifactEnvelope)
    assert receipt.accepted is True


def test_gate_rejects_present_but_wrong_exception_values(fixture) -> None:
    connection, contract, truth = fixture
    handoff = HandoffEnvelope(
        handoff_id="handoff-test-c1",
        sender="payroll-supervisor",
        receiver="report-worker",
        contract=contract,
    )
    valid = lab.worker_write_report(handoff, connection, lab.bench.MONTH)
    wrong_payload = replace(
        valid.payload,
        exception_ids=("E9999",),
        reversed=1,
    )
    wrong = replace(valid, payload=wrong_payload)

    receipt = lab.acceptance(
        wrong,
        contract,
        truth,
        receipt_id="receipt-test-c1",
    )
    codes = {finding.code for finding in receipt.findings}

    assert codes == {lab.ReportFindingCode.REVERSED_MISMATCH.value}


def test_gate_rejects_artifact_from_an_old_contract_version(fixture) -> None:
    connection, contract, truth = fixture
    handoff = HandoffEnvelope(
        handoff_id="handoff-test-d1",
        sender="payroll-supervisor",
        receiver="report-worker",
        contract=contract,
    )
    valid = lab.worker_write_report(handoff, connection, lab.bench.MONTH)
    stale = replace(valid, contract_digest="old-contract-digest")

    receipt = lab.acceptance(
        stale,
        contract,
        truth,
        receipt_id="receipt-test-d1",
    )

    assert receipt.decision is AcceptanceDecision.REJECTED
    assert {
        finding.code for finding in receipt.findings
    } == {lab.ReportFindingCode.CONTRACT_BINDING_MISSING.value}
