<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Typed Intermediate Representation Chain: Narrow Language into Verifiable Structure</h1><p class="publication-deck">Narrow natural language through typed, verifiable structures before write-back.</p>
</header>

## Start with one use-case diagram

A user asks for a turnstile use-case diagram under an existing package. A one-shot response that creates elements, relations, and the view may point to names that do not exist or omit elements from the diagram. A failure forces the entire structure to be regenerated.

## Definition

A typed intermediate representation chain narrows natural-language intent through a series of verifiable data structures. The AI4MBSE modeling agent project can be reconstructed as:

<pre><code class="language-text">ModelingJob -&gt; ElementPlan -&gt; RelationPlan -&gt; ViewPlan -&gt; WriteSet
</code></pre>

Each stage reads an accepted upstream result and emits typed candidates with stable references and provenance. A validator checks well-formedness. The writer consumes a gated `WriteSet` and does not reinterpret the original language.

## Boundary

JSON alone is not a typed IR. Schemas or validators must enforce field types, allowed values, references, and stage invariants. Stages may run as separate agents, repeated model calls, or ordinary functions.

## Provenance

- Initial research source: the AI4MBSE modeling agent project by Liangding Yuan; contract names are an ADPS reconstruction of the published mechanism.
- Lineage: compiler IR, typed ASTs, semantic analysis, and database referential integrity.
- ADPS contribution: models draft candidate IRs, programs validate stage contracts, and the writer consumes only accepted structures.
- Definition status: ADPS restatement.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-planning-execution">Planning, execution, and write-back</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial research practice: Liangding Yuan</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/ark-mbse-agent/">AI4MBSE modeling-agent project</a> (<time datetime="2026-08-02">2026-08-02</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS reconstructed the stage contracts and separated candidate IR, validation, and write-back responsibilities.</dd></div>
<div><dt>Current standing</dt><dd>ADPS restatement</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Initial source:</strong> <a href="https://adpsagent.com/cases/ark-mbse-agent/">AI4MBSE modeling agent project</a>; authored by Liangding Yuan.</p><p><a href="https://adpsagent.com/concepts/">Concept registry</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/cases/ark-mbse-agent/">AI4MBSE modeling-agent project</a> (<time datetime="2026-08-02">2026-08-02</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-typed-ir-chain">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
