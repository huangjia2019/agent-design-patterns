<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Scratchpad Board: A Short-Lived Work Surface for an Agent</h1><p class="publication-deck">Store the current goal, step, observation, blocker, evidence, and next action in a small working surface.</p>
</header>

## Start with a long-running task

After dozens of turns, the current goal, accepted plan, latest observations, blockers, and next action are scattered across the conversation. Resuming the task requires reconstructing the working state from a growing transcript. A scratchpad board keeps the small set of information that is still active in one short-lived work surface.

## Definition

A scratchpad board records the current goal, accepted plan, current step, recent observations, blockers, evidence references, and next action for one running task. The model and the orchestrator can read it. Each field has an owner. At the end of the task, the board is compacted, archived, or discarded.

<pre><code class="language-text">ScratchpadBoard = {
  goal,
  accepted_plan,
  current_step,
  recent_observations,
  blockers,
  evidence_refs,
  next_action,
  revision
}
</code></pre>

Thought, Action, and Observation may appear as trace fields. Tool receipts, business identifiers, and approval decisions remain in their authoritative fact stores.

## Boundary

Use the board while the task is still exploratory and the next action depends on recent observations. Once dependencies stabilize, move strict ordering into a task DAG, mechanical parameters into the mechanical state plane, and cross-task lessons into long-term memory.

## Provenance

- Initial case: Dongfang Yiteng execution agent, contributed by Bo Liang.
- Lineage: the HEARSAY-II blackboard, ReAct traces, CoALA working memory, task boards, and checkpoints.
- ADPS contribution: a shared and inspectable work surface with structured fields, write ownership, and a lifecycle.
- Definition status: ADPS restatement.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-context-memory">Context and memory</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS restated the short-lived reasoning trace as a shared work surface for the model, runtime, and reviewer.</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-scratchpad">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
