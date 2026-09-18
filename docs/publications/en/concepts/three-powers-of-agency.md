<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Three Powers of Agency</h1><p class="publication-deck">Inspect agent power at the points of information, judgement, and action.</p></header>

## Application context: an agent gains two powers before it calls a tool

A payment-agent review often starts with access to the transfer API. Risk begins earlier. Retrieval decides which payee records enter context. Evaluation rules decide what may be declared correct. Tool authority then turns that judgement into a transfer. These three entry points affect decisions, verdicts, and the external world.

## Definition

Three powers can be reviewed separately:

- **Information power**: which information may enter context and influence a decision;
- **Judgement power**: which rule, reviewer, or external evidence may certify a result;
- **Action power**: which identity and authority may change files, records, accounts, or other resources.

Different components may hold each power. A retriever controls information admission, an evaluator or approver controls judgement, and a tool gateway controls action. A tool allowlist cannot substitute for reviewing all three.

## Engineering use

In a payroll change, the policy store supplies versioned evidence but cannot mutate employee data. An evaluator checks policy compliance but cannot issue business authority. The executor consumes only an approved Intent whose preconditions still hold. One faulty component therefore cannot interpret the rule, certify compliance, and commit the change on its own.

## Boundary

The concept supports threat modelling, separation of duties, and architecture review. It does not require a separate service for each power. It does require the design to locate each power, state its basis and owner, and preserve evidence of change.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Jia Huang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/governance-2026-08-18/">First Governance workshop</a> (<time datetime="2026-08-18">2026-08-18</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS separates the power to influence decisions, judge results, and change the external world.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module architecture concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/concepts/">Concept catalogue</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/governance-2026-08-18/">First Governance workshop</a> (<time datetime="2026-08-18">2026-08-18</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-18">2026-08-18</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-three-powers-of-agency">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
