"""Invariant tests for the lecture-37 approval-ticket lab."""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import fields
from pathlib import Path

import pytest

HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab = load_module(HERE / "approval_ticket_lab.py", "approval_ticket_lab")
_bc = sys.modules["collaboration.boundary_contract"]

TOTAL_V1 = 13_706_097.0
TOTAL_V2 = 13_744_541.0


def cfo_ticket(con, ticket_id="APR-T-001", *, fp=None, policy=None,
               expires_on="2026-07-02"):
    fp = fp if fp is not None else lab.settlement_fingerprint(con)
    policy = policy if policy is not None else default_policy()
    return lab.ApprovalTicket(
        ticket_id=ticket_id, approver="chief-financial-officer",
        approver_role="cfo", action="release-june-settlement",
        contract_digest=lab.settlement_contract(con).digest,
        artifact_fingerprint=fp, policy_digest=policy.digest,
        issued_on="2026-06-30", expires_on=expires_on)


def default_policy():
    return lab.PolicyCard("cash-line", 1, "finance-controller",
                          "portfolio claimed total must stay under",
                          13_000_000, "2026 annual budget line")


def admit(gate, con, ticket, *, policy=None, today="2026-06-30"):
    return gate.admit(
        ticket, amount=lab.settle_total(con),
        contract_digest=lab.settlement_contract(con).digest,
        artifact_fingerprint=lab.settlement_fingerprint(con),
        policy=policy if policy is not None else default_policy(),
        today=today)


def test_the_escalated_receipt_carries_no_approver_identity():
    con = lab.month_end()
    assert lab.settle_total(con) == TOTAL_V1
    receipt = lab.evaluate_settlement(con, lab.CASH_LINE)
    assert receipt.decision is _bc.AcceptanceDecision.ESCALATED
    # Field-precise vacuum: nothing in the receipt names who may unblock
    # it, against which artifact content, or for how long.
    for f in fields(receipt):
        value = getattr(receipt, f.name)
        if isinstance(value, str):
            assert "approv" not in value.lower()
    for finding in receipt.findings:
        for text in (finding.code, finding.field, finding.message,
                     finding.evidence):
            assert "approv" not in text.lower()
            assert "expires" not in text.lower()


def test_amounts_route_to_the_role_allowed_to_sign():
    assert lab.required_role(10_000.0) == "payroll-operator"
    assert lab.required_role(10_000.01) == "payroll-supervisor"
    assert lab.required_role(3_000_000.0) == "payroll-supervisor"
    assert lab.required_role(13_000_000.0) == "finance-controller"
    assert lab.required_role(TOTAL_V1) == "cfo"


def test_a_fully_bound_ticket_admits_exactly_once():
    con = lab.month_end()
    gate = lab.ApprovalGate()
    ticket = cfo_ticket(con)
    first = admit(gate, con, ticket)
    assert first.admitted and first.findings == ()
    replay = admit(gate, con, ticket)
    assert not replay.admitted
    assert {f.code for f in replay.findings} == {"approval_replayed"}


def test_the_wrong_tier_is_refused_with_the_required_role_named():
    con = lab.month_end()
    gate = lab.ApprovalGate()
    ticket = lab.ApprovalTicket(
        "APR-T-002", "payroll-supervisor", "payroll-supervisor",
        "release-june-settlement", lab.settlement_contract(con).digest,
        lab.settlement_fingerprint(con), default_policy().digest,
        "2026-06-30", "2026-07-02")
    decision = admit(gate, con, ticket)
    assert not decision.admitted
    (finding,) = decision.findings
    assert finding.code == "approval_authority_mismatch"
    assert "requires=cfo" in finding.evidence


def test_an_expired_ticket_is_refused():
    con = lab.month_end()
    gate = lab.ApprovalGate()
    decision = admit(gate, con, cfo_ticket(con), today="2026-07-15")
    assert not decision.admitted
    assert {f.code for f in decision.findings} == {"approval_expired"}


def test_reinstating_the_reversed_slips_defeats_last_weeks_ticket():
    con = lab.month_end()
    gate = lab.ApprovalGate()
    ticket = cfo_ticket(con)  # bound to the 798-slip settlement
    fp_v1 = ticket.artifact_fingerprint
    lab.reinstate_reversed(con)
    assert lab.settle_total(con) == TOTAL_V2
    assert lab.settlement_fingerprint(con) != fp_v1
    decision = admit(gate, con, ticket, today="2026-07-01")
    assert not decision.admitted
    codes = {f.code for f in decision.findings}
    assert "approval_artifact_drift" in codes
    # the contract scope changed too: 798 input_refs became 800
    assert "approval_contract_mismatch" in codes
    drift = next(f for f in decision.findings
                 if f.code == "approval_artifact_drift")
    assert f"approved={fp_v1}" in drift.evidence


def test_a_ticket_bound_to_a_superseded_policy_is_refused():
    con = lab.month_end()
    gate = lab.ApprovalGate()
    v2 = lab.PolicyCard("cash-line", 2, "finance-controller",
                        "portfolio claimed total must stay under",
                        30_000_000, "one-off retro payment window")
    decision = admit(gate, con, cfo_ticket(con), policy=v2)
    assert not decision.admitted
    assert {f.code for f in decision.findings} == {"approval_policy_mismatch"}


def test_widening_the_cash_line_needs_a_cfo_ticket():
    con = lab.month_end()
    gate = lab.ApprovalGate()
    v1 = default_policy()
    widen = lab.PolicyCard("cash-line", 2, "finance-controller",
                           "portfolio claimed total must stay under",
                           30_000_000, "one-off retro payment window")
    bad = lab.ApprovalTicket(
        "APR-T-003", "payroll-supervisor", "payroll-supervisor",
        "widen-cash-line", lab.settlement_contract(con).digest,
        widen.digest, v1.digest, "2026-07-01", "2026-07-03")
    with pytest.raises(PermissionError, match="approval_authority_mismatch"):
        lab.issue_policy_gated(widen, bad, gate, current_policy=v1,
                               today="2026-07-01")
    good = lab.ApprovalTicket(
        "APR-T-004", "chief-financial-officer", "cfo", "widen-cash-line",
        lab.settlement_contract(con).digest, widen.digest, v1.digest,
        "2026-07-01", "2026-07-03")
    assert lab.issue_policy_gated(widen, good, gate, current_policy=v1,
                                  today="2026-07-01") is widen


def test_every_refusal_finding_carries_evidence_of_the_broken_binding():
    con = lab.month_end()
    gate = lab.ApprovalGate()
    stale = lab.ApprovalTicket(
        "APR-T-005", "chief-financial-officer", "cfo",
        "release-june-settlement", "0" * 16, "1" * 16, "2" * 16,
        "2026-06-01", "2026-06-02")
    decision = admit(gate, con, stale, today="2026-07-15")
    assert not decision.admitted
    assert {f.code for f in decision.findings} == {
        "approval_contract_mismatch", "approval_artifact_drift",
        "approval_policy_mismatch", "approval_expired"}
    for finding in decision.findings:
        assert finding.evidence.strip()
        assert finding.severity is _bc.FindingSeverity.BLOCKER
