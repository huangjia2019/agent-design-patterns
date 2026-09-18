<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Unified Convergence Node</h1><p class="publication-deck">Resolve several reasoning branches into one actionable result under shared evidence and adjudication rules.</p></header>

## Application context

A contract review can inspect payment terms, data compliance, and delivery risk in parallel. Each branch may be locally correct while the branches disagree on whether signing should proceed. If they pass prose directly downstream, the execution layer must improvise which conclusion takes priority.

## Definition

A Unified Convergence Node receives candidate conclusions, evidence references, unresolved items, and versions from several reasoning branches. It applies shared criteria to conflicts and emits one explicit state: accept a conclusion, merge compatible parts, request more evidence, or escalate. The node also names the owner of final adjudication.

```
convergence:
  candidates: [payment_review, compliance_review, delivery_review]
  required_evidence: []
  comparison_rules: []
  hard_conflicts: []
  decision: accept | request_evidence | escalate
  decision_owner: ...
```

## Engineering use

Each branch emits the same typed artifact with a `branch_id`, conclusion, evidence references, unresolved questions, and generating version. Deterministic checks handle missing evidence, prohibited conditions, and version conflicts. A model reviewer compares semantics. Consequential or unresolved conflicts go to a named owner. The trace retains every candidate and the final disposition rather than only the merged answer.

## Boundary with parallel exploration and fan-out/gather

R3 Parallel Exploration creates independent candidates. C2 Fan-Out/Gather distributes and collects work. The convergence node compares and adjudicates the returned candidates. Collection proves that results arrived; it does not resolve their conflict. Calling a stronger model again does not supply evidence priority or decision ownership by itself.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-collaboration-runtime">Collaboration and runtime control</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Dong Zhang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/reasoning-2026-08-26/">First Reasoning workshop</a> (<time datetime="2026-08-26">2026-08-26</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS organized candidates, evidence, conflict handling, and final adjudication from several reasoning branches into one interface.</dd></div>
<div><dt>Current standing</dt><dd>Reasoning-module concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/concepts/">Concept catalogue</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/reasoning-2026-08-26/">First Reasoning workshop</a> (<time datetime="2026-08-26">2026-08-26</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-unified-convergence-node">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
