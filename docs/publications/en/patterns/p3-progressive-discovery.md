<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>P3</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>P3 · Progressive Discovery</h1>
<p class="publication-deck">Scan an unfamiliar information space broadly, inspect promising sources, and deepen the search only where evidence justifies the cost.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Perception × Loop (turn)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (multiple search, read, and evaluation calls)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Perception patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Scan an unfamiliar information space broadly, inspect promising sources, and deepen the search only where evidence justifies the cost.</td>
</tr>
</tbody>
</table>

---

## Problem

An agent faces a large legacy codebase, an unindexed contract collection, or a long incident log. It may not know the name of the relevant code or where the key evidence sits. Loading everything exceeds the window, and RAG may miss an implementation whose variable is `merge_user_state` but whose comments never use the business term “order.”

Progressive discovery starts with a broad scan, lets the evidence reshape the next query, and iterates until the signal is sufficient, no new evidence appears, or the budget is exhausted. It governs active exploration of an unknown space within the current session.

## Classification: Perception × Loop

- **Vertical axis · Perception**: Progressive Discovery acquires evidence in stages and decides which source to inspect next. It operates before the evidence is used to make the domain decision.
- **Horizontal axis · Loop**: Each search round updates the query from observed files, terms, references, or failures. The loop stops when evidence is sufficient, no new signal appears, or a budget is exhausted.

## Solution and mechanics

A single discovery runs the three forage-focus-deepen stages, decreasing in breadth and increasing in depth:

<table>
<thead>
<tr>
<th style="text-align: left;">Stage</th>
<th style="text-align: left;">Action</th>
<th style="text-align: left;">Tools and cost</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Forage (broad scan)</td>
<td style="text-align: left;">Gather candidates from file names, paths, and the context around matched lines</td>
<td style="text-align: left;">grep / glob / find; broad coverage at low cost</td>
</tr>
<tr>
<td style="text-align: left;">Focus (close read)</td>
<td style="text-align: left;">Read the most relevant candidates in full and inspect dependencies and call chains</td>
<td style="text-align: left;">read; spend the main budget after narrowing</td>
</tr>
<tr>
<td style="text-align: left;">Deepen (deep follow)</td>
<td style="text-align: left;">Follow high-signal references into functions, tests, or history</td>
<td style="text-align: left;">read; stop at an explicit depth and budget</td>
</tr>
</tbody>
</table>

Give the agent atomic tools such as grep, read, and glob so that each observation can reshape the next query. Configure hard limits for cycles, per-cycle budget, candidate count, and dependency depth using repository scale, task risk, and replay results. If the limit is reached without evidence, revise the query, switch retrieval methods, or hand off. A lightweight model can derive a compact set of initial keywords, which are then updated from new evidence.

## Applicability

- **Root-cause localization in an unfamiliar codebase**: The original author has left, documentation is sparse, and no one knows which files a pipeline crosses. The agent must find an entry point and narrow the search along call relationships.
- **Operations incident response**: after receiving an alert, derive keywords from the metric, trim the log by time window, localize the fault source through the three stages, and give the on-call engineer an initial assessment report plus a "what to do first" recommendation.
- **Contract and literature search**: The request identifies the issue but not the source location, so findings from one document guide the next query.
- **Privacy-sensitive codebase that remains directly searchable**: grep + read can keep code inside the controlled file system instead of copying it into a vector store.

## Known failure modes

- **Forage keywords too broad**: Translating “user login has gotten slow” only into `["login", "slow"]` produces too many candidates. Add component names, error fields, or call entry points to narrow the query.
- **Focus stage ranks the wrong files**: test files may outrank the production path while `services/auth.rb` remains unread. Tune ranking with repository role, recency, call relationships, and evidence from completed tasks.
- **Deepen dead end**: Following dependencies into a third-party library may produce no new signal. Set scope and depth limits unless current evidence points outside the repository.
- **Discovery collides with RAG**: The two paths may return overlapping or conflicting results. Rank sources by freshness, permission boundary, and index coverage, and preserve provenance for both.

## Verification and metrics

- **cycles\_to\_success**: Track convergence by task class. A sustained increase against the local baseline calls for inspection of keyword derivation, tool availability, and candidate ranking.
- **forage/focus budget ratio**: Forage should stay broad and light while Focus carries most reading. Diagnose shifts together with candidate count and final hits.
- **zero\_signal\_rate**: The share of sessions that stop without useful evidence. When it rises, inspect index freshness, read permissions, scorer behavior, and task descriptions.

## Reference implementation

```
discover(task, keywords):
                loop up to max_cycles:
                    Forage: run grep for each keyword → collect candidates → score by relevance → keep top_k
                    if cycle_tokens exceed budget → stop
                    Focus: pick focus_k to read in full, recording dependencies
                    Deepen: extract dependencies from what was read and follow within deepen_budget
                    if signal is sufficient → success, break
                    else → refine keywords from what was discovered, run another round
                emit one DiscoveryEvent per stage (phase / keyword / candidate count / files_read / tokens / wall_time)
```

Expose search, read, and ranking behind small interfaces. The discovery loop can then use a local file system, an MCP server, or an external index without changing its state transitions or trace schema.

## Illustrative scenario

Consider an e-commerce system whose order-confirmation emails occasionally include another customer's items. Semantic retrieval misses the implementation because the relevant code does not use the word “order.” The agent first runs `grep "send.*confirm"` to locate sending entry points, then reads the mailer and cache call chain, and finally follows `Cache.get_user`. It finds that the cache key lacks a tenant dimension. This failure depends on code structure, so traversing files and calls can be more effective than semantic recall alone.

## Related patterns

- **Context Triage (P1)**: Triage defers lower-priority sources behind handles. Discovery follows those handles when the current investigation needs them.
- **Semantic Compaction (P2)**: Discovery may produce a long search trace. Compaction returns a bounded finding with evidence links to the coordinating agent.
- **Procedural Memory (M5)**: Repeatedly successful search procedures may become versioned skills after evaluation. The files found in one run remain task evidence unless a separate memory-admission policy retains them.

## Design conclusion

Progressive Discovery stops when the agent has enough evidence for the current decision, not when it has read the entire repository. Track search depth, duplicate reads, evidence coverage, and failures caused by a required source that was never opened.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>P3 Progressive Discovery</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-p3-progressive-discovery">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
