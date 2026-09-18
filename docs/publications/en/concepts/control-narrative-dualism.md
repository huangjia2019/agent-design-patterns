<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Control and Narrative Planes</h1><p class="publication-deck">Separate model-readable context from bounded values that drive the runtime.</p>
</header>

![Control and narrative planes in an execution agent](../../assets/images/concepts/control-narrative-dualism.png)

## Application context

A payroll agent receives “create the Singapore payroll group from last month’s template.” The model can interpret the request and explain the intended result. The runtime still needs a finite route, exact tenant and template identifiers, approval state, and a deterministic branch for failure. Free-form language and program control serve different consumers.

## Definition

The narrative plane contains model-readable goals, observations, explanations, and summaries. The control plane contains bounded values that select program branches: intent enums, node states, policy decisions, approval status, retry state, and error codes. Narrative helps the model reason. Control determines what the runtime is allowed to do next.

## Engineering mechanism

<table><thead><tr><th>Plane</th><th>Typical data</th><th>Writer</th><th>Consumer</th></tr></thead><tbody><tr><td>Narrative</td><td>Goal, evidence summary, current explanation</td><td>Model and application</td><td>Model, reviewer, UI</td></tr><tr><td>Control</td><td><code>task_type</code>, node state, approval decision, reason code</td><td>Typed program logic or policy engine</td><td>Router, scheduler, guardrail</td></tr></tbody></table>

The model may propose a control value, but a parser validates it against a finite schema and maps invalid output to an explicit fallback. Tool responses enter mechanical state before a narrative summary is produced.

## Boundary

This separation does not remove language from execution. It prevents prose from becoming the sole authority for routing, approval, and recovery. Content-only work can use a thinner control plane; external writes require explicit control values and recorded transitions.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-system-boundaries">System boundaries and state</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS named the separation between program control signals and model-readable narrative, then stated its boundary.</dd></div>
<div><dt>Current standing</dt><dd>ADPS restatement</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-control-narrative-dualism">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
