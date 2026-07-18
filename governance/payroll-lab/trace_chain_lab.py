"""Lecture 40 hands-on: after the incident, who can put the night back
together?

Three scenes on the month-end payroll world, no API key, no database
damage. Every import here is committed code; the d-observability-harness
pattern industrializes what scene 2 sketches.

    scene 1  state without history: run one governed day with the
             lecture 36-39 objects, then ask three questions. How did
             the Ops envelope spend its 2,748,960 -- how many draws, in
             what order? EnvelopeState holds one number: spent. When
             was the CFO ticket consumed, against which settlement
             version? The gate holds a set of ticket ids. What level
             was the agent last week? AuthorityRecord holds the level
             it has now. Three questions, three final states, zero
             history. Every object remembers where it ended and nothing
             about how it got there.
    scene 2  the trace chain: an append-only sequence of TraceEvent
             entries, each hash-linked to the one before. Every
             governed action passes four stations -- proposal, policy,
             decision, receipt -- and the recorder is not a listener
             on the side: the action goes THROUGH it, so a station can
             be missing only visibly. Editing one entry after the fact
             breaks the chain at exactly that link; skipping a receipt
             leaves a hole the completeness check names.
    scene 3  rebuilding July 8: the full story of lectures 36-39 runs
             again, instrumented -- policy pinned, ticket admitted, 798
             draws, promotion, incident, demotion. Then the chain
             answers scene 1's three questions from the record alone,
             and prints the ordered timeline of the incident day.

Totals are computed from the bench ledger, not typed in. The chain is a
teaching minimum: in-process, single writer, no persistence, no
external anchor for the head hash, no redaction story for sensitive
payloads. Those belong to the pattern, not the intro lab.

Run `python3 trace_chain_lab.py` from the repo root.
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


# Lecture 39's lab chains to 38, 37 and 36. One import brings the whole
# governed world: ladder, envelopes, tickets, policy cards, bench.
_lab39 = load_module(HERE / "authority_ladder_lab.py", "lab39_dep")
_lab38 = sys.modules["lab38_dep"]
_lab37 = sys.modules["lab37_dep"]

month_end = _lab38.month_end
dept_batches = _lab38.dept_batches
execute_settlement = _lab38.execute_settlement
paid_total = _lab38.paid_total
build_book = _lab38.build_book

settle_total = _lab37.settle_total
settlement_fingerprint = _lab37.settlement_fingerprint
settlement_contract = _lab37.settlement_contract
ApprovalGate = _lab37.ApprovalGate
ApprovalTicket = _lab37.ApprovalTicket
PolicyCard = _lab37.PolicyCard

AuthorityRecord = _lab39.AuthorityRecord
demote = _lab39.demote

_bc = sys.modules["collaboration.boundary_contract"]
Finding = _bc.Finding

MONTH = _lab37.MONTH
GENESIS = "0" * 16
REQUIRED_STATIONS = ("proposal", "policy", "decision", "receipt")


# ---- scene 2: the trace chain ---------------------------------------------------

def payload_digest(payload) -> str:
    canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True,
                           separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def entry_hash(seq: int, day: str, action_id: str, kind: str, actor: str,
               summary: str, digest: str, prev_hash: str) -> str:
    canonical = json.dumps(
        [seq, day, action_id, kind, actor, summary, digest, prev_hash],
        ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class TraceEvent:
    """One thing that happened, sealed to everything that happened
    before it."""

    seq: int
    day: str
    action_id: str
    kind: str
    actor: str
    summary: str
    payload_digest: str
    prev_hash: str
    entry_hash: str


class TraceChain:
    """Append-only. There is no update and no delete; a mistake is
    corrected by appending a correction that says so."""

    def __init__(self) -> None:
        self._entries: list[TraceEvent] = []

    def head(self) -> str:
        return self._entries[-1].entry_hash if self._entries else GENESIS

    def append(self, *, day: str, action_id: str, kind: str, actor: str,
               summary: str, payload) -> TraceEvent:
        seq = len(self._entries)
        digest = payload_digest(payload)
        prev = self.head()
        event = TraceEvent(
            seq=seq, day=day, action_id=action_id, kind=kind, actor=actor,
            summary=summary, payload_digest=digest, prev_hash=prev,
            entry_hash=entry_hash(seq, day, action_id, kind, actor,
                                  summary, digest, prev))
        self._entries.append(event)
        return event

    def entries(self) -> tuple:
        return tuple(self._entries)

    @staticmethod
    def verify(entries) -> tuple:
        """Walk the chain and report every link that does not hold."""
        findings = []
        prev = GENESIS
        for event in entries:
            expected = entry_hash(
                event.seq, event.day, event.action_id, event.kind,
                event.actor, event.summary, event.payload_digest,
                event.prev_hash)
            if event.entry_hash != expected:
                findings.append(Finding(
                    code="trace_entry_tampered", field="entry_hash",
                    message="this entry does not hash to what it claims",
                    evidence=f"seq={event.seq} stored={event.entry_hash} "
                             f"recomputed={expected}"))
            if event.prev_hash != prev:
                findings.append(Finding(
                    code="trace_link_broken", field="prev_hash",
                    message="this entry is not sealed to its predecessor",
                    evidence=f"seq={event.seq} stored={event.prev_hash} "
                             f"expected={prev}"))
            prev = event.entry_hash
        return tuple(findings)

    def missing_stations(self, action_id: str) -> tuple:
        seen = {e.kind for e in self._entries if e.action_id == action_id}
        missing = tuple(s for s in REQUIRED_STATIONS if s not in seen)
        if not missing:
            return ()
        return (Finding(
            code="trace_incomplete", field="action_id",
            message="a governed action must pass all four stations",
            evidence=f"action={action_id} missing={','.join(missing)}"),)

    def timeline(self, day: str) -> tuple:
        return tuple(e for e in self._entries if e.day == day)


# ---- scene 3: one governed day, instrumented ------------------------------------

def governed_day(con, chain: TraceChain) -> dict:
    """Lectures 36-39 run again, but this time every step goes through
    the recorder. Returns handles the scenes and tests inspect."""
    policy = _lab39.cash_policy()
    gate = ApprovalGate()
    action = f"settle-{MONTH}"
    fp = settlement_fingerprint(con)
    total = settle_total(con)
    chain.append(day="2026-07-07", action_id=action, kind="proposal",
                 actor="settlement-supervisor",
                 summary=f"claim {total:,.0f} for 798 slips",
                 payload={"fingerprint": fp, "total": total})
    chain.append(day="2026-07-07", action_id=action, kind="policy",
                 actor="finance-controller",
                 summary=f"cash-line v{policy.version} in force",
                 payload={"digest": policy.digest, "value": policy.value})
    ticket = ApprovalTicket(
        ticket_id="APR-2026-07-07-040", approver="chief-financial-officer",
        approver_role="cfo", action=action,
        contract_digest=settlement_contract(con).digest,
        artifact_fingerprint=fp, policy_digest=policy.digest,
        issued_on="2026-07-07", expires_on="2026-07-08")
    decision = gate.admit(ticket, amount=total,
                          contract_digest=settlement_contract(con).digest,
                          artifact_fingerprint=fp, policy=policy,
                          today="2026-07-07")
    chain.append(day="2026-07-07", action_id=action, kind="decision",
                 actor=ticket.approver,
                 summary=f"ticket {ticket.ticket_id} "
                         f"admitted={decision.admitted} against {fp}",
                 payload={"ticket": ticket.ticket_id,
                          "admitted": decision.admitted,
                          "fingerprint": fp})
    book = build_book(con)
    payments, _ = execute_settlement(dept_batches(con), book=book,
                                     retry_storm=("none", 0))
    for dept, emp, amount in payments:
        chain.append(day="2026-07-07", action_id=action, kind="draw",
                     actor="bank-executor",
                     summary=f"env::{dept} {emp} {amount:,.0f}",
                     payload={"dept": dept, "emp": emp, "amount": amount})
    chain.append(day="2026-07-07", action_id=action, kind="receipt",
                 actor="portfolio-safety-boundary",
                 summary=f"paid {paid_total(payments):,.0f}",
                 payload={"paid": paid_total(payments)})

    record = AuthorityRecord("payroll-agent-v2", "autonomous", "2026-07-07")
    chain.append(day="2026-07-07", action_id="authority::payroll-agent-v2",
                 kind="authority", actor="authority-ledger",
                 summary=f"level={record.level} since={record.since_day}",
                 payload={"level": record.level, "since": record.since_day})
    chain.append(day="2026-07-08", action_id="authority::payroll-agent-v2",
                 kind="incident", actor="oncall-finance",
                 summary="INC-2026-07-08 duplicate pay attributed",
                 payload={"incident": "INC-2026-07-08"})
    record = demote(record, "INC-2026-07-08", "2026-07-08")
    chain.append(day="2026-07-08", action_id="authority::payroll-agent-v2",
                 kind="authority", actor="authority-ledger",
                 summary=f"level={record.level} since={record.since_day}",
                 payload={"level": record.level, "since": record.since_day})
    return {"record": record, "gate": gate, "book": book,
            "paid": paid_total(payments), "action": action}


# ---- scenes ---------------------------------------------------------------------

def main() -> None:
    import dataclasses

    con = month_end()
    print("== scene 1: state without history ==")
    handles = governed_day(con, TraceChain())  # same day, no one looks yet
    book, gate, record = handles["book"], handles["gate"], handles["record"]
    ops = book._children["env::Ops"]
    print(f"   Ops envelope after the day: spent={ops.spent:,.0f} "
          f"payments={ops.payments}")
    print(f"   the gate after the day: used={sorted(gate._used)}")
    print(f"   the agent after the incident: {record}")
    print("   -> 三个问题：这 2,748,960 是哪 160 笔、什么顺序？票据是几号、")
    print("      对着哪一版结算集用掉的？这个 agent 上周是什么等级？三个")
    print("      对象都只记得终态。中间发生过什么，进程一退出就没有了。")

    print("\n== scene 2: the chain refuses quiet edits ==")
    chain = TraceChain()
    handles = governed_day(con, chain)
    entries = chain.entries()
    print(f"   entries={len(entries)} head={chain.head()}")
    print(f"   verify clean: {len(TraceChain.verify(entries))} findings")
    tampered = list(entries)
    victim = next(e for e in tampered if e.kind == "receipt")
    tampered[victim.seq] = dataclasses.replace(
        victim, summary="paid 3,706,097")
    findings = TraceChain.verify(tuple(tampered))
    print(f"   edit entry {victim.seq} (the receipt) -> "
          f"{findings[0].code} :: {findings[0].evidence}")
    quiet = TraceChain()
    quiet.append(day="2026-07-07", action_id="settle-side", kind="proposal",
                 actor="payroll-agent", summary="claim 500,000",
                 payload={"total": 500_000})
    quiet.append(day="2026-07-07", action_id="settle-side", kind="draw",
                 actor="bank-executor", summary="paid off the books",
                 payload={"total": 500_000})
    hole = quiet.missing_stations("settle-side")
    print(f"   a settlement with no policy/decision/receipt -> "
          f"{hole[0].code} :: {hole[0].evidence}")
    print("   -> 记录不是旁听。动作从记录器中间过，改一格，那一格自己就")
    print("      对不上号。少一站，完整性检查点名少的是哪一站。")

    print("\n== scene 3: rebuilding July 8 from the chain alone ==")
    draws = [e for e in chain.entries()
             if e.kind == "draw" and e.summary.startswith("env::Ops")]
    print(f"   Q1 Ops 的钱怎么花的：{len(draws)} 笔，"
          f"第一笔 [{draws[0].seq}] {draws[0].summary}，"
          f"最后一笔 [{draws[-1].seq}] {draws[-1].summary}")
    decision = next(e for e in chain.entries() if e.kind == "decision")
    print(f"   Q2 票据什么时候用的：[{decision.seq}] {decision.day} "
          f"{decision.summary}")
    levels = [e for e in chain.entries() if e.kind == "authority"]
    history = " -> ".join(e.summary for e in levels)
    print(f"   Q3 等级历史：{history}")
    print("   incident-day timeline:")
    for e in chain.timeline("2026-07-08"):
        print(f"      [{e.seq}] {e.kind:<9} {e.actor:<16} {e.summary}")
    print("   -> 36 讲钉了策略，37 讲钉了批准，38 讲钉了额度，39 讲钉了")
    print("      权限。这一讲把它们发生过的每一步钉成一条链，事故那天")
    print("      的现场，从链上原样长回来。")


if __name__ == "__main__":
    main()
