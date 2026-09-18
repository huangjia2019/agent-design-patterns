<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/">Pattern catalog</a><span style="margin: 0 0.45rem;">/</span>Cross-cutting plane<span style="margin: 0 0.45rem;">/</span>X1</p>

<header class="publication-head">
<p class="publication-series">ADPS Cross-cutting Engineering Plane Specification</p>
<h1>X1 · Observability</h1>
<p class="publication-deck">Join events, causality, versions, state deltas, and external outcomes into runtime evidence.</p>
</header>

**Events, causality, versions, and external outcomes** anchor X1. Events preserve atomic facts; causality connects calls across agents and tools; versions identify the components that actually ran; external outcomes confirm whether the real system changed. Without all four, runtime records are weak evidence for diagnosis, evaluation, or accountability.

X1 joins normalized events, causal identity, version references, state deltas, and external receipts into evidence that can be queried, evaluated, and attributed.

## Position

Observability spans all seven cognitive functions, six execution topologies, and lifecycle stages. It does not occupy a matrix cell. G4 remains only as a legacy entry point; the current identifier is X1.

## From logs to evidence

<table><thead><tr><th>Observation surface</th><th>Facts to retain</th><th>Use</th></tr></thead><tbody>
<tr><td>Input and context</td><td>Source, version, admission, and discard reason</td><td>Reconstruct what the agent could see</td></tr>
<tr><td>Decision and plan</td><td>Goal, steps, routing, candidates, and verdict summary</td><td>Locate drift, routing, and planning faults</td></tr>
<tr><td>Action and control</td><td>Tool, argument provenance, identity, policy, approval, and quota</td><td>Audit and call-level attribution</td></tr>
<tr><td>State and outcome</td><td>State delta, external receipt, business acceptance, and human correction</td><td>Separate real effects from false success</td></tr>
<tr><td>Runtime foundation</td><td>Model, prompt, skill, knowledge, tool, and policy versions</td><td>Version comparison and regression diagnosis</td></tr>
</tbody></table>

Structured decision summaries, candidates, citations, tool calls, and state transitions are suitable runtime evidence. Retaining hidden reasoning is unstable and enlarges the sensitive-data surface.

## Causality and identity

```
principal → agent → workload → session → run → intent
          → approval → model/tool/sub-agent span → resource → outcome
```

Trace Context propagates across processes, while business objects still require stable identifiers. A retry may create a new span; it must not create a new business intent or duplicate a side effect.

## Evidence across the lifecycle

<table><thead><tr><th>Stage</th><th>Evidence focus</th></tr></thead><tbody>
<tr><td>Register and design</td><td>Owner, capability version, event contract, sensitive fields, retention</td></tr>
<tr><td>Evaluate and shadow</td><td>Cases, trajectories, version diffs, denial, and rollback reasons</td></tr>
<tr><td>Operate</td><td>Call chain, state change, external outcome, latency, cost, policy verdict</td></tr>
<tr><td>Revalidate and evolve</td><td>Failure clusters, change predictions, regressions, promotion, demotion, retirement</td></tr>
</tbody></table>

## Failure modes

- Large volumes of text without object IDs, versions, or state deltas;
- treating HTTP 200 or exit code 0 as business success;
- broken causality across agents, queues, and callbacks;
- sampling biased toward simple tasks;
- unbounded retention of sensitive prompts and credentials;
- mixing X2 evaluation judgements with X1 observed facts.

## Verification

Check trace continuity, identity and version completeness, external confirmation for side effects, orphan writes, evidence latency, sampling bias, and access to sensitive evidence. Test cross-process calls, retries, resume, model fallback, schema upgrades, and collector failure.

## Public implementation

The [DeerFlow Guardrail](https://adpsagent.com/cases/deerflow-guardrail/) case follows a public code path across identity, authorization verdicts, RunJournal, and tool execution. Integrators still supply business state deltas and external outcomes.

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>Suggested citation:</strong> ADPS, <em>X1 · Observability</em>, ADPS Cross-cutting Engineering Plane Specification v0.5, 20 August 2026.</p>
<p><a href="https://adpsagent.com/topics/observability-driven-evolution/">Observability topic</a> · <a href="https://adpsagent.com/workshops/governance-2026-08-18/">Governance workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>Scope:</strong> This page defines engineering scope and interfaces; it does not certify products. Attributed practices remain governed by their case pages and public code.</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-20">2026-08-20</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-x1-observability">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
