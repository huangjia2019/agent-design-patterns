<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Topology Lowering</h1><p class="publication-deck">Compile high-level collaboration semantics into runtime primitives such as serial, parallel, and routing edges.</p></header>

## Application context: a design graph and a runtime graph answer different questions

A code-review team may be designed around an accountable lead, several scanning workers, an independent reviewer, and a final adjudicator. In a workflow framework, that design may reduce to routing, parallel nodes, a gather step, and a conditional loop. If only the runtime graph survives, the team later cannot explain which edge represented delegation, who owned the final verdict, or who had to close a failure.

## Definition

Topology Lowering compiles high-level collaboration designs such as hierarchical delegation, adversarial review, and hand-off chains into serial, parallel, routing, and loop primitives supported by the runtime. The representation changes; role, responsibility, authority, and acceptance semantics do not disappear.

## Engineering mechanism

The design node records `pattern`, `role`, `owner`, `authority`, and `acceptance`. Runtime nodes retain references to those fields, and traces identify the design decision from which each node was lowered. A hierarchy can therefore execute as route, parallel workers, and gather while the lead and workers retain different authority. An adversarial review can execute as a conditional loop without collapsing generation, review, and adjudication into one role.

## Boundary

Use lowering when the runtime vocabulary is smaller than the design language. It does not prove that every collaboration pattern is merely one of three low-level edge types. The same graph can carry different responsibility structures, so review the design graph, compilation mapping, and runtime evidence together.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-collaboration-runtime">Collaboration and runtime control</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Engineering observation: Dong Zhang; name formalized by ADPS</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>Dong Zhang identified serial, parallel, and routing as common runtime primitives; ADPS added rules for preserving higher-level responsibility semantics.</dd></div>
<div><dt>Current standing</dt><dd>Module-level method concept</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-topology-lowering">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
