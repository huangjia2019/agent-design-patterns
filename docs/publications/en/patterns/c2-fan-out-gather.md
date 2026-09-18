<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>C2</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>C2 · Fan-out / Gather</h1>
<p class="publication-deck">The orchestrator distributes independently executable subtasks to parallel sub-agents, then an aggregator deduplicates, resolves conflicts, and merges their results.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Collaboration × Parallel (fan-out)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">High (parallel worker calls plus aggregation)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Collaboration patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern summary</strong></td>
<td style="text-align: left;">The orchestrator distributes independently executable subtasks to parallel sub-agents, then an aggregator deduplicates, resolves conflicts, and merges their results.</td>
</tr>
</tbody>
</table>

---

## Problem

Some tasks cannot meet a business window when one agent processes every item sequentially. A quarterly disclosure review, for example, may contain more documents than one run can inspect before the legal deadline.

Fan-Out/Gather splits a task into independent work units, runs them concurrently, and combines typed results. It may trade higher total compute for shorter wall-clock time. Provider limits, shared dependencies, output overlap, and aggregation determine the actual speedup.

## Classification: Collaboration × Parallel

- **Vertical axis · Collaboration**: Fan-Out/Gather assigns independent work units to multiple participants and combines their typed results. Parallel Exploration (R3) instead runs alternative hypotheses or solution paths for the same decision.
- **Horizontal axis · Parallel**: Work units run concurrently without consuming one another's intermediate state. A gather owner combines their artifacts and records partial failures.

## Solution and mechanics

A single fan-out / gather consists of three stages:

1. **Split and fan out**: Define work units by dependency and write-conflict domains, not by equal item count alone. If one unit requires another's result, keep the dependency serial or model it in an orchestrated graph.
2. **Isolated execution**: Each worker has bounded context, tools, credentials, and mutable resources. Research tasks may need context isolation; concurrent code changes may also need separate worktrees or containers plus shared-resource locks.
3. **Gather**: The aggregator validates schemas, discloses missing partitions, deduplicates overlap, resolves or exposes conflicts, and preserves source attribution.

The gather contract may include the following operations:

<table>
<thead>
<tr>
<th style="text-align: left;">Aggregation step</th>
<th style="text-align: left;">Function</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Dedup</td>
<td style="text-align: left;">Merge the same fact when multiple workers capture it, using semantic similarity to find duplicates</td>
</tr>
<tr>
<td style="text-align: left;">Conflict resolution</td>
<td style="text-align: left;">Decide how to adjudicate when worker A says buy and worker B says sell</td>
</tr>
<tr>
<td style="text-align: left;">Integration</td>
<td style="text-align: left;">Catch problems that surface only at the boundaries between worker slices</td>
</tr>
<tr>
<td style="text-align: left;">Ranking</td>
<td style="text-align: left;">Multi-dimensional combined ranking</td>
</tr>
<tr>
<td style="text-align: left;">Attribution</td>
<td style="text-align: left;">Anchor each conclusion to its original source</td>
</tr>
</tbody>
</table>

## Applicability

- **Batch tasks under wall-clock time pressure**: Quarterly compliance scans, large-scale document review, batch bid evaluation—cases where total duration is the hard bottleneck and the subtasks are independent of one another.
- **Research tasks that split cleanly by semantic independence**: Parallel verification across multiple corpus sources, where each sub-agent queries a different category of content and the outputs barely conflict.
- **Multi-agent parallel code writing**: Assign independent agents to separable work packages and use worktrees or containers to isolate files and commits. Measure whether integration effort cancels the time saved.

Use fan-out when work units are independent enough to run concurrently, wall-clock time matters, and the measured aggregation and execution cost is acceptable. Otherwise keep the task serial or use an explicit dependency graph.

## Known failure modes

