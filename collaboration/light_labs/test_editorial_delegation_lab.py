"""Invariant tests for the lightweight hierarchical delegation lab."""

from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import editorial_delegation_lab as lab  # noqa: E402


def test_vague_delegation_repeats_one_lane_and_misses_two() -> None:
    decision = lab.run(lab.vague_assignments())

    assert decision.accepted is False
    assert decision.coverage == 1
    assert decision.duplicate_lanes == 2
    assert decision.missing_lanes == ("state", "handoff")
    assert {card.lane for card in decision.cards} == {"topology"}


def test_scoped_delegation_covers_the_whole_brief_once() -> None:
    decision = lab.run(lab.scoped_assignments())

    assert decision.accepted is True
    assert decision.coverage == 3
    assert decision.duplicate_lanes == 0
    assert decision.missing_lanes == ()
    assert {card.lane for card in decision.cards} == set(lab.REQUIRED_LANES)


def test_portfolio_gate_rejects_a_duplicate_even_when_cards_are_valid() -> None:
    assignments = [
        lab.Assignment("atlas", "topology", "Study team topology."),
        lab.Assignment("birch", "topology", "Study manager topology."),
        lab.Assignment("comet", "handoff", "Study handoffs."),
    ]

    decision = lab.run(assignments)

    assert decision.accepted is False
    assert decision.duplicate_lanes == 1
    assert decision.missing_lanes == ("state",)


def test_portfolio_gate_rejects_a_card_without_a_source() -> None:
    cards = [lab.research(assignment) for assignment in lab.scoped_assignments()]
    state_card = cards[1]
    cards[1] = lab.ResearchCard(
        worker_id=state_card.worker_id,
        lane=state_card.lane,
        claim=state_card.claim,
        source_id=state_card.source_id,
        source_url="",
    )

    decision = lab.review_cards(cards)

    assert decision.accepted is False
    assert decision.coverage == 3
    assert decision.duplicate_lanes == 0
