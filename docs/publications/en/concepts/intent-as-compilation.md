<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Intent as Compilation</h1><p class="publication-deck">Translate open language into a validated, bounded control signal with an explicit fallback.</p>
</header>

![Compilation from natural language to a bounded control signal](../../assets/images/concepts/intent-as-compilation.png)

## Application context

“Help me configure payroll” may mean a question, an analysis request, or an instruction to change the system. Sending all three into one open ReAct loop exposes unnecessary tools and makes approval boundaries unclear.

## Definition

Intent as Compilation translates open language into a bounded control representation. The output contains a finite task class, extracted entities, confidence or ambiguity, required clarification, and the next permitted route. Invalid output becomes `unknown`; it does not fall through to a privileged default.

## Engineering mechanism

<pre><code class="language-text">message
  → classifier and entity extraction
  → schema validation
  → {task_type, entities, ambiguity, evidence_refs}
  → route policy
  → chat | analyse | resolve | clarify | reject</code></pre>

The vocabulary is derived from downstream capabilities. A new enum is added only when the runtime has a distinct contract, authority set, and acceptance path for it. The original message remains available as narrative evidence.

## Boundary

The compiled intent is a routing signal, not proof that the user’s goal has been fully understood. Complex or high-risk work still requires a Context Contract, plan checks, and confirmation of the action before execution.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-planning-execution">Planning, execution, and write-back</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS restated the language entry point as a compiler front end with bounded enums and an unknown fallback.</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-intent-as-compilation">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
