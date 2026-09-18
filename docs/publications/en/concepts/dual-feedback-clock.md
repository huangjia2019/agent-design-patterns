<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Dual Feedback Clock</h1><p class="publication-deck">Separate immediate within-run feedback from delayed cross-run outcomes.</p></header>

## Application context: a correct response now can still fail in the business days later

A support agent gives an answer consistent with the knowledge base and passes immediate review. Three days later, the customer returns because the issue was not resolved. A coding agent may pass unit tests and expose a compatibility defect only in integration or real adoption. The two outcomes arrive on different schedules.

## Definition

The Dual Feedback Clock records immediate and delayed feedback separately for one task. Immediate feedback comes from format checks, rules, tests, tool receipts, and rapid human review. Delayed feedback comes from downstream processes, repeat contact, business measures, incidents, or long-term use. Both contribute to the final judgement.

## Engineering mechanism

Completion creates an outcome key linked to the agent, prompt, tool, knowledge, and policy versions. Immediate evidence may close the current step while the task remains traceable through a delayed window. Later outcomes link back through the key and enter replay, evaluation sets, or rule revision. Uncertain attribution is recorded rather than silently assigned.

## Boundary

A short transaction with a decisive external receipt does not need an artificial delay. Recommendations, support, code changes, and business decisions often do. Adoption and clicks provide evidence, but they do not automatically prove correctness.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Li Jiaqi; name formalized by ADPS</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/reflection-2026-08-12/">First Reflection workshop</a> (<time datetime="2026-08-12">2026-08-12</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS named the separation between immediate results and delayed business outcomes across teams and runs as two feedback clocks.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/reflection-2026-08-12/">First Reflection workshop</a> (<time datetime="2026-08-12">2026-08-12</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-12">2026-08-12</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-dual-feedback-clock">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
