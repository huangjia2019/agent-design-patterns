# b · Plan-and-Execute

> Column lecture **05-03** · pattern · act × orchestrate
>
> [中文 README](README.zh-CN.md)

## The problem

An HR recruiting agent for a mid-size internet company. End-to-end:
JD parsing, candidate sourcing, scoring, scheduling, interviewing,
offer generation, background check, sending the offer. The v1 wired
17 tools to the LLM and let it figure out which to call.

After the first month finance flagged the LLM bill: **¥180k**. Then
HR sent the actual complaints:

* "The agent emailed the hiring manager the *salary band* before the
  candidate had even interviewed. That's privileged data."
* "The agent **skipped background check** and went straight to
  `send_offer`. Twice."
* "It queried `query_salary_band` fifty times in one day because each
  reasoning step forgot what it had just looked up."

Root cause: the agent was running ReAct-style. Every step was
reactive. There was no plan, just a 200K context full of intermediate
tool results and the model deciding "what next?" each time. Context
windows don't hold twelve-step pipelines well — it kept making the
local decision and missing the global structure.

v2 split the work into three roles, gave each its own model tier,
made the plan a file the user could sign:

```
1. Planner   → produces 12-step DAG (high-tier model)
2. HR review → edits + approves the plan, gets back a token
3. Executor  → walks the DAG, blocks on [HUMAN] markers, fails locally
```

Result: error rate 8.3% → 0.4%, model calls 47 → 13 per candidate,
bill ¥180k → ¥60k. Recruiting cycle 23 days → 16 days.

The lecture's general claim: **plan-and-execute is the engineering
floor under any long-horizon agent.** Below five steps you can wing
it. Above five steps the plan needs to be a typed, durable, signable
artifact, and the executor needs to fail one step at a time, not the
whole run.

## The pattern

Three classes plus four functions:

| Construct | Role |
|---|---|
| `PlanStep` | One node in the DAG. Has `deps`, `handler` name, `args`, `requires_human`, plus runtime status / output / error. |
| `Plan` | The DAG. Knows how to validate (no cycles, every dep references a real step), report `ready_steps()`, check `is_complete()`. |
| `Executor` | Walks the DAG. Looks handlers up by name in a registry, runs them with `prior_outputs` already wired in, cascades skip on failure. |
| `approve` | User-side flip to mark the plan executable. The token is the audit handle. |
| `release_blocked` | One-shot human gate flip on a step. Clears `requires_human` so the next run goes through. |
| `replan_local` | Re-runs the Planner, validates the merged plan, caps how many new steps the patch can add. Anthropic's guidance: replan budget < 10% of plan budget. |

Three behavioral guarantees:

1. **Plan is approved before any step runs.** `Executor.run` on an
   unapproved plan raises `PlanError`. There is no "skip the gate
   just this once."
2. **Step status is the source of truth.** `TODO` / `DOING` / `DONE`
   / `BLOCKED` / `FAILED` / `SKIPPED`. The state machine never goes
   backwards except via `release_blocked` (BLOCKED → TODO) or
   `replan_local` (FAILED/SKIPPED → TODO).
3. **Failure is local.** A failed step cascades `SKIPPED` to its
   transitive descendants and returns — it does not abort the whole
   plan. Sibling subgraphs keep their results. Replan only re-plans
   the affected subtree.

## Quickstart

```bash
python action/b-plan-and-execute/example.py
pytest action/b-plan-and-execute/
```

The demo runs a nine-step recruiting DAG. Three sourcing steps run in
parallel (no dependencies between them). The interview step is
`requires_human=True` and blocks until `release_blocked` is called.
`send_offer` depends on `assemble_offer` which depends on both
`background_check` and `query_salary_band` — the DAG enforces that
no offer can be assembled or sent without the background check
completing.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `StepStatus` + `PlanStep` + `Plan` + `Executor` + `PlanError` + `approve` + `release_blocked` + `replan_local` (~240 lines) |
| `example.py` | Recruiting-agent scenario with parallel sourcing + human interview gate + DAG-enforced background check |
| `test_pattern.py` | 20 invariants: cycle detection, unknown-dep rejection, ready-step set, approval gate, parallel execution, handler sees prior outputs, human block + release one-shot, failure cascade, unknown handler = failed, replan within cap / above cap, completion checks |

## Engineering references (verified)

* **Aider** [`aider/coders/architect_coder.py`](https://github.com/Aider-AI/aider/blob/main/aider/coders/architect_coder.py)
  — the minimal-viable form. 49 lines, of which 9 are the architect /
  editor split: heterogeneous models per role, context reset between
  roles, user approval before execution. Most production deployments
  are this skeleton with more knobs.
* **Claude Code** ExitPlanMode tool — the *plan-as-file* discipline.
  The plan is written to a file by the agent; the tool signals
  "ready for review" without transmitting the plan content (it's
  already on disk). Same principle as the `approve(plan, token)` call
  here: the plan is a durable artifact, not a transient string.
* **LangGraph 1.0** — the production runtime. BSP / Pregel with
  SQLite checkpointing; 90M monthly downloads. The reference here is
  a synchronous in-memory cousin with the same contract (steps have
  status, deps gate execution, replan is local).
* **Manus** — Yichao "Peak" Ji's *Context Engineering for AI Agents*.
  The `todo.md` rewriting pattern: keep the plan at the tail of
  context so the model's recent-attention window covers it. Cache
  hit rate is the single most important production metric.
* **Anthropic (2026)** [*How we built our multi-agent research
  system*](https://www.anthropic.com/research/multi-agent-research)
  — Adaptive Replanning. Check every N steps whether the plan still
  holds; cap the replan budget at <10% of the total plan budget;
  prefer JSON-structured checkpoints over Markdown for long tasks.
* **AWS** [prescriptive guidance on Saga pattern for agents](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)
  — plan-and-execute combined with the saga inverse from
  [Tool Dispatch](../a-tool-dispatch/): destructive steps record
  rollback handlers; partial-run failures trigger reverse saga, not
  silent state corruption.

## When this pattern doesn't apply

* **Short tasks (<5 steps).** Just run them. The DAG plumbing is
  overhead.
* **Exploratory work.** If the agent doesn't know how many steps it
  needs, planning up-front is fantasy. Use
  [Iterative Hypothesis Testing](../../reasoning/d-iterative-hypothesis/)
  instead.
* **Conversational agents where the user steers each turn.** The
  plan is the user's mental model; an explicit DAG fights it.

The pattern's value is concentrated where *goals are clear*, *steps
are enumerable*, and *side effects matter*. Drop any one of the
three and you're over-engineering.

## Honest limitations

The DAG runtime here is single-threaded. Real LangGraph deployments
fan out independent branches across asyncio coroutines. Production
parallelism matters for the recruiting case (three sourcing queries
should run concurrently). The data model already supports it — the
`Executor` just iterates serially; swap it for an `asyncio.gather`
across `ready_steps()` and the contract is unchanged.

The replan currently does not preserve the *user's* edits to the
plan. If HR edited step 5 in their review and step 5 later failed,
`replan_local` invokes the Planner on the original goal and may
regenerate step 5 in a form HR didn't approve. Production needs a
notion of "user-edited steps survive replan" or "edited steps are
locked." The contract is the same; the policy is what changes.

`requires_human` is one-shot. Once flipped, it stays off. That's
correct for an interview-scheduling step (the user approved this
specific candidate). It's wrong for a per-run governance gate
("approve every send_offer call"). Use a separate Approval Gate
pattern (Ch9) for the latter.
