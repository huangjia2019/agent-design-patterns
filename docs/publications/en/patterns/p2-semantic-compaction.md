<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>P2</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>P2 · Semantic Compaction</h1>
<p class="publication-deck">Long sessions approach the context limit. Semantic compaction removes redundant material while preserving goals, accepted evidence, unresolved failures, provenance, and recovery state.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Perception × Chain (relay)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (threshold-triggered summarization plus replay evaluation)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Perception patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Long sessions approach the context limit. Semantic compaction removes redundant material while preserving goals, accepted evidence, unresolved failures, provenance, and recovery state.</td>
</tr>
</tbody>
</table>

---

## Problem

As a long task progresses, the context approaches capacity and some history must be compacted. If a stack trace containing connection-pool settings, queue depth, and call sites becomes only “a database error occurred,” the evidence and previously rejected remedies disappear. The agent may then repeat work that the earlier session already ruled out.

A three-level cascade can trigger from context-occupancy thresholds: remove redundant tool output, summarize older exchanges, then produce a compact recovery record. Each level preserves the current goal, accepted evidence, unresolved failures, provenance, and next action. Replay tests should verify that a later step can recover those fields from the compacted history.

## Classification: Perception × Chain

- **Vertical axis · Perception**: Compaction changes how admitted history is represented inside the current context. It preserves the evidence needed for later reasoning without writing a cross-session memory.
- **Horizontal axis · Chain**: Cleanup, summarization, and deep compaction form an ordered cascade. Each stage consumes the previous representation and emits a smaller, traceable artifact.

## Solution and mechanics

Compaction is triggered in tiers, from light to heavy according to context occupancy, with the error stack protected across the whole flow:

<table>
<thead>
<tr>
<th style="text-align: left;">Level</th>
<th style="text-align: left;">Action</th>
<th style="text-align: left;">Typical compression ratio</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Level 1 Truncation</td>
<td style="text-align: left;">Clean up verbose tool output; keep a pointer and mark it re-fetchable</td>
<td style="text-align: left;">light</td>
</tr>
<tr>
<td style="text-align: left;">Level 2 Summarization</td>
<td style="text-align: left;">Merge old conversation into a persistent anchor without regenerating it from scratch</td>
<td style="text-align: left;">medium</td>
</tr>
<tr>
<td style="text-align: left;">Level 3 Deep compression</td>
<td style="text-align: left;">Reduce older errors to structured records while preserving key parameters and recent evidence</td>
<td style="text-align: left;">deep</td>
</tr>
</tbody>
</table>

The trigger and the persistent anchor determine compaction quality. Set the trigger from evaluations of the chosen model, tool-output mix, and local long-running tasks, leaving margin before quality begins to decline. Merge new information into a stable anchor instead of repeatedly summarizing the whole history. The anchor should record intent, changes, decisions, ruled-out options, and the next step. Ruled-out options keep the agent from retrying paths that have already failed.

## Applicability

- **Long-session customer-support agent**: An intermittent fault may require conversations and internal tool calls across shifts. The anchor can also become a handoff packet for second-line engineers.
- **Multi-step debugging and coding agents**: Long logs, data queries, and API responses can be replaced with re-fetchable pointers after their evidence has been recorded.
- **Research, analysis, and consulting agents**: Trigger compaction when context growth begins to affect task quality in local evaluations.

## Known failure modes

- **Summary loses key information**: Reducing an error with line numbers, pool settings, and queue depth to “a database error occurred” removes the basis for diagnosis. Require the summary to preserve business figures, file paths, function names, and error codes.
- **Compacting an active investigation**: If compaction runs after the agent has narrowed a fault to two files but before it records the evidence and next test, the later step may restart the investigation. Compact completed segments or write a recovery record first.
- **Drift from repeated compaction**: Repeatedly summarizing the same material compounds omissions. Track summary lineage and limit re-compaction; if capacity is still insufficient, hand off or start a new session with a structured packet.
- **Compacting too late**: Waiting until the window is nearly exhausted may allow degraded reasoning before compaction begins. Determine the trigger through replay evaluation.
- **Dropping diagnostic evidence**: Preserve the relevant stack frames, error code, parameters, call site, and source pointer. A generic error summary cannot support recovery or regression testing.

## Verification and metrics

- **Level 3 trigger rate**: Observe how often each task class reaches the deepest tier. Repeated Level 3 use points to a budget, handoff, or early-exit problem.
- **Average compression ratio**: Record after/before together with downstream task quality. A smaller context is not automatically better; replay must confirm that key facts and exclusions remain recoverable.
- **Critical-evidence retention**: Check that error stacks, test results, file paths, and business parameters survive. Missing safety evidence should trigger an alert.

## Reference implementation

```
should_compact(total, budget, threshold): total / budget >= threshold
            compact(turns, target):
                Split: old compressible | protected (recent evidence + all error stacks)
                Level 1: clean up verbose tool output → return if enough
                Level 2: summarize and merge old turns into anchor (intent/changes/decisions/excluded/next) → return if enough
                Level 3: reduce old errors to structured records while keeping key parameters and recent evidence
            Record one CompactionEvent per compaction (level / before-and-after tokens / error stacks preserved)
```

Make `ruled_out_options` a required field in the anchor schema, and append new decisions instead of overwriting prior exclusions. A lower-cost model may perform summarization after it passes the same replay checks.

## Illustrative scenario

Consider a customer reporting an API that fails intermittently during peak traffic and succeeds on retry. A support agent works across shifts, calling log search, metrics, and configuration tools while raw outputs accumulate. The system first removes verbose outputs whose evidence has already been captured and writes an anchor containing symptoms, actions, and ruled-out paths. If the session keeps growing, earlier dialogue is merged into the anchor. If the investigation still does not converge, the runtime exports the anchor and evidence pointers for a second-line engineer.

The handoff should be operational: current symptoms, evidence for and against each hypothesis, rejected paths, and the next untested step. Deep compaction is also an exit signal. Set thresholds from observed session distributions and replay quality rather than inferring them from ticket severity.

## Related patterns

- **Context Triage (P1)**: Triage decides which sources enter the current context. Compaction reduces admitted history when the window approaches its operating limit.
- **Progressive Discovery (P3)**: Discovery acquires missing evidence. Compaction preserves its useful findings without retaining every search step.
- **Layered Retention (M1)**: Compaction manages one session's working history. Memory retains information for later tasks. A compaction anchor becomes memory only after a separate admission and retention decision.

## Design conclusion

Compaction quality can be tested by replaying later steps. The agent should still identify the current goal, accepted evidence, open failures, and next action. If compaction removes an error stack or rejection reason, a later run loses the evidence required for recovery.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>P2 Semantic Compaction</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-p2-semantic-compaction">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
