<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Anchor, Ledger, Collection</h1><p class="publication-deck">Preserve the goal, append task facts, and project only the material needed now.</p>
</header>

![Anchor, ledger, and collection structures for narrative state](../../assets/images/concepts/anchor-ledger-collection.png)

## Application context

A payroll setup task moves through policy confirmation, group creation, employee association, approval, and submission. Late in the run, the newest conversation may focus on one employee. That detail must not replace the original delivery goal or erase earlier milestones.

## Definition

- **Anchor** preserves the original goal, non-goals, acceptance conditions, and stable constraints;
- **Ledger** appends milestones, decisions, blockers, evidence references, and supersession events;
- **Collection** projects the Anchor and relevant Ledger entries into the current read view.

## Engineering mechanism

The Anchor changes only through an explicit revision event. Ledger entries are append-only and carry source, author, time, scope, and links to artifacts. A Collection query selects entries for the current step and records which filters and versions were used. Full source material remains outside the prompt and is loaded through references when needed.

## Boundary

These structures manage task narrative, not authoritative business state. Current balances, approval status, identifiers, and tool receipts remain in the mechanical state plane. Cross-task experience belongs in a separate memory lifecycle.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-context-memory">Context and memory</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS separated the original goal, append-only facts, and current read view by lifetime.</dd></div>
<div><dt>Current standing</dt><dd>Case-derived name</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-anchor-ledger-collection">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
