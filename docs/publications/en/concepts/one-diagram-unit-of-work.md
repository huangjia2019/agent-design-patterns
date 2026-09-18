<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>One-Diagram Unit of Work: Commit One Verifiable Modeling Increment</h1><p class="publication-deck">Commit one diagram, one resolved scope, one write set, and one receipt at a time.</p>
</header>

## Start with “finish the system model”

That goal may include requirements, use cases, block definitions, internal blocks, and state diagrams. It has no stable single-run completion condition, and an early deviation can propagate into later diagrams.

## Definition

A one-diagram unit of work groups one diagram type, one resolved project location, one write, and one acceptance receipt into a transaction boundary.

<pre><code class="language-text">one user operation = one diagram type + one scope_ref + one WriteSet + one receipt
</code></pre>

The boundary defines what may change, which invariants are checked, what the receipt counts, and what a rollback must restore. Larger goals proceed through multiple accepted units.

## Boundary

This unit does not guarantee cross-diagram consistency. An upper-level plan still manages dependencies, versions, and acceptance order. If the host lacks atomic transactions, the adapter needs before-state snapshots, compensation steps, and an explicit partial-failure state.

## Provenance

- Initial research source: the AI4MBSE modeling agent project by Liangding Yuan; the name is an ADPS synthesis.
- Lineage: Unit of Work, Command, and transaction boundaries.
- ADPS contribution: combines diagram type, engineering scope, candidate structure, receipt, and rollback into one agent write-back boundary.
- Definition status: candidate concept.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-planning-execution">Planning, execution, and write-back</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial research practice: Liangding Yuan</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/ark-mbse-agent/">AI4MBSE modeling-agent project</a> (<time datetime="2026-08-02">2026-08-02</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS combined diagram type, model scope, candidate structure, receipt, and undo into one write-back boundary.</dd></div>
<div><dt>Current standing</dt><dd>Candidate concept</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-one-diagram-unit-of-work">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
