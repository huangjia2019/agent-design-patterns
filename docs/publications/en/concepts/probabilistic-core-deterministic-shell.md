<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Probabilistic Core, Deterministic Shell</h1><p class="publication-deck">Models handle open judgement; deterministic mechanisms protect production boundaries.</p></header>

## Application context: a model may infer intent, but a transfer cannot be approximately correct

A user describes a complex payment in natural language. A model is useful for extracting the goal, finding missing information, and proposing steps. Payee identity, amount precision, account state, delegated limit, and idempotent commit require repeatable decisions and reviewable evidence.

## Definition

The probabilistic core handles open-ended interpretation, planning, and candidate generation. The deterministic shell handles identity, state, authority, constraints, tests, commit, and external receipts. The core proposes an action; the shell decides whether it qualifies for execution and verifies whether the external world changed.

## Engineering mechanism

```
natural-language goal
  → model produces a structured Intent
  → schema / policy / state / authority checks
  → controlled tool call
  → receipt and after-read
  → trace and later evaluation
```

The shell does not require a fully hard-coded flow. A model may still choose candidate tools and steps dynamically, but only from versioned capabilities and under repeatable pre- and post-conditions.

## Boundary

Low-risk content work can use a thinner shell. Tasks that affect money, data, authority, production configuration, or user rights need a thicker one. Deterministic mechanisms can also fail, so policies, schemas, and validators require their own versions, tests, and observations.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-system-boundaries">System boundaries and state</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Engineering observation: Dong Zhang; shell formulation: Jia Huang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS connected open model judgement to deterministic controls over identity, state, authority, tests, and external receipts.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module architecture concept</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-probabilistic-core-deterministic-shell">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
