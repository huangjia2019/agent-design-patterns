<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Plan Compilation</h1><p class="publication-deck">Compile a reasoned plan into an executable structure with dependencies, types, authority, and acceptance.</p></header>

## Application context: a plausible plan may be impossible to run safely

An agent proposes: read employee records, calculate adjustments, submit the batch, and notify staff. The prose is coherent, but approval is missing, two steps write the same table concurrently, and notification may occur before the transaction succeeds. Discovering those defects step by step exposes them to the real system.

## Definition

Plan Compilation turns a model-produced structured plan into an executable graph and checks legality, dependencies, authority, conflicts, economy, and acceptance before execution. A rejected plan returns explicit diagnostics for revision or human review instead of guessing during execution.

## Engineering mechanism

The compiler validates step types and argument schemas, makes dependencies explicit, calculates write-conflict domains, checks caller authority and tool versions, and estimates repeated scans, serial-versus-parallel choices, call counts, and budget. Its output pins a plan hash, node contracts, resource keys, and recovery policy. Runtime adaptation is limited to declared dynamic points.

## Boundary

Low-risk exploration can plan while observing and may not need full compilation. Cross-system writes, batches, approvals, parallel work, and long-running execution benefit from it. Compilation proves structural executability, not that the model understood the business goal; Context Contracts and external acceptance remain necessary.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-planning-execution">Planning, execution, and write-back</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Bingsheng Ru; practice discussed by Wei Wang and Pylon Peng</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/action-2026-08-06/">First Action workshop</a> (<time datetime="2026-08-06">2026-08-06</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS organized legality, dependency, authority, conflict, and economy checks into a compilation step before execution.</dd></div>
<div><dt>Current standing</dt><dd>Workshop concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/action-2026-08-06/">First Action workshop</a> (<time datetime="2026-08-06">2026-08-06</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-06">2026-08-06</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-plan-compilation">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
