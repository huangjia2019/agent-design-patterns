# c · Progress Tracking

> Column lecture **03-04** · pattern · memory × orchestrate
>
> [中文 README](README.zh-CN.md)

## The problem

An agent is asked to refactor a 600-line Python module into 4 files
plus tests, with backwards-compatible re-exports. It writes a clean
plan, migrates files 1 through 3, hits a bug in `parsers.py`, and
spends 20 turns debugging it. After the debug detour the agent writes
the tests, runs CI, reports "done."

Then the tests fail. **File 4 never got created.** The agent forgot it
existed during the debug detour. When pointed at it, the agent pauses
three seconds and says "you're right, I missed it."

LLMs have no working memory. Everything they "remember" is in the
context window, and the window has a U-shaped attention curve — the
middle of a long task gets buried. A 20-turn debug detour mid-task
buries the original plan.

The fix is dumb-engineering robust: force the agent to maintain a
structured todo list, externalised into the conversation, and nudge it
back to that list whenever the conversation drifts.

## The pattern

Mirror Claude Code's three-field `TodoWrite`:

| Field | Example | Used for |
|---|---|---|
| `content` | "Fix cache invalidation bug" | the imperative task |
| `active_form` | "Fixing cache invalidation bug" | display while in_progress |
| `status` | `pending` / `in_progress` / `completed` / `needs_review` | the dynamic field that prevents amnesia |

Three invariants:

* **At most one `in_progress` at a time.** Starting a new item bumps
  any other in-progress one back to pending. Forces the agent to
  finish one thing or explicitly defer.
* **Per-owner isolation.** Sub-agents have their own lists; they don't
  pollute the parent's todos.
* **Auto-evict when done.** When all items complete, the list clears.
  Claude Code's counter-intuitive but necessary "clear when done"
  behaviour — keeps stale plans from confusing the next session.

On top of the list, the `ProgressTracker` watches the recent message
flow. When complexity is high (lots of action verbs, sequencing words)
and there are no todos, it injects **escalating nudges** — a calm
reminder first, a "you appear to be drifting" second, a "STOP" third.

## Quickstart

```bash
python memory/c-progress-tracking/example.py
pytest memory/c-progress-tracking/
```

The demo replays the 600-line-refactor incident: plan written, files
1-3 done, 24-turn debug detour, tracker fires context-loss nudge,
agent re-reads the list, picks up the forgotten file 4, completes
everything, list auto-evicts.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `TodoItem` + `TodoList` + `ProgressTracker` + `TodoStatus` (~170 lines) |
| `example.py` | Refactor scenario reproducing the lecture-opening incident |
| `test_pattern.py` | 14 invariants: stable id, single-in-progress, render rules, all_done, auto-evict, context-loss detection, escalating nudges, per-owner isolation |

## Engineering references (verified)

* **Claude Code** `TodoWrite` tool — three fields `content`,
  `activeForm`, `status`. The "if you started a todo system, finish
  the task and clear it" guidance is built into the prompt
* **DeepAgents** `TodoListMiddleware` — the first middleware in the
  default stack of `create_deep_agent`, lives at
  [`libs/deepagents/deepagents/middleware/`](https://github.com/langchain-ai/deepagents)
* **DeerFlow** `TodoMiddleware` — adds **context-loss detection** with
  recent-message complexity scoring + escalating nudges; the inspiration
  for `context_loss_detected()` here
* **Codex CLI** `update_plan` tool — the same idea in a single-list form
* **Anthropic Effective Context Engineering** — the U-shaped attention
  observation that motivates the pattern

## When this pattern doesn't apply

* **Short tasks.** 3-step tasks don't need TodoWrite. Overhead exceeds
  benefit.
* **Pure conversation.** No tools, no multi-step plan — todos are noise.
* **Single Q&A.** One question, one answer — definitely don't.

Claude Code's own prompt lists 4 don't-use-it cases. Forcing the
pattern where it doesn't belong is over-engineering, not discipline.
