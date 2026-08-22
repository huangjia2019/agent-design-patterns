"""A no-key lab for evidence-aware fan-out/gather.

Run from the repository root:
    python3 collaboration/light_labs/editorial_gather_lab.py
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal


Dimension = Literal["session", "workspace", "tools"]
Boundary = Literal["isolated", "shared", "restricted"]
REQUIRED_DIMENSIONS: tuple[Dimension, ...] = ("session", "workspace", "tools")


@dataclass(frozen=True)
class EvidenceCard:
    """One worker's finding about one precisely named boundary."""

    worker_id: str
    dimension: Dimension
    boundary: Boundary
    claim: str
    source_id: str
    source_url: str


@dataclass(frozen=True)
class GatherReport:
    """A typed result that keeps coverage, conflicts, and attribution."""

    verdict: Literal["isolated", "qualified", "insufficient"]
    accepted: bool
    missing_dimensions: tuple[Dimension, ...]
    conflicting_dimensions: tuple[Dimension, ...]
    cards: tuple[EvidenceCard, ...]


CARDS: tuple[EvidenceCard, ...] = (
    EvidenceCard(
        "atlas",
        "session",
        "isolated",
        "Spawn workers use a separate session context.",
        "dsh subagent docs",
        "https://github.com/deepseek-ai/deepseek-harness/blob/main/docs/subsystems/subagent.md",
    ),
    EvidenceCard(
        "birch",
        "workspace",
        "shared",
        "In-process workers can still see the parent workspace.",
        "dsh spawn provider",
        "https://github.com/deepseek-ai/deepseek-harness/tree/main/packages/subagent",
    ),
    EvidenceCard(
        "comet",
        "tools",
        "restricted",
        "Each worker receives a filtered tool catalog.",
        "dsh tool filter",
        "https://github.com/deepseek-ai/deepseek-harness/blob/main/docs/subsystems/subagent.md",
    ),
)


def flatten_and_vote(cards: tuple[EvidenceCard, ...]) -> tuple[str, int]:
    """Demonstrate the lossy shortcut: flatten unlike dimensions into yes/no."""

    votes = Counter("shared" if card.boundary == "shared" else "isolated" for card in cards)
    answer, support = votes.most_common(1)[0]
    return answer, support


def gather(cards: tuple[EvidenceCard, ...]) -> GatherReport:
    """Accept only complete, source-backed, non-conflicting boundary evidence."""

    by_dimension: dict[Dimension, list[EvidenceCard]] = {
        dimension: [] for dimension in REQUIRED_DIMENSIONS
    }
    for card in cards:
        by_dimension[card.dimension].append(card)

    missing = tuple(
        dimension for dimension, matches in by_dimension.items() if not matches
    )
    conflicts = tuple(
        dimension
        for dimension, matches in by_dimension.items()
        if len({card.boundary for card in matches}) > 1
    )
    sources_present = all(card.source_id and card.source_url.startswith("http") for card in cards)
    accepted = not missing and not conflicts and sources_present

    if not accepted:
        verdict: Literal["isolated", "qualified", "insufficient"] = "insufficient"
    elif all(card.boundary == "isolated" for card in cards):
        verdict = "isolated"
    else:
        verdict = "qualified"

    return GatherReport(
        verdict=verdict,
        accepted=accepted,
        missing_dimensions=missing,
        conflicting_dimensions=conflicts,
        cards=cards,
    )


def main() -> None:
    answer, support = flatten_and_vote(CARDS)
    shared = next(card for card in CARDS if card.dimension == "workspace")
    print("== flatten and vote ==")
    print(f"answer={answer} support={support}/{len(CARDS)}")
    print(f"lost={shared.dimension}:{shared.boundary}")

    report = gather(CARDS)
    print("\n== evidence-aware gather ==")
    print(f"verdict={report.verdict} admitted={str(report.accepted).lower()}")
    for card in report.cards:
        print(
            f"{card.dimension:<9} boundary={card.boundary:<10} "
            f"source={card.source_id}"
        )
    print("risk=workspace_shared")


if __name__ == "__main__":
    main()
