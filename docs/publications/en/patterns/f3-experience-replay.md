<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>F3</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>F3 · Experience Replay</h1>
<p class="publication-deck">Turn reviewed trajectories and delayed outcomes into scoped experience records, then measure whether later runs use them successfully.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reflection × Hierarchy</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">High (ongoing investment in storage, retrieval, and injection; returns accumulate over time)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reflection patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Turn reviewed trajectories and delayed outcomes into scoped experience records, then measure whether later runs use them successfully.</td>
</tr>
</tbody>
</table>

---

## Problem

Engineering decisions accumulate across chat, tickets, wikis, reports, and email. A later team may repeat an investigation because prior hypotheses, rejected paths, source data, and decision conditions are difficult to retrieve. Much of this material is useful reference evidence but not stable enough to become a callable skill.

Experience Replay retrieves applicable parts of prior trajectories for a new task and records whether they influenced execution. Skill Packages hold verified callable procedures; Experience Replay holds broader evidence and methods that still require an applicability check. Research provides prior evidence for contextual replay without model retraining, while production value must be measured against a local baseline.

## Classification: Reflection × Hierarchy

- **Vertical axis · Reflection**: The system reviews previous tasks and feeds applicable evidence into later work. It uses complete experience as reference material without requiring that every entry become a callable skill.
- **Horizontal axis · Hierarchy**: The store separates raw trajectories, per-task findings, cross-task lessons, and skill candidates. Higher layers retain provenance links to lower-level evidence.

## Solution and mechanics

An Experience Replay loop has six stages: Task → Retrieve → Adapt → Execute → Distill → Store. Two design decisions determine whether it remains usable as the store grows:

1. **Layered storage**: Separate concrete execution facts from extracted findings and cross-task heuristics. AgentRR distinguishes low-level actions from higher-level strategies; the following three-level form keeps raw evidence, per-task interpretation, and cross-task reuse independently reviewable:

<table>
<thead>
<tr>
<th style="text-align: left;">Level</th>
<th style="text-align: left;">Content</th>
<th style="text-align: left;">Engineering role</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">L0 Raw traces</td>
<td style="text-align: left;">Complete execution trace</td>
<td style="text-align: left;">Execution evidence for debugging and audit</td>
</tr>
<tr>
<td style="text-align: left;">L1 Per-task reflections</td>
<td style="text-align: left;">Reflection text written after a single task</td>
<td style="text-align: left;">Task-specific finding with source links</td>
</tr>
<tr>
<td style="text-align: left;">L2 Cross-task heuristics</td>
<td style="text-align: left;">General regularities distilled across tasks</td>
<td style="text-align: left;">Reviewed lesson derived from several tasks</td>
</tr>
</tbody>
</table>

<ol start="2">
<li><strong>Contextual reuse</strong>: CER injects selected and bounded trajectory material into the current context instead of retraining the model. Retrieval uses task conditions, provenance, version, and outcome evidence; later results update the lesson's review record rather than changing its status automatically.</li>
</ol>

A production system also separates **experience formation from experience use**. Runtime retrieval reads only released experience. An offline process groups traces, human interventions, and business outcomes, consolidates duplicate local patches, adds applicability conditions, and publishes an experience only after replay and review.

Feedback latency matters. Code tasks may receive a test result within minutes; recommendations, service decisions, and operating changes may take days to show an outcome. Store `trajectory_id`, runtime version, contemporaneous evidence, and the later outcome label. Without that link, an entry can be marked as verified simply because it looked reasonable when the task ended.

## Online use and offline curation

- **Online**: Retrieve by task type, environment version, and risk label; run an applicability check; record which experience influenced which step.
- **Offline**: Compare batches of trajectories, hand-offs, and delayed outcomes; merge repeated patches; then replay, review, publish, down-rank, or archive the result.

The online path optimizes latency and rollback. The offline path optimizes coverage and consistency. Writing every runtime patch straight into the shared store creates a growing set of exceptions, conflicts, and retrieval cost.

## Applicability

- **Recurring task families**: Customer service, operations, and data analysis can reuse prior investigations when task conditions and outcomes are traceable.
- **Organizational knowledge accumulation**: Connect experience scattered across the company's wiki, document systems, and reports, then retrieve it in a form usable by the current task. Reusing existing knowledge infrastructure is usually the practical starting point.
- **Reuse of failure assets**: Failed trajectories may still contain useful subgoals, diagnostic evidence, or tool-use fragments. Hindsight relabeling can preserve that value, provided the new label records provenance and does not disguise a failure as a verified success.

## Known failure modes

