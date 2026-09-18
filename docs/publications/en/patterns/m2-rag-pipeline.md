<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>M2</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>M2 · RAG Pipeline · Retrieval-Augmented Generation</h1>
<p class="publication-deck">Organize large knowledge sources into provenance-, version-, and permission-aware indexes, then use a retrieval harness to query, navigate, rerank, and assemble evidence for the current task.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Memory × Chain (pass)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (indexing + retrieval + optional reranking)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Memory patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern summary</strong></td>
<td style="text-align: left;">Organize large knowledge sources into provenance-, version-, and permission-aware indexes, then use a retrieval harness to query, navigate, rerank, and assemble evidence for the current task.</td>
</tr>
</tbody>
</table>

---

## Problem

An enterprise knowledge base can contain far more documents, tickets, logs, and business objects than an LLM context window can hold. RAG builds traceable indexes on the write side and retrieves evidence for the current task on the read side.

Production RAG also has to decide how to search. A one-shot query is often insufficient. The agent may need to rewrite the query, retrieve counterexamples, and compare evidence across corpora before composing an answer.

## Classification: Memory × Chain

- **Vertical axis · Memory**: RAG attaches an external knowledge base to the run. It governs which facts are indexed, how they are retrieved, and which evidence reaches the model.
- **Horizontal axis · Chain**: Source material passes through parsing, annotation, and indexing; an online request passes through query planning, filtering, retrieval, fusion, reranking, and evidence assembly. An agent may rewrite a query and run another bounded pass, while the public matrix retains the sequential backbone as the pattern's single coordinate.

## Solution and mechanics

1. **Govern before indexing**: When parsing documents, logs, and structured objects, record source, owner, permission, valid time, version, and original location. Chunks and summaries are derived assets and must retain source pointers.
2. **Build multiple access paths**: Index body text, summaries, entities, temporal events, identifiers, and relation paths as needed. Error codes and IDs favor exact or structured lookup; open semantic questions use BM25, vectors, and reranking; relationship questions use graph or navigation paths.
3. **Let a retrieval harness choose the path**: An `EvidenceRequest` states the question, time range, scope, and evidence policy. The harness selects search, browse, navigate, lookup, or direct reading and records the choice.
4. **Filter permission, time, and version first**: Remove unauthorized, expired, or superseded content before fusion and ranking. Similarity must not revive an obsolete policy.
5. **Return an evidence bundle**: `EvidenceBundle` contains supporting evidence, counterevidence, source locations, versions, confidence information, and a `RetrievalTrace`. Generation can assess sufficiency or decline to answer.
6. **Bound multi-step retrieval**: Complex questions may be decomposed, rewritten, checked for counterexamples, and validated across corpora. Cap rounds, tokens, tool calls, and wall time.

## Applicability

- **Large-scale natural-language knowledge bases**: Academic literature, case libraries, and support knowledge are well suited when the corpus is large, relatively stable, and rich in synonyms or implicit relationships.
- **Complex queries across many documents**: scenarios that need answers synthesized from multiple sources and that need traceable citations.
- **Organizing enterprise know-how**: Govern knowledge scattered across wikis, Confluence, Slack, email, and tickets so the agent can retrieve it with provenance and access controls.

## Known failure modes

- **Indexing an ungoverned source**: Contradictory documents, missing decisions, stale versions, and inconsistent terminology become easier to retrieve.
- **Forcing all data through vectors**: Exact identifiers, structured fields, and version constraints degrade under semantic retrieval. Preserve full-text, structured lookup, and direct source access.
- **Detaching compiled assets from the source**: A summary, wiki page, or entity relation changes without a pointer to original material, so the system cannot support its conclusion.
- **Chunking static documents and dynamic events the same way**: Policies, sessions, and tool events have different granularity, update cadence, and valid time.
- **Adding tools without converging dispatch**: Search, browsing, graph queries, and direct reading are all exposed, but the harness does not record why it selected one path. A failure cannot be localized to query planning, indexing, ranking, or reading.
- **Index freshness below task requirements**: Code and operational state may change before indexing finishes. Query the live repository, database, or business API when the task needs current ground truth.
- **Stopping at one query, one answer**: when the key information is not found on the first try, naive RAG either says it doesn't know or silently fabricates. Production-grade RAG must be able to rewrite the query and search again.
- **Blindly chasing retrieval precision**: A higher offline embedding score does not replace query rewriting or evidence validation. Evaluate the final answer for correctness, completeness, and citation quality.
- **Untraceable citations**: Where policy or review requires traceability, each conclusion needs a path back to the original passage, location, and version.

