"""Invariants for the collaboration boundary contract."""
from __future__ import annotations

from dataclasses import replace

import pytest

from collaboration.boundary_contract import (
    AcceptanceDecision,
    AcceptanceReceipt,
    ArtifactEnvelope,
    ExecutionBudget,
    Finding,
    HandoffEnvelope,
    TaskContract,
)


def contract() -> TaskContract:
    return TaskContract(
        contract_id="payroll-2026-06-report",
        version=1,
        objective="write the June payroll report",
        output_schema="payroll.monthly-report/v1",
        accountable_owner="payroll-supervisor",
        input_refs=("sqlite://payroll.db?month=2026-06",),
        constraints=("list reversed payslips",),
        allowed_tools=("read_payroll",),
        boundary="read-only report generation",
        budget=ExecutionBudget(max_attempts=2),
    )


def rejected_receipt(task: TaskContract) -> AcceptanceReceipt:
    return AcceptanceReceipt(
        receipt_id="receipt-1",
        contract_digest=task.digest,
        artifact_id="artifact-1",
        checked_by="ledger-gate",
        decision=AcceptanceDecision.REJECTED,
        findings=(
            Finding(
                code="paid_count_mismatch",
                field="paid",
                message="paid count disagrees with the ledger",
                evidence="expected=798 observed=800",
            ),
        ),
    )


def test_contract_digest_changes_with_any_contract_version_change() -> None:
    original = contract()

    assert replace(original, version=2).digest != original.digest
    assert replace(original, constraints=("list every exception ID",)).digest != (
        original.digest
    )


def test_artifact_binds_to_the_exact_contract_digest() -> None:
    task = contract()
    artifact = ArtifactEnvelope(
        artifact_id="artifact-1",
        contract_digest=task.digest,
        schema=task.output_schema,
        produced_by="report-worker",
        payload={"paid": 798},
    )

    assert artifact.contract_digest == task.digest


def test_artifact_bind_uses_the_handoff_contract_and_receiver() -> None:
    task = contract()
    handoff = HandoffEnvelope(
        handoff_id="handoff-1",
        sender="payroll-supervisor",
        receiver="report-worker",
        contract=task,
    )

    artifact = ArtifactEnvelope.bind(
        handoff,
        artifact_id="artifact-1",
        produced_by="report-worker",
        payload={"paid": 798},
        evidence_refs=("sqlite://payroll.db?month=2026-06",),
    )

    assert artifact.contract_digest == task.digest
    assert artifact.schema == task.output_schema
    assert artifact.evidence_refs


def test_artifact_bind_rejects_a_different_producer() -> None:
    handoff = HandoffEnvelope(
        handoff_id="handoff-1",
        sender="payroll-supervisor",
        receiver="report-worker",
        contract=contract(),
    )

    with pytest.raises(ValueError, match="designated receiver"):
        ArtifactEnvelope.bind(
            handoff,
            artifact_id="artifact-1",
            produced_by="other-worker",
            payload={"paid": 798},
        )


def test_retry_requires_a_receipt_from_the_same_contract_version() -> None:
    task = contract()
    receipt = rejected_receipt(task)

    retry = HandoffEnvelope(
        handoff_id="handoff-2",
        sender="payroll-supervisor",
        receiver="report-worker",
        contract=task,
        attempt=2,
        prior_receipt=receipt,
    )

    assert retry.prior_receipt is receipt

    with pytest.raises(ValueError, match="another contract version"):
        HandoffEnvelope(
            handoff_id="handoff-3",
            sender="payroll-supervisor",
            receiver="report-worker",
            contract=replace(task, version=2),
            attempt=2,
            prior_receipt=receipt,
        )


def test_retry_without_prior_receipt_is_rejected() -> None:
    with pytest.raises(ValueError, match="prior acceptance receipt"):
        HandoffEnvelope(
            handoff_id="handoff-2",
            sender="payroll-supervisor",
            receiver="report-worker",
            contract=contract(),
            attempt=2,
        )


def test_first_attempt_rejects_receipts_and_retry_rejects_accepted_receipt() -> None:
    task = contract()
    accepted = AcceptanceReceipt(
        receipt_id="receipt-ok",
        contract_digest=task.digest,
        artifact_id="artifact-ok",
        checked_by="ledger-gate",
        decision=AcceptanceDecision.ACCEPTED,
    )

    with pytest.raises(ValueError, match="first attempt"):
        HandoffEnvelope(
            handoff_id="handoff-1",
            sender="payroll-supervisor",
            receiver="report-worker",
            contract=task,
            prior_receipt=accepted,
        )

    with pytest.raises(ValueError, match="accepted artifact"):
        HandoffEnvelope(
            handoff_id="handoff-2",
            sender="payroll-supervisor",
            receiver="report-worker",
            contract=task,
            attempt=2,
            prior_receipt=accepted,
        )


def test_accepted_receipt_cannot_hide_a_blocker() -> None:
    task = contract()

    with pytest.raises(ValueError, match="cannot carry blocker"):
        AcceptanceReceipt(
            receipt_id="receipt-1",
            contract_digest=task.digest,
            artifact_id="artifact-1",
            checked_by="ledger-gate",
            decision=AcceptanceDecision.ACCEPTED,
            findings=rejected_receipt(task).findings,
        )
