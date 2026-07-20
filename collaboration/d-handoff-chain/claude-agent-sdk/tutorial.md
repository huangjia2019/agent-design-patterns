# Handoff Chain with the Claude Agent SDK

This tutorial adapts a Claude subagent to one `StageFn`. The generic
[`HandoffChain`](../pattern.py) still owns field ownership, type and evidence checks,
semantic validation, immutable commits, receipts, and retry checkpoints.

## Setup

```python
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query

from example import CONTRACT, chain
from pattern import FactValue, StageDelta, new_baton
```

## Define one specialist

```python
route_agent = AgentDefinition(
    description="Route stage: derive the departure deadline for a trip.",
    prompt=(
        "Read the supplied immutable baton facts. Return JSON with exactly "
        "depart_by and evidence_refs. Do not return or rewrite any other fact."
    ),
    model="haiku",
)

options = ClaudeAgentOptions(
    model="haiku",
    agents={"route-specialist": route_agent},
    allowed_tools=["Agent"],
)
```

## Adapt the subagent to `StageFn`

```python
async def model_route(view):
    payload = {
        "stage_run_id": view.stage_run_id,
        "requires": {
            "city": view.facts["city"],
            "date": view.facts["date"],
        },
    }
    text = ""
    async for message in query(
        prompt=json.dumps(payload),
        options=options,
    ):
        for block in getattr(message, "content", None) or []:
            if getattr(block, "text", None):
                text = block.text
    parsed = json.loads(text)
    return StageDelta(
        facts=(
            FactValue(
                "depart_by",
                parsed["depart_by"],
                tuple(parsed["evidence_refs"]),
            ),
        )
    )
```

The model receives a detached `BatonView`, not the mutable committed object. It can
propose one delta. The chain rejects extra keys, missing evidence, wrong types, and
semantic violations before committing a new revision.

## Run the mixed chain

```python
system = chain(route_stage=model_route)
result = await system.run(
    new_baton(
        CONTRACT,
        baton_id="trip-42",
        intent="be in Shanghai tomorrow afternoon",
    )
)
print(result.baton.trace)
print(result.acceptance_receipt.decision.value)
```

The intent and booking stages remain deterministic in this small example. The route
stage is model-backed, but all three cross the same seam contract.

## Production notes

- Give each specialist a workload identity and a narrow tool allowlist.
- Treat `stage_run_id` as the idempotency key when a tool has side effects.
- Persist model input, structured output, evidence, and `StageReceipt`.
- A fresh subagent conversation provides context separation. It does not prove
  evidence freshness or authority transfer.
- Dynamic conversational Handoff additionally needs route allowlists, context
  filtering, and active-agent lifecycle controls.
