<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Context Contract</h1><p class="publication-deck">Specify what information may enter a task context, with source, freshness, and budget.</p></header>

## Application context: loading an entire repository can still omit the decisive information

A coding agent receives dozens of source files but does not know why the change is needed, which interfaces must remain stable, or which checks define success. Another receives only “fix login” without logs or reproduction steps. One has too much undirected material; the other lacks mandatory evidence.

## Definition

A Context Contract specifies what a task must know before it starts, what may be loaded on demand, source precedence, and acceptance material. A useful structure covers Why (goal and business reason), What (objects, scope, and non-goals), How (constraints, interfaces, and available capabilities), and Acceptance (tests, receipts, or human judgement).

## Engineering mechanism

P1 information is mandatory before execution, such as the target object, authority scope, and interfaces that may not break; absence triggers clarification. P2 information is loaded per step, such as neighbouring code, past decisions, and domain material. Retrieval may supply P2 items, but each retains source, version, and scope. The contract is versioned, and the trace records which entries were actually loaded.

## Boundary

A Context Contract does not collect everything up front. It controls the boundary through mandatory and on-demand information. Open exploration can use a broad Why and acceptance definition; operations that write external state require tighter goals, authority, and mechanical state.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-context-memory">Context and memory</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial question: Jia Huang; engineering practice: Xianglong Huang; name formalized by ADPS</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/perception-2026-08-13/">First Perception workshop</a> (<time datetime="2026-08-13">2026-08-13</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS organized Why, What, How, acceptance material, and P1/P2 information boundaries into a testable contract.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/perception-2026-08-13/">First Perception workshop</a> (<time datetime="2026-08-13">2026-08-13</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-context-contract">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
