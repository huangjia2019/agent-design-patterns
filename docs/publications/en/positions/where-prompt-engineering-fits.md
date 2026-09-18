<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/positions/" style="color: var(--color-text-muted);">Positions</a>
</p>

# Where Prompt Engineering Fits in an Agent System

> ADPS position paper  
> Published: 2026-05-30  
> Author: Agent Design Patterns Society

## Scope

Prompt engineering designs the language conditions of a model call: role, task instructions, examples, context arrangement, output format, and tool descriptions. It directly affects how a model interprets input, reasons, and expresses a result.

An agent system also manages runtime state, tool permissions, task progress, recovery, approval, and evidence. Those responsibilities belong to the Harness. A prompt enters the Harness as input to one model call. The Harness decides when the call occurs, which side effects are permitted, and how the result is accepted.

Separating these responsibilities gives prompt engineering a useful and testable boundary.

## Suitable prompt responsibilities

### Role and task semantics

A prompt can define the model's role, current task, domain vocabulary, and intended audience. Role descriptions should point to observable behavior instead of relying on personality labels.

### Examples and boundary cases

Few-shot examples express classification criteria, format conventions, and domain language that are difficult to encode completely as rules. Version the examples with the evaluation set and include positive, negative, and boundary cases.

### Output shape

A prompt can explain field meaning, missing-value behavior, and citation requirements. JSON Schema, type checks, and business validation still run in code. The model proposes a candidate structure; the program decides whether downstream systems may consume it.

### Reasoning and tool-use guidance

The model needs to know which tools are available, what each tool does, and when clarification is required. Generate tool descriptions from the capability registry so several prompts do not maintain drifting copies.

### Soft constraints

Tone, length, explanatory depth, and conservatism can be adjusted through prompts. Runtime controls must enforce hard constraints involving safety, permissions, money, and authoritative data.

## Harness responsibilities

### State and task graphs

Planning, execution, and approval waiting are explicit states. A state machine or task graph stores the current node, dependencies, retries, and recovery position. A prompt may tell the model which state it is in; it cannot persist that state.

### Tool admission

The Tool Registry defines schemas, versions, permissions, and risk classes. A Dispatcher narrows candidates. Hooks or Approval Gates enforce policy around a call. Natural-language instructions provide context rather than enforcement.

### Memory and context

The memory system controls admission, retrieval, expiry, and conflict. A context assembler selects material for the current contract. Repeatedly appending complete history to a prompt increases cost, noise, and stale information.

### Validation and release

Tests, evaluations, business ledgers, and human acceptance provide independent evidence. Model self-scoring may contribute a signal, but cannot by itself authorize release, high-risk execution, or increased autonomy.

### Stop, retry, and recovery

Step limits, budgets, timeouts, idempotency keys, compensation actions, and checkpoints require runtime records. A model may propose the next step; the executor decides whether the run can continue.

## Common boundary violations

<table>
<thead>
<tr>
<th style="text-align: left;">Prompt-level substitution</th>
<th style="text-align: left;">Runtime risk</th>
<th style="text-align: left;">Engineering location</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Describing multi-agent coordination in prose</td>
<td style="text-align: left;">No message, isolation, or handoff contract</td>
<td style="text-align: left;">Collaboration patterns and orchestration</td>
</tr>
<tr>
<td style="text-align: left;">Stating that a dangerous tool is forbidden</td>
<td style="text-align: left;">Instructions can be bypassed</td>
<td style="text-align: left;">Tool admission, permissions, and approval</td>
</tr>
<tr>
<td style="text-align: left;">Putting all history in the prompt</td>
<td style="text-align: left;">Growing noise, staleness, and cost</td>
<td style="text-align: left;">Layered memory and context assembly</td>
</tr>
<tr>
<td style="text-align: left;">Asking the model to maintain workflow state</td>
<td style="text-align: left;">Skips, repeats, and weak recovery</td>
<td style="text-align: left;">State machine or task graph</td>
</tr>
<tr>
<td style="text-align: left;">Publishing after model self-review</td>
<td style="text-align: left;">Generation and review share assumptions</td>
<td style="text-align: left;">Independent tests, evaluations, and acceptance</td>
</tr>
</tbody>
</table>

## Relationship to the ADPS two-axis framework

Prompt engineering affects local steps that ask a model to interpret, reason, generate, or select tools. The Harness implements execution topology:

- Chain controls step order.
- Route selects candidate branches.
- Parallel determines concurrent branches.
- Orchestrate manages the task graph and shared state.
- Loop defines feedback and stopping conditions.
- Hierarchy defines delegation, budgets, and recall.

The same prompt can be reused in different topologies. Wording alone does not create topology, state, or permission boundaries.

## Prompt engineering contract

<pre><code class="language-yaml">prompt_id: payroll_intent_v4
purpose: classify_payroll_request
inputs:
  required: [user_message, tenant_policy]
outputs:
  schema: intent_signal_v2
examples:
  dataset: payroll-intent-boundaries-v3
tools: []
constraints:
  missing_information: ask_clarification
evaluation:
  suite: evals/payroll-intent-v5
  release_gate: no_p0_regression
owner: payroll-agent
</code></pre>

The prompt becomes a versioned artifact covered by code review, regression evaluation, and release records. A team can identify what changed, which tasks were affected, who accepted the change, and which version supports rollback.

## Adoption guidance

Before adding prompt text, identify whether it expresses language-layer behavior or runtime control. Give language-layer work defined inputs, outputs, examples, and evaluations. Implement runtime control through state, code, permissions, or validation.

Prompt engineering remains an important model-interaction discipline. Harness engineering places that discipline inside an observable and recoverable system.

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
<p><a href="https://adpsagent.com/chronicle/#positions-where-prompt-engineering-fits">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
