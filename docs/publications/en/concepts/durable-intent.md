<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Durable Intent</h1><p class="publication-deck">Keep approval wait and resumed execution bound to the same immutable action.</p></header>

## Application context: the action shown to an approver may change before resume

An approver accepts “change employee E-1842's transport allowance from 800 to 1000 next month.” The agent resumes hours later after employee status, current value, policy version, or tool version has changed. A Boolean approved flag cannot prove that the eventual commit is the action that was reviewed.

## Definition

Durable Intent is a canonical action record that remains stable across waiting, retry, and resume. It pins the principal, target resource, desired change, tool and argument versions, risk, preconditions, and recovery policy. Approval binds to this intent digest rather than to a conversation that may continue changing.

## Engineering mechanism

The system stores Intent, Approval, and Execution separately. Approval binds the intent hash, approver, expiry, and consumption count. Resume rereads mutable state: whether the employee remains active, whether the value is still 800, and whether the policy still applies. Failed preconditions invalidate the approval and require review or termination.

## Boundary

A read-only request with no wait point usually needs no durable intent. Approval, asynchronous queues, external retry, and irreversible writes do. Intent cannot freeze the external world, so revalidation on resume is part of the concept rather than an optional check.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Yibo Xu</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/governance-2026-08-18/">First Governance workshop</a> (<time datetime="2026-08-18">2026-08-18</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS connected Durable Intent to G1 Approval Gate and organized Intent, Approval, and Execution as three records.</dd></div>
<div><dt>Current standing</dt><dd>Workshop concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/governance-2026-08-18/">First Governance workshop</a> (<time datetime="2026-08-18">2026-08-18</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-18">2026-08-18</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-durable-intent">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