- **Cold start**: A new store has little evidence. Seed it with reviewed historical records, mark provenance and trust, and capture new trajectories without presenting the seed set as verified runtime experience.
- **Stale-lesson drift**: An experience that was once correct may no longer apply after a product revision, yet the agent keeps injecting it. Bind experience to system versions, downweight stale entries, and review or deprecate them on an explicit schedule.
- **Negative transfer from similar wording**: Embedding similarity does not establish equivalent task structure. Filter by task type, environment, version, and applicability conditions before semantic ranking, then retain the review decision.
- **Unstructured trajectory store**: Raw traces without layers, provenance, outcome labels, or release state create noisy retrieval and weak attribution.
- **Misattributing a delayed outcome**: If a later business result cannot be linked to the original trajectory, version, and time window, the system may reward the wrong experience.
- **Accumulating local patches**: Each runtime failure appends a special rule. Short-term recovery turns into long-term retrieval noise and execution latency unless offline curation consolidates or removes the patches.

## Verification and metrics

- **Retrieval adoption rate**: The proportion of recalled experience that the agent or reviewer actually uses. Low adoption can indicate poor task signatures, weak ranking, or stale entries.
- **Effectiveness evidence**: Compare outcomes when an experience is used with an appropriate baseline, and keep sample size and task type visible. Archive lessons that repeatedly fail review or provide no benefit.
- **Store coverage and retrieval count**: During cold start, track whether representative tasks are being captured and whether retrieval reaches the right task families.
- **Quality gain**: Compare replay-enabled runs with a no-replay baseline on a fixed set. Treat it as a lagging indicator and report retrieval cost alongside it.
- **Trajectory-to-outcome linkage**: Measure how many delayed outcomes can be connected to the exact task, version, and evidence available at execution time.
- **Negative transfer and patch debt**: Track tasks that regress after experience injection and local patches that remain unreviewed or unconsolidated.

## Reference implementation

```
# Retrieve + inject (CER training-free)
            past = retrieve(task)                      # top-K, prioritize high effectiveness + success
            context += render_for_context(past)        # high-level strategy + author metadata
            heuristics = get_L2_by_signature(task)     # cross-task regularities
            context += render(heuristics)

            result = agent.run(task, prior_context=context, trajectory_collector=traj)
            record_adoption(task.id, past, result.trajectory)  # which experience changed which step

            # Record facts first; do not publish a lesson directly
            record_trace(task, traj, immediate_outcome, author_id, runtime_version)
            attach_delayed_outcome(task.id, delayed_outcome)

            # Write back effectiveness (lesson accuracy feedback loop)
            for e in past:
                update_effectiveness(e, current_task_succeeded=result.ok)

            # Consolidate local patches offline and publish only after replay and review
            candidate = consolidate_patches(signature, traces, outcomes)
            publish_L2(candidate, when=replay_passed and review_approved)
```

Choose embedding and distillation models from measured retrieval quality and cost. Keep outcome evidence rather than an unexplained score. Store `author_id`, `trajectory_id`, runtime version, and provenance. Use semantic task features rather than an opaque hash for `task_signature`. Runtime retrieval reads released experience; candidate lessons remain in the offline curation area.

## Illustrative scenario

Consider a data team investigating why retention did not improve after a product change. Different analysts may repeat the same cohort analysis and miss a shared confounder, while a useful historical report remains buried in a document system after its author leaves. Experience Replay can retrieve that report and its heuristic about checking time-window effects, then inject the high-level method together with the original SQL, author, sources, and time range. A reviewer still decides whether the old conditions apply. The reusable design lies in layered storage, provenance, applicability review, and feedback after reuse; any claim about saved effort would require project records from a named case.

## Related patterns

- **Skill Package (F2)**: A Skill Package is a verified callable procedure. Experience Replay retains broader reference material that still needs an applicability check. A runtime can try an approved skill first and retrieve prior experience when no skill matches; repeatedly successful experience may become a skill after evaluation and review.
- **Failure Journals (M4)**: Failure Journals preserve failure events, diagnoses, and lessons. Experience Replay retrieves applicable parts for later tasks and records whether they were used. Failed trajectories may also become training or evaluation material when provenance and labels are preserved.
- **Generator-Critic (F1)**: F1 revises one artifact. Its verdicts and revisions can become source material for F3 after task outcomes and review are available.

## Engineering judgment

Experience Replay organizes historical trajectories, summaries, and reusable artifacts as evidence-bearing retrieval assets. Its value should be measured through later task outcomes, negative transfer, and human hand-off, with delayed outcomes linked back to the original run.

## Further reading

- [Reflection module: Make feedback change the system](https://adpsagent.com/patterns/reflection/)
- [First Reflection workshop, 12 August 2026](https://adpsagent.com/workshops/reflection-2026-08-12/)
- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation)

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>F3 Experience Replay</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-f3-experience-replay">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
