<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/positions/" style="color: var(--color-text-muted);">Positions</a>
</p>

# Governance and Safety: Engineering Runtime Control

> ADPS position paper  
> Published: 2026-05-30  
> Author: Agent Design Patterns Society

## Scope

Agent governance defines which actions a system may perform, under what conditions, who is accountable, and how the system stops, explains, and recovers from a deviation. Safety objectives need runtime controls and reviewable evidence.

A production system should answer:

- which tools, data, and environments are accessible;
- which actions may run automatically and which require approval;
- the permitted impact per task, tenant, and time window;
- the evidence retained for each decision and side effect;
- the conditions for stop, rollback, degradation, or reduced autonomy.

These answers belong in permissions, state, code, and operating procedures. A System Prompt or principles document cannot enforce them.

## Five runtime controls

### 1. Tool admission and least privilege

The Tool Registry records each tool's schema, version, owner, risk class, and credential scope. Runtime policy generates the smallest tool set for the task, tenant, and role. Unregistered, incompatible, or out-of-scope tools never enter the candidate set.

Admission runs outside the model call. The model may propose a tool; program logic verifies the caller, resource, parameters, and permissions.

### 2. Gates for high-risk actions

Approval Gates cover money movement, production writes, deletion, external publication, and irreversible actions. The approval package includes the action, target, quantity, provenance, expected result, and recovery plan. The approval and tool call share one action ID so approval for one proposal cannot authorize another.

Hooks enforce deterministic rules such as path allowlists, prohibited commands, parameter ceilings, and sensitive-field checks. These checks do not require model judgment.

### 3. Blast-radius control

Blast Radius Control limits the objects, quantity, value, environment, and duration affected by an action. Common mechanisms include:

- development, test, and production separation;
- read-only and short-lived credentials;
- per-tenant, per-batch, and per-resource limits;
- sandbox, working-directory, and network-egress restrictions;
- idempotency keys, transactions, compensation, and kill switches.

Downstream systems enforce these limits. Prompt text asking the model to be careful does not establish a hard boundary.

### 4. Observability and audit

Model calls, tool calls, approvals, state changes, and business receipts enter one event chain. Events should correlate run, task, action, tool version, actor, input/output hash, and policy decision.

Audit evidence supports incident reconstruction, release evaluation, and accountability. Sensitive inputs may use hashes, redacted summaries, or controlled references so observability does not create another disclosure surface.

### 5. Progressive autonomy

Agent permissions expand through evidence-based stages such as shadow mode, recommendation, approved execution, bounded automation, and wider autonomy. Promotion criteria should reference task sets, failure classes, human intervention, recovery, and business acceptance.

A version change, domain change, or material incident can trigger demotion. Autonomy is a revocable runtime configuration.

## Action risk contract

<pre><code class="language-yaml">action_type: payroll_batch_submit
risk_class: high
subject:
  tenant_id: tenant_42
scope:
  max_records: 200
  environment: production
permissions:
  required_role: payroll_operator
approval:
  required: true
  approver_role: payroll_manager
preconditions:
  - batch_totals_reconciled
  - employee_ids_resolved
  - idempotency_key_present
execution:
  timeout_seconds: 60
  retry: 0
postconditions:
  - receipt_persisted
  - ledger_matches_receipt
recovery:
  mode: manual_compensation
evidence:
  retention_days: 365
</code></pre>

The contract translates policy into executable fields. Tool dispatch, gates, business ledgers, and audit systems consume the same definition, reducing rule drift between layers.

## Control chain

<pre><code class="language-text">task and identity
    ↓
minimal tools and credentials
    ↓
action proposal and parameter validation
    ↓
deterministic hooks / approval gate
    ↓
execution in a bounded environment
    ↓
business receipt and post-condition checks
    ↓
event chain, alerting, and recovery
</code></pre>

Every layer can fail, so later layers still bound impact and preserve evidence. A failed gate prevents execution. A post-condition mismatch stops later steps. A broken evidence chain sends the run to manual handling.

## Common failures

<table>
<thead>
<tr>
<th style="text-align: left;">Failure</th>
<th style="text-align: left;">Consequence</th>
<th style="text-align: left;">Control</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Permissions exist only in the prompt</td>
<td style="text-align: left;">A bypassed instruction still reaches the tool</td>
<td style="text-align: left;">Program allowlists, credentials, and hooks</td>
</tr>
<tr>
<td style="text-align: left;">Approval shows only a prose summary</td>
<td style="text-align: left;">Target, quantity, or provenance remains hidden</td>
<td style="text-align: left;">Structured action contract and diff</td>
</tr>
<tr>
<td style="text-align: left;">The agent holds long-lived production credentials</td>
<td style="text-align: left;">One error propagates across tasks</td>
<td style="text-align: left;">Short-lived credentials, scope, and isolation</td>
</tr>
<tr>
<td style="text-align: left;">Logs have no correlation identifiers</td>
<td style="text-align: left;">Decisions cannot be tied to side effects</td>
<td style="text-align: left;">Unified run/task/action event chain</td>
</tr>
<tr>
<td style="text-align: left;">Autonomy can only increase</td>
<td style="text-align: left;">Incidents leave prior permissions in place</td>
<td style="text-align: left;">Revocable configuration and demotion criteria</td>
</tr>
<tr>
<td style="text-align: left;">The agent can edit its evaluator and gate</td>
<td style="text-align: left;">Self-validation loses independence</td>
<td style="text-align: left;">Protected governance boundary and dual approval</td>
</tr>
</tbody>
</table>

## Relationship to ADPS patterns

- G1 Approval Gate defines human decision points for high-risk actions.
- G2 Blast Radius Control bounds the effect of errors.
- G3 Progressive Commitment manages permission and autonomy changes.
- X1 Observability establishes runtime evidence.
- G5 Hooks Pipeline enforces deterministic policy outside the model.

Governance patterns appear with Action, Memory, Collaboration, and Reflection patterns. Selection must resolve to concrete actions, data, permissions, and recovery paths.

## Release evidence

Before production, provide at least:

1. a tool and credential inventory;
2. high-risk action contracts;
3. replay records for approvals and hooks;
4. impact-boundary and isolation tests;
5. one complete event chain from proposal to business receipt;
6. stop, rollback, and autonomy-demotion exercises.

Governance is ready when controls run, evidence can be reviewed, and abnormal outcomes have an operating path.

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
<p><a href="https://adpsagent.com/chronicle/#positions-governance-and-safety">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