## Verification and metrics

- **Index coverage and freshness**: Verify that current material has been parsed, annotated, and published within the business update window.
- **Retrieval failure rate**: The share of evaluation cases with no relevant evidence among candidates. Localize failures to indexing, retrieval, or filtering.
- **Evidence-use and citation rate**: Measure which retrieved items the agent actually uses and cites. Low use calls for inspection of candidate noise, query granularity, version filtering, and ranking.
- **Reading correctness**: Once the correct evidence is in context, test whether the model still misreads it, ignores a constraint, or cites a neighboring passage.
- **Number of multi-step retrieval rounds**: Record actual iterations and enforce a hard ceiling. Repeatedly hitting it may indicate a task that needs decomposition, a missing source, or poor first-pass retrieval.
- **Trace completeness**: Each public claim should connect to the query, candidates, exclusion reasons, original location, and version.
- **Final synthesis quality**: Domain reviewers evaluate correctness, completeness, and citation quality against an agreed rubric before the system enters production.

## Reference implementation

```
Write side:
                source → parse → chunk/event/entity
                       → annotate(source, owner, permission, valid_time, version)
                       → full-text + vector + structured/graph indexes + source pointer

            Read side:
                EvidenceRequest(question, scope, time_range, evidence_policy)
                  → retrieval harness selects lookup/search/browse/navigate/read
                  → permission + valid-time + version filter
                  → exact/BM25/vector/graph candidates
                  → fuse + rerank + evidence-sufficiency check
                  → EvidenceBundle(support, counterevidence, citations, trace)

            If evidence is insufficient, rewrite or split the query within round, token, and time limits.
```

Observe index publication separately from online retrieval. A wrong answer should be localizable to source quality, compilation, filtering, retrieval, ranking, reading, or synthesis.

## Illustrative scenario

Consider an academic literature-review agent. Keyword search produces a broad candidate set, while embedding-only retrieval overconcentrates on established topic clusters and misses newer cross-disciplinary work or counterexamples. A later design decomposes the question, rewrites queries, retrieves counterevidence, and validates across arXiv, bioRxiv, and PubMed. Peer-reviewed papers, preprints, and internal material remain in governed corpora with locally calibrated evidence weights. Every claim points to the source chunk, page, and version. Evaluation should measure evidence coverage, source traceability, and version correctness rather than publish an unsupported recall figure.

## Related patterns

- **Layered Retention (M1)**: M1 selects retained task and organizational memory by scope, access cost, and lifecycle state. M2 queries managed knowledge sources that are too large or too dynamic to preload.
- **Procedural Memory (M5)**: M2 returns evidence for the current decision. M5 returns a versioned procedure or executable asset for carrying out a recurring task.
- **Context Triage (P1)**: M2 finds candidate evidence. P1 decides which candidates enter the current context, in what order, and within which budget.
- **Progressive Discovery (P3)**: P3 explores an unfamiliar information space to learn its structure. M2 queries prepared indexes and known source systems. A retrieval harness may use P3 when the available sources or navigation paths are not yet understood.
- **Knowledge Compilation (candidate)**: M2 asks how the current task obtains evidence. Knowledge compilation asks how raw material becomes navigable and searchable on the write side.

## Design conclusion

RAG is an evidence supply chain. Distortion in the source, index, retrieval policy, version filter, reading stage, or citation path can produce a fluent answer that does not hold up.

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-memory-engineering" class="related-case-band">
<p class="related-case-label">Pattern engineering note</p>
<h2 id="related-memory-engineering"><a href="https://adpsagent.com/patterns/engineering/memory-storage-on-kubernetes/">Agent Memory on Kubernetes: Storage Layers and Recovery</a></h2>
<p>Place this pattern in a multi-Pod service and inspect the system of record, version conflicts, retrieval indexes, and recovery path.</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>M2 RAG Pipeline</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-m2-rag-pipeline">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
