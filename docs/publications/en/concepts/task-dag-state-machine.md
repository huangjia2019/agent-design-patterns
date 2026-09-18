<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Task DAG and State Machine</h1><p class="publication-deck">Make dependencies, node status, acceptance, and recovery explicit.</p>
</header>

![Task DAG and node state machine](../../assets/images/concepts/task-dag-state-machine.png)

## Application context

Payroll setup must create a snapshot before importing a template, associate employees only after the payroll group exists, and roll back when import fails. Describing this order in a Skill leaves the model responsible for remembering every dependency during execution.

## Definition

The task DAG stores dependency edges. The node state machine stores lifecycle transitions such as `pending`, `ready`, `running`, `waiting`, `completed`, `failed`, and `compensating`. A node becomes schedulable only when its dependencies and preconditions hold.

## Engineering mechanism

The Planner creates typed nodes with inputs, outputs, resource keys, authority, acceptance, retry, and compensation. The Executor claims a ready node through a lease. The Verifier records acceptance evidence before completion. Every transition is conditional and persisted; recovery reconstructs runnable nodes from the graph and external receipts rather than replaying conversation.

## Boundary

A short, reversible sequence can remain a prompt chain or ReAct loop. Strict dependencies, parallel branches, approval waits, rollback, and cross-session recovery justify a DAG and state machine. The graph controls execution order; it does not decide whether the original business goal was correct.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-planning-execution">Planning, execution, and write-back</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS placed dependency, acceptance, and recovery in one agent task contract.</dd></div>
<div><dt>Current standing</dt><dd>Agent adaptation of established terms</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-task-dag-state-machine">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
