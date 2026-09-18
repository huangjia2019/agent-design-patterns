<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/">Pattern catalog</a><span style="margin: 0 0.45rem;">/</span>Cross-cutting plane<span style="margin: 0 0.45rem;">/</span>X3</p>

<header class="publication-head">
<p class="publication-series">ADPS Cross-cutting Engineering Plane Specification</p>
<h1>X3 · Security &amp; Identity</h1>
<p class="publication-deck">Propagate identity across delegation and constrain each run with least privilege and short-lived credentials.</p>
</header>

**Principals, delegation, credentials, and resource boundaries** form the X3 control line. The principal identifies who acts, delegation records whom it represents and what it may do, credentials enforce the verdict externally, and resource boundaries constrain the objects, environments, and time windows that authority can reach.

X3 propagates identity across users, agents, workloads, runs, tools, and resources, then bounds delegation, authorization, and credentials to a concrete capability and environment.

## Identity chain

```
principal → tenant → agent version → workload → session/run
          → intent → approval → short-lived credential → resource
```

Each hop records who represents whom, which action is allowed, which resource is in scope, and when authority expires. A shared service account identifies a process; it does not prove the user, agent version, or delegation chain behind a request.

## Engineering responsibilities

<table><thead><tr><th>Responsibility</th><th>Question</th><th>Artifact</th></tr></thead><tbody>
<tr><td>Identity</td><td>Which principal, tenant, and agent version is active?</td><td>Principal, workload identity, run identity</td></tr>
<tr><td>Delegation</td><td>What may the downstream agent do on behalf of the upstream principal?</td><td>Capability, resource, environment, expiry, non-delegation</td></tr>
<tr><td>Authorization</td><td>Should this concrete intent be allowed, denied, or reviewed?</td><td>Allow / deny / ask verdict and reason</td></tr>
<tr><td>Credential</td><td>How is the verdict enforced by an external system?</td><td>Short-lived, narrow, revocable credential</td></tr>
</tbody></table>

## Policy, decision, enforcement, and evidence

A policy source owns rules. A decision service evaluates a structured request. G5 Hooks Pipeline enforces the verdict at unavoidable runtime points. X1 records the request, verdict, state delta, and external receipt. Combining all four in one handler entangles policy versions, runtime identity, and audit boundaries.

## Lifecycle

<table><thead><tr><th>Stage</th><th>Security and identity control</th></tr></thead><tbody>
<tr><td>Register</td><td>Record owner, capability, risk class, tenant, and accessible resources</td></tr>
<tr><td>Design and evaluate</td><td>Define least privilege; test overreach, refusal, credential leakage, and cross-tenant cases</td></tr>
<tr><td>Shadow</td><td>Use read-only or sandbox identity; constrain rate, amount, batch, and resource scope</td></tr>
<tr><td>Operate</td><td>Issue short-lived credentials per intent; revalidate preconditions after resume</td></tr>
<tr><td>Revalidate and retire</td><td>Narrow authority after anomalies or regression; revoke old versions and departed principals</td></tr>
</tbody></table>

## Relationship to Governance patterns

G1 binds approval to an intent. G2 sets the impact ceiling. G3 changes the long-term autonomy of a capability. G5 supplies deterministic enforcement points. X3 provides their common identity and authorization foundation while also covering perception data access, memory writes, sub-agent delegation, and publication of reflected assets.

## Failure modes

- All agents share one long-lived service account;
- a role written in a prompt is treated as permission;
- approval binds only a prose summary, not tool version, arguments, and resource;
- resume reuses expired credentials and stale preconditions;
- the user is logged but sub-agent, workload, and delegation identities disappear;
- an eval environment can read production secrets or alter release gates.

## Public path

The [DeerFlow Guardrail](https://adpsagent.com/cases/deerflow-guardrail/) case follows identity propagation, providers, decisions, and enforcement points in public code. The [Governance workshop](https://adpsagent.com/workshops/governance-2026-08-18/) records common questions around assembly-time filtering, runtime revalidation, short-lived credentials, and agent lifecycle.

<div class="document-citation">
<p><strong>Suggested citation:</strong> ADPS, <em>X3 · Security &amp; Identity</em>, ADPS Cross-cutting Engineering Plane Specification v0.5, 20 August 2026.</p>
<p><a href="https://adpsagent.com/cases/deerflow-guardrail/">DeerFlow Guardrail</a> · <a href="https://adpsagent.com/workshops/governance-2026-08-18/">Governance workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>Scope:</strong> This page defines engineering scope and interfaces; it does not certify products. Attributed practices remain governed by their case pages and public code.</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-20">2026-08-20</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-x3-security-and-identity">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
