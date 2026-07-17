"""Invariants for the Hierarchical Delegation pattern."""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import replace

import pytest


sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (  # noqa: E402
    AcceptanceDecision,
    ArtifactEnvelope,
    PortfolioBoundary,
    SafetyBoundary,
    SalaryBatchResult,
    SettlementSupervisor,
    Verdict,
    batch_fingerprint,
    bind_salary_result,
)


ROSTER = [
    {"id": "e1", "client": "acme", "base": 8000},
    {"id": "e2", "client": "acme", "base": 9000},
    {"id": "e3", "client": "globex", "base": 7000},
    {"id": "e4", "client": "initech", "base": 6000},
]


def result_for(handoff, rows, *, total: float = 1000.0) -> SalaryBatchResult:
    ids = tuple(str(row["id"]) for row in rows)
    return SalaryBatchResult(
        batch_id=handoff.contract.contract_id,
        verdict=Verdict.SUCCESS,
        employee_count=len(rows),
        total_amount=total,
        input_fingerprint=batch_fingerprint(ids),
    )


def ok_dispatch(total: float = 1000.0):
    async def dispatch(handoff, rows):
        return bind_salary_result(
            handoff,
            result_for(handoff, rows, total=total),
            evidence_refs=(f"sqlite://payroll/{handoff.contract.contract_id}",),
        )

    return dispatch


def test_decompose_creates_disjoint_versioned_child_contracts() -> None:
    supervisor = SettlementSupervisor(dispatch=ok_dispatch())
    root = supervisor.root_contract(ROSTER)
    assignments = supervisor.decompose(ROSTER, root)

    assert [assignment.batch_id for assignment in assignments] == [
        "batch::acme",
        "batch::globex",
        "batch::initech",
    ]
    assigned_ids = [
        employee_id
        for assignment in assignments
        for employee_id in assignment.handoff.contract.input_refs
    ]
    assert sorted(assigned_ids) == sorted(root.input_refs)
    assert len(assigned_ids) == len(set(assigned_ids))
    for assignment in assignments:
        contract = assignment.handoff.contract
        assert contract.allowed_tools == ("read_roster", "calc_salary")
        assert contract.authority_scope == ("read:assigned-roster", "compute:salary")
        assert root.digest in contract.constraints[0]


def test_worker_artifact_is_bound_to_the_child_contract() -> None:
    supervisor = SettlementSupervisor(dispatch=ok_dispatch())
    assignment = supervisor.decompose(ROSTER)[0]
    artifact = asyncio.run(
        ok_dispatch()(assignment.handoff, assignment.rows)
    )

    assert artifact.contract_digest == assignment.handoff.contract.digest
    assert artifact.schema == assignment.handoff.contract.output_schema
    assert artifact.produced_by == assignment.handoff.receiver


def test_batch_gate_accepts_a_contract_bound_result_with_evidence() -> None:
    supervisor = SettlementSupervisor(dispatch=ok_dispatch())
    summary = asyncio.run(supervisor.run(ROSTER))

    assert all(
        receipt.decision is AcceptanceDecision.ACCEPTED
        for receipt in summary.batch_receipts
    )
    assert summary.auto_approved == (
        "batch::acme",
        "batch::globex",
        "batch::initech",
    )


@pytest.mark.parametrize(
    ("mutate", "finding_code"),
    [
        (
            lambda artifact: replace(artifact, contract_digest="wrong-contract"),
            "contract_digest_mismatch",
        ),
        (
            lambda artifact: replace(artifact, schema="WrongSchema"),
            "schema_mismatch",
        ),
        (
            lambda artifact: replace(artifact, produced_by="other-worker"),
            "producer_mismatch",
        ),
        (
            lambda artifact: replace(artifact, evidence_refs=()),
            "missing_evidence",
        ),
    ],
)
def test_batch_gate_rejects_unbound_or_unevidenced_artifacts(
    mutate,
    finding_code: str,
) -> None:
    supervisor = SettlementSupervisor(dispatch=ok_dispatch())
    assignment = supervisor.decompose(ROSTER)[0]
    artifact = asyncio.run(ok_dispatch()(assignment.handoff, assignment.rows))

    receipt = supervisor.boundary.evaluate(
        assignment.handoff,
        mutate(artifact),
    )

    assert receipt.decision is AcceptanceDecision.ESCALATED
    assert finding_code in {finding.code for finding in receipt.findings}


