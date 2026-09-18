<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/">Pattern matrix</a><span style="margin: 0 0.45rem;">/</span>White paper<span style="margin: 0 0.45rem;">/</span>G2</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>G2 · Blast-Radius Control</h1>
<p class="publication-deck">Use hard limits and a dynamic autonomy envelope to bound action, run, and fleet impact.</p>
</header>

Blast-Radius Control assumes that approval, models, and tools will fail and defines how many resources, how much budget, and how much downstream propagation one error may cause.

## Coordinate and boundary

**Governance × Hierarchy.** Identity bounds capability, capability bounds resources, and resources remain inside quantity, rate, time, cost, concurrency, and network limits. Layers add value only when credentials, processes, and configuration paths are genuinely independent.

## Hard and autonomy envelopes

<table><thead><tr><th>Envelope</th><th>Contents</th><th>Change authority</th></tr></thead><tbody>
<tr><td><strong>Hard</strong></td><td>Tenant isolation, production credential, absolute amount, forbidden tool and data class</td><td>Independent control plane or explicit human process</td></tr>
<tr><td><strong>Autonomy</strong></td><td>Batch, rate, object set, tools, concurrency, automation tier</td><td>Policy may adjust it inside hard limits</td></tr>
</tbody></table>

```
effective_scope = intersect(
    hard_envelope,
    principal_scope,
    task_scope,
    capability_scope,
    current_context_scope,
    evidence_based_scope
)
```

Delegation may preserve or narrow scope, never widen it.

## Aggregate dimensions

Quantity, rate, cost, and concurrency cannot be measured only per tool. Ten child agents below a local cap can still break the run total. Aggregate at the appropriate action, run, principal, tenant, and fleet levels.

<table><thead><tr><th>Dimension</th><th>Examples</th></tr></thead><tbody>
<tr><td>Resource and data</td><td>Tenant, account, environment, object set, field, purpose</td></tr>
<tr><td>Quantity and rate</td><td>Per action, batch, run, tenant, and time window</td></tr>
<tr><td>Cost and time</td><td>Tokens, cloud resources, purchases, credential and run duration</td></tr>
<tr><td>Concurrency and propagation</td><td>Child count, depth, concurrent writes, recipients</td></tr>
<tr><td>Recovery</td><td>Dry run, delayed commit, checkpoint, idempotency, compensation, breaker</td></tr>
</tbody></table>

## Running example

An approved 18-person payroll batch remains limited to one tenant, 20 rows per action, 40 per run, one concurrent write, the intent amount ceiling, and a harder infrastructure ceiling. A duplicate retry meets both idempotency and run-level limits; another tenant fails resource scope.

## Multi-agent execution

A central orchestrator can aggregate directly. Choreography requires shared run, principal, delegation, and remaining-budget references. Local limits expand under fan-out, retry, and loops, so child count, delegation depth, and cross-domain propagation also need caps.

## Failure and verification

Common failures include treating sandboxing as the business boundary, replacing aggregate limits with per-tool limits, allowing the agent to change hard limits, sharing authority with the kill switch, bypassing controls on retry and resume, and discovering an irreversible violation only after execution.

Inject faults to measure worst-case objects, amount, cost, and propagation. Exercise stop latency, aggregation under retry and fan-out, and the agent's inability to modify limiters, breakers, and evidence.

<!-- RELATED-CASE-DEERFLOW:START -->

<section aria-labelledby="related-deerflow-case" class="related-case-band">
<p class="related-case-label">Related open-source engineering case</p>
<h2 id="related-deerflow-case"><a href="https://adpsagent.com/cases/deerflow-guardrail/">DeerFlow: From Pre-Call Interception to Two-Layer Authorization</a></h2>
<p>The Guardrail evolution shared by Willem Jiang uses five public pull requests to connect assembly filtering, runtime authorization, identity, policy, and audit in one tool-execution path.</p>
</section>

<!-- RELATED-CASE-DEERFLOW:END -->

<div class="document-citation">
<p><strong>Suggested citation:</strong>ADPS, <em>G2 · Blast-Radius Control</em>, Agent Design Pattern White Paper v0.4, 19 August 2026.</p>
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
<p><a href="https://adpsagent.com/chronicle/#patterns-g2-blast-radius-control">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
