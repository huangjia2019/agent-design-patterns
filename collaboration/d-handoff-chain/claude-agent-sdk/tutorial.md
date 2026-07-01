# Handoff Chain — Claude Agent SDK Implementation

> "One specialist per stage, and a baton passed hand to hand."

This notebook builds Handoff Chain with the **Claude Agent SDK**. Each stage is a
declarative `AgentDefinition` — an intent parser, a route planner, a flight booker, a
taxi booker, a hotel booker. The orchestrator runs them in sequence, passing a JSON
baton from each to the next.

The chain is a Python sequence, not a graph, but the Baton Contract is the same:
between two subagents, Python checks that the baton carries what the next stage
requires and that no committed fact was overwritten. The subagents do the work; the
seam checks stay in deterministic Python.

Scenario: column lecture **07-05** — "be in Shanghai tomorrow afternoon" becomes a
booked trip, one stage at a time.

## Two implementations, two philosophies

| | `langgraph/` | `claude-agent-sdk/` (this notebook) |
|---|---|---|
| **The chain** | A linear `StateGraph`. | A Python sequence of subagent calls. |
| **The baton** | Accumulating graph state. | A JSON object passed from one subagent to the next. |
| **Seam checks** | A `guarded` node wrapper. | The same `StageSpec` checks in Python between stages. |

The contract is identical; only the runner differs.

## Setup

```python
from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query
from pattern import Baton, SeamError, StageSpec, HandoffChain

print("claude-agent-sdk imports ready:", AgentDefinition.__name__)
```

    claude-agent-sdk imports ready: AgentDefinition

## Step 1 — one subagent per stage

Each stage is an `AgentDefinition` pinned to one job. The `description` says when it
runs in the line; the `prompt` says what it reads off the baton and what it must add.
A cheap model is fine — the chain's correctness is in the contract, not the model.

```python
def stage_agent(name: str, job: str) -> AgentDefinition:
    return AgentDefinition(
        description=f"Handoff-chain stage '{name}': {job}",
        prompt=(f"You are the '{name}' stage of a trip-booking chain. Read the baton "
                f"JSON, {job}, and return the baton with ONLY your fields added. "
                "Never rewrite a fact another stage already committed."),
        tools=["Read", "Bash"],
        model="haiku",
    )

STAGES = {
    "intent": stage_agent("intent", "extract city and date from the request"),
    "route":  stage_agent("route", "plan the route and set depart_by"),
    "flight": stage_agent("flight", "book the flight and set boarding"),
    "taxi":   stage_agent("taxi", "book the airport taxi and set taxi_eta"),
    "hotel":  stage_agent("hotel", "book the hotel"),
}
print(f"{len(STAGES)} stage subagents:", list(STAGES))
```

    5 stage subagents: ['intent', 'route', 'flight', 'taxi', 'hotel']

## Step 2 — the contract lives in Python, between stages

We reuse the exact `StageSpec`s and `HandoffChain` from `pattern.py`. The subagents
produce each stage's delta; `HandoffChain` validates the seam. Here we run it with
mock stage functions to show the contract holding with no API key — the live version
in Step 3 swaps the mocks for `query()`.

```python
def mock_delta(**facts):
    async def fn(baton: Baton) -> dict:
        return {"facts": facts}
    return fn

specs = [
    (StageSpec("intent", provides=("city", "date")), mock_delta(city="Shanghai", date="2026-07-02")),
    (StageSpec("route", requires=("city", "date"), provides=("depart_by",)), mock_delta(depart_by="18:00")),
    (StageSpec("flight", requires=("city", "date"), provides=("boarding",)), mock_delta(boarding="19:30")),
    (StageSpec("taxi", requires=("depart_by", "boarding"), provides=("taxi_eta",)), mock_delta(taxi_eta="19:00")),
    (StageSpec("hotel", requires=("city", "date"), provides=("hotel",)), mock_delta(hotel="ctrip#88")),
]
baton = asyncio.run(HandoffChain(specs).run(Baton(intent="be in Shanghai tomorrow PM")))
print("trace:", " -> ".join(baton.trace))
print("facts:", baton.facts)
```

    trace: intent -> route -> flight -> taxi -> hotel
    facts: {'city': 'Shanghai', 'date': '2026-07-02', 'depart_by': '18:00', 'boarding': '19:30', 'taxi_eta': '19:00', 'hotel': 'ctrip#88'}

## Step 3 — the live chain

Each stage becomes a `query()` against its subagent, handed the current baton as
JSON, returning the baton with its fields added. Between stages, the same
`HandoffChain` seam check runs. This cell needs a live API key + the Claude Code CLI,
so it is not executed in the build.

```python
async def run_stage(name: str, baton: Baton) -> dict:
    opts = ClaudeAgentOptions(model="haiku", agents={name: STAGES[name]},
                              allowed_tools=["Read", "Bash", "Agent"])
    prompt = (f"Use the {name} subagent. Baton so far:\n{json.dumps(baton.facts)}\n"
              "Return ONLY the new facts this stage adds, as JSON.")
    text = ""
    async for msg in query(prompt=prompt, options=opts):
        for block in getattr(msg, "content", None) or []:
            if getattr(block, "text", None):
                text = block.text
    return {"facts": json.loads(text)}                 # seam check happens in HandoffChain

# Wrap each live stage so HandoffChain still validates the contract between them:
# specs_live = [(spec, (lambda n: lambda b: run_stage(n, b))(spec.name)) for spec in SPECS]
# baton = await HandoffChain(specs_live).run(Baton(intent="be in Shanghai tomorrow PM"))
print("run_stage defined — wrap each stage in HandoffChain and call with a live key.")
```

    run_stage defined — wrap each stage in HandoffChain and call with a live key.

## What the SDK gives you here

1. **A specialist per seam.** Adding a stage (say, travel insurance) is one more
   `AgentDefinition` and one more `StageSpec`.
2. **Isolation per stage.** Each subagent is a fresh conversation; it sees the baton,
   not the previous stage's reasoning.
3. **The contract is still Python.** `HandoffChain` validates every seam with the
   same `StageSpec` the unit tests use. A dropped handoff fails fast, named — the
   model does not get to paper over it.

## When this breaks

| Failure | With the SDK |
|---|---|
| **Baton bloat** | Passing each subagent's full transcript to the next. Pass the JSON `facts`, not the conversation. |
| **Silent overwrite** | A late stage rewriting a committed fact. `HandoffChain`'s append-only check refuses it. |
| **Lost attribution** | Skipping the Python seam check and letting stages call each other directly. Keep the chain in `HandoffChain` so a break is named. |

Back to the explicit line: [`../langgraph/tutorial.md`](../langgraph/tutorial.md).