def test_batch_gate_checks_roster_facts_the_worker_does_not_author() -> None:
    supervisor = SettlementSupervisor(dispatch=ok_dispatch())
    assignment = supervisor.decompose(ROSTER)[0]
    dropped = assignment.rows[:-1]
    artifact = bind_salary_result(
        assignment.handoff,
        result_for(assignment.handoff, dropped),
        evidence_refs=("sqlite://payroll/dropper",),
    )

    receipt = supervisor.boundary.evaluate(assignment.handoff, artifact)
    codes = {finding.code for finding in receipt.findings}

    assert receipt.decision is AcceptanceDecision.ESCALATED
    assert {"roster_count_mismatch", "roster_fingerprint_mismatch"} <= codes


def test_batch_gate_escalates_business_risk() -> None:
    supervisor = SettlementSupervisor(
        dispatch=ok_dispatch(total=60_000),
        boundary=SafetyBoundary(amount_threshold=50_000),
    )
    summary = asyncio.run(supervisor.run(ROSTER))

    assert not summary.auto_approved
    assert {
        finding.code
        for receipt in summary.batch_receipts
        for finding in receipt.findings
    } == {"amount_threshold_exceeded"}


def test_worker_exception_becomes_an_evidenced_failure_artifact() -> None:
    async def flaky(handoff, rows):
        if handoff.contract.contract_id == "batch::globex":
            raise RuntimeError("worker crashed")
        return await ok_dispatch()(handoff, rows)

    summary = asyncio.run(SettlementSupervisor(dispatch=flaky).run(ROSTER))
    failed = next(
        artifact.payload
        for artifact in summary.batch_artifacts
        if artifact.payload.batch_id == "batch::globex"
    )

    assert failed.verdict is Verdict.FAILURE
    assert failed.failure_code == "RuntimeError: worker crashed"
    assert "batch::globex" in summary.human_review
    assert "batch::acme" in summary.auto_approved


def test_portfolio_gate_catches_a_sum_no_batch_can_see() -> None:
    supervisor = SettlementSupervisor(
        dispatch=ok_dispatch(total=40_000),
        boundary=SafetyBoundary(amount_threshold=50_000),
        portfolio_boundary=PortfolioBoundary(max_total_amount=100_000),
    )
    summary = asyncio.run(supervisor.run(ROSTER))

    assert all(
        receipt.decision is AcceptanceDecision.ACCEPTED
        for receipt in summary.batch_receipts
    )
    assert summary.portfolio_receipt.decision is AcceptanceDecision.ESCALATED
    assert {
        finding.code for finding in summary.portfolio_receipt.findings
    } == {"portfolio_amount_exceeded"}


def test_portfolio_gate_catches_missing_roster_coverage() -> None:
    async def dropper(handoff, rows):
        kept = rows[:-1] if handoff.contract.contract_id == "batch::acme" else rows
        return bind_salary_result(
            handoff,
            result_for(handoff, kept),
            evidence_refs=("sqlite://payroll/dropper",),
        )

    summary = asyncio.run(SettlementSupervisor(dispatch=dropper).run(ROSTER))
    codes = {finding.code for finding in summary.portfolio_receipt.findings}

    assert "portfolio_coverage_mismatch" in codes
    assert "child_batches_unresolved" in codes


def test_run_dispatches_every_batch_concurrently() -> None:
    started: list[str] = []
    release = asyncio.Event()

    async def track(handoff, rows):
        started.append(handoff.contract.contract_id)
        if len(started) == 3:
            release.set()
        await asyncio.wait_for(release.wait(), timeout=1)
        return await ok_dispatch()(handoff, rows)

    summary = asyncio.run(SettlementSupervisor(dispatch=track).run(ROSTER))

    assert sorted(started) == ["batch::acme", "batch::globex", "batch::initech"]
    assert summary.employee_count == len(ROSTER)


def test_policy_configuration_is_validated_at_construction() -> None:
    with pytest.raises(ValueError, match="amount_threshold"):
        SafetyBoundary(amount_threshold=0)
    with pytest.raises(ValueError, match="max_total_amount"):
        PortfolioBoundary(max_total_amount=-1)


def test_dispatch_must_return_an_artifact_envelope() -> None:
    async def wrong_type(handoff, rows):
        return result_for(handoff, rows)

    summary = asyncio.run(SettlementSupervisor(dispatch=wrong_type).run(ROSTER))

    assert all(
        artifact.payload.verdict is Verdict.FAILURE
        for artifact in summary.batch_artifacts
    )
    assert all(
        isinstance(artifact, ArtifactEnvelope)
        for artifact in summary.batch_artifacts
    )
