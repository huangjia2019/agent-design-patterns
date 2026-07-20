# Fan-out-Gather — LangGraph Implementation

> "Fan-out is the easy half. The gather is the soul."

This notebook builds Fan-out-Gather as an **explicit LangGraph `StateGraph`**: a
plan node, a parallel fan-out that sends the **same** task to N source workers, a
reducer that fans their readings back in, and a **gather** node that does the real
work — reconciling the readings into one answer.

The scenario is column lecture **07-03**: the June settlement is done, but the
ledger is off by a chunk and nobody knows where. Instead of one agent guessing,
we fan the **same June total** out to four workers, each bound to one data source
— payroll, social-security, attendance, GL — and let them compute it by their own
lens. The gather does not concatenate; it compares each line item across the four
sources. Where they **diverge is where the gap is**.

Everything is defined inline:

- the `FanOutState` (with a **reducer** — the fan-in seam)
- a `SourceReading` Pydantic schema (what a worker is allowed to return)
- the `source_worker` node (bound to one source, isolated, structured output)
- `Send`-based fan-out (**same rows** to every source)
- the `gather` node, reusing `Reconciler` from [`pattern.py`](../pattern.py)

Default model: AI Studio + `ernie-5.1` (OpenAI-compatible). See
[`.env.example`](../../../.env.example) and [`model_config.py`](../../../model_config.py).

## Two implementations, two philosophies

| | `langgraph/` (this notebook) | `claude-agent-sdk/` |
|---|---|---|
| **You write** | The graph — plan node, source workers, `Send` fan-out, reducer fan-in, gather node. Every edge visible in LangGraph Studio. | Declarative `AgentDefinition`s, one per source. The runtime delegates and isolates context for you. |
| **Fan-out** | `Send` — same rows to N nodes. | Parallel subagent queries, one per source. |
| **Gather** | A `gather` node calling `Reconciler`. | Reconcile in Python after the subagents return. |
| **Model** | Provider-agnostic (`model_config`, default `ernie-5.1`). | Claude-native (`sonnet` / `haiku` aliases per source). |

Same pattern, same `pattern.py` reconciler, two ways to wire the agents.

## Setup

```python
from __future__ import annotations

import operator
import os
import sys
from typing import Annotated, TypedDict

# Make the pattern folder importable (reuse Reconciler / SourceResult from pattern.py)
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "../../..")))

from pydantic import BaseModel, Field
from langgraph.graph import START, END, StateGraph
from langgraph.types import Send

from pattern import Reconciler, ReconciliationReport, SourceResult

print("Imports ready")
```

    Imports ready

## The shape we're filling

The framework-agnostic pattern lives in [`pattern.py`](../pattern.py): a
`SourceResult` (what one source-bound worker returns), a `Reconciler` (the
three-layer gather), and the `Aggregator's Four Questions`. This notebook maps
that shape onto LangGraph primitives:

| pattern.py | LangGraph |
|---|---|
| fan the **same** task to N sources | a `Send` per source, all with the same `rows` |
| worker bound to one source, returns only a reading | a `source_worker` node writing **only** to a reduced key |
| parallel dispatch | `Send` fan-out on a conditional edge |
| the reconciler (the soul) | a `gather` node calling `Reconciler` |

## Step 1 — State with a reducer (the fan-in seam)

When N source workers run in parallel and all write to the same state key,
LangGraph needs to know **how to combine** their writes. That is a *reducer*.
Without one, parallel writes to the same key raise `InvalidUpdateError` —
LangGraph refuses to silently drop data. `Annotated[list, operator.add]` says
"append, don't overwrite," turning N parallel readings into one accumulated list.
This is the single most common thing to get wrong when you first fan out in
LangGraph, and the error is loud, which is a mercy.

```python
class SourceReading(BaseModel):
    """What one source worker returns. Bound to an ATTRIBUTABLE source, so its
    divergence from the others can point at a root cause, not just uncertainty."""
    source: str
    line_items: dict[str, float] = Field(default_factory=dict)
    confidence: float = 1.0


class FanOutState(TypedDict):
    rows: list[dict]
    sources: list[str]                               # set by plan
    # The reducer. N workers append here in parallel; no reducer -> InvalidUpdateError.
    readings: Annotated[list[dict], operator.add]
    report: ReconciliationReport | None

print("State ready — note the operator.add reducer on `readings`")
```

    State ready — note the operator.add reducer on `readings`

## Step 2 — The source worker: bound to one source, isolated

Every worker is pinned to **one data source** and computes the same June total by
that source's lens. Two things make it a real worker and not just a function:

