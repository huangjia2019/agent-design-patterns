# Handoff Chain — LangGraph Implementation

> "A chain is a line, and every seam is a place the baton can be dropped."

This notebook builds Handoff Chain as a **linear LangGraph**: one node per stage,
plain edges in sequence, and the Baton Contract checked at every node boundary.

The scenario is column lecture **07-05**: an AI travel assistant turns "be in
Shanghai tomorrow afternoon" into a booked trip by passing a baton down a chain —
intent → route → flight → taxi → hotel. Each node reads the accumulated state, does
its stage, and adds to it. The whole risk of the pattern lives at the seams between
nodes: drop one fact the next stage needs and the trip breaks.

We reuse `StageSpec` and `SeamError` from [`pattern.py`](../pattern.py) so a stage
that is handed a baton missing what it requires — or that tries to overwrite a
committed fact — fails fast, named, at the seam.

## Two implementations, two philosophies

| | `langgraph/` (this notebook) | `claude-agent-sdk/` |
|---|---|---|
| **The chain** | A linear `StateGraph`: `intent → route → flight → taxi → hotel`. | A Python sequence that runs one subagent per stage. |
| **The baton** | The graph's accumulating state (`facts` / `legs` / `trace`). | A JSON baton passed from one subagent to the next. |
| **Seam checks** | A `guarded` wrapper reusing `StageSpec` / `SeamError`. | The same checks in Python between subagents. |

Same pattern, same contract, two ways to run the line.

## Setup

```python
from __future__ import annotations

import os
import sys
from typing import TypedDict

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../../..")))

from langgraph.graph import START, END, StateGraph

from pattern import SeamError, StageSpec   # reuse the Baton Contract types

print("Imports ready")
```

    Imports ready

## Step 1 — State: what accumulates down the line

Unlike Fan-out-Gather, nothing runs in parallel here, so no reducer is needed. Each
node reads the running `facts` / `legs` / `trace` and returns the updated whole. The
`intent` is set once and carried unchanged.

```python
class ChainState(TypedDict):
    intent: str
    facts: dict         # committed facts accumulate here (append-only by contract)
    legs: list          # booked legs accumulate
    trace: list         # stages that have run

print("State ready")
```

    State ready

## Step 2 — the seam guard: the Baton Contract at every node

`guarded` wraps a stage so that, at its boundary, it (1) refuses to run if the baton
is missing what it `requires`, (2) refuses to silently overwrite a committed fact,
and (3) checks it delivered what it `provides`. This is the whole safety of the
pattern, and it lives at the seam.

```python
def guarded(spec: StageSpec, stage_fn):
    def node(state: ChainState) -> dict:
        missing = [k for k in spec.requires if k not in state["facts"]]
        if missing:
            raise SeamError(f"stage '{spec.name}' requires {missing}")   # entry seam
        delta = stage_fn(state)
        new = delta.get("facts", {})
        clobber = [k for k, v in new.items() if k in state["facts"] and state["facts"][k] != v]
        if clobber:
            raise SeamError(f"stage '{spec.name}' overwrote committed {clobber}")  # append-only
        undelivered = [k for k in spec.provides if k not in new and k not in state["facts"]]
        if undelivered:
            raise SeamError(f"stage '{spec.name}' did not provide {undelivered}")  # exit seam
        return {"facts": {**state["facts"], **new},
                "legs": state["legs"] + delta.get("legs", []),
                "trace": state["trace"] + [spec.name]}
    return node

print("Seam guard ready")
```

    Seam guard ready

## Step 3 — the stages (mock, no API key)

Each stage returns only its delta — the facts and legs it adds. In production each
is a specialist agent; here they are deterministic mocks so the chain runs with no
key.

