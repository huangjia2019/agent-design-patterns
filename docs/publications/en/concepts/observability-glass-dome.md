<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Activity Events and Timeline</h1><p class="publication-deck">Record model, tool, state, latency, cost, and external results on one execution timeline.</p>
</header>

![Agent activity events and execution timeline](../../assets/images/concepts/observability-glass-dome.png)

## Application context

A user reports that an agent selected the wrong template and stopped at approval. A platform trace shows model latency and tool spans, while the business reviewer needs the interpreted intent, route decision, parameter source, approval state, and external result on one timeline.

## Definition

Activity Events provide a semantic execution record for one task. An Activity identifies a meaningful stage such as intent classification, planning, tool execution, approval, or verification. Frames within the Activity record model calls, tool calls, state transitions, duration, cost, evidence references, and visible output.

## Engineering mechanism

Events share `run_id`, `activity_id`, causation, principal, component version, and redaction policy. The UI can show a business timeline while engineers open detailed frames under role-based access. Checkpoints and external receipts link to the same event chain, allowing replay and failure attribution.

## Boundary

Provider traces remain useful for model and tool diagnostics. Activity Events add domain meaning and state transitions; they do not require prompts or private reasoning to be visible to every operator. Retention and detail follow risk, privacy, and audit policy.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS organized model, tool, state, latency, and cost events on one timeline.</dd></div>
<div><dt>Current standing</dt><dd>Case-derived name</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-observability-glass-dome">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