1. **Attributable boundary** — it reads only its own source's system. That is what
   lets divergence between workers locate a subsystem instead of merely flagging
   "uncertain."
2. **Structured output** — `model.with_structured_output(SourceReading)` forces the
   schema, so the reconciler compares typed numbers, not prose.

```python
WORKER_PROMPT = """You are the {source} reconciliation worker. Compute the June \
totals for each line item (基本工资 / 社保代扣 / 加班费 / ...) STRICTLY from the \
{source} system's own records. Do not borrow another system's numbers. Return a \
SourceReading: source={source}, line_items mapping each item to its amount, and \
confidence 0-1.

Roster ({n} employees):
{rows}
"""

def make_source_worker(model):
    structured = model.with_structured_output(SourceReading)

    def source_worker(payload: dict) -> dict:        # payload = {"source", "rows"}
        reading = structured.invoke(WORKER_PROMPT.format(
            source=payload["source"], n=len(payload["rows"]), rows=payload["rows"],
        ))
        reading.source = payload["source"]           # trust our label, not the model's
        return {"readings": [reading.model_dump()]}  # write ONLY to the reduced key
    return source_worker

print("Worker factory ready")
```

    Worker factory ready

## Step 3 — Fan out with `Send` (same rows to every source)

This is the difference from Hierarchical Delegation. There, each `Send` carried a
**different** batch. Here every `Send` carries the **same** `rows` — the whole
point is that all workers compute the same total, so their divergence is
meaningful. `Send(node, payload)` schedules an independent run; return a list and
LangGraph runs them all in parallel.

```python
SOURCES = ["payroll", "gl", "social_security", "attendance"]

def plan(state: FanOutState) -> dict:
    """Pick the sources to reconcile against. Each must be an INDEPENDENT system —
    Brooks' law: only independent subtasks get an N-times speedup from fan-out."""
    return {"sources": SOURCES}


def fan_out(state: FanOutState) -> list[Send]:
    """Conditional-edge router: SAME rows to every source -> N workers in parallel."""
    return [Send("source_worker", {"source": s, "rows": state["rows"]})
            for s in state["sources"]]

print("Fan-out ready")
```

    Fan-out ready

## Step 4 — The gather node: reconcile, don't concatenate

This is the soul. The `gather` node runs *after* the fan-in, when the reducer has
collected every worker's reading into `state["readings"]`. It does **not** join
them into a report. It hands them to `Reconciler` from `pattern.py`, which
compares each line item across sources and sorts the divergence into three
layers: agree (gap not here), attributable (the gap *is* located to a source),
unexplained (human review).

```python
def gather(state: FanOutState) -> dict:
    results = [
        SourceResult.from_mapping(
            source_id=r["source"],
            snapshot_ref=f"snapshot://{r['source']}/2026-06-30T23:59:59Z",
            period="2026-06",
            unit="CNY",
            line_items=r["line_items"],
            confidence=r.get("confidence", 1.0),
        )
        for r in state["readings"]
    ]
    report = Reconciler(tol=1.0).reconcile(results)   # the framework-agnostic gather
    return {"report": report}

print("Gather ready — it calls pattern.py's Reconciler, not concatenate")
```

    Gather ready — it calls pattern.py's Reconciler, not concatenate

## Step 5 — Wire the graph

`plan → (fan_out) → source_worker ×N → gather → END`. The conditional edge from
`plan` to `source_worker` carries the `Send` fan-out; the plain edge from
`source_worker` to `gather` is the fan-in (the reducer merges the parallel
writes).

```python
def build_graph(model):
    g = StateGraph(FanOutState)
    g.add_node("plan", plan)
    g.add_node("source_worker", make_source_worker(model))
    g.add_node("gather", gather)
    g.add_edge(START, "plan")
    g.add_conditional_edges("plan", fan_out, ["source_worker"])   # fan-out
    g.add_edge("source_worker", "gather")                         # fan-in (reducer merges)
    g.add_edge("gather", END)
    return g.compile()

print("Graph builder ready")
```

    Graph builder ready

## Step 6 — Run it

### Mock run (no API key) — prove the wiring

A tiny mock model returns each source's view of the same June total. payroll and
GL agree on everything; `social_security` is 12万 low on 社保代扣 (base not synced),
`attendance` is 15万 high on 加班费 (overtime rule changed, payroll never got it).
The reconciler should agree on 基本工资 and **locate** the two gaps.

