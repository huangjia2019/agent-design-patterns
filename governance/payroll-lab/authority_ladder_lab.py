"""Lecture 39 hands-on: where does an agent's authority come from?

Three scenes on the month-end payroll world, no API key, no database
damage (payments are simulated in memory). Every import here is
committed code; the c-progressive-commitment pattern industrializes
what scenes 2 and 3 sketch.

    scene 1  authority on paper: every TaskContract in this course
             declares an authority_scope, the digest seals it, tests
             assert it -- and not one committed line reads it when an
             action happens. A contract that grants read:roster only
             watches its worker pay out 13,706,097. Deployed today,
             track record zero, full write authority: nothing in the
             committed world even has a field for "how long has this
             agent been trusted".
    scene 2  the ladder: authority becomes a chain of levels --
             observe, recommend, shadow, limited, autonomous. Each
             level names what it may do. Promotion moves exactly one
             link up and needs three things: fresh clean runs earned at
             the current level, a promotion fingerprint, and a lecture-37
             approval ticket whose signer is routed by the money the
             new level can touch. Skipping a link, thin evidence, stale
             evidence, dirty evidence: each dies with its own finding.
    scene 3  the asymmetry: at "limited" the agent holds one Ops-sized
             envelope (lecture 38) and can settle 2,748,960 of the
             month; promotion to "autonomous" needs a CFO ticket, then
             the full 13,706,097 flows. One incident later the agent
             drops from autonomous to observe in a single move -- no
             ticket, no chain -- and its old receipts are stale for
             re-promotion. Climbing is link by link; falling is
             immediate. Authority is earned slowly and lost at once.

Totals are computed from the bench ledger, not typed in. The ladder is
a teaching minimum: no decay of unused authority, no per-capability
ladders, no probation timers, no appeal path. Those belong to the
pattern, not the intro lab.

Run `python3 authority_ladder_lab.py` from the repo root.
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


# Lecture 38's lab chains to 37's and 36's. One import brings the bench,
# the envelopes, the tickets and the policy cards.
_lab38 = load_module(HERE / "budget_envelope_lab.py", "lab38_dep")
_lab37 = sys.modules["lab37_dep"]

month_end = _lab38.month_end
dept_batches = _lab38.dept_batches
execute_settlement = _lab38.execute_settlement
paid_total = _lab38.paid_total
build_book = _lab38.build_book
BudgetEnvelope = _lab38.BudgetEnvelope
BudgetBook = _lab38.BudgetBook

settle_total = _lab37.settle_total
ApprovalTicket = _lab37.ApprovalTicket
ApprovalGate = _lab37.ApprovalGate
required_role = _lab37.required_role
PolicyCard = _lab37.PolicyCard

_bc = sys.modules["collaboration.boundary_contract"]
Finding = _bc.Finding
TaskContract = _bc.TaskContract

MONTH = _lab37.MONTH

# ---- the chain ------------------------------------------------------------------

LEVELS = ("observe", "recommend", "shadow", "limited", "autonomous")

CAPABILITIES = {
    "observe": ("read",),
    "recommend": ("read", "draft"),
    "shadow": ("read", "draft", "shadow_run"),
    "limited": ("read", "draft", "shadow_run", "pay"),
    "autonomous": ("read", "draft", "shadow_run", "pay"),
}

# How much money the new level can touch. The lecture-37 routing table
# turns this stake into the role that must sign the promotion ticket.
PROMOTION_STAKES = {
    "recommend": 0.0,
    "shadow": 0.0,
    "limited": 3_000_000.0,
}
EVIDENCE_QUORUM = 3


@dataclass(frozen=True)
class RunReceipt:
    run_id: str
    agent_id: str
    level: str
    day: str
    clean: bool


@dataclass(frozen=True)
class AuthorityRecord:
    """What the agent is trusted to do today, and since when."""

    agent_id: str
    level: str
    since_day: str


def promotion_fingerprint(agent_id: str, target: str, evidence) -> str:
    canonical = json.dumps(
        {"agent_id": agent_id, "target": target,
         "runs": sorted(r.run_id for r in evidence)},
        ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def promotion_stake(con, target: str) -> float:
    if target == "autonomous":
        return settle_total(con)
    return PROMOTION_STAKES[target]


def promote(con, record: AuthorityRecord, target: str, evidence,
            ticket: ApprovalTicket, gate: ApprovalGate,
            policy: PolicyCard, today: str):
    """One link up the chain, on fresh evidence, behind the gate."""
    findings = []
    next_level = LEVELS[LEVELS.index(record.level) + 1] \
        if record.level != LEVELS[-1] else None
    if target != next_level:
        findings.append(Finding(
            code="promotion_skips_level", field="level",
            message="promotion moves exactly one link up the chain",
            evidence=f"current={record.level} target={target} "
                     f"next={next_level}"))
    usable = [r for r in evidence if r.agent_id == record.agent_id
              and r.clean and r.level == record.level
              and r.day >= record.since_day]
    stale = [r for r in evidence if r.level != record.level
             or r.day < record.since_day]
    dirty = [r for r in evidence if not r.clean]
    if dirty:
        findings.append(Finding(
            code="promotion_evidence_dirty", field="evidence",
            message="a failed run cannot argue for more authority",
            evidence=f"dirty_runs={sorted(r.run_id for r in dirty)}"))
    if stale:
        findings.append(Finding(
            code="promotion_evidence_stale", field="evidence",
            message="evidence must be earned at the current level, "
                    "after the last transition",
            evidence=f"stale_runs={sorted(r.run_id for r in stale)} "
                     f"since={record.since_day}"))
    if len(usable) < EVIDENCE_QUORUM:
        findings.append(Finding(
            code="promotion_evidence_thin", field="evidence",
            message="not enough fresh clean runs at the current level",
            evidence=f"usable={len(usable)} required={EVIDENCE_QUORUM}"))
    if findings:
        return None, tuple(findings)
    decision = gate.admit(
        ticket, amount=promotion_stake(con, target),
        contract_digest=ticket.contract_digest,
        artifact_fingerprint=promotion_fingerprint(
            record.agent_id, target, evidence),
        policy=policy, today=today)
    if not decision.admitted:
        return None, decision.findings
    return AuthorityRecord(record.agent_id, target, today), ()


def demote(record: AuthorityRecord, incident_id: str,
           today: str) -> AuthorityRecord:
    """Any distance down, immediately, no ticket. The incident is the
    evidence; the fall does not wait for a signature."""
    return AuthorityRecord(record.agent_id, "observe", today)


def allowed(record: AuthorityRecord, capability: str):
    if capability in CAPABILITIES[record.level]:
        return ()
    needed = next(lv for lv in LEVELS if capability in CAPABILITIES[lv])
    return (Finding(
        code="authority_level_insufficient", field="capability",
        message="this capability lives higher up the ladder",
        evidence=f"level={record.level} capability={capability} "
                 f"allowed_at={needed}"),)


def level_book(con, record: AuthorityRecord) -> BudgetBook | None:
    """What lecture 38 gives each level: limited holds one Ops-sized
    envelope, autonomous holds the full settlement tree."""
    if record.level == "autonomous":
        return build_book(con)
    if record.level == "limited":
        ops = dict(dept_batches(con))["Ops"]
        root = BudgetEnvelope(
            envelope_id="env::root::limited", holder=record.agent_id,
            max_amount=3_000_000.0, max_payments=len(ops),
            allowed_refs=frozenset(emp for emp, _ in ops))
        book = BudgetBook(root)
        book.reserve(BudgetEnvelope(
            envelope_id="env::Ops", holder=record.agent_id,
            max_amount=sum(a for _, a in ops), max_payments=len(ops),
            allowed_refs=frozenset(emp for emp, _ in ops)))
        return book
    return None


def settle_as(con, record: AuthorityRecord):
    """The whole stack in one call: capability gate, then envelopes."""
    refused = allowed(record, "pay")
    if refused:
        return 0.0, refused
    book = level_book(con, record)
    payments, refusals = execute_settlement(
        dept_batches(con), book=book, retry_storm=("none", 0))
    return paid_total(payments), tuple(refusals)


# ---- scenes ---------------------------------------------------------------------

def cash_policy() -> PolicyCard:
    return PolicyCard("cash-line", 1, "finance-controller",
                      "portfolio claimed total must stay under",
                      13_000_000, "2026 annual budget line")


def ticket_for(agent: str, target: str, evidence, *, role: str,
               approver: str, policy: PolicyCard,
               day: str) -> ApprovalTicket:
    return ApprovalTicket(
        ticket_id=f"APR-{day}-{target}", approver=approver,
        approver_role=role, action=f"promote:{agent}:{target}",
        contract_digest="authority-ledger",
        artifact_fingerprint=promotion_fingerprint(agent, target, evidence),
        policy_digest=policy.digest, issued_on=day,
        expires_on=day)


def main() -> None:
    con = month_end()
    total = settle_total(con)
    print("== scene 1: authority on paper ==")
    read_only = TaskContract(
        contract_id=f"settle-{MONTH}-readonly", version=1,
        objective="observe the June settlement",
        output_schema="PayrollPortfolioResult",
        accountable_owner="payroll-agent-v2",
        authority_scope=("read:roster",),
    )
    print(f"   contract grants: {read_only.authority_scope}")
    payments, _ = execute_settlement(dept_batches(con), book=None,
                                     retry_storm=("none", 0))
    print(f"   worker pays anyway: {paid_total(payments):,.0f}")
    print("   -> authority_scope 写进了契约、进了摘要、进了测试断言。可是在")
    print("      动作发生的那一行，已提交的代码没有任何一处读它。授权只在")
    print("      纸上。这个 agent 今天刚部署，战绩为零，实付权限是满的。")

    print("\n== scene 2: the ladder, link by link ==")
    policy = cash_policy()
    gate = ApprovalGate()
    record = AuthorityRecord("payroll-agent-v2", "observe", "2026-07-01")
    print(f"   {record.agent_id}: level={record.level} "
          f"since={record.since_day}")
    _, refused = settle_as(con, record)
    print(f"   try to pay -> {refused[0].code} :: {refused[0].evidence}")
    skip = promote(con, record, "limited", (), ApprovalTicket(
        "APR-skip", "cfo", "cfo", "promote", "authority-ledger",
        "x", policy.digest, "2026-07-02", "2026-07-02"),
        gate, policy, "2026-07-02")
    print(f"   observe -> limited in one jump -> {skip[1][0].code}")
    thin_runs = tuple(RunReceipt(f"run-{i}", record.agent_id, "observe",
                                 "2026-07-02", True) for i in range(2))
    thin = promote(con, record, "recommend", thin_runs, ticket_for(
        record.agent_id, "recommend", thin_runs,
        role="payroll-operator", approver="ops-desk", policy=policy,
        day="2026-07-02"), gate, policy, "2026-07-02")
    print(f"   two clean runs only -> {thin[1][0].code} :: "
          f"{thin[1][0].evidence}")
    runs = tuple(RunReceipt(f"run-{i}", record.agent_id, "observe",
                            "2026-07-02", True) for i in range(3))
    record, _ = promote(con, record, "recommend", runs, ticket_for(
        record.agent_id, "recommend", runs,
        role="payroll-operator", approver="ops-desk", policy=policy,
        day="2026-07-03"), gate, policy, "2026-07-03")
    print(f"   three fresh runs + operator ticket -> level={record.level}")
    print("   -> 晋级恰好一格，证据要新、要干净、要在本级挣的，票据的签字人")
    print("      由新等级能碰到的钱决定。")

    print("\n== scene 3: the asymmetry ==")
    record = AuthorityRecord("payroll-agent-v2", "limited", "2026-07-05")
    paid, refusals = settle_as(con, record)
    print(f"   limited: paid {paid:,.0f}, "
          f"{len(refusals)} draws outside the envelope refused")
    limited_runs = tuple(RunReceipt(f"lrun-{i}", record.agent_id,
                                    "limited", "2026-07-06", True)
                         for i in range(3))
    wrong = promote(con, record, "autonomous", limited_runs, ticket_for(
        record.agent_id, "autonomous", limited_runs,
        role="payroll-supervisor", approver="shift-lead", policy=policy,
        day="2026-07-07"), gate, policy, "2026-07-07")
    print(f"   supervisor signs the autonomous ticket -> "
          f"{wrong[1][0].code} :: {wrong[1][0].evidence}")
    record, _ = promote(con, record, "autonomous", limited_runs,
                        ticket_for(record.agent_id, "autonomous",
                                   limited_runs, role="cfo",
                                   approver="chief-financial-officer",
                                   policy=policy, day="2026-07-07"),
                        gate, policy, "2026-07-07")
    paid, _ = settle_as(con, record)
    print(f"   autonomous: paid {paid:,.0f}")
    record = demote(record, "INC-2026-07-08-dupe-pay", "2026-07-08")
    print(f"   incident INC-2026-07-08 -> level={record.level} "
          f"since={record.since_day} (no ticket, one move)")
    retry = promote(con, record, "recommend", limited_runs, ticket_for(
        record.agent_id, "recommend", limited_runs,
        role="payroll-operator", approver="ops-desk", policy=policy,
        day="2026-07-09"), gate, policy, "2026-07-09")
    codes = ",".join(f.code for f in retry[1])
    print(f"   re-promotion on pre-incident receipts -> {codes}")
    print("   -> 升级一格一格走链，降级一步到底。事故之前攒的证据，事故")
    print("      之后一张都不算数，信任从头挣。")


if __name__ == "__main__":
    main()
