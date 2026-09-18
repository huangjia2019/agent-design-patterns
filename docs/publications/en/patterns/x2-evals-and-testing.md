<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/">Pattern catalog</a><span style="margin: 0 0.45rem;">/</span>Cross-cutting plane<span style="margin: 0 0.45rem;">/</span>X2</p>

<header class="publication-head">
<p class="publication-series">ADPS Cross-cutting Engineering Plane Specification</p>
<h1>X2 · Evaluation &amp; Validation</h1>
<p class="publication-deck">Use repeatable cases, graders, regression, and external acceptance to govern capability evidence.</p>
</header>

**Cases, graders, regression, and acceptance** form X2's capability evidence. Cases define tasks and boundaries, graders make criteria repeatable, regression protects established behavior, and external acceptance checks the result in the real system.

X2 governs evidence that a capability works. It joins deterministic tests, behavioral evals, external acceptance, and production feedback into release and revalidation decisions.

## Scope

The system under test may be a model, prompt, tool, skill, router, workflow, governance policy, or complete agent system. Each object requires its own cases, environment, graders, and release gate.

<table><thead><tr><th>Evidence</th><th>Decision supported</th></tr></thead><tbody>
<tr><td>External facts and business receipts</td><td>Whether the real target state was reached</td></tr>
<tr><td>Schema, rule, state-machine, and idempotency assertions</td><td>Whether deterministic contracts hold</td></tr>
<tr><td>Trajectories, sandboxes, and fault injection</td><td>Whether execution, recovery, and authority boundaries hold</td></tr>
<tr><td>Calibrated model graders</td><td>Semantic quality that resists hard rules</td></tr>
<tr><td>Expert or user review</td><td>Ambiguous criteria and high-risk release decisions</td></tr>
</tbody></table>

## Eval Contract

<pre><code class="language-yaml">eval_id: payroll-change-regression-v3
system_under_test: payroll-agent@v8
task: change_one_allowance
environment: payroll-sandbox@2026.08
allowed_authority: no_production_write
required_outcomes: [receipt_matches_after_read]
forbidden_outcomes: [modify_unrelated_employee]
graders: [schema_contract, ledger_probe]
trials: 5
release_gate: all_required_cases_pass
evidence: artifacts/evals/payroll-v3/</code></pre>

## Lifecycle

Design defines capability cases and negative cases. Pre-release runs capability and regression sets. Shadow operation compares candidates with the current version. Production failures become replayable cases. Model, tool, policy, or data changes trigger re-certification. G3 authority changes consume X2 evidence rather than a single demonstration.

## Boundary with X1 and X3

X1 records what happened. X2 judges the result against a contract. X3 limits what the grader and candidate system may read or change. Editing the agent and grader together, or letting a candidate rewrite its own release gate, destroys independence.

## Failure modes

- Testing the final text while ignoring external state;
- treating one stochastic success as stable capability;
- positive cases without refusal, overreach, recovery, or unknown input;
- one golden trajectory that rejects alternative correct paths;
- a composite score without sample-level failures and trajectories;
- uncalibrated graders whose score changes cannot be explained.

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>Suggested citation:</strong> ADPS, <em>X2 · Evaluation &amp; Validation</em>, ADPS Cross-cutting Engineering Plane Specification v0.5, 20 August 2026.</p>
<p><a href="https://adpsagent.com/topics/agent-evals-and-testing/">Agent evaluation and validation topic</a> · <a href="https://adpsagent.com/workshops/reflection-2026-08-12/">Reflection workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>Scope:</strong> This page defines engineering scope and interfaces; it does not certify products. Attributed practices remain governed by their case pages and public code.</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-20">2026-08-20</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-x2-evals-and-testing">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
