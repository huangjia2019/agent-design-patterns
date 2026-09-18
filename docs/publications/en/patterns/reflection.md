<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>Reflection</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper · Module Overview</p>
<h1>Reflection Module: Turning Feedback into Controlled Change</h1>
<p class="publication-deck">Feedback evidence, online and offline loops, change authority, formal patterns, and open research questions.</p>
</header>

Reflection may happen after one output or after a batch of completed runs. It reads artifacts, trajectories, and external outcomes; compares them with inspectable criteria; decides whether to change the current output, execution path, or reusable assets; and then gathers new evidence to determine whether the change helped.

Asking a model to think again is the lightest implementation. Without evidence, a stopping rule, and a defined change boundary, another inference pass does not establish that the system improved.

## Four questions before adding a reflection loop

1. **What signal starts the review?** A failed test, a rule violation, user dissatisfaction, an expert label, or a model score?
2. **What evidence can decide quality?** Compilation, schemas, business rules, expert judgement, and user behaviour differ in reliability and arrival time.
3. **What may this loop change?** The current answer, plan, Skill, memory, business rule, or production code?
4. **How will the change be verified?** Re-running the original check, regression suites, controlled comparisons, human review, and business outcomes answer different questions.

If any of these questions has no answer, keep the loop in observation or recommendation mode.

## Observability, evaluation, reflection, and release

<table>
<thead>
<tr>
<th style="text-align: left;">Stage</th>
<th style="text-align: left;">Output</th>
<th style="text-align: left;">Effect on the system</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>Observability</strong></td>
<td style="text-align: left;">Traces, logs, tool calls, state changes, and cost</td>
<td style="text-align: left;">Records what happened</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Evaluation</strong></td>
<td style="text-align: left;">Pass/fail, scores, issue classes, and evidence</td>
<td style="text-align: left;">Judges an output or path against criteria</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Reflection</strong></td>
<td style="text-align: left;">A scoped, evidence-backed change proposal</td>
<td style="text-align: left;">Attempts to change an artifact, path, or reusable asset</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Release and governance</strong></td>
<td style="text-align: left;">Approval, version, canary, rollback, and accountability record</td>
<td style="text-align: left;">Decides whether the change receives durable authority</td>
</tr>
</tbody>
</table>

Evaluation produces a judgement. Reflection consumes that judgement and proposes or applies a change. When a change enters a shared Skill library, memory store, policy repository, or production environment, a governance gate owns the release decision.

## Two clocks: online and offline reflection

The ADPS Reflection workshop on 12 August 2026 reached the same boundary across several production settings: reflection runs on two clocks.

<table>
<thead>
<tr>
<th style="text-align: left;"></th>
<th style="text-align: left;"><strong>Online reflection</strong></th>
<th style="text-align: left;"><strong>Offline reflection</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Purpose</td>
<td style="text-align: left;">Complete the current task or stop it safely</td>
<td style="text-align: left;">Improve later runs and correct system-wide problems</td>
</tr>
<tr>
<td style="text-align: left;">Signals</td>
<td style="text-align: left;">Tests, rules, tool receipts, and structural checks available now</td>
<td style="text-align: left;">Batches of traces, bad cases, expert labels, user feedback, and delayed business outcomes</td>
</tr>
<tr>
<td style="text-align: left;">Scope</td>
<td style="text-align: left;">The current output and local path</td>
<td style="text-align: left;">Cross-run, cross-version, and cross-team behaviour</td>
</tr>
<tr>
<td style="text-align: left;">Change authority</td>
<td style="text-align: left;">Usually limited to the current output, parameters, or rollback-safe changes</td>
<td style="text-align: left;">May propose changes to Skills, memory, harnesses, datasets, and workflows; release still requires validation</td>
</tr>
<tr>
<td style="text-align: left;">Time budget</td>
<td style="text-align: left;">Milliseconds to minutes, with explicit iteration, latency, and token limits</td>
<td style="text-align: left;">Hours, days, or weeks, suitable for batch comparison and human participation</td>
</tr>
</tbody>
</table>

These are operating modes, not new pattern coordinates. F1 and F4 often run online, while their rubrics, failure classes, and stop thresholds need offline calibration. F2 loads Skills online but creates, tests, evaluates coexistence, and releases them mainly offline. F3 also spans both clocks: experience is distilled offline and replayed when a later task needs it.

## When the outcome arrives

The arrival time of the success signal determines the reflection clock.

