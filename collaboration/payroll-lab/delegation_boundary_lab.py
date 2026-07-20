"""Lecture 31: controlled ablation at an Agent delegation boundary.

The supervisor owns one complete contract for June's payroll report. Three
scenes deliberately cross the boundary in different ways:

1. a legacy objective-only packet is published without acceptance;
2. the same legacy result is rejected, then retried with the full contract;
3. the full contract crosses the boundary on the first attempt.

The fixture measures contract propagation, not model capability. The valid path
uses the shared collaboration interface:

``TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt``.

Run ``python3 collaboration/payroll-lab/delegation_boundary_lab.py``.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from sqlite3 import Connection


HERE = Path(__file__).parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "reflection" / "payroll-lab"))

from collaboration.boundary_contract import (  # noqa: E402
    AcceptanceDecision,
    AcceptanceReceipt,
    ArtifactEnvelope,
    ExecutionBudget,
    Finding,
    HandoffEnvelope,
    TaskContract,
)

import bench  # noqa: E402


class ReportFindingCode(str, Enum):
    CONTRACT_BINDING_MISSING = "contract_binding_missing"
    SCHEMA_MISMATCH = "schema_mismatch"
    PAID_COUNT_MISMATCH = "paid_count_mismatch"
    REVERSED_MISMATCH = "reversed_mismatch"
    CONCLUSION_MISMATCH = "conclusion_mismatch"


@dataclass(frozen=True)
class LegacyPacket:
    """The objective-only handoff kept solely as the teaching baseline."""

    objective: str


@dataclass(frozen=True)
class LedgerTruth:
    paid: int
    reversed_ids: tuple[str, ...]

    @property
    def conclusion(self) -> str:
        return "exceptions-pending" if self.reversed_ids else "all-clear"


@dataclass(frozen=True)
class ReportPayload:
    month: str
    paid: int
    reversed: int
    exception_ids: tuple[str, ...]
    conclusion: str

    def render(self) -> str:
        exceptions = ",".join(self.exception_ids) or "none"
        return (
            f"month={self.month} paid={self.paid} reversed={self.reversed} "
            f"exceptions={exceptions} conclusion={self.conclusion}"
        )


@dataclass(frozen=True)
class LegacyReport:
    artifact_id: str
    payload: ReportPayload

    def render(self) -> str:
        return f"MONTHLY-REPORT schema=UNBOUND {self.payload.render()}"


ReportOutput = LegacyReport | ArtifactEnvelope[ReportPayload]


def monthly_report_contract(month: str) -> TaskContract:
    return TaskContract(
        contract_id=f"payroll-report-{month}",
        version=1,
        objective=f"summarize {month} payroll into the monthly report",
        output_schema="payroll.monthly-report/v1",
        accountable_owner="payroll-supervisor",
        input_refs=(f"sqlite://payroll.db?month={month}",),
        constraints=(
            "REVERSED payslips must be listed as exceptions",
            "conclusion must reflect ledger facts",
        ),
        allowed_tools=("read_payroll",),
        authority_scope=("payroll:read",),
        boundary="read only the contracted month; do not publish or mutate payroll",
        budget=ExecutionBudget(max_attempts=2, timeout_seconds=30),
    )


def ledger_truth(connection: Connection, month: str) -> LedgerTruth:
    paid = connection.execute(
        "SELECT COUNT(*) FROM payroll WHERE month=? AND status='PAID'",
        (month,),
    ).fetchone()[0]
    reversed_ids = tuple(
        row[0]
        for row in connection.execute(
            "SELECT emp_id FROM payroll "
            "WHERE month=? AND status='REVERSED' ORDER BY emp_id",
            (month,),
        ).fetchall()
    )
    return LedgerTruth(paid=paid, reversed_ids=reversed_ids)


def worker_write_report(
    packet: LegacyPacket | HandoffEnvelope,
    connection: Connection,
    month: str,
) -> ReportOutput:
    """Produce exactly what the received interface allows the worker to know."""

    if isinstance(packet, LegacyPacket):
        paid = connection.execute(
            "SELECT COUNT(*) FROM payroll WHERE month=?",
            (month,),
        ).fetchone()[0]
        return LegacyReport(
            artifact_id="legacy-report-a1",
            payload=ReportPayload(
                month=month,
                paid=paid,
                reversed=0,
                exception_ids=(),
                conclusion="all-clear",
            ),
        )

    contract = packet.contract
    truth = ledger_truth(connection, month)
    return ArtifactEnvelope(
        artifact_id=f"report-a{packet.attempt}",
        contract_digest=contract.digest,
        schema=contract.output_schema,
        produced_by=packet.receiver,
        payload=ReportPayload(
            month=month,
            paid=truth.paid,
            reversed=len(truth.reversed_ids),
            exception_ids=truth.reversed_ids,
            conclusion=truth.conclusion,
        ),
        evidence_refs=contract.input_refs,
    )


def acceptance(
    output: ReportOutput,
    contract: TaskContract,
    truth: LedgerTruth,
    *,
    receipt_id: str,
) -> AcceptanceReceipt:
    """Bind a decision to the exact contract, artifact, and ledger evidence."""

    findings: list[Finding] = []
    if isinstance(output, LegacyReport):
        payload = output.payload
        artifact_id = output.artifact_id
        findings.append(
            Finding(
                code=ReportFindingCode.CONTRACT_BINDING_MISSING.value,
                field="contract_digest",
                message="artifact is not bound to the delegated contract version",
                evidence=f"expected contract_digest={contract.digest}, got=UNBOUND",
            )
        )
        findings.append(
            Finding(
                code=ReportFindingCode.SCHEMA_MISMATCH.value,
                field="schema",
                message="artifact does not use the contracted report schema",
                evidence=f"expected schema={contract.output_schema}, got=UNBOUND",
            )
        )
    else:
        payload = output.payload
        artifact_id = output.artifact_id
        if output.contract_digest != contract.digest:
            findings.append(
                Finding(
                    code=ReportFindingCode.CONTRACT_BINDING_MISSING.value,
                    field="contract_digest",
                    message="artifact belongs to another contract version",
                    evidence=(
                        f"expected contract_digest={contract.digest}, "
                        f"got={output.contract_digest}"
                    ),
                )
            )
        if output.schema != contract.output_schema:
            findings.append(
                Finding(
                    code=ReportFindingCode.SCHEMA_MISMATCH.value,
                    field="schema",
                    message="artifact does not use the contracted report schema",
                    evidence=(
                        f"expected schema={contract.output_schema}, got={output.schema}"
                    ),
                )
            )

    if payload.paid != truth.paid:
        findings.append(
            Finding(
                code=ReportFindingCode.PAID_COUNT_MISMATCH.value,
                field="paid",
                message="paid count disagrees with the ledger",
                evidence=f"expected paid={truth.paid}, got={payload.paid}",
            )
        )
    if (
        payload.reversed != len(truth.reversed_ids)
        or payload.exception_ids != truth.reversed_ids
    ):
        findings.append(
            Finding(
                code=ReportFindingCode.REVERSED_MISMATCH.value,
                field="exception_ids",
                message="reversed count or exception IDs disagree with the ledger",
                evidence=(
                    f"expected reversed={len(truth.reversed_ids)} "
                    f"ids={truth.reversed_ids}, got reversed={payload.reversed} "
                    f"ids={payload.exception_ids}"
                ),
            )
        )
    if payload.conclusion != truth.conclusion:
        findings.append(
            Finding(
                code=ReportFindingCode.CONCLUSION_MISMATCH.value,
                field="conclusion",
                message="conclusion disagrees with the ledger state",
                evidence=(
                    f"expected conclusion={truth.conclusion}, got={payload.conclusion}"
                ),
            )
        )

    decision = (
        AcceptanceDecision.REJECTED
        if findings
        else AcceptanceDecision.ACCEPTED
    )
    return AcceptanceReceipt(
        receipt_id=receipt_id,
        contract_digest=contract.digest,
        artifact_id=artifact_id,
        checked_by="ledger-acceptance-gate",
        decision=decision,
        findings=tuple(findings),
    )


def render_output(output: ReportOutput) -> str:
    if isinstance(output, LegacyReport):
        return output.render()
    return (
        f"MONTHLY-REPORT schema={output.schema} "
        f"contract={output.contract_digest} {output.payload.render()}"
    )


def run_demo() -> None:
    connection = bench.month_end_state()
    contract = monthly_report_contract(bench.MONTH)
    truth = ledger_truth(connection, bench.MONTH)

    print(
        f"== ledger truth: paid={truth.paid}, "
        f"reversed={list(truth.reversed_ids)} =="
    )
    print(
        f"== supervisor contract: id={contract.contract_id} "
        f"v={contract.version} digest={contract.digest} =="
    )

    print("\n== scene 1: legacy objective-only handoff, no acceptance ==")
    legacy = LegacyPacket(objective=contract.objective)
    print("   crossing: objective only; contract fields omitted")
    output = worker_write_report(legacy, connection, bench.MONTH)
    print("   worker: done.")
    print(f"   supervisor publishes:\n      {render_output(output)}")
    hidden_receipt = acceptance(
        output,
        contract,
        truth,
        receipt_id="receipt-hidden",
    )
    print(
        f"   published wrong: {str(not hidden_receipt.accepted).lower()}; "
        "no gate ran before publication"
    )

    print("\n== scene 2: same legacy result, gate rejects and contract is reissued ==")
    output = worker_write_report(legacy, connection, bench.MONTH)
    receipt = acceptance(output, contract, truth, receipt_id="receipt-a1")
    print(
        f"   attempt 1 -> {receipt.decision.value.upper()}, "
        f"{len(receipt.findings)} findings:"
    )
    for finding in receipt.findings:
        print(
            f"      - [{finding.code}] field={finding.field} "
            f"evidence={finding.evidence}"
        )
    retry = HandoffEnvelope(
        handoff_id="handoff-report-a2",
        sender="payroll-supervisor",
        receiver="report-worker",
        contract=contract,
        attempt=2,
        prior_receipt=receipt,
    )
    output = worker_write_report(retry, connection, bench.MONTH)
    receipt = acceptance(output, contract, truth, receipt_id="receipt-a2")
    print(f"   supervisor reissues full contract -> {render_output(output)}")
    print(f"   acceptance: {receipt.decision.value.upper()} (cost: one redo)")

    print("\n== scene 3: the complete contract crosses on the first attempt ==")
    handoff = replace(
        retry,
        handoff_id="handoff-report-b1",
        attempt=1,
        prior_receipt=None,
    )
    output = worker_write_report(handoff, connection, bench.MONTH)
    receipt = acceptance(output, contract, truth, receipt_id="receipt-b1")
    print(
        "   crossing: objective + input refs + constraints + schema + "
        "tools + authority + budget + owner"
    )
    print(f"   worker's first pass:\n      {render_output(output)}")
    print(f"   acceptance: {receipt.decision.value.upper()} (cost: zero redos)")

    print("\n[VERDICT] same worker, one supervisor contract, three crossings.")
    print("The legacy path shipped an unbound artifact. The gate returned a")
    print("version-bound receipt and forced a valid re-delegation. Sending the")
    print("complete contract first produced an accepted artifact in one pass.")
    connection.close()


if __name__ == "__main__":
    run_demo()
