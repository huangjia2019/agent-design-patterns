<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>A3</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>A3 · Prompt Chaining</h1>
<p class="publication-deck">Decompose a workflow into ordered model or tool steps with explicit input, output, and acceptance contracts. Each artifact is validated before the next step consumes it.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Action × Chain (relay)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (split into N segments, N calls, but each segment can use a cheaper model to amortize)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Action patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern summary</strong></td>
<td style="text-align: left;">Decompose a workflow into ordered model or tool steps with explicit input, output, and acceptance contracts. Each artifact is validated before the next step consumes it.</td>
</tr>
</tbody>
</table>

---

## Problem

A single prompt that handles proofreading, rewriting, style, number checking, headlines, summaries, and image suggestions makes several constraints compete for attention. A rewrite step may alter a figure from the source, and later steps then propagate the error.

Prompt Chaining separates a workflow into model or tool steps that run in sequence. Each step has a bounded responsibility, an input and output schema, a model or tool selected from step-level evaluation, and an acceptance condition. The structure makes intermediate failures visible and allows a failed step to be retried without rerunning completed work.

## Classification: Action × Chain

- **Vertical axis · Action**: The pattern turns a task into an executable sequence of model and tool steps. Each step produces an artifact that the next step can validate and consume.
- **Horizontal axis · Chain**: Each step consumes the previous step's accepted artifact in a fixed order. If the workflow needs branching dependencies or replanning, use an orchestrated plan instead.

## Solution and mechanics

The Unix pipe provides a useful precedent: `cat data.csv | grep ERROR | sort | uniq -c` connects programs through explicit input and output. A prompt chain applies the same compositional idea to model and tool steps, but each boundary also needs a schema, acceptance check, and trace.

The extra layer beyond the Unix pipe is the gate. A programmatic check sits between stages and retries or escalates on failure. In a research chain, for example, the gate can validate topic coverage, source type, and traceability against project policy before allowing the next stage to run.

Each step needs the following controls:

- **Each prompt segment uses an explicit contract**: role, task, context, format, and constraints can be represented with structured tags so the next step can validate the output.
- **Each segment selects its model independently**: Proofreading, creative rewriting, and number checking may use different models and tools. Choose each model from step-level evaluation and calculate the whole-chain cost from replay.
- **Gates need tolerance**: do not require an exact word count when the business accepts a range. Express content requirements separately from length tolerance.
- **Retries should include failure evidence**: pass the failed assertion, rejected field, or tool error into the next attempt. Measure the pass rate by failure class instead of assuming that additional context improves it.

Agent-coding tools expose the same structure in several forms. A tool result feeds the next model call; a command can package a fixed sequence such as status → diff → review → draft → commit; and a skill can define a reusable multi-step segment inside a larger workflow.

## Applicability

- **The workflow has clear stages, and acceptance between stages can be expressed with deterministic checks or a concise rubric**: content editing, contract review, and customer-ticket triage.
- **Reusable workflow entry points**: A command or API can invoke a versioned chain without requiring the caller to reconstruct each step.
- **Output that needs to be traceable**: A full-chain trace lets reviewers move backward from the final draft through each input, output, gate result, and human change.

## Known failure modes

- **Missing downstream evidence**: An intermediate artifact omits a source or field required later. Define cumulative evidence separately from the transformed artifact and reference it by version.
- **Brittle gates**: Exact-value checks can reject usable results indefinitely. Encode required conditions and business tolerances separately.
- **Unmeasured chain reliability**: Each additional step and gate introduces another failure path. Measure step and full-chain success on the same replay set and remove links that add no decision value.
- **Assembly of the first prompt is overlooked**: a production system prompt is usually assembled from several data sources—base instructions, user identity, history, current task, tool list, style, format constraints—and hardcoding it into one long string makes the most frequently updated part impossible to maintain independently.

## Verification and metrics

- **Full-chain success rate**: Failure at any gate counts as a chain failure. Inspect whether failures concentrate in model output, data transfer, or gate rules.
- **Per-step latency distribution**: Compare the median and tail for each step to locate a slow model, tool, or external dependency.
- **Gate retry distribution**: A sudden increase at one step calls for inspection of input drift, model changes, and gate criteria.

## Reference implementation

```
chain = [step1, step2, step3]        # each step carries its own system_prompt + model + gate
            current = initial_input
            for step in chain:
                for attempt in range(max_retry + 1):
                    result = step.run(current)   # call the corresponding model
                    if result passes the gate:
                        current = result.output
                        break
                    elif retries remain:
                        current += "[did not meet standard: reason. retry]"   # feed back the failure reason
                    else:
                        return failure(step, trace)
            return success(current, total_tokens, trace)
```

Store gate tolerances in the contract and emit structured token, latency, retry, and artifact-version events. A step that verifies source facts should read the original source or an authoritative system, not a transformed upstream draft.

## Illustrative scenario

Consider a financial-media editing agent that separates proofreading, rewriting, style normalization, number checking, headline generation, summarization, and image suggestions. Number checking returns to the original draft or an authoritative data source rather than trusting the rewritten text. Each step has its own schema, model choice, and gate, and the trace records where a figure was read, checked, or changed. The same structure can support contract review, medical assistance, or customer-service triage, but each domain needs its own gates.

## Related patterns

- **Plan-and-Execute (A2)**: Use A3 for a fixed linear flow and A2 for a dependency graph with scheduling, checkpoints, and replanning. An A2 step may contain an A3 chain.
- **Tool Dispatch (A1)**: A chain step may invoke A1 to select and admit a tool call.
- **Guardrail Sandwich (A4)**: A chain gate validates an artifact between steps. A4 applies policy checks and result validation around a tool action.

## Design conclusion

An explicit prompt chain gives each step a contract, model or tool assignment, gate, and trace. That structure supports step-level replay and failure localization; a free-form multi-turn exchange does not provide those guarantees by itself.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>A3 Prompt Chaining</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-a3-prompt-chaining">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