<table>
<thead>
<tr>
<th style="text-align: left;">Success signal</th>
<th style="text-align: left;">Typical settings</th>
<th style="text-align: left;">Recommended loop</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Compilation, tests, schemas, deterministic tool receipts</td>
<td style="text-align: left;">Code, configuration, structured write-back</td>
<td style="text-align: left;">Online repair and re-verification can be appropriate for low-risk changes</td>
</tr>
<tr>
<td style="text-align: left;">Stable rules, reference sets, domain checkers</td>
<td style="text-align: left;">Policy interpretation, regulated content, domain queries</td>
<td style="text-align: left;">Online review may work when the rule version is pinned</td>
</tr>
<tr>
<td style="text-align: left;">User satisfaction, business metrics, downstream human edits</td>
<td style="text-align: left;">Support, operations, analytical recommendations</td>
<td style="text-align: left;">Collect outcomes and analyse them offline; do not manufacture an immediate ground truth</td>
</tr>
<tr>
<td style="text-align: left;">Long feedback chains across teams and systems</td>
<td style="text-align: left;">Requirements to release, recommendation to business action</td>
<td style="text-align: left;">Preserve delayed labels and use human attribution before changing the system</td>
</tr>
</tbody>
</table>

Open-ended work can still receive online checks for citations, structure, contradictions, and known risks. The final business-value judgement waits for the relevant outcome.

## The reflection contract

A production loop should express its control surface as data:

<pre><code class="language-yaml">reflection_id: ref_01K2...
scope: artifact              # artifact | trajectory | asset | system
trigger:
  type: test_failure
  ref: trace://run-8842/check-9
evidence:
  - type: deterministic_test
    ref: test://payroll/net-pay-balance
judge:
  policy: reflection-rubric-v4
proposal:
  target: src/payroll/net_pay.py
  allowed_change: diagnosed_files_only
authority:
  mode: auto_in_sandbox      # suggest | auto_in_sandbox | approval_required
budget:
  max_iterations: 3
  max_latency_ms: 90000
verification:
  suite: payroll-regression-v12
  rollback_on_regression: true
retention:
  disposition: candidate_lesson
</code></pre>

The full loop is **Trigger → Evidence pack → Diagnose → Change proposal → Policy gate → Apply → Verify → Record**. A model may diagnose and propose. Tests, rules, people, and business outcomes decide whether it may continue.

## How the four specifications divide the work

<table>
<thead>
<tr>
<th style="text-align: left;">Pattern</th>
<th style="text-align: left;">Primary change target</th>
<th style="text-align: left;">Feedback</th>
<th style="text-align: left;">Main boundary</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/patterns/f1-generator-critic/"><strong>F1 Generator-Critic</strong></a></td>
<td style="text-align: left;">Current artifact</td>
<td style="text-align: left;">Rules, references, expert rubrics, or an independent model</td>
<td style="text-align: left;">The critic must be evaluated; a score cannot replace evidence</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/patterns/f2-skill-package/"><strong>F2 Skill Package</strong></a></td>
<td style="text-align: left;">Reusable workflow and capability asset</td>
<td style="text-align: left;">Cross-run outcomes, failures, and coexistence tests</td>
<td style="text-align: left;">A Skill that passes alone may still degrade a larger Skill set</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/patterns/f3-experience-replay/"><strong>F3 Experience Replay</strong></a></td>
<td style="text-align: left;">Context supplied to a later task</td>
<td style="text-align: left;">Historical trajectories, outcomes, and delayed feedback</td>
<td style="text-align: left;">Preserve source, version scope, and uncertainty to avoid negative transfer</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/patterns/f4-self-heal-loop/"><strong>F4 Self-Heal Loop</strong></a></td>
<td style="text-align: left;">Rollback-safe state, configuration, or code</td>
<td style="text-align: left;">Deterministic failure and re-run evidence</td>
<td style="text-align: left;">Missing knowledge, changed business logic, and irreversible actions require escalation or an offline release</td>
</tr>
</tbody>
</table>

Online/offline, hard evidence/soft judgement, local/global scope, and feedback delay are selection parameters. They do not alter the cognitive-function × execution-topology framework.

## A four-layer production structure

The workshop distilled a four-layer implementation:

1. **Hard validation:** Compilation, tests, schemas, business invariants, and system receipts take priority.
2. **Reflection diagnosis:** Models inspect evidence and identify possible defects in outputs, trajectories, or assets.
3. **Memory and assets:** Candidate lessons, Skills, rules, and failure records cross task boundaries only after admission.
4. **Scheduling and control:** The harness decides whether to reflect, which reviewer to use, how many rounds to allow, and when to degrade or hand off.

Automatic triggering, termination, observability, and bounded cost apply to every production loop. Reuse needs a narrower rule: a one-run correction may be deliberately discarded; anything that will affect later runs requires admission, versioning, and retirement.

## Three problems that appear at scale

**Local patches can damage global efficiency.** An anonymized environment-building agent accumulated local fixes over time. Stability improved while the overall path became heavier. Offline reflection must detect duplicate, conflicting, and expired patches instead of appending every bad case to a prompt.

