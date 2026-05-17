# a · Context Triage

> Column lecture **02-02** · pattern · perception × router
>
> [中文 README](README.zh-CN.md)

## The problem

When the candidate context items add up to more than the model's window, you
have to choose. Pick badly and the agent silently looks at the wrong thing.
The classic failure mode is a loan-evaluation agent that ranked documents by
filename order, dropped a 2024 collateral appraisal, kept a 2019 expired
business registration, and recommended approval. The bug was not reasoning —
the agent never *saw* the disqualifying document.

## The pattern

Sort the candidate items into four tiers, fill the budget from the top down,
keep error traces invariant.

| Tier | What goes here | Loaded? |
|---|---|---|
| **P0 CRITICAL** | system prompt, safety rules, tenant identity, current task | always |
| **P1 IMPORTANT** | current file, recent tool result, error traces | budget permitting |
| **P2 SUPPORTING** | past dialogue, background docs | budget permitting, compressible |
| **P3 DEFERRABLE** | knowledge base, archive, runbooks | not pre-loaded; pulled via tool handle |

One invariant overrides everything: **error stack traces are never dropped.**

The pattern is the operating-system priority scheduler in new clothing. P0 is
the realtime queue. P3 is paged-out virtual memory waiting on a fault.

## Quickstart

```bash
python perception/a-context-triage/example.py
pytest perception/a-context-triage/
```

Expected output of `example.py` shows the selected items, the deferred P3
handles, and confirms the two invariants — error trace preserved, P3 not
loaded.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | The `ContextTriage` class — ≈ 90 lines, no dependencies |
| `example.py` | Multi-tenant SaaS scenario, twelve candidate items, 8K budget |
| `test_pattern.py` | Seven invariants the pattern must hold |

## Engineering references (verified)

* Aider's `RepoMap`: [`aider/aider/repomap.py`](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)
  — automatic symbol extraction + PageRank-style ranking, the opposite end of
  the human/algorithm axis from Claude Code's CLAUDE.md
* Anthropic Claude Code memory hierarchy: [Best Practices · Memory](https://docs.claude.com/en/docs/claude-code/memory)
  — four tiers (Enterprise / User / Project / Local) plus `@import` for
  on-demand inclusion. The often-cited "200-line CLAUDE.md sweet spot" is
  defined here
* DeerFlow's schema-driven triage: [bytedance/deer-flow](https://github.com/bytedance/deer-flow)
  — `tenant_id`, `user_id`, `project_id` enforced as schema fields, not
  optional metadata
* The Manus failure story (487-token stack trace compacted into
  "a database error occurred") is documented in
  [Manus' Context Engineering blog](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

## When this pattern doesn't apply

If your task's full candidate set is under ~50K tokens — a narrow chatbot, a
single-document summariser — just put everything in the prompt. Triage adds
engineering cost without payback until you hit the window.
