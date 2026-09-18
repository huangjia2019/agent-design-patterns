<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Three Collaboration Planes</h1><p class="publication-deck">Review Agent-Agent, Human-Agent, and Human-Human collaboration around the system.</p></header>

## Application context: agents can hand off successfully while the team forgets

A requirements agent hands a specification to a coding agent, which hands a patch to a reviewer. The machine chain looks complete. Meanwhile, product, architecture, and test staff decide in a meeting not to change the public schema and to add a compatibility layer in the next release. If that decision remains only in chat, a later agent may propose the rejected path again.

## Definition

Agent systems contain at least three collaboration planes. Agent-Agent covers decomposition, parallel work, hand-off, and review. Human-Agent covers intent, missing evidence, approval, takeover, and acceptance. Human-Human carries team decisions, continuing responsibility, and organizational rules. The third plane occurs between people but directly changes what later agents should decide.

## Engineering mechanism

Versioned artifacts connect the planes. Agents use a Handoff Contract. Human clarification, approval, and takeover become resumable runtime events. Team decisions that affect later work enter an RFC, ADR, runbook, or project rule with source and scope. Raw meetings need not be copied wholesale; capture decisions that change goals, constraints, authority, or acceptance.

## Boundary

The planes are not three separate systems. They are a completeness check for collaboration designs that otherwise omit people and organizations. Short, low-risk work can use lightweight records; long-running, multi-person work needs one evidence chain across all three.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-collaboration-runtime">Collaboration and runtime control</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Wei Wang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS organized Agent-Agent, Human-Agent, and Human-Human relations around the agent environment into one design view.</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-three-collaboration-planes">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
