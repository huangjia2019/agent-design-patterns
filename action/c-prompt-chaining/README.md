# c · Prompt Chaining

> Column lecture **05-04** · pattern · act × chain
>
> [中文 README](README.zh-CN.md)

## The problem

The Payroll Lab splits settlement, reconciliation, instruction
generation, and payment-request drafting into four fixed steps. A
deterministic mock model transposes two digits in the payroll total.
A checksum gate rejects the artifact; a non-empty gate lets the
270,000-yuan discrepancy reach the final request.

The experiment demonstrates propagation mechanics, not a fixed model
accuracy rate. `PromptChain` is a central linear runtime: it owns
ordering, retries, and tracing. Unlike Plan-and-Execute, it has no
global DAG or model-directed path selection.

## The pattern

Two classes plus a small library of gate factories:

| Construct | Role |
|---|---|
| `ChainStep` | One prompt step. Carries `system_prompt`, `prompt_template`, `model`, a `gate` callable, and `max_retries`. The template is interpolated with the user input + every prior step's output, keyed by `step_id`. |
| `PromptChain` | Runs steps in order. Passes outputs forward, retries on gate failure (bounded), records every attempt in a `ChainTrace`. |
| `length_gate`, `keys_gate`, `regex_gate`, `any_gate`, `all_gate` | Cheap programmatic gate factories. Semantic evaluation can be a separate evaluator step while deterministic schema, provenance, and budget checks remain outside it. |

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
2. **Broken template wiring fails closed.** Missing keys and
   `static_args` that shadow `user_input` or prior artifact ids stop
   the chain before the model is called.
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
| `test_pattern.py` | 16 invariants: gate factories, construction guards, prior-output access, bounded retries, fail-fast provider errors, fail-closed template wiring and artifact shadowing, and trace bookkeeping |

## Engineering references (verified)

* **Aider** [`aider/history.py`](https://github.com/Aider-AI/aider/blob/main/aider/history.py)
  — `ChatSummary.summarize_real()` recursively compresses history
  when a summary plus tail remains over budget, with an explicit
  depth bound.
* **Claude Code Skills** — reusable prompt and workflow packages. A
  skill may contain a fixed chain, tool calls, subagents, or a loop;
  the file format does not determine the runtime topology.
* **Anthropic** [*Building Effective
  Agents*](https://www.anthropic.com/research/building-effective-agents)
  — prompt chaining listed as the simplest and most under-used agent
  pattern. The reference shape is "small number of well-defined
  steps with gates between them."
* **Anthropic** [*Prompt engineering
  best practices*](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
  — separate instructions, context, and output format clearly.
  Measure the effect on your own dataset rather than assuming a
  universal improvement percentage.
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

Missing template keys and artifact-name collisions fail closed.
Debug tooling may still record the configuration error in the trace,
but the incomplete prompt is never sent to the model.

The retry semantics for gate failures are simple — re-prompt with
the same template. Real chains often want to *include the gate's
description in the retry prompt* so the model knows what it failed.
The hook is there (gates have `__name__` set by the factory); the
template rendering doesn't wire it through by default. That's a
two-line change in `_run_step` if you need it.
