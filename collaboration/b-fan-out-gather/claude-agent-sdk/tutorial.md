# Fan-out-Gather — Claude Agent SDK Implementation

> "Isolation you don't wire. The gather you still own."

This notebook builds Fan-out-Gather with the **Claude Agent SDK**. Each data
source becomes a declarative `AgentDefinition`; the orchestrator fans out by
delegating to them through the **Agent tool**. The SDK gives you the isolation
for free — each subagent runs in its own fresh conversation and only its final
message returns to the parent — so the "orchestrator drowns in worker traces"
failure can't happen by construction.

But the **gather stays in Python**. The whole point of the pattern is that
divergence between sources *locates* the gap, and that comparison must be
deterministic — not something an orchestrator improvises in prose. So every
source subagent returns a small JSON reading, and the same `Reconciler` from
[`pattern.py`](../pattern.py) does the three-layer reconciliation.

Scenario: column lecture **07-03** — the June ledger is off, and four sources
(payroll / GL / social-security / attendance) each compute the same total by
their own lens.

## Two implementations, two philosophies

| | `langgraph/` | `claude-agent-sdk/` (this notebook) |
|---|---|---|
| **You write** | An explicit `StateGraph` — `Send` fan-out, reducer fan-in, gather node. | Declarative `AgentDefinition`s, one per source. The runtime delegates and isolates. |
| **Fan-out** | `Send` — same rows to N nodes. | The **Agent tool**, or one parallel `query()` per source. |
| **Isolation** | You wire it (reducer / `output_mode`). | **Built in** — each subagent is a fresh conversation; only its final message returns. |
| **Gather** | A `gather` node calling `Reconciler`. | The **same** `Reconciler`, in Python, after the subagents return. |

The gather is identical on both sides. That's the point of keeping it in
`pattern.py`: the reconciliation is framework-agnostic and deterministic.

## Setup

```python
from __future__ import annotations

import asyncio
import json
import os
import sys

# reuse the framework-agnostic gather from pattern.py
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))

from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions, query
from pattern import Reconciler, SourceResult

print("claude-agent-sdk imports ready:", AgentDefinition.__name__, query.__name__)
```

    claude-agent-sdk imports ready: AgentDefinition query

## The shape we're filling

| pattern.py | Claude Agent SDK |
|---|---|
| fan the **same** task to N sources | N `AgentDefinition`s + the Agent tool (or one `query()` per source) |
| worker isolated, returns only a reading | **built in** — each subagent is a fresh conversation; only its final message returns |
| each worker bound to an attributable source | a subagent whose `prompt` pins it to ONE source system |
| the reconciler (the soul) | the **same** `Reconciler`, kept in deterministic Python |

## Step 1 — one subagent per data source

Each source is a declarative `AgentDefinition`. Three fields carry the pattern:

- **`description`** — when the orchestrator should delegate to it (the routing key).
- **`prompt`** — pins the subagent to ONE source system, so its reading is
  *attributable*. That binding is what turns divergence into a locator.
- **`tools`** / **`model`** — read-only access, and a cheap model (the judgment is
  in the Python reconciler, not the worker).

```python
SOURCE_SYSTEMS = {
    "payroll":         "the payroll master system",
    "gl":              "the general-ledger (GL) system",
    "social_security": "the social-security system",
    "attendance":      "the attendance & overtime system",
}

def source_agent(source: str, system: str) -> AgentDefinition:
    return AgentDefinition(
        description=f"Reconciles the June total from {system}. Use for the {source} lens.",
        prompt=(
            f"You reconcile payroll totals STRICTLY from {system}. Compute each line "
            "item (基本工资 / 社保代扣 / 加班费 / ...) from THIS system's records only; "
            "never borrow another system's number. Return a JSON object with keys "
            "`source` and `line_items` (a mapping of line item to amount)."
        ),
        tools=["Read", "Bash"],      # read-only access to this one source
        model="haiku",               # cheap; the judgment lives in the Python reconciler
    )

SUBAGENTS = {f"src-{s}": source_agent(s, sysname) for s, sysname in SOURCE_SYSTEMS.items()}
print(f"{len(SUBAGENTS)} source subagents:", list(SUBAGENTS))
```

    4 source subagents: ['src-payroll', 'src-gl', 'src-social_security', 'src-attendance']

## Step 2 — the orchestrator options

`ClaudeAgentOptions` wires the orchestrator: a stronger `model`, the `agents`
map, and — crucially — `"Agent"` in `allowed_tools`, which is the delegation
tool the orchestrator uses to spawn subagents.

```python
options = ClaudeAgentOptions(
    model="sonnet",                              # orchestrator; workers are haiku
    agents=SUBAGENTS,
    allowed_tools=["Read", "Bash", "Agent"],     # "Agent" = the delegation tool
)
print("options ready — orchestrator can delegate to", len(options.agents), "subagents")
```

    options ready — orchestrator can delegate to 4 subagents

