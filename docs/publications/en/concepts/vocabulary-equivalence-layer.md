<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Vocabulary Equivalence Layer: Align Planning Terms with the Host Metamodel</h1><p class="publication-deck">Align planning terms, domain types, and the host metamodel through one tested mapping.</p>
</header>

## Start with a type false positive

This problem appears when an agent writes into an established engineering tool. Users and planners speak in domain terms, while the host system already has fixed types, enums, and versioned schemas. Two labels may refer to the same business object without being equal strings.

For example, a user asks for a "system actor" in a SysML model. The planner emits `SystemActor`, the modeling tool stores `uml:Actor`, and the write-back API returns the normalized type `Actor`. A validator that compares strings rejects a legal write.

The same issue appears between customer, account, and contact in a CRM; layer, feature class, and published service in GIS; and user, principal, and service account in cloud IAM. These systems need a tested semantic-equivalence mapping, not scattered alias checks in prompts and adapters.

## Definition

A vocabulary equivalence layer explicitly maps planning terms, canonical domain types, host metamodel types, and returned write-back types.

<pre><code class="language-text">planning type
  -&gt; canonical domain type
  -&gt; host metamodel type
  -&gt; returned write-back type
</code></pre>

The mapping handles aliases, inheritance, compatibility, diagram-specific rules, and host versions. Planners, validators, and writers use the same versioned mapping and log both original and normalized values.

## Boundary

Mappings need versions, unit tests, and host-upgrade regressions. The layer solves deterministic semantic adaptation; it does not replace open-domain retrieval. Without conversion traces, adapter defects are easily misdiagnosed as model hallucinations.

## Provenance

- Initial research source: the AI4MBSE modeling agent project by Liangding Yuan; the name is an ADPS synthesis.
- Lineage: Adapter, Anti-Corruption Layer, schema mapping, and canonical data models.
- ADPS contribution: treats the mapping as a tested runtime asset selected by diagram type and host version.
- Definition status: ADPS restatement.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-planning-execution">Planning, execution, and write-back</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial research practice: Liangding Yuan</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/ark-mbse-agent/">AI4MBSE modeling-agent project</a> (<time datetime="2026-08-02">2026-08-02</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS restated vocabulary mapping as a testable runtime asset selected by diagram type and host version.</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-vocabulary-equivalence-layer">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
