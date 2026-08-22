"""Invariant tests for the lightweight adversarial review lab."""

from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import editorial_review_lab as lab  # noqa: E402


def test_comments_without_a_gate_do_not_stop_publication() -> None:
    proposal = lab.risky_proposal()
    receipt = lab.review(proposal)

    assert len(receipt.objections) == 2
    assert lab.weak_publish(proposal, receipt) is True


def test_blockers_prevent_the_risky_claim_from_publishing() -> None:
    proposal = lab.risky_proposal()
    receipt = lab.review(proposal)

    assert receipt.passed is False
    assert lab.gated_publish(proposal, receipt) is False


def test_revised_claim_can_pass_the_same_review_contract() -> None:
    proposal = lab.revised_proposal()
    receipt = lab.review(proposal)

    assert receipt.objections == ()
    assert receipt.passed is True
    assert lab.gated_publish(proposal, receipt) is True


def test_old_receipt_cannot_authorize_a_new_version() -> None:
    old_receipt = lab.review(lab.risky_proposal())
    revised = lab.revised_proposal()

    assert old_receipt.authorizes(revised) is False


def test_source_change_invalidates_an_old_receipt() -> None:
    original = lab.revised_proposal()
    receipt = lab.review(original)
    changed = lab.Proposal(
        original.proposal_id,
        original.version,
        original.text,
        "different-source",
    )

    assert receipt.authorizes(changed) is False
