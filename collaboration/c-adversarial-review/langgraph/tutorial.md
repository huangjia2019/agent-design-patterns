# Adversarial Review with LangGraph

This tutorial makes the `review -> revise -> review` loop a visible graph back-edge.
It reuses the contract, receipt, and gate from [`pattern.py`](../pattern.py).

## Setup

```python
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, replace
from typing import TypedDict

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../../..")))

from langgraph.graph import END, START, StateGraph

from pattern import (
    ArtifactEnvelope,
    Objection,
    ReviewGate,
    ReviewPanel,
    ReviewPolicy,
    ReviewReceipt,
    ReviewRequest,
    ReviewerSpec,
    Severity,
    TaskContract,
)
```

## One contract and one candidate

```python
@dataclass(frozen=True)
class TravelPlan:
    taxi_eta: str
    boarding: str


CONTRACT = TaskContract(
    contract_id="confirm-trip",
    version=1,
    objective="confirm one reviewed itinerary",
    output_schema="TravelPlan",
    accountable_owner="travel-controller",
    boundary="reviewers may object; only the gate may confirm",
)


def bind(plan: TravelPlan, revision: int, producer: str):
    return ArtifactEnvelope(
        artifact_id=f"travel-plan-r{revision}",
        contract_digest=CONTRACT.digest,
        schema=CONTRACT.output_schema,
        produced_by=producer,
        payload=plan,
        evidence_refs=("booking://flight-42", "booking://taxi-7"),
    )


def fingerprint(plan: TravelPlan) -> str:
    return f"{plan.taxi_eta}|{plan.boarding}"
```

## A reviewer that can object, not approve

```python
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
            claim=f"taxi={plan.taxi_eta} boarding={plan.boarding}",
            evidence_refs=("booking://flight-42", "booking://taxi-7"),
        ),
    )


PANEL = ReviewPanel(
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
POLICY = ReviewPolicy(
    rubric_version="travel-release-v1",
    required_rule_ids=("boarding-time",),
    max_rounds=3,
)
GATE = ReviewGate()
```

The reviewer declares which rules it checks. A clean objection list is useful only
when the resulting `ReviewReceipt` also proves that every required rule was checked.

## Graph state and nodes

```python
class ReviewState(TypedDict):
    artifact: ArtifactEnvelope
    revision: int
    receipt: ReviewReceipt | None
    outcome: str


async def review_node(state: ReviewState) -> dict:
    artifact = state["artifact"]
    request = ReviewRequest(
        contract=CONTRACT,
        artifact=artifact,
        artifact_revision=state["revision"],
        artifact_fingerprint=fingerprint(artifact.payload),
        rubric_version=POLICY.rubric_version,
    )
    receipt = await PANEL.review(request, POLICY)
    return {"receipt": receipt}


def route(state: ReviewState) -> str:
    receipt = state["receipt"]
    if GATE.may_confirm(receipt):
        return "confirm"
    if not receipt.complete or state["revision"] + 1 >= POLICY.max_rounds:
        return "hold"
    return "revise"


def revise_node(state: ReviewState) -> dict:
    revision = state["revision"] + 1
    revised = replace(state["artifact"].payload, taxi_eta="19:00")
    return {
        "artifact": bind(revised, revision, "travel-reviser"),
        "revision": revision,
    }


def confirm_node(state: ReviewState) -> dict:
    return {"outcome": "confirmed"}


def hold_node(state: ReviewState) -> dict:
    return {"outcome": "held_for_human"}
```

## Wire the loop

```python
graph = StateGraph(ReviewState)
graph.add_node("review", review_node)
graph.add_node("revise", revise_node)
graph.add_node("confirm", confirm_node)
graph.add_node("hold", hold_node)
graph.add_edge(START, "review")
graph.add_conditional_edges(
    "review",
    route,
    {"revise": "revise", "confirm": "confirm", "hold": "hold"},
)
graph.add_edge("revise", "review")
graph.add_edge("confirm", END)
graph.add_edge("hold", END)
app = graph.compile()
```

Run it:

```python
out = await app.ainvoke(
    {
        "artifact": bind(TravelPlan("19:40", "19:30"), 0, "travel-author"),
        "revision": 0,
        "receipt": None,
        "outcome": "",
    }
)
print(out["outcome"], out["artifact"].artifact_id, out["receipt"].blockers)
```

The graph exits through `confirm` only for a complete receipt with zero blockers.
Missing rule coverage, reviewer failure, or an exhausted repair budget exits through
`hold`.

## Production notes

- Give each reviewer a workload identity. An `actor_id` string is a teaching
  contract, not proof of process isolation.
- Persist `ReviewReceipt` and the final acceptance decision together.
- Add timeout and retry policy around reviewer calls.
- Keep the rubric version under change control. A gate cannot invent a missing rule.
