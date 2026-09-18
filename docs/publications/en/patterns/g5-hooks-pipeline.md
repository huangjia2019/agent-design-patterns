<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/">Pattern matrix</a><span style="margin: 0 0.45rem;">/</span>White paper<span style="margin: 0 0.45rem;">/</span>G5</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>G5 · Hooks Pipeline</h1>
<p class="publication-deck">Run ordered, testable deterministic controls at unavoidable lifecycle points.</p>
</header>

Hooks Pipeline places deterministic authorization, argument, quota, format, and audit rules at a small set of unavoidable execution points. It avoids executable boundaries in prompts and inconsistent if statements across handlers.

## v0.4 classification

**Extension pattern · Deterministic enforcement mechanism.** The pipeline is ordered internally but spans the agent lifecycle and does not occupy a core matrix cell.

## Four layers

<table><thead><tr><th>Layer</th><th>Responsibility</th><th>Examples</th></tr></thead><tbody>
<tr><td>Policy Source</td><td>Store domain rules and configuration</td><td>RBAC provider, policy store, tenant config</td></tr>
<tr><td>Decision</td><td>Evaluate identity, arguments, resources, environment</td><td>allow, deny, ask, reason, obligation</td></tr>
<tr><td>Enforcement</td><td>Apply the verdict at an unavoidable point</td><td>middleware, hook, gateway, sandbox</td></tr>
<tr><td>Evidence</td><td>Record input, versions, rules, result</td><td>audit event, trace, RunJournal</td></tr>
</tbody></table>

A hook is an enforcement point. Hard-coding all policy there blocks domain evolution; using a model inside the hook to issue authority removes determinism.

## Lifecycle points

<table><thead><tr><th>Point</th><th>Controls</th></tr></thead><tbody>
<tr><td>Assembly</td><td>Tool filtering, skill admission, credentials, version pinning</td></tr>
<tr><td>Input</td><td>Schema, source, tenant, sensitivity, injection marker</td></tr>
<tr><td>Pre-tool</td><td>Identity, arguments, resource, quota, approval, preconditions</td></tr>
<tr><td>Pre-commit</td><td>Fresh state, idempotency, single use, transaction condition</td></tr>
<tr><td>Post-tool</td><td>Schema, state delta, sensitive output, external receipt</td></tr>
<tr><td>End, resume, retire</td><td>Acceptance, checkpoint, intent revalidation, resource recovery</td></tr>
</tbody></table>

## Assembly and runtime

```
task needs
  ∩ tool groups
  ∩ agent/subagent allow-deny
  ∩ active skill policy
  ∩ principal authorization
  = model-visible tools

visible tool + arguments + resource + environment + quota + approval
  → runtime verdict
```

Assembly narrows model choice; invocation handles arguments, resources, and changing state. Neither substitutes for the other.

## Public DeerFlow evolution

[Five public DeerFlow pull requests](https://adpsagent.com/cases/deerflow-guardrail/) add pre-tool middleware, a trusted Principal, RunJournal, an independent RBAC provider, and two-layer authorization. Tests cover sync and async paths plus lead agents, subagents, and embedded clients.

The public implementation covers allow/deny PRE guards. Human ask, durable intent, and general POST business verification remain integration work.

## Failure semantics and verification

Define order, verdict conflicts, timeout and exception defaults, sync/async equivalence, audit failure, and retry semantics. High-risk authorization usually fails closed; low-risk telemetry may buffer and continue.

Look for prompt-only rules, bypass entries, protected-field mutation, POST replacing PRE, policy and enforcement in one function, fail-open dependencies, and retried non-idempotent hooks. Verify all agent and client paths, zero handler calls after deny, stable order, and contract tests for every reason and fault branch.

## Workshop revision, 25 August 2026: Boundary of Hook Composition

Hooks can perform orchestration, governance, observation, and recovery. G5 retains its historical identifier and focuses on deterministic governance enforcement. Cross-module composition is documented separately; no C7 is added.

[Collaboration workshop record](https://adpsagent.com/workshops/collaboration-2026-08-25/)

<div class="document-citation">
<p><strong>Suggested citation:</strong>ADPS, <em>G5 · Hooks Pipeline</em>, Agent Design Pattern White Paper v0.4, 19 August 2026.</p>
<p><a href="https://adpsagent.com/patterns/">Pattern catalog</a> · <a href="https://adpsagent.com/workshops/governance-2026-08-18/">Governance workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>Scope:</strong>Public review draft. Definitions and classifications are open for discussion and citation; running examples explain mechanisms, while attributed practice appears in the case library.</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-07-18">2026-07-18</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-g5-hooks-pipeline">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
