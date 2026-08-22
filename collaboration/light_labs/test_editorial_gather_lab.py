"""Invariant tests for the lightweight fan-out/gather lab."""

from __future__ import annotations

import sys
from pathlib import Path


HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import editorial_gather_lab as lab  # noqa: E402


def test_flat_vote_erases_the_shared_workspace_boundary() -> None:
    answer, support = lab.flatten_and_vote(lab.CARDS)

    assert answer == "isolated"
    assert support == 2
    assert any(card.boundary == "shared" for card in lab.CARDS)


def test_typed_gather_preserves_all_three_boundaries() -> None:
    report = lab.gather(lab.CARDS)

    assert report.accepted is True
    assert report.verdict == "qualified"
    assert report.missing_dimensions == ()
    assert {card.dimension for card in report.cards} == set(lab.REQUIRED_DIMENSIONS)


def test_gather_rejects_a_missing_dimension() -> None:
    report = lab.gather(tuple(card for card in lab.CARDS if card.dimension != "tools"))

    assert report.accepted is False
    assert report.verdict == "insufficient"
    assert report.missing_dimensions == ("tools",)


def test_gather_rejects_conflicting_values_in_one_dimension() -> None:
    conflicting = lab.EvidenceCard(
        "delta",
        "workspace",
        "isolated",
        "A second worker interpreted workspace isolation differently.",
        "independent review",
        "https://example.com/independent-review",
    )

    report = lab.gather((*lab.CARDS, conflicting))

    assert report.accepted is False
    assert report.conflicting_dimensions == ("workspace",)