## Step 3 — the gather stays in Python (the soul)

Whichever way you fan out, do **not** let the orchestrator reconcile in prose.
Each subagent returns a JSON reading; Python parses it into a `SourceResult` and
runs the deterministic `Reconciler`. Here we reconcile the four readings the
subagents *would* return (mocked so this cell runs with no API key) — the live
version in Step 4 produces the same JSON from `query()`.

```python
# What the four subagents return. Live, these strings come from query(); here
# they are mocked so the gather runs deterministically with no API key.
MOCK_RETURNS = [
    '{"source":"payroll","line_items":{"基本工资":3100000,"社保代扣":120000,"加班费":100000}}',
    '{"source":"gl","line_items":{"基本工资":3100000,"社保代扣":120000,"加班费":100000}}',
    '{"source":"social_security","line_items":{"基本工资":3100000,"社保代扣":108000,"加班费":100000}}',
    '{"source":"attendance","line_items":{"基本工资":3100000,"社保代扣":120000,"加班费":250000}}',
]

def to_source_result(payload: dict) -> SourceResult:
    source = payload["source"]
    return SourceResult.from_mapping(
        source_id=source,
        snapshot_ref=f"snapshot://{source}/2026-06-30T23:59:59Z",
        period="2026-06",
        unit="CNY",
        line_items=payload["line_items"],
    )

readings = [to_source_result(json.loads(r)) for r in MOCK_RETURNS]
report = Reconciler(tol=1.0).reconcile(readings)      # the SAME gather as the LangGraph version

print("agreed:", list(report.agreed_items))
for verdict in report.attributable_divergences:
    print(
        f"located: {verdict.item} gap {verdict.gap:,.0f} -> "
        f"{list(verdict.low_sources)} low vs {list(verdict.high_sources)} high"
    )
```

    agreed: ['基本工资']
    located: 加班费 gap 150,000 -> ['payroll', 'gl', 'social_security'] low vs ['attendance'] high
    located: 社保代扣 gap 12,000 -> ['social_security'] low vs ['payroll', 'gl', 'attendance'] high

## Step 4 — fan out for real with `query()`

One `query()` per source is an explicit, deterministic fan-out: `asyncio.gather`
runs them concurrently, each subagent works in its own isolated conversation, and
only its final JSON comes back. Then — again — Python reconciles. This cell needs
a live API key and the Claude Code CLI, so it is not executed in the build.

```python
async def run_reconciliation(rows: list[dict]) -> dict:
    """Fan out one isolated subagent per source, gather in Python."""

    async def ask(source: str) -> SourceResult:
        opts = ClaudeAgentOptions(
            model="haiku",
            agents={f"src-{source}": SUBAGENTS[f"src-{source}"]},
            allowed_tools=["Read", "Bash", "Agent"],
        )
        prompt = (f"Use the src-{source} subagent to compute this month's line-item "
                  "totals for the roster, and return its JSON verbatim.")
        text = ""
        async for msg in query(prompt=prompt, options=opts):
            for block in getattr(msg, "content", None) or []:
                if getattr(block, "text", None):
                    text = block.text            # keep the last text block = final answer
        return to_source_result(json.loads(text))

    # parallel fan-out; each subagent is isolated by the SDK
    readings = await asyncio.gather(*(ask(s) for s in SOURCE_SYSTEMS))
    return Reconciler(tol=1.0).reconcile(readings)   # the gather stays in Python

# asyncio.run(run_reconciliation(roster))   # needs a live API key + the Claude Code CLI
print("run_reconciliation defined — call it with a live key to fan out for real.")
```

    run_reconciliation defined — call it with a live key to fan out for real.

## What the SDK gives you here

1. **Isolation for free** → each subagent is a fresh conversation; only its final
   message returns. No reducer to wire, no `output_mode` to remember. The
   orchestrator can't drown in worker traces.
2. **Declarative fan-out** → adding a fifth source is one more `AgentDefinition`.
3. **The gather is still yours** → the reconciliation is deterministic Python
   (`Reconciler`), unit-tested with no model. The SDK moves the *data*; it does
   not get a vote on where the gap is.

## When this breaks

| Failure | With the SDK |
|---|---|
| **Reconciling in prose** | Letting the orchestrator "summarise" the four readings instead of returning them for the Python `Reconciler`. Divergence-location must be deterministic. |
| **Non-attributable workers** | Subagent prompts that don't pin one source system. Then their divergence only flags uncertainty; it can't locate a subsystem. |
| **Aggregation bottleneck** | One orchestrator reading dozens of subagent outputs. For scale, the SDK docs point at the `Workflow` tool over many subagents; group and combine hierarchically. |
| **Straggler / partial failure** | A subagent that errors. Wrap `ask()` in try/except → an `ok=False` `SourceResult`, and let `pattern.py`'s `min_success_rate` floor decide. |

Back to the explicit version if you want to see every edge:
[`../langgraph/tutorial.md`](../langgraph/tutorial.md).
