# Handoff Chain with LangGraph

This tutorial makes a specialist pipeline visible as a linear graph while reusing
the exact commit boundary from [`pattern.py`](../pattern.py).

## Setup

```python
from __future__ import annotations

import os
import sys
from typing import TypedDict

sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))

from langgraph.graph import END, START, StateGraph

from example import CONTRACT, chain
from pattern import Baton, new_baton
```

`example.chain()` contains three specialist stages:

```text
intent -> route -> booking
```

Each stage owns different facts. `HandoffChain.advance()` validates and commits only
the next stage, so LangGraph does not need a second copy of the seam logic.

## Graph state

```python
class ChainState(TypedDict):
    baton: Baton


CHAIN = chain()


async def advance(state: ChainState) -> dict:
    next_baton, receipt = await CHAIN.advance(state["baton"])
    print(
        receipt.stage_name,
        receipt.input_revision,
        "->",
        receipt.output_revision,
    )
    return {"baton": next_baton}
```

The node receives an immutable checkpoint. The stage itself gets a detached
`BatonView` and can only return `StageDelta`.

## Wire the line

```python
graph = StateGraph(ChainState)
graph.add_node("intent", advance)
graph.add_node("route", advance)
graph.add_node("booking", advance)
graph.add_edge(START, "intent")
graph.add_edge("intent", "route")
graph.add_edge("route", "booking")
graph.add_edge("booking", END)
app = graph.compile()
```

Run it:

```python
out = await app.ainvoke(
    {
        "baton": new_baton(
            CONTRACT,
            baton_id="trip-42",
            intent="be in Shanghai tomorrow afternoon",
        )
    }
)
baton = out["baton"]
print(baton.trace)
print(dict(baton.facts))
print([receipt.receipt_id for receipt in baton.stage_receipts])
```

Every graph node commits one new revision and one `StageReceipt`. If `route` fails,
the exception carries the checkpoint after `intent`. Retrying that checkpoint runs
`route` again with the same `stage_run_id`.

## Model-backed stages

Replace a deterministic `StageFn` with a model adapter that returns `StageDelta`.
The graph and chain remain unchanged. Validate model JSON before constructing
`FactValue`, and attach evidence references to each fact.

## Production notes

- Persist the baton snapshot and stage receipt atomically.
- Use `stage_run_id` as the idempotency key for external tools.
- Resume from `SeamError.checkpoint` instead of restarting the graph from revision
  zero.
- Add an outbox or equivalent durable side-effect boundary for payment and booking.