```python
LEDGER = {
    "payroll":         {"基本工资": 3_100_000.0, "社保代扣": 120_000.0, "加班费": 100_000.0},
    "gl":              {"基本工资": 3_100_000.0, "社保代扣": 120_000.0, "加班费": 100_000.0},
    "social_security": {"基本工资": 3_100_000.0, "社保代扣": 108_000.0, "加班费": 100_000.0},
    "attendance":      {"基本工资": 3_100_000.0, "社保代扣": 120_000.0, "加班费": 250_000.0},
}

class _MockStructured:
    def __init__(self, src): self.src = src
    def invoke(self, prompt: str) -> SourceReading:
        # a real model would read the source system; here we look it up
        for name in LEDGER:
            if name in prompt.split("\n", 1)[0]:
                return SourceReading(source=name, line_items=LEDGER[name])
        return SourceReading(source="?", line_items={})

class _MockModel:
    def with_structured_output(self, schema): return _MockStructured(schema)

app = build_graph(_MockModel())
out = app.invoke({"rows": [{"id": "e1"}], "sources": [], "readings": [], "report": None})
rep = out["report"]
print("agreed:     ", list(rep.agreed_items))
for verdict in rep.attributable_divergences:
    print(f"located:     {verdict.item} gap {verdict.gap:,.0f}  "
          f"[{list(verdict.low_sources)} low vs {list(verdict.high_sources)} high]")
print("to_human:   ", [verdict.item for verdict in rep.to_human])
```

    agreed:      ['基本工资']
    located:     加班费 gap 150,000  [['payroll', 'gl', 'social_security'] low vs ['attendance'] high]
    located:     社保代扣 gap 12,000  [['social_security'] low vs ['payroll', 'gl', 'attendance'] high]
    to_human:    []

The graph ran four source workers in parallel, the reducer merged their
readings, and the gather **located** both gaps to a subsystem — no agent guessed.
基本工资 agreed, so the gap is not there. That is divergence-as-locator.

### Real run — plug in a model

Swap the mock for a real model. Each source worker is cheap (the reconciler is
deterministic Python, so you spend model budget only on reading the sources).

```python
from model_config import get_model      # registers CN providers; reads .env

model = get_model()                     # each source worker; cheap model is fine
if model:
    app = build_graph(model)
    out = app.invoke({"rows": [{"id": "e1"}], "sources": [], "readings": [], "report": None})
    print(out["report"].attributable_divergences)
else:
    print("No API key — set one in .env to run the real version.")
```

    No API key — set one in .env to run the real version.

## The reducer gotcha, once more

If you forget the `Annotated[list, operator.add]` reducer on `readings`, the
second parallel worker to write raises:

```
InvalidUpdateError: At key 'readings': Can receive only one value per step.
```

That is a **feature**. LangGraph will not silently let one worker's reading
overwrite another's — a silent overwrite in a reconciliation is the kind of bug
that ships a wrong number. Loud beats silent.

## What LangGraph gives you here

1. **Parallel fan-out + safe fan-in** → `Send` (same rows to N sources) +
   `Annotated[list, operator.add]`. The `InvalidUpdateError` without a reducer
   refuses to drop a reading.
2. **Structured readings** → `with_structured_output` means the reconciler
   compares typed numbers, not parsed prose.
3. **A gather you can test in isolation** → the `gather` node is a thin wrapper
   over `Reconciler`, which has its own unit tests with no graph and no model.

## When this breaks

The failure modes from the lecture, and where they live in this graph:

| Failure | In this graph |
|---|---|
| **Redundant analysis** (same finding three times) | The gather concatenating instead of reconciling. Answer Q3 (dedup) — for competing results, compare; for additive, collapse aliases. |
| **Missing integration** (a seam only visible across workers) | No seam reviewer. Answer Q4 — add a reviewer that reads the assembled report, not a slice. |
| **Aggregation bottleneck** (gather drowns as N grows) | One gather reading 50 workers. Go hierarchical — combine in groups first. |
| **Straggler / partial failure** | An unhandled exception in a source worker. Isolate it (as `pattern.py`'s `_run_one` does) and enforce the `min_success_rate` floor. |
| **Fan-in data loss** | Forgetting the `operator.add` reducer → `InvalidUpdateError` (loud, not silent — good). |
| **Non-attributable workers** | Workers resampling the same data instead of binding to distinct sources. Then divergence only flags uncertainty; it can't locate a root cause. |

Next: the same pattern with the Claude Agent SDK, where each source is a
declarative subagent and isolation is built in →
[`../claude-agent-sdk/tutorial.md`](../claude-agent-sdk/tutorial.md).
