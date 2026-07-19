"""Deterministic two-person approval example."""
from __future__ import annotations

import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

from pattern import (  # noqa: E402
    ActionProposal,
    ApprovalGate,
    Reversibility,
    RiskLevel,
)


proposal = ActionProposal(
    proposal_id="payroll-2026-06",
    version=1,
    contract_digest="contract-2026-06",
    artifact_id="reviewed-payroll-run",
    artifact_digest="reviewed-payroll-run-content-v1",
    requested_by="payroll-agent",
    action="payroll.disburse",
    resource_scope=("payroll:2026-06", "bank:payroll"),
    idempotency_key="payroll-2026-06-v1",
    risk=RiskLevel.CRITICAL,
    reversibility=Reversibility.IRREVERSIBLE,
    amount=13_706_097.0,
    subject_count=798,
    evidence_refs=("sqlite://payroll.db/paid",),
)

role_directory = {
    "alice": ("payroll-controller",),
    "bob": ("treasury-controller",),
}
gate = ApprovalGate(
    role_resolver=lambda approver_id: role_directory.get(approver_id, ()),
)
routed = gate.evaluate(proposal, now="2026-07-17T10:00:00+00:00")
print(f"route={routed.route.value} decision={routed.receipt.decision.value}")
print(f"ticket={routed.ticket.ticket_id} reasons={list(routed.ticket.reason_codes)}")

first = gate.attest(
    routed.ticket.ticket_id,
    approver_id="alice",
    role="payroll-controller",
    approved=True,
    at="2026-07-17T10:05:00+00:00",
)
print(f"after payroll review={first.receipt.decision.value}")

final = gate.attest(
    routed.ticket.ticket_id,
    approver_id="bob",
    role="treasury-controller",
    approved=True,
    at="2026-07-17T10:06:00+00:00",
)
print(f"after treasury review={final.receipt.decision.value}")
print(
    "authorized="
    f"{gate.authorize(proposal, final.receipt, at='2026-07-17T10:10:00+00:00')}"
)
