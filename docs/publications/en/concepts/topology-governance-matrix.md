<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Topology Governance Matrix</h1><p class="publication-deck">Review serial, parallel, and routed structures across identity, authority, safeguards, and provenance.</p></header>

## Application context: parallel branches do not say who may see what

A lead distributes 800 résumés across workers for parallel verification. The runtime graph explains sharding and gathering, but not whose identity each worker represents, which fields it may read, whether it may write back, or how the gatherer traces each conclusion. If every worker inherits the lead's long-lived token, parallelism copies maximum authority into every branch.

## Definition

The Topology Governance Matrix crosses runtime structures such as serial, parallel, and routing with four controls: identity, authority, safeguards, and provenance. The topology shows how control unfolds; the four controls determine whether that structure is ready for production.

## Engineering mechanism

<table><thead><tr><th>Structure</th><th>Additional questions</th></tr></thead><tbody><tr><td>Serial</td><td>Whom does each hop represent, which temporary authority is reclaimed, and where does a bad result stop?</td></tr><tr><td>Parallel</td><td>Are shards isolated, is gathering read-only by default, and how do child spans join one trace?</td></tr><tr><td>Routing</td><td>Is the route decision recorded, do risky routes receive tighter authority, and what handles unknown classes?</td></tr></tbody></table>

Effective authority usually intersects user delegation, task scope, agent role, tool capability, and resource boundary. The same fields should appear in design review, deployment checks, and incident analysis.

## Boundary

The matrix is a review instrument, not a replacement for IAM, policy enforcement, or observability. It exposes the common gap where a graph is complete but its production controls are not.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-collaboration-runtime">Collaboration and runtime control</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Dong Zhang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS edited the four-layer identity, authority, safeguard, and provenance checklist for public use.</dd></div>
<div><dt>Current standing</dt><dd>Workshop concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-topology-governance-matrix">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
