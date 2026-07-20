"""Invariant tests for the lecture-40 trace-chain lab."""
from __future__ import annotations

import dataclasses
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


lab = load_module(HERE / "trace_chain_lab.py", "trace_chain_lab")
_bc = sys.modules["collaboration.boundary_contract"]


def small_chain():
    chain = lab.TraceChain()
    for kind in lab.REQUIRED_STATIONS:
        chain.append(day="2026-07-07", action_id="act-1", kind=kind,
                     actor="t", summary=f"{kind} happened",
                     payload={"kind": kind})
    return chain


def test_every_entry_is_sealed_to_its_predecessor():
    chain = small_chain()
    entries = chain.entries()
    prev = lab.GENESIS
    for event in entries:
        assert event.prev_hash == prev
        prev = event.entry_hash
    assert chain.head() == entries[-1].entry_hash
    assert lab.TraceChain.verify(entries) == ()


def test_editing_one_entry_is_detected_at_exactly_that_link():
    chain = small_chain()
    entries = list(chain.entries())
    entries[2] = dataclasses.replace(entries[2], summary="something else")
    findings = lab.TraceChain.verify(tuple(entries))
    tampered = [f for f in findings if f.code == "trace_entry_tampered"]
    assert len(tampered) == 1
    assert "seq=2" in tampered[0].evidence


def test_dropping_an_entry_breaks_the_link_of_the_next_one():
    chain = small_chain()
    entries = list(chain.entries())
    del entries[1]
    findings = lab.TraceChain.verify(tuple(entries))
    assert any(f.code == "trace_link_broken" for f in findings)


def test_the_chain_head_is_deterministic_and_value_sensitive():
    a, b = small_chain(), small_chain()
    assert a.head() == b.head()
    c = lab.TraceChain()
    for kind in lab.REQUIRED_STATIONS:
        c.append(day="2026-07-07", action_id="act-1", kind=kind,
                 actor="t", summary=f"{kind} happened",
                 payload={"kind": kind, "amount": 999})
    assert c.head() != a.head()


def test_a_complete_action_passes_and_a_hole_is_named():
    chain = small_chain()
    assert chain.missing_stations("act-1") == ()
    chain.append(day="2026-07-07", action_id="act-2", kind="proposal",
                 actor="t", summary="claim", payload={})
    chain.append(day="2026-07-07", action_id="act-2", kind="draw",
                 actor="t", summary="paid", payload={})
    (finding,) = chain.missing_stations("act-2")
    assert finding.code == "trace_incomplete"
    assert "missing=policy,decision,receipt" in finding.evidence


def test_the_governed_day_produces_a_clean_complete_chain():
    con = lab.month_end()
    chain = lab.TraceChain()
    handles = lab.governed_day(con, chain)
    assert lab.TraceChain.verify(chain.entries()) == ()
    assert chain.missing_stations(handles["action"]) == ()
    assert handles["paid"] == 13_706_097.0


def test_the_chain_answers_what_the_final_states_cannot():
    con = lab.month_end()
    chain = lab.TraceChain()
    lab.governed_day(con, chain)
    ops_draws = [e for e in chain.entries()
                 if e.kind == "draw" and e.summary.startswith("env::Ops")]
    assert len(ops_draws) == 160
    assert [e.seq for e in ops_draws] == sorted(e.seq for e in ops_draws)
    decision = next(e for e in chain.entries() if e.kind == "decision")
    assert "APR-2026-07-07-040" in decision.summary
    assert lab.settlement_fingerprint(con) in decision.summary
    levels = [e.summary for e in chain.entries() if e.kind == "authority"]
    assert levels == ["level=autonomous since=2026-07-07",
                      "level=observe since=2026-07-08"]


def test_the_incident_day_timeline_is_ordered_and_complete():
    con = lab.month_end()
    chain = lab.TraceChain()
    lab.governed_day(con, chain)
    timeline = chain.timeline("2026-07-08")
    assert [e.kind for e in timeline] == ["incident", "authority"]
    assert timeline[0].seq < timeline[1].seq


def test_the_scene1_objects_really_hold_no_history():
    con = lab.month_end()
    handles = lab.governed_day(con, lab.TraceChain())
    ops = handles["book"]._children["env::Ops"]
    assert set(vars(ops)) == {"envelope", "spent", "payments"}
    assert handles["gate"]._used == {"APR-2026-07-07-040"}
    record_fields = {f.name for f in dataclasses.fields(handles["record"])}
    assert record_fields == {"agent_id", "level", "since_day"}


def test_verification_findings_are_blockers_with_evidence():
    chain = small_chain()
    entries = list(chain.entries())
    entries[1] = dataclasses.replace(entries[1], summary="edited")
    del entries[3]
    findings = lab.TraceChain.verify(tuple(entries))
    assert findings
    for finding in findings:
        assert finding.severity is _bc.FindingSeverity.BLOCKER
        assert finding.evidence.strip()
