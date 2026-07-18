"""Invariant tests for the lecture-39 authority-ladder lab."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab = load_module(HERE / "authority_ladder_lab.py", "authority_ladder_lab")
_bc = sys.modules["collaboration.boundary_contract"]

AGENT = "payroll-agent-v2"
OPS_TOTAL = 2_748_960.0
FULL = 13_706_097.0


def runs(level, day, n=3, clean=True, prefix="r"):
    return tuple(lab.RunReceipt(f"{prefix}-{i}", AGENT, level, day, clean)
                 for i in range(n))


def ticket(target, evidence, *, role, day):
    return lab.ticket_for(AGENT, target, evidence, role=role,
                          approver=f"{role}-person",
                          policy=lab.cash_policy(), day=day)


def promote(con, record, target, evidence, tck, gate=None, today=None):
    return lab.promote(con, record, target, evidence, tck,
                       gate or lab.ApprovalGate(), lab.cash_policy(),
                       today or tck.issued_on)


def test_a_read_only_scope_does_not_stop_a_full_settlement():
    con = lab.month_end()
    payments, refusals = lab.execute_settlement(
        lab.dept_batches(con), book=None, retry_storm=("none", 0))
    assert refusals == []
    assert lab.paid_total(payments) == FULL


def test_capabilities_grow_monotonically_up_the_chain():
    seen = set()
    for level in lab.LEVELS:
        caps = set(lab.CAPABILITIES[level])
        assert seen <= caps
        seen = caps
    assert "pay" not in lab.CAPABILITIES["shadow"]
    assert "pay" in lab.CAPABILITIES["limited"]


def test_a_lower_level_cannot_pay_and_the_refusal_names_the_needed_level():
    record = lab.AuthorityRecord(AGENT, "recommend", "2026-07-01")
    con = lab.month_end()
    paid, refused = lab.settle_as(con, record)
    assert paid == 0.0
    (finding,) = refused
    assert finding.code == "authority_level_insufficient"
    assert "allowed_at=limited" in finding.evidence


def test_promotion_moves_exactly_one_link():
    con = lab.month_end()
    record = lab.AuthorityRecord(AGENT, "observe", "2026-07-01")
    evidence = runs("observe", "2026-07-02")
    result, findings = promote(con, record, "shadow", evidence,
                               ticket("shadow", evidence,
                                      role="payroll-operator",
                                      day="2026-07-02"))
    assert result is None
    assert any(f.code == "promotion_skips_level" for f in findings)


def test_thin_dirty_and_stale_evidence_each_refuse_by_name():
    con = lab.month_end()
    record = lab.AuthorityRecord(AGENT, "observe", "2026-07-05")
    thin = runs("observe", "2026-07-06", n=2)
    _, f1 = promote(con, record, "recommend", thin,
                    ticket("recommend", thin, role="payroll-operator",
                           day="2026-07-06"))
    assert {f.code for f in f1} == {"promotion_evidence_thin"}
    dirty = runs("observe", "2026-07-06", clean=False)
    _, f2 = promote(con, record, "recommend", dirty,
                    ticket("recommend", dirty, role="payroll-operator",
                           day="2026-07-06"))
    assert "promotion_evidence_dirty" in {f.code for f in f2}
    stale = runs("observe", "2026-07-01")  # before since_day
    _, f3 = promote(con, record, "recommend", stale,
                    ticket("recommend", stale, role="payroll-operator",
                           day="2026-07-06"))
    assert "promotion_evidence_stale" in {f.code for f in f3}


def test_the_promotion_ticket_signer_is_routed_by_the_new_stake():
    con = lab.month_end()
    assert lab.promotion_stake(con, "autonomous") == FULL
    assert lab.required_role(lab.promotion_stake(con, "autonomous")) == "cfo"
    assert lab.required_role(lab.promotion_stake(con, "limited")) \
        == "payroll-supervisor"
    record = lab.AuthorityRecord(AGENT, "limited", "2026-07-05")
    evidence = runs("limited", "2026-07-06")
    _, findings = promote(con, record, "autonomous", evidence,
                          ticket("autonomous", evidence,
                                 role="payroll-supervisor",
                                 day="2026-07-07"))
    assert {f.code for f in findings} == {"approval_authority_mismatch"}
    result, findings = promote(con, record, "autonomous", evidence,
                               ticket("autonomous", evidence, role="cfo",
                                      day="2026-07-07"))
    assert findings == () and result.level == "autonomous"


def test_limited_settles_one_ops_envelope_and_autonomous_settles_all():
    con = lab.month_end()
    paid, refusals = lab.settle_as(
        con, lab.AuthorityRecord(AGENT, "limited", "2026-07-05"))
    assert paid == OPS_TOTAL
    assert len(refusals) == 798 - 160
    paid, refusals = lab.settle_as(
        con, lab.AuthorityRecord(AGENT, "autonomous", "2026-07-07"))
    assert paid == FULL and refusals == ()


def test_demotion_is_immediate_unsigned_and_resets_the_clock():
    record = lab.AuthorityRecord(AGENT, "autonomous", "2026-07-07")
    after = lab.demote(record, "INC-1", "2026-07-08")
    assert after.level == "observe"
    assert after.since_day == "2026-07-08"


def test_pre_incident_receipts_cannot_argue_for_re_promotion():
    con = lab.month_end()
    before = runs("limited", "2026-07-06", prefix="old")
    record = lab.demote(
        lab.AuthorityRecord(AGENT, "autonomous", "2026-07-07"),
        "INC-1", "2026-07-08")
    result, findings = promote(con, record, "recommend", before,
                               ticket("recommend", before,
                                      role="payroll-operator",
                                      day="2026-07-09"))
    assert result is None
    codes = {f.code for f in findings}
    assert codes == {"promotion_evidence_stale", "promotion_evidence_thin"}


def test_every_refusal_is_a_blocker_with_evidence():
    con = lab.month_end()
    record = lab.AuthorityRecord(AGENT, "observe", "2026-07-01")
    evidence = runs("limited", "2026-06-30", n=2, clean=False)
    _, findings = promote(con, record, "recommend", evidence,
                          ticket("recommend", evidence,
                                 role="payroll-operator",
                                 day="2026-07-02"))
    assert len(findings) >= 3
    for finding in findings:
        assert finding.severity is _bc.FindingSeverity.BLOCKER
        assert finding.evidence.strip()
