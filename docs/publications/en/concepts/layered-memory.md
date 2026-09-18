<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Layered Memory L1/L2/L3</h1><p class="publication-deck">Separate current input, task facts, and reviewed cross-task experience.</p>
</header>

![Layered memory L1, L2, and L3](../../assets/images/concepts/layered-memory.png)

## Application context

An agent needs current user input on every turn, task facts throughout one run, and selected lessons across later runs. Applying one retention and loading rule to all three either loses useful history or fills every prompt with stale material.

## Definition

<table><thead><tr><th>Layer</th><th>Scope</th><th>Examples</th><th>Loading rule</th></tr></thead><tbody><tr><td>L1</td><td>Current turn or step</td><td>Message, observation, temporary scratchpad</td><td>Loaded directly; discarded or promoted after the step</td></tr><tr><td>L2</td><td>Current task or session</td><td>Milestones, decisions, evidence, artifacts</td><td>Selected by task and step; retained through recovery</td></tr><tr><td>L3</td><td>Across tasks</td><td>Reviewed preferences, lessons, procedures</td><td>Retrieved by scope and task signature; source facts loaded on demand</td></tr></tbody></table>

## Engineering mechanism

Promotion is explicit. An L1 observation becomes L2 only when it changes progress, evidence, or a decision. An L2 lesson becomes L3 after source review, scope assignment, conflict checks, and publication. L3 summaries keep references to L2 facts so the runtime can load the full record when a decision requires detail.

## Boundary

The three labels are functional tiers, not required databases. A deployment may use files, relational tables, object storage, and indexes together. Fast-changing control state remains outside memory even when it is referenced from a task record.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-context-memory">Context and memory</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS added loading and reference rules for current input, task facts, and cross-task experience.</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-layered-memory">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