```python
def make_stages():
    def intent(s): return {"facts": {"city": "Shanghai", "date": "2026-07-02"}}
    def route(s):  return {"facts": {"depart_by": "18:00"}}
    def flight(s): return {"facts": {"boarding": "19:30"}, "legs": [{"type": "flight"}]}
    def taxi(s):   return {"facts": {"taxi_eta": "19:00"}, "legs": [{"type": "taxi"}]}
    def hotel(s):  return {"facts": {"hotel": "ctrip#88"}, "legs": [{"type": "hotel"}]}
    return {"intent": intent, "route": route, "flight": flight, "taxi": taxi, "hotel": hotel}

SPECS = [
    StageSpec("intent", requires=(), provides=("city", "date")),
    StageSpec("route",  requires=("city", "date"), provides=("depart_by",)),
    StageSpec("flight", requires=("city", "date"), provides=("boarding",)),
    StageSpec("taxi",   requires=("depart_by", "boarding"), provides=("taxi_eta",)),
    StageSpec("hotel",  requires=("city", "date"), provides=("hotel",)),
]
print("Stages + specs ready")
```

    Stages + specs ready

## Step 4 — wire the chain (a straight line)

`START → intent → route → flight → taxi → hotel → END`. Plain edges, in order. The
seam checks live inside each `guarded` node, not in the edges.

```python
def build_graph(stages):
    g = StateGraph(ChainState)
    for spec in SPECS:
        g.add_node(spec.name, guarded(spec, stages[spec.name]))
    g.add_edge(START, "intent")
    for a, b in zip([s.name for s in SPECS], [s.name for s in SPECS][1:]):
        g.add_edge(a, b)                 # intent->route->flight->taxi->hotel
    g.add_edge("hotel", END)
    return g.compile()

print("Graph builder ready")
```

    Graph builder ready

## Step 5 — run it (mock)

```python
app = build_graph(make_stages())
out = app.invoke({"intent": "be in Shanghai tomorrow PM", "facts": {}, "legs": [], "trace": []})
print("trace:", " -> ".join(out["trace"]))
print("facts:", out["facts"])
print("legs: ", [leg["type"] for leg in out["legs"]])
```

    trace: intent -> route -> flight -> taxi -> hotel
    facts: {'city': 'Shanghai', 'date': '2026-07-02', 'depart_by': '18:00', 'boarding': '19:30', 'taxi_eta': '19:00', 'hotel': 'ctrip#88'}
    legs:  ['flight', 'taxi', 'hotel']

The baton went down the line, each node adding its part, and the contract
held at every seam. Now break it — a route stage that forgets `depart_by`:

```python
broken = make_stages()
broken["route"] = lambda s: {"facts": {}}      # forgets to hand off depart_by
try:
    build_graph(broken).invoke(
        {"intent": "x", "facts": {}, "legs": [], "trace": []})
except SeamError as e:
    print("SeamError:", e)
```

    SeamError: stage 'route' did not provide ['depart_by']

The chain stopped at the `route` seam — the exact node that dropped the
handoff — instead of booking a taxi that can't make the flight. That is the Baton
Contract earning its keep.

### Real run

Swap each mock stage for an agent node (`model.with_structured_output(...)` per
stage). The chain, the edges, and the seam guard do not change — only how each stage
produces its delta.

```python
# from model_config import get_model
# model = get_model()
# stages = {name: make_agent_stage(model, name) for name in ...}
# app = build_graph(stages)
print("Swap mock stages for model-backed ones; the chain and its seams are unchanged.")
```

    Swap mock stages for model-backed ones; the chain and its seams are unchanged.

## When this breaks

| Failure | In this graph |
|---|---|
| **Dropped handoff** | A stage that doesn't provide what it promised. The `provides` check catches it at that node. |
| **Silent overwrite** | A late stage rewriting a committed fact. The append-only check refuses it. |
| **Wrong order** | Edges out of sequence, so a stage runs before its `requires` are met. The `requires` check fails fast, named. |
| **Baton bloat** | Passing the whole conversation down the line instead of committed facts. Keep the baton to `facts` / `legs`, not raw traces. |

Next: the same chain with the Claude Agent SDK, where each stage is a subagent and
the baton is JSON passed hand to hand →
[`../claude-agent-sdk/tutorial.md`](../claude-agent-sdk/tutorial.md).
