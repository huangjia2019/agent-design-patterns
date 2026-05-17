# Perception · Module

> Column chapter **02-感知-世界之美** · cognitive function row in the
> 7 × 6 pattern matrix
>
> [中文 README](README.zh-CN.md)

## What perception covers

Perception is the first cognitive function in the agent stack and the one
where most production agents quietly fail. The module covers four patterns
that together answer "what does the agent see, in what order, and at what
cost?"

| Folder | Pattern | Topology | Lecture |
|---|---|---|---|
| `a-context-triage` | Context Triage — sort by priority, drop the rest | Router | 02-02 |
| `b-semantic-compaction` | Semantic Compaction — anchored iterative summary | Sequential | 02-03 |
| `c-progressive-discovery` | Progressive Discovery — agentic search | Loop | 02-04 (placeholder) |
| `d-multimodal-fusion` | Multi-Modal Fusion — image / table / text | Parallel | 02-05 (placeholder) |

The four sit at four different cells of the same row (perception), each at a
different execution topology. That is the design point of the column's
two-axis framework: one cognitive function gives you many patterns because
each runtime shape changes how the function is realised.

## How to read this module

Read `a-context-triage` first. It is the simplest pattern, the one every
production agent eventually needs, and the foundation that the other three
build on. Read `b-semantic-compaction` next — it picks up where Triage runs
out of budget. The `c` and `d` patterns extend the story to "what if I
don't know what to read in the first place" (Progressive Discovery) and
"what if the input isn't text" (Multi-Modal Fusion).

## Run the whole module

```bash
# From repo root
python perception/a-context-triage/example.py
python perception/b-semantic-compaction/example.py
pytest perception/
```

## The signature insight

Perception is not "feed the model more context." Perception is
*budget allocation under uncertainty* — the same problem operating-system
schedulers have been solving since the 1970s, with priority queues, virtual
memory, and lazy loading. Every pattern in this module is a re-statement of
that observation for the LLM substrate.
