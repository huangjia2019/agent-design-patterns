<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>F4</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>F4 · Self-Heal Loop</h1>
<p class="publication-deck">Use a bounded diagnose-repair-verify loop for deterministic failures inside an approved repair domain.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reflection × Loop (cyclic)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium-high (diagnosis, isolated repair, full verification, rollback, and hand-off)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reflection patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Use a bounded diagnose-repair-verify loop for deterministic failures inside an approved repair domain.</td>
</tr>
</tbody>
</table>

---

## Problem

Failing tests, lint errors, broken builds, and red CI runs provide clear criteria for automated repair. Missing dependencies, misplaced configuration, and local logic errors often follow repeatable diagnostic paths. Engineers still define the allowed scope, release authority, and hand-off path; an agent can perform the repeated diagnosis and verification inside those limits.

Self-Heal Loop turns failure signals into a bounded repair sequence: diagnose the cause → generate a fix → apply it → verify the result. A failed fix starts another bounded attempt or hands the case to a person. Coding agents and internal repair systems provide practical examples, but reported production results still need primary-source review and local reproduction.

## Classification: Reflection × Loop

- **Vertical axis · Reflection**: The pattern consumes an explicit failure signal, diagnoses a bounded cause, proposes a repair, and evaluates the changed artifact.
- **Horizontal axis · Loop**: Verification determines the next transition: accept, rollback, retry within budget, or hand off. Every attempt retains the original failure, diagnosis, diff, and new result.

## Solution and mechanics

A production Self-Heal Loop uses six stages plus three stop controls: Test Fail → Diagnose → Generate Fix → Critic → Atomic Apply → Verify. A failed verification rolls back the current attempt before retry or hand-off.

Before repair, classify the failure and check the permitted change scope:

<table>
<thead>
<tr>
<th style="text-align: left;">Failure class</th>
<th style="text-align: left;">Typical signal</th>
<th style="text-align: left;">Default response</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Runtime</td>
<td style="text-align: left;">Timeout, dependency error, resource pressure</td>
<td style="text-align: left;">Retry, switch, or degrade within policy</td>
</tr>
<tr>
<td style="text-align: left;">Process</td>
<td style="text-align: left;">Wrong tool order, bad arguments, omitted step</td>
<td style="text-align: left;">Revise the current plan or call</td>
</tr>
<tr>
<td style="text-align: left;">Business</td>
<td style="text-align: left;">Conflicting rules, missing domain knowledge, unmet approval condition</td>
<td style="text-align: left;">Request evidence or hand off; do not infer missing policy</td>
</tr>
<tr>
<td style="text-align: left;">Experience</td>
<td style="text-align: left;">Correct result with excessive wait, weak explanation, broken interaction</td>
<td style="text-align: left;">Feed product and workflow improvement</td>
</tr>
</tbody>
</table>

Each class maps to `change_scope` and `release_authority`. Editing a temporary artifact, rerunning a sandbox task, and changing a production rule are different permissions. If the required change exceeds authority, the loop stops and hands over the evidence.

Three controls bound the repair loop:

1. **`max_iterations` hard circuit break**: cap repair attempts according to task risk and local evaluation. This limits repeated fixes that keep moving the failure.
2. **independent critic verifier**: use an independently configured reviewer to inspect the fix. A different model family may reduce shared blind spots, but independence also depends on prompts, evidence, and trace separation. Place verification at the risk points that matter to the workflow.
3. **stability check via signature**: compare failure signatures to distinguish progress from a switch to a new problem, and define regression rules for severity, affected scope, performance, security, and coverage.

A layered cascade such as format → lint → build → test runs cheap signals first and reserves expensive checks for changes that pass the earlier gates. The exact layers should match the repository's toolchain.

## Online repair and offline release

Online repair suits low-risk, reversible changes with immediate verification, such as correcting arguments in a sandbox, regenerating a temporary artifact, or opening a reviewable pull request. Changes to shared rules, skills, prompts, routing, and production configuration enter an offline process for grouped analysis, replay, impact review, approval, and versioned release. A local incident should not silently become a global policy.

## Applicability

- **Domains with explicit acceptance signals, such as code, tests, and CI**: Examples include lint fixes, CI repair, and diagnosis of failing tests.
- **Coding-agent repair paths**: Lint, build, test, and CI failures provide structured signals for diagnosis, bounded changes, and deterministic reruns.
- **Engineering pipelines with layered acceptance signals**: self-heal works best when CI exposes distinct formatter, lint, build, and test failures. Each signal should map to a bounded repair action and a deterministic rerun.

## Known failure modes

