# d · Handoff Chain

> Column lecture **07-05** · pattern · Collaborate × Chain
>
> [中文 README](README.zh-CN.md)

## The problem

An AI travel assistant turns "I need to be in Shanghai tomorrow afternoon" into a
booked trip by passing a baton down a line of specialists: intent → route (Amap) →
flight → airport taxi (Didi) → hotel (Ctrip). Each stage reads the baton, does its
one job, and adds to it.

This is not a tree (that is Hierarchical Delegation) and not parallel copies (that is
Fan-out-Gather). It is a line, and the whole risk lives at the **seams** between
stages. If the route stage forgets to hand off the departure deadline, the taxi stage
books a car that can't make the flight — and you find out at the airport, three
stages downstream from the mistake, where the cause is already unrecoverable.

## The pattern

Two named tools carry it (from the lecture):

**The Baton Contract (接力棒规约)** — every stage declares what it `requires` from the
baton and what it `provides`. The chain validates both at each seam. A stage handed a
baton missing what it needs, or a stage that doesn't deliver what it promised, fails
fast — *at the seam that dropped it*, with the stage named — not three stages later
where the cause is lost.

**Append-only baton (棒上不回改)** — the intent is set once and carried unchanged;
committed facts are locked once set. A later stage may add, never silently overwrite.
The handoff passes values, not a shared mutable scratchpad, so one stage cannot
quietly rewrite what an earlier stage committed.

Both rules are enforced in `pattern.py`, so a broken chain raises a `SeamError` that
names the culprit — the fix is one place, not a hunt.

## Two runnable implementations

Same pattern, same `pattern.py` contract, two ways to run the line:

| | [`langgraph/`](langgraph/tutorial.ipynb) | [`claude-agent-sdk/`](claude-agent-sdk/tutorial.ipynb) |
|---|---|---|
| **The chain** | A linear `StateGraph`: `intent → route → flight → taxi → hotel`. | A Python sequence running one subagent per stage. |
| **The baton** | The graph's accumulating state. | A JSON baton passed hand to hand. |
| **Seam checks** | A `guarded` node wrapper reusing `StageSpec` / `SeamError`. | The same `HandoffChain` checks in Python between subagents. |
| **Model** | Provider-agnostic (`model_config`). | Claude-native (a `haiku` specialist per stage). |

No parallelism here means no reducer — the chain is a straight line. The contract is
identical on both sides.

## Files

| File | What |
|---|---|
| [`pattern.py`](pattern.py) | Framework-agnostic reference (~140 lines): `Baton`, `StageSpec`, `SeamError`, `HandoffChain`, and `trip_chain`. A pluggable `StageFn` is the seam both tutorials fill. |
| [`example.py`](example.py) | Runs the trip chain with mock stages — no API key. Shows a clean run and a dropped handoff failing fast at the culprit stage. |
| [`test_pattern.py`](test_pattern.py) | 8 tests: accumulation + order, the missing-requirement seam error, append-only enforcement, the underdelivery check, and intent carried unchanged. |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | Step-by-step: accumulating State → a `guarded` seam wrapper → a linear graph → a broken chain failing at its seam. |
| [`claude-agent-sdk/tutorial.ipynb`](claude-agent-sdk/tutorial.ipynb) | Step-by-step: one `AgentDefinition` per stage → the `HandoffChain` contract in Python → a live `query()` chain. |

## Run

```bash
# framework-agnostic core — no API key
python collaboration/d-handoff-chain/example.py
pytest collaboration/d-handoff-chain/test_pattern.py -v

# the two implementations need a model — see .env.example
```

## Where this pattern sits

Collaborate (cognitive function) × Chain (execution topology). Its module-mates:
Hierarchical Delegation (a tree), Fan-out-Gather (parallel copies), Adversarial
Review (a loop). Handoff Chain is the line — the simplest topology, and the one where
the danger is entirely at the joints. See the [two-axis matrix](../../README.md).
