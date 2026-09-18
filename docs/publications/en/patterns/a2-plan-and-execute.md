<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>A2</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>A2 · Plan-and-Execute</h1>
<p class="publication-deck">Represent a long task as a versioned dependency plan, execute ready steps, and replan affected future work when assumptions change.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Action × Orchestrate (coordination)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (plan once, execute many times; heterogeneous models can cut cost substantially)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Action patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Represent a long task as a versioned dependency plan, execute ready steps, and replan affected future work when assumptions change.</td>
</tr>
</tbody>
</table>

---

## Problem

In a long process, a purely reactive agent can lose the global sequence. An HR recruiting agent may send compensation information after rejection, skip a required background check, or query the same record repeatedly when each step is chosen only from the latest observation.

Plan-and-Execute represents the task as a versioned plan before execution. The plan records dependencies, expected artifacts, resources, approval nodes, and acceptance conditions. A scheduler advances ready steps, writes checkpoints, and replans affected future work when assumptions change.

## Classification: Action × Orchestrate

- **Vertical axis · Action**: The pattern turns a goal into a controlled sequence of external actions and verifies progress against a plan.
- **Horizontal axis · Orchestrate**: One orchestrator owns the dependency graph, schedules ready steps, maintains checkpoints, and revises affected future nodes. Prompt Chaining (A3) passes artifacts through a fixed linear sequence instead.

## Solution and mechanics

Plan-and-Execute depends on separation, approval, and context reset. Aider's architect mode is a compact product example: the architect produces a plan, the editor starts from that artifact, and user confirmation can sit between planning and execution.

Three implementation choices shape the runtime:

- **Independent model selection**: Evaluate planning and execution responsibilities separately. They may use different models, tools, or effort levels when the task evidence supports that choice.
- **The plan is a user-owned artifact**: Claude Code writes the plan to a file instead of keeping it only in the prompt. People and agents can review, version, and diff the same artifact. It becomes part of the audit trail when approvals, revisions, and execution references point back to that version.
- **Local replanning**: When reality conflicts with the plan, change only affected future nodes and preserve committed work. Set review frequency and replan budget from task length, external volatility, and replay results.

ReWOO illustrates a related optimization: plan variable dependencies first, execute intermediate tool calls without returning to the model for every step, then synthesize the result. Its published results are research evidence for that benchmark, not a universal production ratio.

## Applicability

- **Goals with enumerable dependencies and consequential actions**: HR recruiting, credit workflows, and operations changes benefit from explicit order, approval, and recovery state.
- **Compliance scenarios with hard process constraints**: for example, "the background check must come before the offer." Such constraints can be encoded into a plan validator that rejects a violating plan during the planning phase.
- **Long tasks that need crash recovery**: write a checkpoint at each step, resume from the checkpoint after a crash, and design plan-execute as a recoverable transaction.

## Known failure modes

- **Plan ossification**: A withdrawal, schema change, or API change invalidates future steps, but execution continues. Revalidate assumptions at defined milestones and before high-risk actions.
- **Plan thrashing**: Every local failure rewrites the plan. Limit replans, preserve unaffected completed work, and distinguish retryable execution faults from invalid plan assumptions.
- **Stale or inconsistent task state**: free-form notes may retain obsolete assumptions while still looking plausible. Use typed state, version references, and validation at step boundaries so incompatible updates fail before execution.
- **Cache friendliness ignored**: Rewriting stable prefixes at every step prevents cache reuse. Keep system instructions, tool definitions, and plan prefixes stable where semantics allow, while refreshing external state separately.

## Verification and metrics

- **Long-task success rate / error rate**: Compare with a reactive baseline and classify errors as planning, execution, or external-state failures.
- **LLM calls per task**: Track the distribution by task complexity. Unexpected growth often points to repeated replanning or retries.
- **Replan frequency**: High frequency may indicate thrashing; no replans may indicate ignored environmental change. Inspect the reasons, not only the count.
- **Cache hit rate**: Observe reuse of stable prefixes together with stale-state incidents so that cache efficiency does not hide outdated context.

## Reference implementation

```
plan = planner(goal, context)            # model selected from planning evaluation
            if user does not approve → return
            while plan is not complete:
                ready = steps in plan whose dependencies are satisfied   # topological order
                execute ready in parallel:
                    success → mark completed, write checkpoint
                    failure → replan (bounded by MAX_REPLANS)
                every N steps → adaptive replan check whether the plan still holds
            return plan + full execution trace
```

Keep Planner, Executor, and Approval behind explicit interfaces. Version the plan, register compensation where a side effect is reversible, and retain receipts for irreversible actions.

## Illustrative scenario

Bo Liang's team explicitly separates strategic planning from tactical execution. The planning layer writes a DAG into the Workspace, and a deterministic scheduler advances by dependency rather than asking the LLM to rediscover the overall path at every step. In an HR workflow, Planner creates the dependency graph, Executor handles only the current node, and changes to screening criteria or candidate status pass through an Approval Gate. Cost, cycle time, and error outcomes should be published only with the named team's approved measurement.

## Related patterns

- **Prompt Chaining (A3)**: A3 executes a fixed linear sequence. A2 owns a dependency graph and recovery state; one A2 step may contain an A3 chain.
- **Tool Dispatch (A1)**: An executable plan step may invoke A1 to select and admit a tool call.
- **Guardrail Sandwich (A4)**: Approval and policy nodes in the plan can invoke A4 checks around the corresponding action.
- **Iterative Hypothesis Testing (R4)**: R4 revises hypotheses from evidence. A2 replans future actions when evidence invalidates a plan assumption.

## Design conclusion

Plan-and-Execute makes dependencies, approvals, checkpoints, and recovery explicit. Its value can be measured through plan omissions, repeated side effects, replan causes, recovery success, and acceptance evidence.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>A2 Plan and Execute</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-a2-plan-and-execute">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