- **No reliable acceptance signal**: Writing and design may need rubric-based Generator-Critic review instead of automated repair. High-impact changes such as production schema migration require approval and a controlled deployment path.
- **Failure drift**: Without a stability check, the agent fixes one error and introduces another. Use failure-signature comparison, regression detection, and `max_iterations` together.
- **Regression cascade**: Changes from several attempts accumulate without a rollback boundary. Isolate each attempt, record its diff, and restore a known state before the next diagnosis.
- **False recovery**: The repair weakens a test or acceptance rule instead of fixing the defect. Review changes to checks separately and enforce coverage and policy constraints.
- **Repairing without the missing knowledge**: A model cannot recover an absent business rule, domain fact, or goal definition from a failure signal. Request evidence or hand off to the responsible owner.
- **Wrong diagnosis**: Similar failure signatures may have different causes. Preserve original evidence, diagnosis confidence, and alternative hypotheses; high-risk cases need independent review.
- **Writing durable assets without authority**: A runtime fix directly changes a shared skill, prompt, or production configuration. Durable changes require offline evaluation, approval, versioning, and rollback.
- **No owner after budget exhaustion**: A failed loop needs an accountable queue, evidence packet, rollback state, and response target based on severity.

## Verification and metrics

- **Self-heal success rate**: the proportion of repair attempts that pass the complete validation suite without human intervention. Compare it with the same task set under manual or non-repair baselines.
- **Repair attempts to convergence**: record how many attempts successful and failed cases consume. Set the circuit breaker from observed risk, cost, and marginal gain.
- **Regression rate**: the proportion of repairs that introduce a new failure or weaken an existing check. Define regression across correctness, security, performance, scope, and coverage.
- **HITL queue latency**: measure how long a bottomed-out case waits for human handling. The target follows the operational severity and service commitment of the system.
- **Misdiagnosis rate**: Review sampled cases against the final resolution and separate failed repair from an incorrect initial diagnosis.
- **Authority block and hand-off completeness**: Track whether the loop stops when `change_scope` is exceeded and whether the hand-off includes evidence, attempted changes, diff, and rollback state.

## Reference implementation

```
for i in range(MAX_ITERATIONS):           # configured from task risk and evaluation
                diagnosis = diagnose(current_failure)
                if diagnosis.required_scope > change_authority:
                    return handoff("insufficient_authority", evidence, diagnosis)
                fix = generate_fix(diagnosis)         # modify only files in the diagnosis
                critique = independent_critic(fix)    # configured with separate evidence and review duties
                if critique.block:
                    return "blocked_by_critic"        # hand off to HITL
                commit = atomic_apply(fix)            # per-iteration atomic commit
                new_failure = verify()                # format/lint/build/test four-tier cascade
                if new_failure is None:
                    return "fixed"
                if is_regression(current_failure, new_failure):   # business-defined regression rules
                    rollback(all applied commits)
                    return "rolled_back_regression"
                current_failure = new_failure
            return "max_iterations_human_handoff"     # bottomed out, hand off to human review
```

The Critic should be independent enough to challenge the repair. Regression rules come from the repository and business domain. Each attempt stays isolated so rollback restores a known state. Durable changes to shared assets and production configuration do not ship directly from the online loop.

## Illustrative scenario

Consider a CI repair agent whose first version applies every proposed fix directly, with no independent critic, rollback boundary, or stability check. A failing test can turn into a different error, and later attempts may touch unrelated code while the system still reports that it is making progress. A stronger version places a hard cap on attempts, compares failure signatures, reviews each proposed change independently, runs layered validation, and isolates every attempt for rollback. Cases that do not converge enter an owned human-review queue with the trace and diff attached. Evaluate this design by full-suite acceptance, regression, rollback, and handoff evidence; production outcome claims require an attributed incident record.

## Related patterns

- **Generator-Critic (F1)**: Generator-Critic improves a usable output through a linear review chain; replay is optional. Self-Heal starts from a verified failure and requires a bounded repair loop. Their stop conditions, rollback requirements, and change scope therefore differ.
- **Adversarial Review (C3)**: C3 can provide an independent repair reviewer when separation of duties or stronger challenge is required.
- **Iterative Hypothesis Testing (R4)**: R4 maintains competing diagnoses and evidence. F4 applies a bounded change and verifies whether it repaired the explicit failure.
- **Guardrail Sandwich (A4)**: A4 enforces change scope, permissions, and post-action checks around repair actions.

## Engineering judgment

Self-Heal Loop applies when failure is explicit, repair is verifiable, rollback is available, and the change falls within delegated authority. Missing evidence, irreversible impact, or a wider change scope requires human handling.

## Further reading

- [Reflection module: Make feedback change the system](https://adpsagent.com/patterns/reflection/)
- [First Reflection workshop, 12 August 2026](https://adpsagent.com/workshops/reflection-2026-08-12/)
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>F4 Self-Heal Loop</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-f4-self-heal-loop">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
