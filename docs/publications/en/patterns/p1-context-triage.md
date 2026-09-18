<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>P1</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>P1 · Context Triage</h1>
<p class="publication-deck">When candidate information exceeds the context budget, decide what enters now, what remains available for later retrieval, and what is excluded.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Perception × Route</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (one lightweight priority judgment, no extra reasoning chain)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Perception patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">When candidate information exceeds the context budget, decide what enters now, what remains available for later retrieval, and what is excluded.</td>
</tr>
</tbody>
</table>

---

## Problem

Production agents routinely draw on source code, conversation history, tool output, and enterprise knowledge. The combined material can exceed the model's effective window. Truncating by filename or chronology may preserve stale material while dropping decisive evidence, leaving the agent to reason from an incomplete record.

Context triage turns this into an engineering process: it divides all candidate information into four levels, P0/P1/P2/P3, and loads from high to low until the token budget runs out. It governs window allocation for a single request, with the goal of guaranteeing that the most critical information is not drowned out.

## Classification: Perception × Route

- **Vertical axis · Perception**: Triage selects the evidence available to the current request before reasoning begins. It does not change output format or persist information across sessions.
- **Horizontal axis · Route**: Each candidate is routed to one of four treatments: load, summarize, defer behind a handle, or drop. Priority, task relevance, identity, and safety constraints determine the route.

## Solution and mechanics

A single triage layers the candidate information by priority, then uses the token budget to allocate a quota to each layer:

<table>
<thead>
<tr>
<th style="text-align: left;">Level</th>
<th style="text-align: left;">Typical content</th>
<th style="text-align: left;">Loading strategy</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">P0 always loaded</td>
<td style="text-align: left;">system prompt, safety rules, current task, business identity (tenant_id)</td>
<td style="text-align: left;">reserve capacity first; ordinary material cannot displace it</td>
</tr>
<tr>
<td style="text-align: left;">P1 loaded if space allows</td>
<td style="text-align: left;">current file, recent tool results, error stack</td>
<td style="text-align: left;">load according to importance for the current task</td>
</tr>
<tr>
<td style="text-align: left;">P2 loaded after compression</td>
<td style="text-align: left;">conversation history, background documents</td>
<td style="text-align: left;">summarize first, then use the remaining budget</td>
</tr>
<tr>
<td style="text-align: left;">P3 handle only</td>
<td style="text-align: left;">resources accessible but not preloaded</td>
<td style="text-align: left;">keep outside the prompt and retrieve through tools on demand</td>
</tr>
</tbody>
</table>

Priority can come from human rules or an algorithm. Claude Code's `CLAUDE.md` hierarchy is an example of human triage: a team can place safety rules at P0 and preferences at P2. Aider's RepoMap is algorithmic triage: it extracts symbols with tree-sitter and scores them through a code graph. Error stacks need cross-tier protection because repair and regression checks depend on that feedback. Each triage decision should also produce a trace so operators can distinguish information that was never discovered from information that was found but deferred or dropped.

## Applicability

- **Multi-tenant SaaS customer-service agent**: One agent serves multiple tenants whose knowledge bases cannot fit in one window. `tenant_id` must be a hard P0 constraint, with the remaining knowledge triaged across the four levels.
- **Code agent facing an unfamiliar codebase**: When each request uses a different repository, symbol extraction and repository graphs can rank relevant files without requiring project-specific instructions in advance.
- **Engineering agent serving the same team long term**: The team can use CLAUDE.md to state safety rules, project constraints, and loading priorities, then let an algorithm handle dynamic triage.
- **Long-running agent connected to a file system or knowledge base**: Explicit triage is needed whenever candidate material may exceed the effective window.

## Known failure modes

- **Priority misjudgment**: If a critical file is marked P3, the agent must retrieve it midway through reasoning, adding tool calls and increasing the risk of cascading errors. When uncertain, raise its priority temporarily and use re-read traces to tune the rule.
- **Over-aggressive triage**: A tight budget may defer files required by several later steps. Repeated retrieval then consumes the tokens and latency the policy was meant to save. Track re-reads and promote repeatedly requested evidence.
- **Vague P3 handle naming**: A name like `doc://manual-page` leaves the agent unsure whether to fetch it. Handles should carry a clear “what is this” signal, for example scope + topic + time.
- **Cross-tenant data leakage**: A P3 handle fetching the wrong tenant's data into the context is a data-breach incident. A resource with a tenant prefix must be force-validated against the P0 tenant\_id at load time.
- **Trace sampled away**: Low-rate random sampling can miss a boundary problem concentrated in a small set of tenants. Triage decisions involving tenant isolation or safety should be retained as structured records.

## Verification and metrics

- **re-read ratio**: The share of deferred material that the agent later requests during reasoning. A sustained increase against the local baseline suggests over-aggressive triage or unclear handle descriptions.
- **Long-tail distribution of dropped\_count**: Means hide requests in which most candidate material is discarded. Inspect the tail alongside task type and failure traces.
- **p3\_hit\_rate**: The share of P3 handles later retrieved. Persistently low use suggests an overly broad handle pool; persistently high use suggests frequent material was misclassified. Calibrate thresholds on local workloads.

## Reference implementation

```
Sort candidates by priority (P0 > P1 > P2 > P3), with protected evidence first:
                for each candidate:
                    P3                     → add a retrievable handle; do not preload
                    within remaining budget → add to context and count tokens
                    over budget             → defer or drop according to policy
                return selected, handles, and one TriageDecision
            TriageDecision records timestamp, budget, selected, deferred, dropped, and tokens_used
```

Production implementations should use the real model tokenizer, extend error detection for the business domain, and emit `TriageDecision` records to an observability system. Review `dropped_count` and retrieval traces at a cadence set by task risk and operating policy.

## Illustrative scenario

Consider a loan-review agent receiving current financial statements, a collateral valuation, historical registration material, and correspondence. If the system truncates by filename, it may drop the current valuation while keeping stale registration documents. Four-level triage protects current financials, collateral evidence, and anomaly or missing-data markers; older material is downgraded by recency, with traceable handles for anything not loaded. The first question is whether the input set is complete enough for a decision, before evaluating the model's reasoning.

## Related patterns

- **Semantic Compaction (P2)**: Triage decides what enters the current context; compaction reduces material already admitted while preserving required evidence.
- **Progressive Discovery (P3)**: Triage may defer a source behind a handle. Progressive Discovery follows that handle when later evidence makes the source relevant.
- **Layered Retention (M1)**: Triage manages one request's context allocation. Memory manages information retained across tasks and sessions. Both should preserve version and provenance in their handles.

## Design conclusion

Context Triage allocates limited context capacity to evidence required by the current goal. Evaluate it through missed required evidence, irrelevant-context ratio, retrieval latency, and downstream task quality.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>P1 Context Triage</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-p1-context-triage">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
