"""A no-key lab for adversarial review as a publication gate.

Run from the repository root:
    python3 collaboration/light_labs/editorial_review_lab.py
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Literal


Severity = Literal["warning", "blocker"]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class Proposal:
    """A versioned claim proposed for publication."""

    proposal_id: str
    version: int
    text: str
    source_ref: str

    @property
    def content_digest(self) -> str:
        return digest(f"{self.text}\nsource:{self.source_ref}")


@dataclass(frozen=True)
class Objection:
    """A machine-readable reason to hold or annotate a proposal."""

    reviewer_id: str
    rule_id: str
    severity: Severity
    message: str
    evidence_ref: str


@dataclass(frozen=True)
class ReviewReceipt:
    """The gate's decision bound to one exact proposal version and digest."""

    proposal_id: str
    version: int
    proposal_digest: str
    objections: tuple[Objection, ...]
    passed: bool

    def authorizes(self, proposal: Proposal) -> bool:
        return (
            self.passed
            and self.proposal_id == proposal.proposal_id
            and self.version == proposal.version
            and self.proposal_digest == proposal.content_digest
        )


def boundary_reviewer(proposal: Proposal) -> tuple[Objection, ...]:
    if "fully isolated" not in proposal.text.lower():
        return ()
    return (
        Objection(
            "boundary-reviewer",
            "workspace-boundary",
            "blocker",
            "Session isolation does not prove filesystem isolation.",
            "dsh-subagent-docs#tool-and-workspace-boundaries",
        ),
    )


def scope_reviewer(proposal: Proposal) -> tuple[Objection, ...]:
    if not proposal.text.lower().startswith("all dsh subagents"):
        return ()
    return (
        Objection(
            "scope-reviewer",
            "provider-scope",
            "blocker",
            "The claim merges providers with different context semantics.",
            "dsh-subagent-docs#providers",
        ),
    )


def review(proposal: Proposal) -> ReviewReceipt:
    objections = (*boundary_reviewer(proposal), *scope_reviewer(proposal))
    passed = not any(objection.severity == "blocker" for objection in objections)
    return ReviewReceipt(
        proposal_id=proposal.proposal_id,
        version=proposal.version,
        proposal_digest=proposal.content_digest,
        objections=objections,
        passed=passed,
    )


def weak_publish(proposal: Proposal, receipt: ReviewReceipt) -> bool:
    """The failure mode: collect comments, then ignore their control effect."""

    return bool(proposal.text)


def gated_publish(proposal: Proposal, receipt: ReviewReceipt) -> bool:
    return receipt.authorizes(proposal)


def risky_proposal() -> Proposal:
    return Proposal(
        "dsh-brief",
        1,
        "All dsh subagents are fully isolated by default.",
        "dsh-subagent-docs",
    )


def revised_proposal() -> Proposal:
    return Proposal(
        "dsh-brief",
        2,
        (
            "In-process spawn subagents use separate sessions. "
            "Filesystem and tool boundaries depend on provider and runtime policy."
        ),
        "dsh-subagent-docs",
    )


def main() -> None:
    first = risky_proposal()
    first_receipt = review(first)
    blockers = sum(
        objection.severity == "blocker" for objection in first_receipt.objections
    )
    print("== review as comments ==")
    print(f"proposal=v{first.version} blockers={blockers}")
    print(f"published={str(weak_publish(first, first_receipt)).lower()}")
    print("problem=objections_recorded_but_not_enforced")

    second = revised_proposal()
    second_receipt = review(second)
    print("\n== review as gate ==")
    print(
        f"proposal=v{first.version} "
        f"published={str(gated_publish(first, first_receipt)).lower()}"
    )
    print(
        f"proposal=v{second.version} blockers={len(second_receipt.objections)} "
        f"published={str(gated_publish(second, second_receipt)).lower()}"
    )
    print(f"receipt={second_receipt.proposal_digest}")


if __name__ == "__main__":
    main()
