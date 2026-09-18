<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Hook Composition</h1><p class="publication-deck">Compose orchestration, governance, observation, and recovery at lifecycle events.</p></header>

## Application context: one hook label can hide four responsibilities

A team starts a coding agent after requirements close, pauses before a dangerous tool call, records a trace after execution, and saves a checkpoint on failure. All four can be implemented as hooks, yet they belong to orchestration, governance, observation, and recovery. When callbacks are scattered across configuration and plugins, the real control flow disappears from the main design.

## Definition

Hook Composition treats deterministic trigger points as an ordered, stateful control chain. Each hook declares its event, condition, read and write set, priority, idempotency key, failure semantics, and emitted event. The composition layer resolves order and conflicts.

## Engineering mechanism

<table><thead><tr><th>Duty</th><th>Example</th><th>Failure semantics</th></tr></thead><tbody><tr><td>Orchestration</td><td>Start coding after specification acceptance</td><td>Do not create the same job twice</td></tr><tr><td>Governance</td><td>Wait for approval before production write</td><td>Block and preserve a resume point</td></tr><tr><td>Observation</td><td>Record request, verdict, and receipt</td><td>Block or degrade according to risk</td></tr><tr><td>Recovery</td><td>Checkpoint and release leases</td><td>Retry idempotently</td></tr></tbody></table>

The composition manifest should produce a readable control graph and enter version control and regression testing.

## Boundary

A hook is a mechanism, not automatically a collaboration topology. If one hook manager invokes participants under a complete plan, the design remains orchestration. Choreography requires control to reside in the local rules of event participants.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-collaboration-runtime">Collaboration and runtime control</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial problem and practice: Wei Wang; classification formalized by ADPS</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS separated orchestration, governance, observation, and recovery duties and added ordering, idempotency, and failure semantics.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-hook-composition">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
