<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>C1</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>C1 · Hierarchical Delegation</h1>
<p class="publication-deck">A supervisor delegates bounded tasks and authority to workers, then verifies and integrates their artifacts against a shared contract.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Collaboration × Hierarchy (split)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">High (multiple worker calls plus coordination and synthesis)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Collaboration patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">A supervisor delegates bounded tasks and authority to workers, then verifies and integrates their artifacts against a shared contract.</td>
</tr>
</tbody>
</table>

---

## Problem

A single agent may need to research, draft, generate figures, and assemble a report while carrying every intermediate trace in one context. As the workflow grows, earlier tool output and local decisions compete with the current coordination state.

Hierarchical Delegation gives one supervisor responsibility for decomposition, assignment, progress, and synthesis. Workers receive bounded task contracts and return typed artifacts from isolated contexts. The additional calls and coordination are justified only when evaluation shows better quality, latency, isolation, or capability coverage than a simpler design.

## Classification: Collaboration × Hierarchy

- **Vertical axis · Collaboration**: Several agent roles contribute distinct artifacts to one outcome under explicit contracts.
- **Horizontal axis · Hierarchy**: A supervisor owns assignment and synthesis. Worker-to-worker dependencies either return through the supervisor or use another explicitly modelled topology.

## Solution and mechanics

A single hierarchical delegation consists of three stages:

1. **Task decomposition**: The supervisor creates bounded work units from the goal, dependencies, available capabilities, and conflict domains. The decomposition may be fixed for stable workflows or generated within evaluated limits.
2. **Isolated execution**: Each worker runs in an isolated context, does not inherit the supervisor's history, and receives only its own system prompt, its specific task instruction, and its own tool set. Workers run in parallel wherever they can.
3. **Centralized synthesis**: The supervisor consumes structured artifacts and evidence links. Full worker traces remain retrievable for review without occupying the coordination context.

Supervisor and worker models can be selected independently. Evaluate the supervisor on decomposition, assignment, and synthesis, and evaluate workers on their bounded tasks. Different roles may justify different models, budgets, tools, and context limits; the topology itself does not require a particular capability or price tier.

The artifact a worker returns should have at least a three-field structure:

<table>
<thead>
<tr>
<th style="text-align: left;">Field</th>
<th style="text-align: left;">Purpose</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">verdict (success / partial / failure)</td>
<td style="text-align: left;">States whether the artifact is complete, partial, or failed</td>
</tr>
<tr>
<td style="text-align: left;">ranked findings</td>
<td style="text-align: left;">Conclusions ordered by importance, with evidence references</td>
</tr>
<tr>
<td style="text-align: left;">confidence / uncertainty</td>
<td style="text-align: left;">A calibrated expression of uncertainty, not a standalone arbitration rule</td>
</tr>
</tbody>
</table>

## Applicability

- **Long workflows with separable responsibilities**: Research, analysis, drafting, and verification may need different tools, evidence, permissions, or context boundaries.
- **Isolated processing of similar items**: contract review, resume screening, and document compliance scanning can assign each item to a worker with its own bounded context and result schema.
- **Tasks valuable enough to cover the collaboration overhead**: Compare a single-agent baseline with the delegated version on the same task set, including quality, latency, total tokens, and review effort.

## Known failure modes

- **Delegation without isolation**: when the supervisor receives every worker trace, intermediate details accumulate and reduce the context available for coordination. Workers should return schema-defined artifacts with evidence links; full traces remain addressable outside the supervisor prompt.
- **Undeclared worker dependencies**: Worker A calls worker B outside the supervisor's plan, so authority, retries, and failure propagation disappear from the coordination trace. Route the dependency through the supervisor or model it explicitly.
- **No boundary on worker failure**: a worker throws an uncaught exception, the supervisor receives a raw exception rather than a failure artifact, and the whole task is interrupted. Each worker needs a timeout plus exception wrapping.
- **Too many parallel workers**: As worker count grows, the supervisor may struggle to compare and synthesize the returned artifacts. Set the concurrency and fan-out limit from provider capacity, artifact size, and measured synthesis quality.
- **Delegation without an isolation or capability benefit**: Splitting one prompt into several roles may add cost without changing tools, evidence, permissions, or context. Compare with one agent and a structured prompt chain.

## Verification and metrics

- **Coordination overhead ratio**: Measure the tokens and wall-clock time spent on supervisor-worker communication. If it dominates useful work, compress artifacts, reduce round trips, or use a lighter coordination channel.
- **Worker failure cascade rate**: Measure whether one worker failure interrupts unrelated branches or the supervisor. High-risk workflows should test isolation and partial-failure handling explicitly.
- **Artifact compliance rate**: Track whether worker returns conform to the schema. Free text that bypasses the contract creates redispatch, manual correction, and additional latency.
- **Multi-agent cost ratio**: Compare total tokens, model spend, and wall-clock time with the single-agent baseline. Fall back to a smaller delegation scope when the added value does not justify the overhead.

## Reference implementation

```
SupervisorAgent.execute(task):
                plan = decompose(task)              # dynamic split, tied to the input
                artifacts = parallel gather(        # concurrency cap is configuration
                    IsolatedSubAgent(worker).execute(subtask)
                    for worker, subtask in plan
                )
                return synthesize(task, artifacts)  # look only at artifacts, not raw trajectory

            IsolatedSubAgent.execute(subtask):
                local messages = [system_prompt, subtask]   # do not inherit parent history
                try: raw = wait_for(llm(messages, tools), timeout)  # failure boundary
                except: return Artifact(verdict="failure", ...)
                return reduce_to_artifact(raw)      # force reduce to verdict/findings/confidence
```

Start each worker from the contracted context, require a schema artifact, wrap timeouts and failures into typed results, and cap concurrency. Shared mutable state requires explicit ownership and conflict control.

## Illustrative scenario

Consider a law-firm contract review agent. A first version lets every sub-agent return its full analysis, quickly filling the supervisor's context with detail. A stronger version assigns each contract to an isolated worker and requires a fixed-schema artifact containing `contract_id`, `risk_level`, `top_concerns`, `recommendation`, and a tamper-evident `contract_hash`. High-risk contracts enter a lawyer-review queue, timed-out workers return a failure artifact, and the portfolio report is retained for audit. Actual throughput and review quality must be evaluated on an authorized contract set.

## Related patterns

- **Sub-Agent Isolation (C5)**: C1 defines assignment and reporting; C5 defines the worker's context, permissions, runtime, failure boundary, and returned artifact. Use them together when delegated work must not expose its full trace or authority to the supervisor.
- **Fan-Out/Gather (C2)**: C2 distributes independent work units for parallel completion. C1 adds a hierarchical assignment and reporting relationship and may include different worker capabilities.
- **Handoff Chain (C4)**: C1 keeps a supervisor responsible for the whole task. C4 transfers responsibility and state from one participant to the next.
- **Plan-and-Execute (A2)**: A2 schedules a dependency graph. C1 can supply workers for selected plan nodes while the orchestrator retains task ownership.

## Design conclusion

Hierarchical delegation divides both work and information scope. The supervisor receives structured conclusions from the layer below instead of inheriting every worker's raw trajectory, keeping synthesis and responsibility boundaries manageable.

## Workshop revision, 25 August 2026: Task identities and production pinning

Delegation narrows task, context, and authority together. Workers use task identities or short-lived credentials rather than inheriting a principal's full access. Supervisor, worker, model, tool, and policy versions are progressively pinned toward production.

[Collaboration workshop record](https://adpsagent.com/workshops/collaboration-2026-08-25/)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>C1 Hierarchical Delegation</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-c1-hierarchical-delegation">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
