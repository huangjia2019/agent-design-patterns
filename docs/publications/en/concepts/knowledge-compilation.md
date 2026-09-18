<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Knowledge Compilation</h1><p class="publication-deck">Transform knowledge sources into traceable, incrementally updated runtime assets.</p></header>

## Application context: documents are stored, yet the agent cannot retrieve an operational answer

A team chunks policies, meeting notes, and incident reports into a vector store. A query about when an allowance becomes effective returns many similar passages, but none carries region, effective time, superseded version, and original location together. The material is stored; it has not been prepared for reliable runtime use.

## Definition

Knowledge Compilation is the write-side transformation that turns source material into summaries, entities, events, relations, navigation structures, and source pointers, then builds full-text, vector, field, and graph indexes. Like a compiler front end, it preserves source locations while producing structures for different retrieval paths.

## Engineering mechanism

A compilation run records source hashes, parser version, segmentation policy, extraction model, time, and scope. Every derived claim points back to source text. Updates recompile affected units and record supersession. Retrieval chooses exact text, vector search, entity lookup, or navigation according to the question instead of assigning every access path to similarity search.

## Boundary

Knowledge Compilation fits versionable material with a manageable update rate. Live balances, approval status, and order outcomes still come from authoritative systems and cannot be replaced by compiled summaries. Automatically extracted claims need admission and sampled audit before entering long-term recall.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-context-memory">Context and memory</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Introduced into ADPS workshops by Yingfeng Zhang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/memory-2026-08-05/">First Memory workshop</a> (<time datetime="2026-08-05">2026-08-05</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS placed it on the write side of M2 while recognizing that the term has a broader public technical lineage.</dd></div>
<div><dt>Current standing</dt><dd>Workshop concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/memory-2026-08-05/">First Memory workshop</a> (<time datetime="2026-08-05">2026-08-05</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-05">2026-08-05</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-knowledge-compilation">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
