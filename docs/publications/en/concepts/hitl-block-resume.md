<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>HITL Block and Resume</h1><p class="publication-deck">Persist a protected execution point, revalidate it, and resume the same action after review.</p>
</header>

![Human approval that blocks and resumes one execution](../../assets/images/concepts/hitl-block-resume.png)

## Application context

A payroll agent prepares a payment batch and reaches a protected commit node. Approval may arrive hours later. Ending the conversation and starting a new request would lose the exact plan node, action digest, parameter versions, and already completed side effects.

## Definition

HITL Block and Resume represents human review as a durable runtime state. The task moves to `waiting_for_approval`, persists its checkpoint and Intent, then resumes the same node after a decision and precondition check.

## Engineering mechanism

The approval request carries action summary, affected resources, risk, evidence, intent hash, expiry, and allowed decisions. Approval is append-only and single-use unless policy says otherwise. Resume reacquires leases, refreshes mutable state, confirms tool and policy versions, and checks idempotency before commit. Rejection, expiry, or changed preconditions follows an explicit transition.

## Boundary

Narrative confirmation can continue a low-risk conversation. Runtime blocking is needed when the system must preserve execution identity across a wait point. Approval does not replace post-action verification or compensation.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS treated approval as durable runtime state and added revalidation before resume.</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-hitl-block-resume">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
