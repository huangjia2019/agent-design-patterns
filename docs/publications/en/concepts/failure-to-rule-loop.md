<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Failure-to-Rule Loop: Make an Incident Change the Next Run</h1><p class="publication-deck">Require every repeated failure to change a rule, test, template, or capability asset.</p>
</header>

## Start with a template collision

A viewer template used Python `string.Template` while its JavaScript contained `${...}`. Python interpreted the JavaScript placeholders, producing blank legends or a generation error. Writing “template issue” in a retrospective would not prevent the next generated pipeline from repeating the failure.

## Definition

A failure-to-rule loop requires an incident record to produce a verifiable system change. The record holds the symptom, signature, root cause, immediate handling, prevention action, and source. The prevention action points to a rule, default, template constraint, test, or generated capability asset.

<pre><code class="language-text">runtime failure -&gt; structured incident card -&gt; review -&gt; rule or asset change
        ^                                            |
        +------------ verify on a later case --------+
</code></pre>

The loop ends when later behavior changes, not when the document is finished.

## Boundary

Repeated, enumerable, testable failures are good candidates for rules. Open failures may remain under human judgment or offline analysis. A model may draft a card, but an unverified root-cause guess must not become a runtime rule.

## Provenance

- Initial case: Xuanxu Technology GIS publishing agent, contributed by Yuke Xiong.
- Lineage: SRE postmortems, corrective actions, failure journals, and regression tests.
- ADPS contribution: every incident action links back into runtime rules or capability assets and is tested on a later run.
- Definition status: candidate concept.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Yuke Xiong</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu GIS publishing-agent case</a> (<time datetime="2026-07-30">2026-07-30</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS requires a failure record to change a rule, test, default, or capability asset and then verify non-recurrence.</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-failure-to-rule-loop">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
