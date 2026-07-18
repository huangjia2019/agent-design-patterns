"""Lecture 37 hands-on: what an approval actually is, once you write it down.

Three scenes on the month-end payroll world, no API key, no database
damage. Every import here is committed code; the a-approval-gate pattern
industrializes what scene 2 sketches.

    scene 1  the escalation vacuum: the June settlement (798 PAID slips,
             13,706,097) hits the REAL committed PortfolioBoundary with
             the 13,000,000 cash line and comes back ESCALATED. The
             receipt says a human must look -- and stops there. No field
             of the receipt names who may unblock it, under which
             identity, against which artifact version, or for how long.
             Today the unblock is a chat message, and the chat message
             binds to nothing.
    scene 2  the ticket: an ApprovalTicket carries five bindings -- an
             approver with a role, the contract digest, the settlement
             fingerprint, the policy digest (lecture 36's PolicyCard),
             and an expiry window. The ApprovalGate admits on all five
             or refuses with a Finding whose code says which binding
             broke. Approval stops being a sentence and becomes an
             object the gate can check.
    scene 3  the routing: amounts route to the role allowed to sign
             them, on the same lines the course already shipped --
             10,000 operator, 3,000,000 supervisor, 13,000,000 finance
             controller, above that CFO. Then the 38,444 comes back:
             reinstating E0007 and E0012 changes the settlement
             fingerprint, and last week's CFO ticket refuses to ride on
             the new version. Finally the gate turns on the policy
             change itself: widening the cash line needs a ticket too.

Totals are computed from the bench ledger, not typed in. The ticket and
gate here are a teaching minimum: no delegation of authority, no
multi-signature quorum, no revocation feed. Those belong to the pattern,
not the intro lab.

Run `python3 approval_ticket_lab.py` from the repo root.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Lecture 36's lab already loads the committed delegation pattern and the
# bench, and defines PolicyCard. Build on it with one import.
_lab36 = load_module(HERE / "ungoverned_policy_lab.py", "lab36_dep")
PolicyCard = _lab36.PolicyCard
PortfolioBoundary = _lab36.PortfolioBoundary
PayrollPortfolioResult = _lab36.PayrollPortfolioResult

_bc = sys.modules["collaboration.boundary_contract"]
AcceptanceDecision = _bc.AcceptanceDecision
ArtifactEnvelope = _bc.ArtifactEnvelope
Finding = _bc.Finding
TaskContract = _bc.TaskContract

import bench  # noqa: E402  (path installed by lab36)

MONTH = bench.MONTH
CASH_LINE = 13_000_000.0


# ---- the settlement set, computed from the ledger -------------------------------

def month_end():
    return bench.month_end_state()


def settle_rows(con) -> tuple[tuple[str, float], ...]:
    """The slips that would actually be paid: PAID status only."""
    return tuple(
        (emp, float(amount))
        for emp, amount in con.execute(
            "SELECT emp_id, base + bonus + adjustment FROM payroll "
            "WHERE month = ? AND status = 'PAID' ORDER BY emp_id",
            (MONTH,),
        )
    )


def settle_total(con) -> float:
    return sum(amount for _, amount in settle_rows(con))


def settlement_fingerprint(con) -> str:
    """Content digest of the exact settlement set an approver looked at."""
    canonical = json.dumps(
        {"month": MONTH, "rows": settle_rows(con), "total": settle_total(con)},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def settlement_contract(con) -> TaskContract:
    return TaskContract(
        contract_id=f"settle-{MONTH}", version=1,
        objective="release the June settlement to the bank",
        output_schema="PayrollPortfolioResult",
        accountable_owner="settlement-supervisor",
        input_refs=tuple(emp for emp, _ in settle_rows(con)),
    )


def evaluate_settlement(con, limit: float):
    """The committed boundary, judging the PAID-only settlement."""
    contract = settlement_contract(con)
    depts = [d for (d,) in con.execute(
        "SELECT DISTINCT dept FROM employees ORDER BY dept")]
    total = settle_total(con)
    portfolio = PayrollPortfolioResult(
        claimed_total_amount=total,
        admitted_total_amount=total,
        employee_count=len(settle_rows(con)),
        auto_approved=tuple(f"batch::{d}" for d in depts),
        human_review=(),
        child_receipt_ids=tuple(f"receipt::batch::{d}" for d in depts),
    )
    artifact = ArtifactEnvelope(
        artifact_id=f"settlement-{MONTH}",
        contract_digest=contract.digest,
        schema=contract.output_schema,
        produced_by="settlement-supervisor",
        payload=portfolio,
        evidence_refs=(f"sqlite://payroll.db?month={MONTH}&status=PAID",),
    )
    return PortfolioBoundary(max_total_amount=limit).evaluate(contract, artifact)


def reinstate_reversed(con) -> None:
    """The retro correction: E0007 and E0012 go back into the settlement."""
    con.execute(
        "UPDATE payroll SET status='PAID' WHERE month=? AND emp_id IN (?, ?)",
        (MONTH, *bench.REVERSED_IDS))
    con.commit()


# ---- scene 2: the ticket and the gate -------------------------------------------

APPROVAL_ROUTES = (
    (10_000.0, "payroll-operator"),
    (3_000_000.0, "payroll-supervisor"),
    (13_000_000.0, "finance-controller"),
)
FALLBACK_ROLE = "cfo"


def required_role(amount: float) -> str:
    """Route the amount to the role allowed to sign for it."""
    for ceiling, role in APPROVAL_ROUTES:
        if amount <= ceiling:
            return role
    return FALLBACK_ROLE


@dataclass(frozen=True)
class ApprovalTicket:
    """One approval, written down: who signed, what exactly they saw,
    under which rule, and until when the signature is worth anything."""

    ticket_id: str
    approver: str
    approver_role: str
    action: str
    contract_digest: str
    artifact_fingerprint: str
    policy_digest: str
    issued_on: str    # ISO date
    expires_on: str   # ISO date, inclusive


@dataclass(frozen=True)
class GateDecision:
    ticket_id: str
    action: str
    admitted: bool
    findings: tuple


class ApprovalGate:
    """Admit on five bindings or refuse with the binding that broke."""

    def __init__(self) -> None:
        self._used: set[str] = set()

    def admit(self, ticket: ApprovalTicket, *, amount: float,
              contract_digest: str, artifact_fingerprint: str,
              policy: PolicyCard, today: str) -> GateDecision:
        findings = []
        needed = required_role(amount)
        if ticket.approver_role != needed:
            findings.append(Finding(
                code="approval_authority_mismatch", field="approver_role",
                message="this amount routes to a different signer",
                evidence=f"amount={amount:,.0f} requires={needed} "
                         f"ticket={ticket.approver_role}"))
        if ticket.contract_digest != contract_digest:
            findings.append(Finding(
                code="approval_contract_mismatch", field="contract_digest",
                message="ticket was signed against another task version",
                evidence=f"ticket={ticket.contract_digest} "
                         f"current={contract_digest}"))
        if ticket.artifact_fingerprint != artifact_fingerprint:
            findings.append(Finding(
                code="approval_artifact_drift", field="artifact_fingerprint",
                message="the settlement changed after the approver looked",
                evidence=f"approved={ticket.artifact_fingerprint} "
                         f"current={artifact_fingerprint}"))
        if ticket.policy_digest != policy.digest:
            findings.append(Finding(
                code="approval_policy_mismatch", field="policy_digest",
                message="the rule the approver saw is not the rule in force",
                evidence=f"ticket={ticket.policy_digest} "
                         f"in_force={policy.digest}"))
        if today > ticket.expires_on:
            findings.append(Finding(
                code="approval_expired", field="expires_on",
                message="the signature has lapsed; approve again",
                evidence=f"expires_on={ticket.expires_on} today={today}"))
        if ticket.ticket_id in self._used:
            findings.append(Finding(
                code="approval_replayed", field="ticket_id",
                message="a ticket admits exactly one execution",
                evidence=f"ticket_id={ticket.ticket_id} already used"))
        if findings:
            return GateDecision(ticket.ticket_id, ticket.action,
                                admitted=False, findings=tuple(findings))
        self._used.add(ticket.ticket_id)
        return GateDecision(ticket.ticket_id, ticket.action,
                            admitted=True, findings=())


def issue_policy_gated(card: PolicyCard, ticket: ApprovalTicket,
                       gate: ApprovalGate, *, current_policy: PolicyCard,
                       today: str) -> PolicyCard:
    """Lecture 36 pinned the policy; this closes the loop -- changing the
    policy is itself a high-risk action and goes through the same gate."""
    decision = gate.admit(
        ticket, amount=card.value, contract_digest=ticket.contract_digest,
        artifact_fingerprint=card.digest, policy=current_policy, today=today)
    if not decision.admitted:
        codes = ",".join(f.code for f in decision.findings)
        raise PermissionError(
            f"policy '{card.policy_id}' v{card.version} refused: {codes}")
    return card


# ---- scenes ---------------------------------------------------------------------

def main() -> None:
    con = month_end()
    total = settle_total(con)
    print(f"== scene 1: the escalation vacuum "
          f"(June settlement {total:,.0f}, {len(settle_rows(con))} slips) ==")
    receipt = evaluate_settlement(con, CASH_LINE)
    print(f"   cash line {CASH_LINE:,.0f} -> {receipt.decision.value}")
    for f in receipt.findings:
        print(f"      finding: {f.code} :: {f.evidence}")
    print("   -> 回执说“要人看”，然后就没有了。谁有资格点头、对着哪一版结算集、")
    print("      点头之后管多久，回执里一个字段都没有。今天补上这一步的，是聊天")
    print("      里的一句“同意”，它跟上面任何一个摘要都没有绑定。")

    print("\n== scene 2: the ticket, five bindings ==")
    fp_v1 = settlement_fingerprint(con)
    contract_v1 = settlement_contract(con)
    policy_v1 = PolicyCard("cash-line", 1, "finance-controller",
                           "portfolio claimed total must stay under",
                           13_000_000, "2026 annual budget line")
    gate = ApprovalGate()
    ticket = ApprovalTicket(
        ticket_id="APR-2026-06-30-001", approver="chief-financial-officer",
        approver_role="cfo", action="release-june-settlement",
        contract_digest=contract_v1.digest, artifact_fingerprint=fp_v1,
        policy_digest=policy_v1.digest,
        issued_on="2026-06-30", expires_on="2026-07-02")
    decision = gate.admit(ticket, amount=total,
                          contract_digest=contract_v1.digest,
                          artifact_fingerprint=fp_v1, policy=policy_v1,
                          today="2026-06-30")
    print(f"   ticket {ticket.ticket_id} ({ticket.approver_role}) "
          f"-> admitted={decision.admitted}")
    replay = gate.admit(ticket, amount=total,
                        contract_digest=contract_v1.digest,
                        artifact_fingerprint=fp_v1, policy=policy_v1,
                        today="2026-06-30")
    print(f"   same ticket again -> admitted={replay.admitted} "
          f"({replay.findings[0].code})")
    fresh = ApprovalTicket(
        "APR-2026-06-30-002", ticket.approver, "cfo", ticket.action,
        contract_v1.digest, fp_v1, policy_v1.digest,
        "2026-06-30", "2026-07-02")
    late = gate.admit(fresh, amount=total,
                      contract_digest=contract_v1.digest,
                      artifact_fingerprint=fp_v1, policy=policy_v1,
                      today="2026-07-15")
    print(f"   unused ticket on 2026-07-15 -> admitted={late.admitted} "
          f"({late.findings[0].code})")
    print("   -> 批准是一张票据：签的人、看到的结算集、当时生效的尺度、有效期，")
    print("      全在票面上。门只认票面，不认人声。")

    print("\n== scene 3: routing, and the 38,444 comes back ==")
    for amount in (9_800.0, 2_400_000.0, 12_500_000.0, total):
        print(f"   {amount:>13,.0f} -> {required_role(amount)}")
    reinstate_reversed(con)
    total_v2 = settle_total(con)
    stale = ApprovalTicket(
        "APR-2026-06-30-003", "chief-financial-officer", "cfo",
        "release-june-settlement", contract_v1.digest, fp_v1,
        policy_v1.digest, "2026-06-30", "2026-07-02")
    drift = gate.admit(stale, amount=total_v2,
                       contract_digest=settlement_contract(con).digest,
                       artifact_fingerprint=settlement_fingerprint(con),
                       policy=policy_v1, today="2026-07-01")
    print(f"   E0007+E0012 补发后结算集 {total_v2:,.0f} "
          f"(+{total_v2 - total:,.0f})")
    print(f"   上周的 CFO 票据 -> admitted={drift.admitted}")
    for f in drift.findings:
        print(f"      {f.code} :: {f.evidence}")
    print("   -> 38,444 想搭上周那句“同意”的车进来，票面指纹对不上，门是关的。")

    widen = PolicyCard("cash-line", 2, "finance-controller",
                       "portfolio claimed total must stay under",
                       30_000_000, "one-off retro payment window")
    try:
        issue_policy_gated(
            widen,
            ApprovalTicket("APR-2026-07-01-004", "payroll-supervisor",
                           "payroll-supervisor", "widen-cash-line",
                           contract_v1.digest, widen.digest,
                           policy_v1.digest, "2026-07-01", "2026-07-03"),
            gate, current_policy=policy_v1, today="2026-07-01")
    except PermissionError as err:
        print(f"   widening by supervisor ticket: {err}")
    issued = issue_policy_gated(
        widen,
        ApprovalTicket("APR-2026-07-01-005", "chief-financial-officer",
                       "cfo", "widen-cash-line", contract_v1.digest,
                       widen.digest, policy_v1.digest,
                       "2026-07-01", "2026-07-03"),
        gate, current_policy=policy_v1, today="2026-07-01")
    print(f"   widening by CFO ticket: issued cash-line v{issued.version} "
          f"digest={issued.digest}")
    print("   -> 36 讲给策略钉了身份，这一讲把“改策略”本身也送进了门。")


if __name__ == "__main__":
    main()
