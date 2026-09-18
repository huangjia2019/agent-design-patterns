<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/positions/" style="color: var(--color-text-muted);">Positions</a>
</p>

# Multi-Agent Systems: Adoption Criteria and Engineering Boundaries

> ADPS position paper · No. 1  
> Published: 2026-05-30  
> Author: Agent Design Patterns Society

## Scope

A multi-agent system uses several agents with independent runtime boundaries to complete a task. Role names, different prompts, or a sequence of model calls do not establish those boundaries.

Four boundaries matter in implementation:

1. **Context boundary:** what each agent can read and whether its internal process can affect another role.
2. **Tool and permission boundary:** which tools, credentials, and scopes each agent can use.
3. **State and failure boundary:** whether one agent can fail, retry, or roll back without invalidating the entire run.
4. **Handoff boundary:** whether agents exchange structured artifacts, evidence, and state instead of entire conversations.

Without these boundaries, the design is usually a staged single-agent workflow. Additional roles then add scheduling, context duplication, and debugging cost without isolation benefits.

## Adoption principle

A single agent with a clear tool set and observable Harness should provide the comparison baseline. A multi-agent design needs a structural reason and should be compared on the same task set for quality, latency, cost, and recovery.

Structural reasons include:

- genuinely parallel branches with no runtime dependencies;
- information, permission, or tool isolation between roles;
- independent failure domains where one branch can fail without ending the run;
- independent review backed by different evidence or decision criteria.

More roles, organizational metaphors, and a richer demo are not adoption criteria.

## Suitable structures

### Parallel exploration

A Planner divides work into independent branches, Workers produce artifacts concurrently, and an Aggregator reconciles the results. Parallel leaves in the task DAG should have no data dependencies; dependent work remains sequential or orchestrated.

Acceptance checks should cover:

- explicit input, output, and stopping conditions for each branch;
- independent retry and discard;
- conflict, duplicate, and omission handling during aggregation;
- wall-clock savings that exceed orchestration overhead.

### Independent review

A Generator produces a candidate artifact. A Critic evaluates it with an explicit rubric, source evidence, or deterministic checks. Different models may add perspective, but model diversity alone does not establish independence. Context, evidence sources, permissions, and accountability still need separation.

A useful review reports the location, evidence, severity, and recommended disposition of each finding. Agreement labels or one aggregate score do not support repair and audit.

### Hierarchical delegation

A parent agent owns the goal, budget, and final acceptance. Child agents work within bounded scopes and return structured results without copying their full internal conversations into the parent context.

This structure fits large-repository search, cross-domain evidence collection, and permission-segmented tasks. A delegation contract should state the goal, allowed tools, resource budget, delivery schema, failure states, and recall conditions.

## Unsuitable structures

### Role splitting in a linear workflow

Splitting a strictly sequential chain into several roles creates no parallelism. State must be serialized and interpreted at each handoff, increasing failure opportunities. A single agent with Chain, Plan and Execute, or Prompt Chaining is usually easier to control.

### Shared context and shared state

When every role reads the same context, uses the same tools, and writes to the same state object in sequence, isolation is largely absent. Treat the roles as stages of one runtime unless the design establishes another boundary.

### No comparable single-agent baseline

Without a baseline, the team cannot attribute a change to parallelism, isolation, model diversity, prompt design, or tool design. At minimum, record task outcomes, material failure types, latency, cost, human intervention, and recovery.

## Minimal isolation contract

<pre><code class="language-yaml">agent_role: repository_reviewer
task_scope:
  repository: payroll-service
  paths: ["src/payroll/**"]
context:
  include: ["change.patch", "acceptance.md"]
  exclude: ["generator_scratchpad"]
tools:
  allow: ["read_file", "search_code", "run_tests"]
  deny: ["write_file", "deploy", "database_write"]
budget:
  max_steps: 12
  max_duration_seconds: 180
handoff:
  schema: review_finding_v1
  required: ["location", "evidence", "severity", "recommendation"]
failure:
  retry: 1
  on_timeout: return_partial
</code></pre>

The contract turns an independent role into a runtime property. Without scope, tools, budget, and handoff constraints, the role remains a prompt-level label.

## Decision table

<table>
<thead>
<tr>
<th style="text-align: left;">Dimension</th>
<th style="text-align: left;">Single agent favored</th>
<th style="text-align: left;">Multi-agent candidate</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Task dependency</td>
<td style="text-align: left;">Strong sequence or frequent shared state</td>
<td style="text-align: left;">Independent parallel branches</td>
</tr>
<tr>
<td style="text-align: left;">Context</td>
<td style="text-align: left;">Information can be read together</td>
<td style="text-align: left;">Separation reduces interference or disclosure</td>
</tr>
<tr>
<td style="text-align: left;">Permissions</td>
<td style="text-align: left;">Same tools and credentials</td>
<td style="text-align: left;">Segregation of duties or least privilege</td>
</tr>
<tr>
<td style="text-align: left;">Recovery</td>
<td style="text-align: left;">Whole-run retry is inexpensive</td>
<td style="text-align: left;">Local retry and independent failure domains</td>
</tr>
<tr>
<td style="text-align: left;">Review evidence</td>
<td style="text-align: left;">One evidence set supports acceptance</td>
<td style="text-align: left;">Independent evidence or specialist judgment</td>
</tr>
<tr>
<td style="text-align: left;">Runtime foundation</td>
<td style="text-align: left;">Baseline and tracing are incomplete</td>
<td style="text-align: left;">Each branch can be compared for quality and cost</td>
</tr>
</tbody>
</table>

This table is not a scoring formula. Validate every candidate against the task DAG, isolation contract, and controlled comparison.

## Relationship to ADPS patterns

Multi-agent systems combine collaboration patterns with Parallel, Hierarchy, Route, or Orchestrate topologies:

- C1 Hierarchical Delegation defines parent-child responsibility and acceptance.
- C2 Fan-Out and Gather handles independent parallel branches.
- C3 Adversarial Review separates generation and review evidence.
- C4 Handoff Chain defines cross-role transfer.
- C5 Sub-Agent Isolation constrains context, tools, and failure domains.
- C6 Choreography studies event-based collaboration without a central orchestrator and remains under review.

Pattern names describe structure. Production readiness still depends on state management, observability, permissions, stopping conditions, and regression evaluation.

## Evidence expected

A public multi-agent account should include:

1. a single-agent baseline;
2. the task DAG and parallel branches;
3. the sub-agent isolation contract;
4. end-to-end traces and recovery records;
5. quality, latency, cost, and human-intervention comparisons on the same task set.

ADPS continues to collect reviewable field cases. Percentages, multipliers, and anonymous stories without source records are not treated as evidence for pattern validity.

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
<p><a href="https://adpsagent.com/chronicle/#positions-when-to-use-multi-agent">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
