<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Capability Certification Lifecycle: How a Capability Earns Automatic Execution Rights</h1><p class="publication-deck">Grant automatic execution rights only to a tested capability version and scope.</p>
</header>

## Start with a generated pipeline

A coding agent has produced a new publishing pipeline. That output should not begin receiving production tasks immediately. The team must run a complete example, inspect the delivered result, and explicitly grant an operating boundary.

## Definition

A capability certification lifecycle defines how a generated or modified capability gains, retains, and loses the right to run automatically.

<pre><code class="language-text">draft -&gt; candidate -&gt; active
</code></pre>

A complete evidence run moves the capability to `candidate`. Human certification moves it to `active`. A change in code, templates, or critical rules invalidates the old evidence and returns the capability to a review state.

## Boundary

Lifecycle states must control real routing permissions, not serve as display labels. Certification is tied to a specific version, test set, evidence record, and declared scope. High-risk capabilities also require authorization, blast-radius limits, and rollback.

## Provenance

- Initial case: Xuanxu Technology GIS publishing agent, contributed by Yuke Xiong.
- Lineage: artifact registries, staging-to-production promotion, model registries, and progressive delivery.
- ADPS contribution: applies promotion and invalidation to pipelines, skills, tool wrappers, and agent subflows, with explicit automatic execution rights.
- Definition status: candidate concept.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Yuke Xiong</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu GIS publishing-agent case</a> (<time datetime="2026-07-30">2026-07-30</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS extended certification to pipelines, skills, tool wrappers, and subflows, with explicit automatic execution rights.</dd></div>
<div><dt>Current standing</dt><dd>Candidate concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Initial source:</strong> <a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu Technology GIS publishing-agent case</a>; contributed by Yuke Xiong.</p><p><a href="https://adpsagent.com/concepts/">Concept registry</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu GIS publishing-agent case</a> (<time datetime="2026-07-30">2026-07-30</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-07-30">2026-07-30</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-capability-certification-lifecycle">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
