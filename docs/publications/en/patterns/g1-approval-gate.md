<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/">Pattern matrix</a><span style="margin: 0 0.45rem;">/</span>White paper<span style="margin: 0 0.45rem;">/</span>G1</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>G1 · Approval Gate</h1>
<p class="publication-deck">Bind approval to an immutable execution intent, then revalidate identity, arguments, resources, policy, and business state before action.</p>
</header>

Approval Gate runs before a high-risk action becomes effective. Its input is a concrete intent made of an immutable tool version, canonical arguments, resource scope, delegated identity, and business preconditions.

## Coordinate and boundary

**Governance × Route.** The same tool can reach deny, allow, or ask according to principal, arguments, environment, impact, and reversibility. Action generation belongs to the Action module; G2 bounds impact after admission.

## Three records

<table><thead><tr><th>Record</th><th>Contents</th><th>Constraint</th></tr></thead><tbody>
<tr><td><strong>Intent</strong></td><td>Agent ID, run, tool digest, arguments, resources, policy version, preconditions</td><td>A material change creates a new intent</td></tr>
<tr><td><strong>Approval</strong></td><td>Reviewer, decision, basis, expiry, use count, intent digest</td><td>One decision refers to one explicit object</td></tr>
<tr><td><strong>Execution</strong></td><td>Revalidation, idempotency, actual call, state delta, external receipt</td><td>Proves execution matches approval</td></tr>
</tbody></table>

<pre><code class="language-yaml">intent:
  tool_digest: sha256:4ef...
  parameters_ref: artifact://intent/int_01/params
  resource_scope: {tenant: tenant_42, max_records: 20}
  policy_version: payroll-v12
  preconditions: {ledger_version: 417}
approval:
  intent_digest: sha256:93a...
  expires_at: 2026-08-19T09:30:00Z
  max_uses: 1
execution:
  idempotency_key: payrun-2026-08-batch-17
</code></pre>

Canonicalize arguments before hashing. Field order, defaults, time zones, and numeric precision otherwise make identity comparison unreliable.

## Ordered decisions

1. Deterministic rules handle hard denial, explicit admission, and mandatory review.
2. A model classifier adds context and rationale but does not issue authority.
3. A policy engine joins identity, arguments, resources, and environment into a structured verdict.

Conflict order is part of policy. A high-risk path normally stops when policy or review is unavailable.

## Pause and resume

```
DRAFT → EVALUATING → DENIED
                  ↘ ALLOWED → EXECUTING → CONSUMED
                  ↘ PENDING → APPROVED → REVALIDATING → EXECUTING
                                      ↘ EXPIRED / INVALIDATED
```

Resume checks the intent digest, tool and policy versions, expiry, single-use state, and material preconditions. The domain decides which changes invalidate approval.

## Running example

A payroll agent prepares an 18-person batch. Policy finds a changed payee account and shows the account diff, total, source ledger, and reason. Another amount changes during review. The old approval is invalidated, a replacement intent is reviewed, and the new approval is consumed atomically. The payment receipt and state delta complete Execution.

## Failure and verification

Common failures include approving only a tool name or prose summary, omitting expiry and single use, allowing model risk scores to issue authority, bypassing the gate on retry or resume, and hiding parameter or resource differences from reviewers.

Test tampering, policy change, expiry, concurrent consumption, duplicate callbacks, precondition change, and review-service failure. Monitor approved-versus-executed digest equality, stale-approval rejection, high-risk bypass, and unnecessary low-risk review.

## Related specifications

[G2](https://adpsagent.com/patterns/g2-blast-radius-control/) bounds impact; [G3](https://adpsagent.com/patterns/g3-progressive-commitment/) supplies capability autonomy; [X1](https://adpsagent.com/patterns/x1-observability/) links the three records; [G5](https://adpsagent.com/patterns/g5-hooks-pipeline/) enforces pre-call and resume checks.

<!-- RELATED-CASE-DEERFLOW:START -->

<section aria-labelledby="related-deerflow-case" class="related-case-band">
<p class="related-case-label">Related open-source engineering case</p>
<h2 id="related-deerflow-case"><a href="https://adpsagent.com/cases/deerflow-guardrail/">DeerFlow: From Pre-Call Interception to Two-Layer Authorization</a></h2>
<p>The Guardrail evolution shared by Willem Jiang uses five public pull requests to connect assembly filtering, runtime authorization, identity, policy, and audit in one tool-execution path.</p>
</section>

<!-- RELATED-CASE-DEERFLOW:END -->

<div class="document-citation">
<p><strong>Suggested citation:</strong>ADPS, <em>G1 · Approval Gate</em>, Agent Design Pattern White Paper v0.4, 19 August 2026.</p>
<p><a href="https://adpsagent.com/patterns/">Pattern catalog</a> · <a href="https://adpsagent.com/workshops/governance-2026-08-18/">Governance workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>Scope:</strong>Public review draft. Definitions and classifications are open for discussion and citation; running examples explain mechanisms, while attributed practice appears in the case library.</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-g1-approval-gate">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
