<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Execution vs Content Agents</h1><p class="publication-deck">Choose runtime controls from the deliverable, state dependency, and cost of failure.</p>
</header>

![Design differences between execution and content agents](../../assets/images/concepts/execution-vs-content.png)

## Application context

The same model can draft a payroll-policy note and create a payroll group. The first task delivers text that a user can revise or regenerate. The second changes employee, payroll, and approval records; one misbound identifier can affect later steps and external systems.

## Definition

Classify an agent by the object it delivers and the consequence of failure.

<table><thead><tr><th>Class</th><th>Primary deliverable</th><th>State between steps</th><th>Typical controls</th></tr></thead><tbody><tr><td>Content agent</td><td>Report, answer, slide, draft</td><td>Mostly text and cited material</td><td>Review, citation checks, regeneration</td></tr><tr><td>Execution agent</td><td>Completed business change</td><td>Identifiers, statuses, versions, approvals, receipts</td><td>State machine, idempotency, authority, rollback, external acceptance</td></tr></tbody></table>

## Engineering mechanism

In expense processing, invoice upload must receive the `application_id` returned by the preceding create call. The runtime stores that value with tenant, source call, tool version, and timestamp, then injects it into the next request. The model can select the business route and explain the result; it does not regenerate the identifier from conversation text.

## Boundary

Many systems contain both classes. Research may produce a draft before an approved action changes a record. Apply stronger execution controls at the point where state, money, authority, production configuration, or user rights can change.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-system-boundaries">System boundaries and state</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS turned delivery object, state dependency, and failure consequence into an architecture-selection test.</dd></div>
<div><dt>Current standing</dt><dd>Candidate concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Initial source:</strong> <a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng Execution Agent case report</a>; contributed by Bo Liang.</p><p><a href="https://adpsagent.com/concepts/">Concept registry</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-execution-vs-content">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
