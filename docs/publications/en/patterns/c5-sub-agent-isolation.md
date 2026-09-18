<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>C5</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>C5 · Sub-Agent Isolation</h1>
<p class="publication-deck">Run each delegated worker within bounded context, tools, credentials, budget, and workspace, then return a schema-valid artifact with evidence links and failure state.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Collaboration × Hierarchy</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Cross-cutting (a cross-cutting concern layered on top of other collaboration patterns)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Collaboration patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern summary</strong></td>
<td style="text-align: left;">Run each delegated worker within bounded context, tools, credentials, budget, and workspace, then return a schema-valid artifact with evidence links and failure state.</td>
</tr>
</tbody>
</table>

---

## Problem

If every worker returns its complete trace, supervisor context grows with each item and leaves less capacity for comparison and synthesis. Most coordination steps need a verdict, findings, evidence links, unresolved questions, and failure state.

Sub-Agent Isolation bounds each worker's context, tools, credentials, budget, workspace, and failure propagation. The worker returns a schema-valid artifact while its full trace remains separately addressable for review.

## Classification: Collaboration × Hierarchy

- **Vertical axis · Collaboration**: Sub-Agent Isolation adds context and permission boundaries to delegated work. The supervisor sends a task contract and receives a bounded artifact instead of the worker's full trace.
- **Horizontal axis · Hierarchy**: A parent assigns a bounded task and consumes the returned artifact. C1 defines assignment and reporting; C5 defines the worker boundary.

## Solution and mechanics

The worker boundary covers four areas:

1. **Context isolation**: When the sub-agent starts, it does not inherit the parent's history; it receives only its own system prompt, the specific task instruction, and its own tool set. It cannot see what the supervisor has run or what other sub-agents are doing.
2. **Schema-valid artifact return**: The sub-agent returns a Pydantic or JSON Schema artifact containing verdict, ranked findings, citations, and unresolved questions. The supervisor validates it without inferring state from free text.
3. **Failure boundary isolation**: When a sub-agent times out or throws an exception, the supervisor receives an artifact with `verdict=failure` rather than an unhandled exception. A local failure remains attached to its branch.
4. **Parallel non-interference**: N sub-agents each run their own context, cannot see each other's intermediate state, and do not communicate directly—exchanging information must go through the supervisor.

## Applicability

- **Batch tasks where subtasks produce a lot of output and the supervisor's context is tight**: contract review, document scanning, large-scale code search, where each sub-agent handles one item and returns only a refined conclusion.
- **Independent item review**: Each contract or record receives only its authorized task context, reducing cross-item influence and accidental disclosure.
- **Restricted data scope**: Worker credentials and context expose only the records required for that task. Isolation complements, but does not replace, authorization enforcement.
- **Verbose local exploration**: Trial-and-error traces remain in the worker runtime while the supervisor receives a bounded artifact.

## Known failure modes

- **The sub-agent inherits the supervisor's history**: As the parent history grows, every new sub-agent starts with unrelated tokens, increasing cost and interference. Start from local messages with only the contracted task context.
- **Returning free text instead of a schema artifact**: Free text cannot be reliably parsed, ranked, or routed by deterministic code. Enforce the artifact schema and reject non-conforming returns.
- **Uncontrolled worker-to-worker calls**: if worker A can invoke worker B outside the supervisor's plan, dependencies and authority move beyond the coordinator's trace. Route cross-worker requests through the supervisor or an explicit shared protocol.
- **Failure has no boundary**: An uncaught worker exception interrupts the parent task. Convert timeout, cancellation, and execution errors into typed failure artifacts and apply partial-failure policy.
- **Wrapping isolation around a trivial subtask**: When the output is already small or the supervisor genuinely needs intermediate detail, isolation may add needless overhead. Compare it with direct execution under the real context budget.

## Verification and metrics

- **Supervisor context usage**: Measure the share consumed by all returned artifacts and reserve enough room for aggregation, conflict resolution, and final reasoning.
- **Artifact compliance rate**: Track whether sub-agent returns conform to the schema. Free text bypass creates redispatch, manual correction, and latency.
- **Failure cascade rate**: Test whether one sub-agent failure interrupts unrelated branches. Verify process, context, tool-permission, and error-boundary isolation separately.
- **Artifact compression and retention**: Compare raw trajectory size with the reduced artifact, while checking whether required findings, evidence, and uncertainty survive compression.

## Reference implementation

```
IsolatedSubAgent.execute(task):
                local_context = [system_prompt, task]      # no parent history passed in → context isolation
                try:
                    raw = run_loop(task, local_context)     # independent LLM call + independent tool set
                except: return Artifact(verdict="failure")  # failure boundary
                return reduce_to_artifact(raw)              # force reduce to verdict/findings/citations

            SupervisorWithSubAgents.execute(task):
                artifacts = parallel gather(                 # N in parallel, each with its own context → non-interference
                    sub.execute(dispatch_subtask(task, sub)) for sub in sub_agents
                )
                return synthesize_from_artifacts(artifacts) # supervisor sees only artifacts, never raw trajectory
```

Start from local messages, validate the returned artifact, convert timeout and exceptions into typed failures, and isolate mutable state for concurrent workers.

## Illustrative scenario

Consider a law-firm contract review agent. A first version lets every worker return its complete analysis, leaving too little context for portfolio-level synthesis. A stronger version gives each contract an independent review context and requires `verdict`, `top_concerns`, `recommendation`, citations, and uncertainty in the returned artifact. A failed worker does not interrupt the others, and low-confidence findings are routed to lawyers. Sub-agent runtimes such as task-oriented coding-agent tools illustrate the same boundary: separate context and tools, then return a final artifact instead of injecting the full internal trace. Actual context savings and review quality require measurement on an authorized corpus.

## Related patterns

- **Hierarchical Delegation (C1)**: C1 defines how a supervisor assigns work; C5 defines the context, permissions, runtime, and result boundary of each worker. They are commonly combined, but they answer different design questions.
- **Fan-Out/Gather (C2)**: C5 supplies the context, permission, runtime, failure, and artifact boundary for each parallel branch.
- **Layered Retention (M1)**: M1 controls retained information by scope and access tier. C5 applies an independent working set and credential scope to one delegated task.
- **Context Triage (P1)**: The supervisor may retrieve detailed worker evidence on demand instead of preloading every intermediate trace.

## Design conclusion

Sub-agent isolation limits each worker's context, tools, credentials, budget, and workspace. The supervisor receives a verifiable artifact, so local work and local failure do not automatically contaminate the parent task.

## Workshop revision, 25 August 2026: Cross-session isolation

Isolation extends to worktrees, requirement IDs, shared configuration, test databases, deployment environments, and external quotas. The scheduler checks write-conflict domains and records locks, leases, policies, and release conditions.

[Collaboration workshop record](https://adpsagent.com/workshops/collaboration-2026-08-25/)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-handoff-engineering" class="related-case-band">
<p class="related-case-label">Pattern engineering note</p>
<h2 id="related-handoff-engineering"><a href="https://adpsagent.com/patterns/engineering/cross-agent-handoff/">Connecting Two Agents: From Context Reference to Task Handoff</a></h2>
<p>Place this pattern in a frontend finding, backend repair, and frontend retest, then inspect ownership transfer, authority, and acceptance evidence.</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>C5 Sub-Agent Isolation</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-c5-sub-agent-isolation">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
