# c · Prompt Chaining

> Column lecture **05-04** · pattern · act × chain
>
> [中文 README](README.zh-CN.md)

## The problem

A content-editing agent for a financial news outlet. The first
version did seven things in one prompt: proofread typos, rewrite for
clarity, apply house style, fact-check numbers, generate a title,
write a summary, suggest images. One prompt, one model call.

A week in, a piece went live. The original draft said "GMV grew 35%."
The agent published "GMV grew 53%." Both 3 and 5 were in the source;
the agent saw them — but by step 4 (fact-check) it was no longer
*looking at* the source, it was looking at its own step-2 rewrite,
and the rewrite had transposed the digits.

The fix wasn't a smarter prompt. It was splitting the seven things
into seven independent steps, each with its own model (`Haiku` for
proofread, `Sonnet` for rewrite, `Opus` with thinking for fact-check),
and a cheap programmatic *gate* between consecutive steps that
checked the obvious — numbers preserved, length in range, required
fields present. Crucially, **the fact-check step explicitly reads
the original draft, not the rewritten version.** Numbers-correct
accuracy went from 87% to 99.4%. Editor trust 42% → 91%. Cost +30%,
latency 12s → 38s. Worth it.

The general claim: **prompt chaining is Unix pipes ported to LLMs.**
Each step does one thing. Cheap gates between steps. Pick the right
model per step. Recover from one step's mistake before it poisons
the next.

## The pattern

Two classes plus a small library of gate factories:

| Construct | Role |
|---|---|
| `ChainStep` | One prompt step. Carries `system_prompt`, `prompt_template`, `model`, a `gate` callable, and `max_retries`. The template is interpolated with the user input + every prior step's output, keyed by `step_id`. |
| `PromptChain` | Runs steps in order. Passes outputs forward, retries on gate failure (bounded), records every attempt in a `ChainTrace`. |
| `length_gate`, `keys_gate`, `regex_gate`, `any_gate`, `all_gate` | Cheap gate factories. **Gates are programmatic checks, not LLM calls.** A gate that calls an LLM is just another step. |

Two named failure modes from the lecture, each addressed by the
pattern:

| Failure mode | What it is | What addresses it |
|---|---|---|
| **Information starvation** | Step 3 needs data Step 1 produced, but Step 2 dropped it on the floor. | Every step sees *every* prior output by id, not just the immediately previous one. Reference them by name in the template. |
| **Gate tyranny** | Gate set too strictly ("exactly 500 words") rejects 499 and 501 forever. | `max_retries` is the hard cap. Failed-gate retries log the exact gate description so the operator can loosen it. |

Three behaviors worth knowing:

1. **Gates retry; LLM errors don't.** A gate-failed output triggers
   re-prompt up to `max_retries`. A raised LLM exception fails the
   step immediately. Different exceptions, different response.
2. **Missing template keys don't crash.** A `{nonexistent}` in the
   template gets replaced with a `[chain: missing template key: …]`
   marker. The chain runs to completion; the marker shows up in the
   trace so a debug pass can find the broken wiring. The contract:
   surface, don't hide.
3. **Step ids are stable.** They appear as keys in `prior_outputs`,
   as references in templates, and as audit handles in the trace.
   Renaming an id is a chain-breaking change.

## Quickstart

```bash
python action/c-prompt-chaining/example.py
pytest action/c-prompt-chaining/
```

The demo runs the five-step editing pipeline: proofread → rewrite →
style → fact-check → title. The fact-check step explicitly references
both the original `user_input` and the most-recent `style` output,
so the lecture-opening bug (the rewrite mutating the source) cannot
occur — the fact-checker always has the original draft.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `StepResult` + `ChainStep` + `StepRun` + `ChainTrace` + `PromptChain` + 5 gate factories (~200 lines) |
| `example.py` | Five-step content-editing pipeline reproducing the lecture-opening incident's fix |
| `test_pattern.py` | 15 invariants: each gate factory, chain construction guards (empty / duplicate ids), happy path, prior-output access by id, retry-on-gate-failure with cap, success-on-retry, fail-fast on LLM errors, missing-template-key fallback, trace bookkeeping |

## Engineering references (verified)

* **Aider** [`aider/history.py`](https://github.com/Aider-AI/aider/blob/main/aider/history.py)
  — the recursive-summary chain in 49 lines. `depth=0` is the hard
  recursion cap (no infinite chains), the inner `summarize_all` has
  its own fallback-model chain, and partial summaries are *errors,
  not return values*. The minimum form of this pattern.
* **Claude Code** PRA loop — every Read / Grep / Edit / Bash result
  is the next reasoning step's input. The loop is an implicit
  prompt chain; making it explicit (with gates) is what this pattern
  does. Slash commands like `/commit` and `/review` are pre-built
  chains in disguise.
* **Claude Code Skills** — declarative chain segments. A `SKILL.md`
  in `.claude/skills/` is a chain that the model composes on demand.
  Same pattern, different surface.
* **Anthropic** [*Building Effective
  Agents*](https://www.anthropic.com/research/building-effective-agents)
  — prompt chaining listed as the simplest and most under-used agent
  pattern. The reference shape is "small number of well-defined
  steps with gates between them."
* **Anthropic** [*Prompt engineering
  best practices*](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
  — each step's prompt as five-part XML structure (role / task /
  context / format / constraints). Measured 8–15% reliability lift
  on chains vs unwrapped paragraphs.
* **Anthropic** self-check block recommendation — append "before
  answering, check X / Y / Z" to each step's prompt. Costs 200–500
  tokens per step, catches most "small errors propagating down
  the chain." The pattern's gate is the *out-of-band* version of
  this trick (Python `if`, not LLM self-check); both are useful.
* **Doug McIlroy** — "Do one thing and do it well." The Unix pipe
  philosophy this pattern ports to LLMs.

## When this pattern doesn't apply

* **One-shot tasks.** "Translate this sentence." One step, no gate
  needed.
* **DAG-shaped work.** If the dependencies are a graph, not a line,
  use [Plan-and-Execute](../b-plan-and-execute/) instead.
* **Hard-real-time loops.** Each step is a round-trip to a model
  provider; five steps means five RTTs. The pipeline can't fit a
  300ms budget. Single-step or batched-by-the-model only.

In production most chains end up at 3–5 steps. More than 5 and the
work is usually a DAG in disguise — promote to Plan-and-Execute. Fewer
than 3 and the chain plumbing is overhead — collapse to one step.

## Honest limitations

The reference is synchronous. Production deployments fan out
independent prior outputs in parallel (e.g. when step 3 depends on
step 1 but step 2 is unrelated). The chain class here doesn't have
DAG semantics; if you need them, that's [Plan-and-Execute](../b-plan-and-execute/).
Promote, don't squeeze.

The default missing-template-key behavior — leaving a marker in the
prompt — is deliberate but unusual. Code review will sometimes ask
to make it raise instead. Both shapes are defensible; this reference
picks the "stay alive, surface the problem in the trace" form
because content-editing pipelines tend to have one-off template
typos that shouldn't kill the whole batch. For payment / medical
chains, override the renderer to raise.

The retry semantics for gate failures are simple — re-prompt with
the same template. Real chains often want to *include the gate's
description in the retry prompt* so the model knows what it failed.
The hook is there (gates have `__name__` set by the factory); the
template rendering doesn't wire it through by default. That's a
two-line change in `_run_step` if you need it.
