"""Invariant tests for the lecture-36 governance-intro lab."""
from __future__ import annotations

import importlib.util
import sys
from contextlib import closing
from pathlib import Path

import pytest

HERE = Path(__file__).parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lab = load_module(HERE / "ungoverned_policy_lab.py", "ungoverned_lab")
_bc = sys.modules["collaboration.boundary_contract"]

GROSS = 13_706_097.0


def test_every_inventory_literal_is_still_in_the_committed_source():
    rows = lab.verify_inventory()
    assert len(rows) == 6
    assert all(row["found"] for row in rows)


def test_the_cash_line_escalates_and_the_widened_line_accepts():
    with closing(lab.month_end()) as con:
        assert lab.june_gross(con) == GROSS
        strict = lab.evaluate_with_limit(con, 13_000_000)
        loose = lab.evaluate_with_limit(con, 30_000_000)
        assert strict.decision is _bc.AcceptanceDecision.ESCALATED
        assert {f.code for f in strict.findings} == {"portfolio_amount_exceeded"}
        assert loose.decision is _bc.AcceptanceDecision.ACCEPTED


def test_only_the_refusal_receipt_names_the_policy():
    with closing(lab.month_end()) as con:
        strict = lab.evaluate_with_limit(con, 13_000_000)
        loose = lab.evaluate_with_limit(con, 30_000_000)
        assert any("limit=13000000" in mark for mark in lab.policy_traces(strict))
        assert lab.policy_traces(loose) == []
        # Field-precise: no scalar field of the acceptance receipt mentions the
        # limit that judged it, under either spelling.
        from dataclasses import fields
        for f in fields(loose):
            value = getattr(loose, f.name)
            if isinstance(value, str):
                assert "30000000" not in value and "30,000,000" not in value
        assert loose.findings == ()


def test_policy_card_digest_is_deterministic_and_value_sensitive():
    a = lab.PolicyCard("cash-line", 1, "finance-controller", "r", 13_000_000, "x")
    b = lab.PolicyCard("cash-line", 1, "finance-controller", "r", 13_000_000, "x")
    c = lab.PolicyCard("cash-line", 1, "finance-controller", "r", 30_000_000, "x")
    assert a.digest == b.digest
    assert a.digest != c.digest


def test_governed_receipts_pin_the_policy_that_judged_them():
    with closing(lab.month_end()) as con:
        v1 = lab.PolicyCard("cash-line", 1, "fc", "r", 13_000_000, "budget")
        v2 = lab.PolicyCard("cash-line", 2, "fc", "r", 30_000_000, "retro window")
        g1 = lab.evaluate_governed(con, v1)
        g2 = lab.evaluate_governed(con, v2)
        assert g1.policy_digest == v1.digest and g2.policy_digest == v2.digest
        assert g1.policy_digest != g2.policy_digest
        assert g1.receipt.decision is _bc.AcceptanceDecision.ESCALATED
        assert g2.receipt.decision is _bc.AcceptanceDecision.ACCEPTED


def test_change_control_requires_distinct_proposer_and_approver():
    card = lab.PolicyCard("cash-line", 3, "fc", "r", 99_000_000, "why not")
    with pytest.raises(PermissionError):
        lab.issue_policy(card, proposed_by="agent-x", approved_by="agent-x")
    assert lab.issue_policy(card, proposed_by="fc", approved_by="cfo") is card


def test_structured_policy_drift_scene_is_ready_for_the_workbench():
    result = lab.run_policy_drift()

    assert result["inventory"]["verified"] == result["inventory"]["count"] == 6
    assert result["before"]["decision"] == "escalated"
    assert result["after"]["decision"] == "accepted"
    assert result["before"]["raw_policy_marks"]
    assert result["after"]["raw_policy_marks"] == ()
    assert result["before"]["policy_digest"] != result["after"]["policy_digest"]
