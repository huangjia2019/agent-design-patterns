# Adversarial Review with the Claude Agent SDK

This tutorial uses a Claude subagent as one independent reviewer. The generic
[`AdversarialReview`](../pattern.py) loop still owns version binding, rule coverage,
repair budget, and admission.

## Setup

```python
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, replace

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query
from pattern import (
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
```

## Define the reviewer

```python
itinerary_critic = AgentDefinition(
    description="Audits a travel candidate against boarding-time rules.",
    prompt=(
        "You are an independent trip auditor. Inspect only the supplied candidate "
        "and evidence. Return a JSON list of objections. Each item must contain "
        "code, rule_id, severity, field, claim, and evidence_refs. "
        "Use rule_id boarding-time. You may report objections; you may not approve."
    ),
    model="sonnet",
)

options = ClaudeAgentOptions(
    model="sonnet",
    agents={"itinerary-critic": itinerary_critic},
    allowed_tools=["Agent"],
)
```

The prompt creates objective isolation. The subagent conversation creates a separate
context. Production identity isolation still needs workload identity and access
control outside the prompt.

## Bind the candidate

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

## Adapt the subagent to `ReviewerSpec`

```python
async def review_boarding(request):
    plan = request.artifact.payload
    prompt = json.dumps(
        {
            "artifact_id": request.artifact.artifact_id,
            "rubric_version": request.rubric_version,
            "candidate": {
                "taxi_eta": plan.taxi_eta,
                "boarding": plan.boarding,
            },
            "evidence_refs": request.artifact.evidence_refs,
        }
    )
    text = ""
    async for message in query(prompt=prompt, options=options):
        for block in getattr(message, "content", None) or []:
            if getattr(block, "text", None):
                text = block.text
    return tuple(
        Objection(
            code=item["code"],
            rule_id=item["rule_id"],
            severity=Severity(item["severity"]),
            field=item["field"],
            claim=item["claim"],
            evidence_refs=tuple(item["evidence_refs"]),
        )
        for item in json.loads(text)
    )


reviewer = ReviewerSpec(
    reviewer_id="boarding-reviewer",
    actor_id="claude-itinerary-critic",
    rule_ids=("boarding-time",),
    evidence_scope=("read:flight", "read:taxi"),
    review=review_boarding,
)
```

The panel binds `reviewer_id` itself and rejects objections for undeclared rules.
Failed reviewers do not count toward rule coverage.

## Run the bounded review loop

```python
async def revise(request, blockers):
    plan = replace(request.artifact.payload, taxi_eta="19:00")
    revision = request.artifact_revision + 1
    return bind(plan, revision, "travel-reviser")


system = AdversarialReview(
    ReviewPanel("travel-review-panel", (reviewer,)),
    ReviewPolicy(
        rubric_version="travel-release-v1",
        required_rule_ids=("boarding-time",),
        max_rounds=3,
    ),
    author_actor_id="travel-author",
    fingerprint=fingerprint,
    reviser=ReviserSpec(
        reviser_id="travel-reviser",
        actor_id="travel-reviser",
        revise=revise,
    ),
)

result = await system.run(
    CONTRACT,
    bind(TravelPlan("19:40", "19:30"), 0, "travel-author"),
)
print(result.outcome.value)
print(result.latest_review.artifact_id)
print(result.latest_review.rubric_version)
```

The reviewer produces objections. `ReviewGate` decides admission from the complete
`ReviewReceipt`. If the final allowed round still has a blocker, the loop returns the
last reviewed artifact and escalates instead of creating an unreviewed revision.

## Production notes

- Validate model JSON with a schema before constructing `Objection`.
- Give evidence references integrity protection and freshness bounds.
- Calibrate model reviewers against deterministic checks and human review.
- Track false release, false hold, missing-rule, reviewer-failure, and repair-loop
  rates by rubric version.
