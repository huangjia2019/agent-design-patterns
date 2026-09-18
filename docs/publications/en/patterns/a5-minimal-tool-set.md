<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>A5</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>A5 · Minimal Tool Set</h1>
<p class="publication-deck">Reduce tool ambiguity by removing obsolete tools, consolidating overlaps, routing by task, and loading specialist tools on demand.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Action × Constraint (cross-cutting, belongs to no single topology)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Low (cutting tools itself saves tokens, a net gain)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern Group</strong></td>
<td style="text-align: left;">Action patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern Summary</strong></td>
<td style="text-align: left;">Reduce tool ambiguity by removing obsolete tools, consolidating overlaps, routing by task, and loading specialist tools on demand.</td>
</tr>
</tbody>
</table>

---

## Problem

As a tool registry grows, overlapping names and parameters compete for model attention. For a question such as “when will my order arrive,” an agent may try several order tools and spend much of its reasoning budget choosing an interface.

Minimal Tool Set exposes only the tools required for the current role and task stage. The total registry may remain large, while the default candidate set stays focused and Tool Search loads uncommon capabilities on demand.

## Classification: Action × Constraint

Minimal Tool Set constrains per-decision exposure and can be applied to several execution topologies.

- **Vertical axis · Action**: It governs which executable capabilities are visible at an action decision.
- **Horizontal axis · Constraint**: Minimal Tool Set does not define an execution topology. It limits the tools exposed at one decision point and can therefore attach to Route, Chain, Hierarchy, or another action structure. Record it as Action × Constraint. Evaluate candidate-set coverage, schema-token cost, selection errors, and permission surface instead of imposing one global numeric cap.

## Solution and mechanics

The relevant limit is not a universal tool count. It is the point at which descriptions consume too much context or similar candidates become hard to distinguish. Find that point through local replay and ablation by task class.

Three controls reduce the default candidate set:

<table>
<thead>
<tr>
<th style="text-align: left;">Strategy</th>
<th style="text-align: left;">How</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Drop low-frequency</td>
<td style="text-align: left;">Move long-unused tools into decommission review instead of the default candidate set</td>
</tr>
<tr>
<td style="text-align: left;">Merge similar</td>
<td style="text-align: left;">Review tools with overlapping semantics and parameters for consolidation</td>
</tr>
<tr>
<td style="text-align: left;">Push down secondary</td>
<td style="text-align: left;">Put low-frequency but useful tools (OCR, PDF parsing, image translation) into a dedicated sub-agent</td>
</tr>
</tbody>
</table>

Pair pruning with progressive disclosure: keep core tools resident and load extended tools through Tool Search. The appropriate default set depends on role, permissions, and task distribution.

## Applicability

- **Latency-sensitive, accuracy-sensitive user-experience scenarios**: customer service, conversation, and consumer agents benefit directly from a smaller candidate set.
- **Controlling per-call exposure with external tool protocols**: A large underlying registry can still present a small task-specific candidate set, with Tool Search for uncommon tools.
- **Multi-function agents with persistent selection errors**: If task-specific pruning cannot separate overlapping capabilities, move a coherent capability and its tools behind a dedicated role or sub-agent.

It does not mean that every agent needs the same small number of tools. Code agents and multifunction enterprise systems may require a broad registry; the pattern governs per-decision exposure, not an arbitrary global cap.

## Known failure modes

- **Treating “all-capable” as the goal**: A single agent that exposes every organizational capability accumulates ambiguous tools. Organize candidates around the user's current outcome.
- **Losing semantic boundaries when merging**: Combining tools with different preconditions, permissions, or side effects creates a vague interface. Merge only when their contracts genuinely overlap.
- **Pruning without progressive disclosure**: Removing low-frequency tools from every path makes rare tasks unreachable. Keep them discoverable through Tool Search or a dedicated capability.
- **Not reviewing after cutting**: New features gradually expand the default set again. Establish a recurring review based on use, overlap, success, and risk.

## Verification and metrics

- **Tools per dispatch**: Track candidate-set size by task class and use ablation to find where selection quality changes.
- **Total tool-description tokens**: Measure context occupied by tool schemas together with selection errors, retries, and latency.
- **Default-loaded / total tool ratio**: Keep the default set focused and retrieve uncommon tools on demand. Calibrate by role and workload.
- **Tool selection accuracy**: Compare before and after pruning on the same replay set, while checking capability coverage.

## Reference implementation

```
prune(all_tools, stats, target_size):
                score each tool = value, success, recency, and risk in the local observation window
                sort by score descending, keep the top target_size as resident
            evict_stale(stats):
                return tools with no effective use over the review window
            merge_similar(tools, similarity_threshold):
                use embeddings to compute description similarity, recommend merging those > threshold
            # remaining tools are not deleted; move them to a sub-agent + attach to the Tool Search entry
```

Keep a small resident set and discover extended tools on demand. Score candidates with task coverage, use, success, recency, permissions, and risk, and retain a discovery path for uncommon work.

## Illustrative scenario

Consider a translation and localization agent whose default set covers translation, language detection, glossary lookup, quality checks, format preservation, and cultural adaptation. OCR, PDF parsing, and image translation move to specialized sub-agents; long-unused tools enter decommission review; overlapping tools enter consolidation review; rare tasks use Tool Search. Compare selection accuracy, coverage, token use, and latency on a fixed replay set before changing the default set.

## Related patterns

- **Tool Dispatch (A1)**: A5 defines the candidate set; A1 selects and admits a call within it.
- **Layered Retention (M1)**: Both use progressive disclosure, but A5 exposes executable capabilities while M1 assembles retained information.
- **Plan-and-Execute (A2)**: Task decomposition can assign a coherent capability and its tools to one plan step or sub-agent, reducing exposure elsewhere.

## Design conclusion

Minimal Tool Set manages per-decision exposure rather than imposing one global cap. The right candidate set preserves task coverage while reducing schema context, near-duplicate choices, and permission surface.

## Open-source implementation

[**DeerFlow Guardrails and Two-Layer Authorization**](https://adpsagent.com/cases/deerflow-guardrail/) traces five public pull requests across assembly filtering, run-time authorization, trusted identity, RBAC, and RunJournal, with explicit boundaries for this pattern.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>A5 Minimal Tool Set</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-07-18">2026-07-18</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-a5-minimal-tool-set">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
