# d · Failure Journals

> Column lecture **03-05** · pattern · remember × loop
>
> [中文 README](README.zh-CN.md)

## The problem

A Claude Code session, two weeks ago, was asked to fix a 302 redirect
loop in `auth-service`. It fixed the bug. While editing the OAuth
config it also wrote the *test* environment's `client_id` into
`config/prod/oauth.yaml`. The pre-deploy diff catch saved production.

Two weeks later, a different Claude Code session in a different
microservice was asked to fix an unrelated OAuth refresh bug. It fixed
that bug too. While editing the OAuth config it wrote a different test
`client_id` into a different `config/prod/oauth.yaml`. Caught again,
this time later, after one staging deploy.

**The model was not stupider the second time.** The model was, in
fact, identical. What was missing was the journal entry from the first
incident — a structured record saying *"two weeks ago, on this kind of
task, you did this exact thing; before you touch any prod config,
re-read this."* No such record existed because nothing wrote one.

This is the gap between observability (the engineer can search Sentry
for it after the fact) and *recall* (the agent reads the lesson
*before* taking the action). Failure Journals closes that gap.

## The pattern

Four stages, after [arxiv:2509.25370 (Where LLM Agents Fail)](https://arxiv.org/abs/2509.25370):

```
Detection → Classification → Recording → Recall
```

The third stage is where most teams stop. The fourth is what turns a
log into experience.

The schema for one entry:

| Field | Example | Why it's typed and not free text |
|---|---|---|
| `failure_id` | `eec56c352a1e` | Stable hash so retries don't duplicate entries |
| `task_signature` | "fix oauth callback bug in auth-service; touch config/oauth.yaml" | The key recall matches against |
| `category` | `BOUNDARY_LEAK` | One of 10 typed categories; lets the journal cluster, filter, and prioritize |
| `summary` | "Test client_id 'test-acme-3489' written to config/prod/oauth.yaml" | One line, capped at 200 chars |
| `root_cause` | `RuntimeError` | Class or short cause string |
| `lessons` | ["always re-read env header", "diff unrelated config changes"] | The actionable carryover to inject into next prompt |
| `access_count` | `3` | Recall hits — entries that earn their keep survive eviction |

The ten categories condense [Hermes Agent's 13 `FailoverReason` enum](https://github.com/openhermes/agent)
(auth, billing, rate_limit, overloaded, server_error, timeout,
context_overflow, payload_too_large, image_too_large, model_not_found,
provider_policy_blocked, format_error, thinking_signature) plus three
agent-era extras:

* `SEMANTIC_DRIFT` — agent stopped solving the user's task
* `BOUNDARY_LEAK` — config/env/tenant slipped across a boundary that
  should have held (the lecture-opening incident)
* `INDEX_LAG` — Boris-Cherny-era failure: data exists on disk but the
  retrieval index hasn't caught up

Two of those — `BOUNDARY_LEAK` and `PERMISSION_DENY` — are *high-risk*.
The journal protects them from eviction and surfaces them on every
recall regardless of similarity score. They are the failures you
cannot afford to ever forget.

## Quickstart

```bash
python memory/d-failure-journals/example.py
pytest memory/d-failure-journals/
```

The demo replays the lecture-opening incident. Two weeks separate the
two sessions; the second session calls `recall_for_task` before
touching any config, and the prior entry surfaces into the prompt
before the agent acts.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `FailureCategory` + `FailureEntry` + `FailureJournal` (~240 lines) |
| `example.py` | Two-session OAuth scenario reproducing the lecture-opening incident |
| `test_pattern.py` | 15 invariants: stable id, classification, recall ranking, top_k, high-risk override, eviction protection, render format, health report |

## The Manus rule the pattern enforces

From [Yichao Peak Ji's *Context Engineering for AI Agents* essay](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus):

> "When the model sees a failed action and the resulting observation
> or stack trace, it implicitly updates its internal beliefs, shifting
> its prior away from similar actions and reducing the chance of
> repeating the same mistake. Erasing failure removes evidence, and
> without evidence, the model can't adapt."

That is the operational reason the pattern exists. The journal isn't
an audit log; it's the evidence the model needs at recall time.

## Engineering references (verified)

* **Hermes Agent** [`agent/error_classifier.py`](https://github.com/openhermes/agent) — the
  13-`FailoverReason` enum and `trajectory_compressor.py` that
  compresses completed agent trajectories for training-data reuse.
  The closest production analog to what this pattern reifies.
* **Aider** [`aider/coders/base_coder.py`](https://github.com/Aider-AI/aider/blob/main/aider/coders/base_coder.py) —
  `max_reflections=3` + `reflected_message` field — the in-task self-heal
  loop. Failure Journals is what Aider would be if `reflected_message`
  persisted across sessions.
* **Manus** [*Context Engineering for AI Agents*](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) —
  the "don't hide errors from the model" rule.
* **arxiv:2603.21357 (AgentHER)** — *Hindsight Experience Replay for
  LLM Agents.* The training-side counterpart: re-label failed
  trajectories as successes under a relaxed task. 85% of failed
  trajectories become usable training data after hindsight relabel.
* **arxiv:2506.06698 (CER)** — *Contextual Experience Replay.* The
  training-free counterpart: inject recalled experiences into the
  prompt at runtime. This pattern is a minimal CER.
* **arxiv:2509.25370 (Where LLM Agents Fail)** — gives the four-stage
  framework Detection → Classification → Recording → Recall.
* **NeuralWired (2026)** [*Why AI Agents Fail in Production*](https://neuralwired.com/2026/04/28/why-ai-agents-fail-production/) —
  the 48h/30d/90d tiered retention guidance the `_evict_if_needed`
  method approximates in single-tier form.
* **Mem0 (2026)** [*State of AI Agent Memory*](https://mem0.ai/blog/state-of-ai-agent-memory-2026) —
  the procedural-memory hit-rate metric `health_report()` exposes.

## When this pattern doesn't apply

* **Single-shot scripts and prototypes.** No future session to recall
  from. The overhead doesn't pay back.
* **Stateless agents with strict no-PII storage policies.** Recording
  failure summaries that contain task signatures may be regulated.
  Strip or hash the signatures, or keep the journal to category +
  count only.
* **Pure conversation agents.** No actions, no failures with
  external consequence. A journal will collect "model said an
  awkward thing" noise that nobody acts on.

The journal's value is concentrated in long-running production agents
that touch configuration, tools, or tenant data. That is also exactly
where the lecture-opening incident lives.

## Engineering shortcuts taken (be honest about them)

The reference is a minimal honest version. To run this in production
you would add:

* **Embedding-based similarity.** The default `_jaccard_similarity` is
  word-set overlap. Real recall uses cosine similarity on
  `text-embedding-3-small` or `bge-base-en`.
* **Persistent storage.** In-memory dict, swap for sqlite/postgres
  through the same recording / recall API.
* **Schema-enforced write path.** Let agents propose entries, but
  validate `category`, cap `summary` length, and gate `lessons` for
  actionability before persisting.
* **Tiered retention.** 48h hot / 30d warm / 90d+ cold per
  NeuralWired's guidance, with separate backends per tier.

These are deployment concerns, not pattern concerns. The pattern is
the four-stage contract and the schema. Everything else is plumbing.
