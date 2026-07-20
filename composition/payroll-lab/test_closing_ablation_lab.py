"""Invariant tests for the course-finale leave-one-out capstone lab."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab = _load(HERE / "closing_ablation_lab.py", "closing_ablation_lab")


def test_the_full_day_verifies_all_seven_layers():
    run = lab.run_day()
    assert run["all_verified"] is True
    assert run["verified"] == set(lab.SEATS)
    assert run["missing"] == set()
    assert run["defect_blocked"] is True
    assert run["reconstructable"] is True
    assert run["chain"].verify() is True


def test_the_gross_to_net_gap_is_the_two_reversed_payslips():
    assert lab.GROSS_TO_NET_GAP == 38_444
    assert lab.REVERSALS == {"E0007": 30_000.0, "E0012": 8_444.0}


def test_leave_one_out_darkens_exactly_the_dropped_seat():
    # Each seat is an independent detection/containment layer: knocking one
    # out removes exactly that link and leaves the other six verified.
    for seat in lab.SEATS:
        run = lab.run_day(drop=seat)
        assert run["missing"] == {seat}, seat
        assert run["verified"] == set(lab.SEATS) - {seat}, seat
        # The chain still records every seat -- a dark link is visible.
        assert len(run["chain"].receipts) == len(lab.SEATS)
        assert run["chain"].verify() is True


def test_dropping_action_lets_the_defect_reach_the_payslip():
    run = lab.run_day(drop="action")
    assert run["defect_blocked"] is False
    # Only the write gate is a containment seat; detection seats do not
    # by themselves stop the write.
    assert run["reconstructable"] is True


def test_dropping_governance_makes_the_night_unreconstructable():
    run = lab.run_day(drop="governance")
    assert run["reconstructable"] is False
    assert run["defect_blocked"] is True


def test_the_detection_seats_do_not_touch_containment_or_audit():
    for seat in ("perception", "memory", "reasoning",
                 "collaboration", "reflection"):
        run = lab.run_day(drop=seat)
        assert run["defect_blocked"] is True, seat
        assert run["reconstructable"] is True, seat


def test_editing_one_receipt_breaks_the_chain_at_that_link():
    chain = lab.run_day()["chain"]
    assert chain.verify() is True
    victim = chain._entries[3]
    chain._entries[3] = lab.Receipt(
        victim.seq, victim.seat, victim.claim, not victim.ok,
        victim.evidence_digest, victim.prev_hash, victim.entry_hash)
    assert chain.verify() is False


def test_only_committed_engines_are_imported():
    # Four seats wrap a real committed pattern engine; none of them is
    # Codex's uncommitted capstone_lab.py.
    assert hasattr(lab._TRIAGE, "ContextTriage")
    assert hasattr(lab._HYP, "IterativeHypothesisLoop")
    assert hasattr(lab._FANOUT, "Reconciler")
    assert hasattr(lab._CRITIC, "GeneratorCriticChain")


def test_unknown_seat_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        lab.run_day(drop="nonsense")
