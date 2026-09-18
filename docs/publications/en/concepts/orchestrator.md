<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Responsibility Boundary Between the Orchestrator and MessageHandler</h1><p class="publication-deck">Keep control flow in the orchestrator and input/output presentation in the facade.</p>
</header>

<p style="color: var(--color-text-muted); font-size: 1.05rem; margin: -0.4rem 0 1.6rem;">From the Dongfang Yiteng execution agent (case contributed by Bo Liang)</p>

![Responsibility boundary between the Orchestrator and MessageHandler](../../assets/images/concepts/en/orchestrator.png)

## Application context: a browser reconnect must preserve task semantics

A user starts payroll configuration from a web interface and receives progress over SSE. If the page refreshes or the network reconnects, the backend task should continue from its prior state while the new connection replays visible events. When an input handler also owns the task graph, tool calls, and recovery, changing the transport can change execution behavior.

Runtime control should remain independent of Web, CLI, and messaging transports. The outer component handles protocol and presentation. The Orchestrator handles the task lifecycle.

## Definition

The Orchestrator manages runtime control flow for a session. It consumes control signals, invokes reasoning, memory, retrieval, and action modules, and transfers control between them.

The MessageHandler is an outer facade. It receives user messages, calls the Orchestrator, subscribes to activity events, and streams progress and results to the interface through protocols such as SSE.

## Engineering mechanism

<table>
<thead>
<tr>
<th style="text-align: left;">Component</th>
<th style="text-align: left;">Responsible for</th>
<th style="text-align: left;">Excludes</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Orchestrator</td>
<td style="text-align: left;">Routing, capability orchestration, mode transitions, and completion decisions</td>
<td style="text-align: left;">UI rendering and typewriter effects</td>
</tr>
<tr>
<td style="text-align: left;">MessageHandler</td>
<td style="text-align: left;">Input adaptation, event subscription, and streaming output</td>
<td style="text-align: left;">Reasoning decisions and business scheduling</td>
</tr>
</tbody>
</table>

The Orchestrator publishes Activity events with a stable schema and no dependency on a particular frontend. The MessageHandler converts those events into SSE messages. Dongfang Yiteng implements the publish-subscribe path with Go goroutines and channels.

The intent gateway sits inside or below the Orchestrator. It consumes control signals such as `chat`, `analyze`, `resolve`, and `unknown`, then selects an execution path. Session entry is the `pre` stage, capability orchestration is `middle`, and response synthesis is `post`.

## Case usage

A payroll-group request enters intent classification during `pre`. The `middle` stage performs template matching, snapshot creation, and import. The `post` stage synthesizes the result. Each step emits events; the MessageHandler only presents them on the Web timeline.

Adding an action capability requires registering the capability and its control signals. Changing the Web presentation does not change orchestration logic.

## Adoption conditions

Separate the Orchestrator from the input/output facade when an agent contains several capabilities, selects execution paths from control signals, and exposes the same run through different interfaces or protocols. See [Intent as Compilation](https://adpsagent.com/concepts/intent-as-compilation/) and [Control and Narrative Planes](https://adpsagent.com/concepts/control-narrative-dualism/) for the source of those control signals.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-system-boundaries">System boundaries and state</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS used the Facade, Mediator, and workflow-engine lineage to state the boundary between I/O adaptation and control.</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-orchestrator">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
