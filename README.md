# Agent Design Patterns

> Companion code for **"Agent 设计模式之美"** column on Geek Time and the
> Manning book *Designing AI Agents* by Jia Huang (黄佳).
>
> Each folder maps to one column lecture. Every pattern ships with a minimal,
> runnable Python reference implementation plus a short README so you can
> understand the pattern without leaving GitHub.

[简体中文 README](README.zh-CN.md)

---

## What this repo is

Production agents fail at the seams — the places where one capability hands
off to another. Most of those seams are well-understood design problems with
names from operating-system theory, distributed systems, and forty years of
software engineering: priority scheduling, lazy loading, virtual memory,
event-driven control loops. The Agent Design Patterns project is an attempt to
name those seams and give each one a small, honest reference implementation.

The patterns are organised along two axes:

* **Cognitive function** — what the agent is doing (perceive / remember /
  reason / act / reflect / collaborate / govern).
* **Execution topology** — how the work is laid out at runtime (single-step /
  sequential / parallel / loop / router / hierarchy).

The matrix has 7 × 6 = 42 cells. Most cells are not interesting on their own.
The 27 that are interesting are the patterns you will find here.

## Repo layout

```
perception/       # Perception patterns (chapter 02)
  a-context-triage/
  b-semantic-compaction/
  c-progressive-discovery/
  d-multimodal-fusion/

memory/           # Memory patterns (chapter 03)        — coming
collaboration/    # Collaboration patterns (chapter 04) — coming
composition/      # Pattern composition (chapter 05)    — coming
```

Letter prefixes (`a-`, `b-`, ...) reflect the order patterns appear in the
column. They do not imply dependency: every pattern folder is self-contained.

## Quickstart

```bash
git clone https://github.com/<your-username>/agent-design-patterns.git
cd agent-design-patterns
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run the first pattern's runnable example
python perception/a-context-triage/example.py

# Or run the full test suite
pytest
```

Each pattern folder also has its own `README.md` with one-screen quickstart.

## Patterns shipped so far

| Folder | Pattern | Column lecture | Status |
|---|---|---|---|
| `perception/a-context-triage` | Context Triage (P0/P1/P2/P3 priority scheduling) | 02-02 | runnable |
| `perception/b-semantic-compaction` | Semantic Compaction (anchored iterative summarisation) | 02-03 | runnable |
| `perception/c-progressive-discovery` | Progressive Discovery (agentic search) | 02-04 | placeholder |
| `perception/d-multimodal-fusion` | Multi-Modal Fusion | 02-05 | placeholder |

## How to read a pattern folder

Every pattern folder has the same shape:

```
README.md / README.zh-CN.md   # The story: why this pattern exists
pattern.py                    # The smallest honest reference implementation
example.py                    # A runnable demo that shows the pattern in action
test_pattern.py               # pytest: behaviour we promise the pattern has
```

Read the README first to understand the problem. Then read `pattern.py` to
see the smallest amount of code that solves it. Run `example.py` to see it
work on real-looking data. The tests pin down the invariants you should not
break when adapting the pattern to your own project.

## Engineering claims and verifiable references

When the column or a README cites a file in another open-source framework
(Aider's `repomap.py`, OpenHands' `condenser_config.py`, etc.), the citation
is a real file at a real path in that project. If you find a citation that
doesn't match the upstream code, open an issue — that's a bug, not a
documentation choice.

## Status

This is a teaching repository. APIs are intentionally small and unstable —
the goal is clarity, not framework adoption. If you want a production runtime,
use one of the harnesses the column dissects (Claude Code, Aider, OpenHands,
DeepAgents, ...). If you want to understand what those harnesses are doing,
read this repo alongside the column.

## License

MIT. See [LICENSE](LICENSE).
