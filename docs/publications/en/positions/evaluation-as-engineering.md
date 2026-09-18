<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/positions/" style="color: var(--color-text-muted);">Positions</a>
</p>

# Evaluation as Engineering: From Design Constraints to Production Evidence

> ADPS position paper  
> Published: 2026-05-30  
> Author: Agent Design Patterns Society

## Scope

Agent systems combine deterministic software with probabilistic behavior. Data structures, permissions, tool contracts, idempotency, and business ledgers remain covered by conventional tests. Evaluations measure model output, execution paths, and variation across runs.

Four validation activities produce different evidence:

<table>
<thead>
<tr>
<th style="text-align: left;">Activity</th>
<th style="text-align: left;">Subject</th>
<th style="text-align: left;">Typical result</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Test</td>
<td style="text-align: left;">Deterministic components, contracts, and state changes</td>
<td style="text-align: left;">Pass/fail and fault location</td>
</tr>
<tr>
<td style="text-align: left;">Evaluation</td>
<td style="text-align: left;">Capability, behavior, and failure distribution on a task set</td>
<td style="text-align: left;">Scores, classes, and sample evidence</td>
</tr>
<tr>
<td style="text-align: left;">Monitoring</td>
<td style="text-align: left;">Production traffic, cost, latency, and drift</td>
<td style="text-align: left;">Time series, alerts, and abnormal traces</td>
</tr>
<tr>
<td style="text-align: left;">Acceptance</td>
<td style="text-align: left;">Business outcome and release accountability</td>
<td style="text-align: left;">Approve, reject, limit, or roll back</td>
</tr>
</tbody>
</table>

A deterministic grader may appear in both a test suite and an evaluation. Record where its evidence comes from, who maintains it, and which decision it supports.

## Evaluation as a design input

Design begins with the task, environment, permissions, successful outcomes, and forbidden outcomes. Latency, cost, and quality targets influence model choice, tools, topology, caching, and human involvement.

Without these constraints, a team can only judge whether the finished system feels good. It cannot explain which objective an architecture decision was meant to serve.

## Evaluation contract

<pre><code class="language-yaml">eval_id: payroll-action-v5
system_under_test:
  agent_version: payroll-agent-2.3
  components:
    - planner
    - tool_dispatcher
    - action_guard
task_set:
  dataset: payroll-action-boundaries-v4
environment:
  database: disposable_snapshot
  tools: sandbox_registry_v3
permissions:
  max_risk_class: medium
outcomes:
  required:
    - correct_business_ids
    - no_skipped_dependencies
    - ledger_matches_receipts
  forbidden:
    - production_write
    - duplicate_submission
graders:
  - deterministic_ledger_check
  - dependency_order_check
  - rubric_review
trials: 3
release_gate:
  p0_failures: 0
  regression: no_material_drop
owner: payroll-platform
evidence: artifacts/evals/payroll-action-v5/
</code></pre>

The contract keeps the system under test, task distribution, environment, permissions, graders, and release gate together. Tasks with material randomness retain repeated trials and each trace so a mean score cannot hide a rare severe failure.

## Three stages

### Design

Use a compact representative task set to test architecture constraints:

- whether the task can be observed and accepted;
- whether tool and permission boundaries can be implemented;
- whether the selected topology meets latency and cost objectives;
- which outcomes require human or business-system confirmation.

### Development and pre-production

Deterministic tests run with each change. Capability evaluation, regression evaluation, permission tests, and sandbox acceptance are layered by risk. Compare a candidate with the current version on the same task set, and let release gates read sample-level failures and complete traces.

Capability sets test whether a new function works. Regression sets protect established behavior. They may share infrastructure, while their maintenance purpose and release rules remain distinct.

### Production

Production requests supply the real distribution and delayed outcomes. Sample traffic by risk and connect inputs, component versions, traces, business receipts, and human disposition. New failures enter the regression set after redaction, attribution, and reproduction.