- **Hidden dependencies between units**: Workers exchange intermediate state or must process material in sequence, and the gather step attempts to reconstruct the missing order. Model those dependencies before dispatch.
- **Unfunded aggregation**: The design budgets worker calls but not schema validation, deduplication, conflict handling, and integration review. Measure gather cost as part of the pattern.
- **Aggregation bottleneck**: The aggregator cannot fit or compare all worker artifacts. Reduce artifact size, aggregate in reviewed layers, or lower fan-out; do not assume logarithmic savings without measurement.
- **Partitioning that ignores write conflicts**: Separate files can still share identifiers, configuration, databases, or deployment environments. Declare conflict domains and keep unknown overlaps serial.
- **Implicit batching cuts concurrency**: The application may launch many calls while the model provider queues or batches them, so observed concurrency is much lower. The implementation must measure and align with provider limits.

## Verification and metrics

- **Worker completion rate**: The proportion of partitions that return a valid artifact. Compliance reports must list incomplete partitions instead of hiding them behind the completed set.
- **Duplication rate**: The proportion of semantically repeated entries after aggregation. A sustained rise points to weak partition boundaries, normalization, or deduplication.
- **Speedup ratio**: Compare observed wall-clock time with the sequential baseline. Investigate provider throttling, shared dependencies, and gather bottlenecks when the gain is small.
- **Aggregation cost share**: Track the compute, model spend, and latency consumed by gather. Stricter artifacts, layered aggregation, or deterministic deduplication may reduce it.

## Reference implementation

```
FanoutGather.execute(goal, perspectives, strategy):
                workers = decompose(goal, perspectives)    # split into N parts by semantic independence
                results = parallel gather(                  # semaphore for concurrency + retry + backoff
                    execute_worker(w) for w in workers      # independent context each, failures don't block others
                )
                return aggregate(goal, results, strategy)   # validate, disclose gaps, merge, attribute

            aggregate(results, strategy):
                concatenate → simple concatenation (only when no overlap)
                vote        → majority vote
                synthesize  → synthesis model selected by evaluation, with explicit contradiction resolution and deduplication
                structured  → schema-based structured merge
```

Select worker and aggregator models from local evaluations, align concurrency with provider limits, isolate unrelated worker failures, disclose incomplete partitions, and retain each branch trace for audit and replay.

## Illustrative scenario

Consider a quarterly compliance-scanning agent. Sequential review cannot meet the disclosure window, while parallel workers introduce duplicate findings, inconsistent terminology, and incomparable confidence labels. The gather stage therefore performs semantic deduplication, concept normalization, evidence merging, and `needs_review` classification. Government or regulated bid-evaluation workflows may also require worker independence and policy-defined trace retention. Every partial failure remains visible in the final report. Throughput and coverage claims require results from an authorized document set.

## Related patterns

- **Parallel Exploration (R3)**: C2 assigns different work units; R3 runs alternative reasoning or evidence paths for the same decision.
- **Hierarchical Delegation (C1)**: C1 adds a supervisor-worker responsibility structure. A design may use C1 for role assignment and C2 for independent workers that run concurrently.
- **Adversarial Review (C3)**: C2 branches contribute parts of one result. C3 reviewers challenge the same decision under distinct review duties.
- **Sub-Agent Isolation (C5)**: C5 supplies context, permission, runtime, failure, and artifact boundaries for each parallel worker.

## Design conclusion

Fan-out / gather exchanges additional execution and aggregation work for shorter wall-clock time. It works when partitions are independent, outputs are contract-shaped, and the gather stage can reconstruct one auditable result.

## Workshop revision, 25 August 2026: Write-conflict domains and read-only gather

Separate files do not imply independent resources. Declare files, identifiers, configuration, domain objects, and external environments before fan-out. Keep work serial when conflicts are unknown. A gatherer without mutation responsibility remains read-only.

[Collaboration workshop record](https://adpsagent.com/workshops/collaboration-2026-08-25/)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>C2 Fan-Out/Gather</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-c2-fan-out-gather">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