**Skills must be evaluated in combination.** Trigger accuracy and task success show that one Skill works alone. A growing library also needs false-trigger, missed-trigger, overlap, conflict, loading-cost, and coexistence tests.

**Attribution comes before healing.** Failures can be separated into runtime, execution-process, business-result, and experience classes. Invalid parameters, network instability, and missing steps may have direct remedies. Missing domain knowledge, changed business rules, and conflicting team goals cannot be filled in safely by the original agent.

## Implementation details from the workshop

**Dong Zhang moved rule changes through development, evaluation, and production environments.** A bad case first joins the evaluation set, from which a model may propose a candidate lesson or rule. The candidate passes a benchmark, then pre-production, before it receives production authority. The live path remains stable; new experience does not write directly into the rule set currently serving users.

**Mo Zhou separated the reflection runtime into hard validation, model diagnosis, memory retention, and scheduling control.** Compilation, interface regression, and business rules carry higher evidentiary weight. The model explains the failure and proposes a change. A reusable result passes admission before entering Memory or a Skill. The scheduler bounds iterations, tokens, and latency. The accompanying measures include repair success, no-improvement rounds, over-correction, reflection activation, and end-to-end delay.

**Pylon Peng's daily replay looks for required asset changes in trajectories.** When a Skill fails because a command parameter has been removed, the system first distinguishes agent misuse from a dependency-version change, then updates the operating instructions, tests, and applicable version. Candidate changes to Memory, Skills, or the Harness are accepted by executable checks such as an `evaluation.json`, rather than by substituting another unconstrained model judgment.

**Jiaqi Li used feedback arrival time to choose online or offline reflection.** Compilation, tests, and deployment logs can return during the current task and support immediate repair. The value of a business recommendation may appear only after an operational change and user response, days later. The system must retain the original version and trajectory for offline attribution. He also identified two scale problems: multiple Skills for one task need comparative and composition evaluation; a generator and critic using the same model can preserve the same blind spots. Cross-model review adds diversity, while rules, tests, and source data still decide the outcome.

## Engineering progress in 2026

By August 2026, major platforms expose the evaluation components that reflection depends on:

- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation) separates pre-release offline evaluation from online evaluation over production traces and feeds failures back into datasets. [AgentEvals](https://docs.langchain.com/oss/python/langchain/test/evals) evaluates tool-use trajectories directly.
- Anthropic's January 2026 guide, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), recommends combining code, model, and human graders. Its [enterprise Skills guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise) adds triggering, isolation, coexistence, instruction-following, and output-quality checks.
- OpenAI's [AgentKit](https://openai.com/index/introducing-agentkit/) brings trace grading, datasets, and graders into the agent optimisation workflow.

These systems first address seeing and judging. Reflection begins when a judgement becomes a controlled change and regression evidence confirms the result.

## Directions without new catalog numbers

**Meta-reflection** reviews the critic and its rubric. It currently fits as a high-risk F1 configuration rather than a separate pattern.

**Deliberative reflection** uses reviewers with different assumptions in a structured debate. It overlaps F1 Generator-Critic and C3 Adversarial Review, and still lacks stable stopping and cost evidence.

**Prospective reflection** checks plans, assumptions, and risk before action. Its responsibilities already appear across F1, A4 Guardrail Sandwich, and G1 Approval Gate. More independent practice is needed before cataloguing it separately.

## Questions for further industry evidence

- How can a large Skill estate separate agent quality, Skill quality, and combination effects?
- When dimensions in a rubric move in opposite directions, who owns the trade-off?
- Which reflections may change a harness automatically, and which may only open a change proposal?
- When outcomes arrive days or weeks later, how should the system preserve the original trajectory, version, and accountability chain?
- How can teams detect, consolidate, remove, or roll back conflicting patches accumulated by online loops?

## Workshop record

This overview incorporates the first ADPS Reflection Module Workshop held on 12 August 2026. Hosts: Haili Zhang and Jia Huang. Core workshop guests: Dong Zhang, Mo Zhou, Wei Wang, Qianchun Lu, Pylon Peng, and Jiaqi Li. Findings are grouped by theme; anonymized enterprise practice is not mapped point by point to an individual.

[Read the full workshop record](https://adpsagent.com/workshops/reflection-2026-08-12/) · [White Paper contributors](https://adpsagent.com/founders/#white-paper-contributors)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>Suggested citation:</strong> ADPS, <em>Reflection Module: Make Feedback Change the System</em>, Agent Design Pattern White Paper v0.3, 2026-08-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>Scope:</strong> This page describes the Reflection subsystem as a whole. The F1–F4 specifications remain authoritative for pattern-level mechanics and verification.</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/reflection-2026-08-12/">First Reflection Module Workshop</a> (12 August 2026); <a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents dynamic collaboration study</a></dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-12">2026-08-12</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-reflection">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