Monitoring detects change. Evaluation determines whether capability changed. Acceptance decides whether to release, limit, or roll back.

## Evidence priority

1. **External facts and business receipts:** database state, transaction receipts, compilation, and execution artifacts.
2. **Deterministic rules:** schemas, reference integrity, state machines, and business invariants.
3. **Independent test environments:** sandboxes, snapshots, and repeatable tasks.
4. **Expert and human labels:** domain judgment, subjective quality, and high-risk boundaries.
5. **Model graders:** wider coverage, calibrated and sampled for human review.

Model graders help with open-ended output. They do not establish tool side effects, permission compliance, or business facts. Model diversity can add perspective but does not by itself establish independence.

## Dataset lifecycle

<pre><code class="language-text">specifications and business acceptance
        ↓
initial capability set
        ↓
development runs and sample analysis
        ↓
production failures, human review, and new boundaries
        ↓
redaction, deduplication, attribution, and reproduction
        ↓
regression set and versioned release record
        ↓
retire stale samples while retaining historical baselines
</code></pre>

Each sample records provenance, applicable versions, expected outcomes, graders, and change history. When the agent and grader change together, preserve the old baseline or the scores cannot be compared.

## Release gates

A release gate combines several layers of evidence. One aggregate score cannot replace them. Typical rules include:

- zero P0 failures;
- all critical regression cases pass;
- permission, isolation, and side-effect tests pass;
- quality, latency, and cost stay within agreed boundaries;
- high-risk samples receive human acceptance;
- evidence and the rollback version are archived.

Rules should match task risk. Low-risk content generation may use probabilistic thresholds. Money movement, production data, and external publication require stronger deterministic evidence.

## Common failures

<table>
<thead>
<tr>
<th style="text-align: left;">Failure</th>
<th style="text-align: left;">Effect</th>
<th style="text-align: left;">Correction</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Only public benchmarks are run</td>
<td style="text-align: left;">Business traffic is not represented</td>
<td style="text-align: left;">Domain task sets and production samples</td>
</tr>
<tr>
<td style="text-align: left;">Evaluation starts after implementation</td>
<td style="text-align: left;">Architecture lacks design constraints</td>
<td style="text-align: left;">Define the contract with task and permissions</td>
</tr>
<tr>
<td style="text-align: left;">Only an aggregate score is retained</td>
<td style="text-align: left;">Severe minority failures are averaged away</td>
<td style="text-align: left;">Keep samples, traces, and failure classes</td>
</tr>
<tr>
<td style="text-align: left;">Agent and grader change together</td>
<td style="text-align: left;">Old and new results cannot be compared</td>
<td style="text-align: left;">Independent versions, frozen baselines, and replay</td>
</tr>
<tr>
<td style="text-align: left;">Production events omit component versions</td>
<td style="text-align: left;">Drift cannot be attributed</td>
<td style="text-align: left;">Link model, prompt, skill, and tool versions</td>
</tr>
<tr>
<td style="text-align: left;">Evaluation success directly expands permissions</td>
<td style="text-align: left;">Capability evidence bypasses governance</td>
<td style="text-align: left;">Separate approval, isolation, and recovery gates</td>
</tr>
</tbody>
</table>

## Relationship to ADPS

Evaluation provides evidence for pattern selection and evolution. Perception covers input and missed signals. Memory covers admission, retrieval, and expiry. Reasoning covers paths and conclusions. Action covers tool side effects. Reflection covers whether modifications improve outcomes. Collaboration covers handoffs and isolation. Governance covers permissions and impact.

The pattern catalog describes available structures. Evaluation records whether one implementation meets its objectives in a specified environment.

---

ADPS · Agent Design Patterns Society · adpsagent.com

---

<p style="font-size: 0.92rem; color: var(--color-text-muted);">
<a href="https://adpsagent.com/positions/">← Back to all positions</a>
</p>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS technical position; arguments and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#positions-evaluation-as-engineering">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
