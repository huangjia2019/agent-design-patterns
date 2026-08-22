"""A no-key lab for responsibility-scoped hierarchical delegation.

Run from the repository root:
    python3 collaboration/light_labs/editorial_delegation_lab.py
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Literal


Lane = Literal["topology", "state", "handoff"]
REQUIRED_LANES: tuple[Lane, ...] = ("topology", "state", "handoff")


@dataclass(frozen=True)
class Assignment:
    """A bounded responsibility handed from the editor to one researcher."""

    worker_id: str
    lane: Lane | None
    question: str
    deliverable: str = "one claim card with a source"


@dataclass(frozen=True)
class ResearchCard:
    """The small artifact returned by a researcher."""

    worker_id: str
    lane: Lane
    claim: str
    source_id: str
    source_url: str


@dataclass(frozen=True)
class BriefDecision:
    """The parent agent's portfolio-level acceptance result."""

    accepted: bool
    coverage: int
    duplicate_lanes: int
    missing_lanes: tuple[Lane, ...]
    cards: tuple[ResearchCard, ...]


FACTS: dict[Lane, tuple[str, str, str]] = {
    "topology": (
        "CrewAI",
        "Crews coordinate agents while Flows provide structured control.",
        "https://docs.crewai.com/",
    ),
    "state": (
        "Claude Managed Agents",
        "Managed agents run in isolated session threads with scoped context.",
        "https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration",
    ),
    "handoff": (
        "A2A v1.0",
        "A2A separates conversational messages from deliverable artifacts.",
        "https://github.com/a2aproject/A2A/blob/main/docs/specification.md",
    ),
}


def research(assignment: Assignment) -> ResearchCard:
    """Return a deterministic card so the delegation failure stays reproducible."""

    # A vague brief falls back to the most visible topic in this fixture.
    lane: Lane = assignment.lane or "topology"
    source_id, claim, source_url = FACTS[lane]
    return ResearchCard(
        worker_id=assignment.worker_id,
        lane=lane,
        claim=claim,
        source_id=source_id,
        source_url=source_url,
    )


def review_cards(cards: list[ResearchCard]) -> BriefDecision:
    """Accept a portfolio only when every required lane appears exactly once."""

    counts = Counter(card.lane for card in cards)
    missing = tuple(lane for lane in REQUIRED_LANES if counts[lane] == 0)
    duplicate_count = sum(max(0, count - 1) for count in counts.values())
    sources_present = all(card.source_id and card.source_url for card in cards)
    accepted = not missing and duplicate_count == 0 and sources_present
    return BriefDecision(
        accepted=accepted,
        coverage=len(REQUIRED_LANES) - len(missing),
        duplicate_lanes=duplicate_count,
        missing_lanes=missing,
        cards=tuple(cards),
    )


def vague_assignments() -> list[Assignment]:
    return [
        Assignment(worker_id, None, "Research multi-agent collaboration.")
        for worker_id in ("atlas", "birch", "comet")
    ]


def scoped_assignments() -> list[Assignment]:
    return [
        Assignment("atlas", "topology", "Who coordinates the team and dispatches work?"),
        Assignment("birch", "state", "How are agent context and state isolated?"),
        Assignment("comet", "handoff", "How do results move across agent boundaries?"),
    ]


def run(assignments: list[Assignment]) -> BriefDecision:
    return review_cards([research(assignment) for assignment in assignments])


def print_decision(title: str, decision: BriefDecision) -> None:
    print(f"== {title} ==")
    for card in decision.cards:
        print(f"{card.worker_id:<6} lane={card.lane:<8} source={card.source_id}")
    print(
        f"coverage={decision.coverage}/{len(REQUIRED_LANES)} "
        f"duplicates={decision.duplicate_lanes} "
        f"admitted={str(decision.accepted).lower()}"
    )
    if decision.missing_lanes:
        print(f"missing={','.join(decision.missing_lanes)}")


def main() -> None:
    print_decision("vague delegation", run(vague_assignments()))
    print()
    print_decision("scoped delegation", run(scoped_assignments()))


if __name__ == "__main__":
    main()
