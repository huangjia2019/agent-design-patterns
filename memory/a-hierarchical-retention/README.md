# a · Hierarchical Retention

> Column lecture **03-02** · pattern · memory × route
>
> [中文 README](README.zh-CN.md)

## The problem

An online Python school built a programming coach agent. Week one the
agent was stateless. A student would return for a third session and the
agent would still ask "have you learned `list`?" — yes, she had, the
previous two sessions.

The team added a chat-history field. Now the agent loaded the entire
prior conversation into the prompt. By the fifth session the prompt was
30K tokens of irrelevant history; the agent had forgotten what they
were currently working on. The student fed back: "It used to forget
everything. Now it remembers everything but doesn't know what matters."

Agent memory is not one thing. The user's Python skill level (changes
every few months) lives in a different scope from the project's tech
stack (changes per project) from the session's current topic (changes
every conversation) from the turn's just-defined helper function
(changes every tool round). Stuffing all four into one prompt either
explodes the token budget or buries the signal.

## The pattern

Four layers, coarse to fine, each with its own backend, TTL, and token
budget. Inner layers override outer layers when keys conflict; the
read-from-finest routing is the topology behind the pattern's matrix
placement.

| Layer | Scope | Typical backend | TTL | Token budget |
|---|---|---|---|---:|
| **USER** | across all sessions, all projects | postgres | permanent | 2,000 |
| **PROJECT** | within one project, across sessions | file | permanent | 4,000 |
| **SESSION** | within one conversation | redis | 24h | 8,000 |
| **TURN** | within one tool round | in-process | 5 min | 2,000 |

Two invariants:

* **Read inner-first.** A SESSION value for `preference` wins over a
  USER value for `preference` — without overwriting USER. The override
  is contextual, not destructive.
* **Assemble outer-first.** When building the prompt, render USER →
  PROJECT → SESSION → TURN so the model reads context coarse-to-fine,
  matching how humans absorb hierarchical information.

## Quickstart

```bash
python memory/a-hierarchical-retention/example.py
pytest memory/a-hierarchical-retention/
```

The demo simulates Alice's fourth session at the Python school: USER
profile loaded from postgres, PROJECT loaded from file backend, SESSION
restored from redis, TURN starts empty. Watch override semantics in
action and TTL-driven TURN expiry.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `HierarchicalRetention` + `Layer` + `MemoryLayer` (~150 lines) |
| `example.py` | Programming-coach scenario, Alice's 4th session |
| `test_pattern.py` | 10 invariants: read/write per layer, inner-overrides-outer, TTL expiry, evict_expired, assemble order, health report, custom config |

## Engineering references (verified)

* **Claude Code** memory hierarchy: 4 tiers (Enterprise / User / Project /
  Local) + `@import` for on-demand inclusion. See
  [Best Practices · Memory](https://docs.claude.com/en/docs/claude-code/memory).
* **MemGPT** (Packer et al., 2023, [arXiv:2310.08560](https://arxiv.org/abs/2310.08560))
  — virtual-memory analogue for LLMs with hot/warm/cold tiering. Earliest
  influential statement of the OS-memory-hierarchy analogy.
* **CoALA** (Sumers et al., 2024) — three-layer cognitive architecture
  (working / episodic / semantic). Hierarchical Retention's 4 layers
  refine the CoALA story toward production agent infrastructure.
* **Hermes Honcho** — two-layer split: persistent user model + ephemeral
  session context. A minimal real-world implementation.
* **Cline Memory Bank** — file-based persistence per project, equivalent
  to the PROJECT layer here.

## When this pattern doesn't apply

* **Single-turn agents.** No need for SESSION or TURN. USER + PROJECT
  is enough.
* **Single-user agents.** Skip USER. PROJECT + SESSION suffices.
* **Cold-only agents.** Pipelines that run on demand, never resumed —
  one layer is enough.
* **Massive scale with strict privacy.** Cross-session retention may
  conflict with data-residency rules; talk to your privacy team before
  enabling the USER layer.
