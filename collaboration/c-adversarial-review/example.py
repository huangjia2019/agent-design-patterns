"""Small runnable example for the contract-bound Adversarial Review pattern."""
from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass, replace


sys.path.insert(0, os.path.dirname(__file__))

from pattern import (  # noqa: E402
    AdversarialReview,
    ArtifactEnvelope,
    Objection,
    ReviewPanel,
    ReviewPolicy,
    ReviewerSpec,
    ReviserSpec,
    Severity,
    TaskContract,
)


@dataclass(frozen=True)
class TravelPlan:
    taxi_eta: str
    boarding: str
    total_price: float


def contract() -> TaskContract:
    return TaskContract(
        contract_id="confirm-trip",
        version=1,
        objective="confirm one reviewed itinerary",
        output_schema="TravelPlan",
        accountable_owner="travel-controller",
        boundary="the reviewer may object; only the gate may confirm",
    )


def artifact(plan: TravelPlan, revision: int, producer: str):
    return ArtifactEnvelope(
        artifact_id=f"travel-plan-r{revision}",
        contract_digest=contract().digest,
        schema=contract().output_schema,
        produced_by=producer,
        payload=plan,
        evidence_refs=("booking://flight-42", "booking://taxi-7"),
    )


async def review_boarding(request):
    plan = request.artifact.payload
    if plan.taxi_eta <= plan.boarding:
        return ()
    return (
        Objection(
            code="taxi_after_boarding",
            rule_id="boarding-time",
            severity=Severity.BLOCKER,
            field="taxi_eta",
            claim=f"taxi_eta={plan.taxi_eta} boarding={plan.boarding}",
            evidence_refs=("booking://flight-42", "booking://taxi-7"),
        ),
    )


async def revise(request, blockers):
    plan = replace(
        request.artifact.payload,
        taxi_eta="19:00",
        total_price=request.artifact.payload.total_price + 20.0,
    )
    return artifact(plan, request.artifact_revision + 1, "travel-reviser")


async def main() -> None:
    panel = ReviewPanel(
        "travel-review-panel",
        (
            ReviewerSpec(
                reviewer_id="boarding-reviewer",
                actor_id="travel-risk-agent",
                rule_ids=("boarding-time",),
                evidence_scope=("read:flight", "read:taxi"),
                review=review_boarding,
            ),
        ),
    )
    system = AdversarialReview(
        panel,
        ReviewPolicy(
            rubric_version="travel-release-v1",
            required_rule_ids=("boarding-time",),
            max_rounds=3,
        ),
        author_actor_id="travel-author",
        fingerprint=lambda plan: (
            f"{plan.taxi_eta}|{plan.boarding}|{plan.total_price:.2f}"
        ),
        reviser=ReviserSpec(
            reviser_id="travel-reviser",
            actor_id="travel-reviser",
            revise=revise,
        ),
    )
    result = await system.run(
        contract(),
        artifact(
            TravelPlan("19:40", "19:30", 3180.0),
            revision=0,
            producer="travel-author",
        ),
    )

    print(f"Outcome: {result.outcome.value}")
    for item in result.rounds:
        print(
            f"  round {item.round_number}: "
            f"artifact={item.receipt.artifact_id} "
            f"blockers={len(item.receipt.blockers)}"
        )
    plan = result.artifact.payload
    print(
        f"Final taxi ETA: {plan.taxi_eta} "
        f"(boarding {plan.boarding}) · total ¥{plan.total_price:,.0f}"
    )
    print(
        f"Acceptance: {result.acceptance_receipt.decision.value} "
        f"for {result.acceptance_receipt.artifact_id}"
    )


if __name__ == "__main__":
    asyncio.run(main())
