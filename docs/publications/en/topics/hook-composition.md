<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/topics/">Topics</a><span style="margin:0 0.45rem;">/</span>Hook Composition</p>

<header class="publication-head"><p class="publication-series">ADPS Topic Study</p><h1>Hook Composition · Make hidden callbacks a readable control structure</h1><p class="publication-deck">Compose orchestration, governance, observation, and recovery at lifecycle events with explicit order, idempotency, and failure semantics.</p></header>

Hooks place deterministic code at stable lifecycle events. A hook can shrink context before a model call, check authority before a tool call, start the next agent after an artifact is accepted, record trace data, save a checkpoint, or release resources.

A hook is a mechanism. Its role comes from the event, the state it reads, the authority it holds, and its failure semantics.

## Four roles

<table>
<thead>
<tr>
<th style="text-align: left;">Role</th>
<th style="text-align: left;">Typical events</th>
<th style="text-align: left;">Actions</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Orchestration</td>
<td style="text-align: left;">artifact accepted, stage completed</td>
<td style="text-align: left;">start stage, route task, gather results</td>
</tr>
<tr>
<td style="text-align: left;">Governance</td>
<td style="text-align: left;">before tool, before commit</td>
<td style="text-align: left;">identity, policy, approval, quota, argument checks</td>
</tr>
<tr>
<td style="text-align: left;">Observation</td>
<td style="text-align: left;">model/tool/step completed</td>
<td style="text-align: left;">events, versions, state deltas, receipts</td>
</tr>
<tr>
<td style="text-align: left;">Recovery</td>
<td style="text-align: left;">failure, timeout, cancel</td>
<td style="text-align: left;">checkpoint, compensation, lease release, escalation</td>
</tr>
</tbody>
</table>

## Composition

<pre><code class="language-text">before_model → context_policy → prompt_trace
before_tool  → identity_check → policy_decision → approval_if_needed
after_tool   → receipt_capture → state_diff → next_stage_or_recovery
</code></pre>

The runtime should display the effective order. When two hooks rewrite arguments, order changes behavior. When an audit hook fails, the design must state whether business execution blocks or observation degrades.

For a payroll commit, `before_tool` first verifies the caller, then reads policy and determines whether approval is required. After resume, `before_commit` rechecks employee state and the Intent digest. Following a successful call, `after_tool` records the receipt and after-read. A telemetry failure may degrade a low-risk read, while a production write normally blocks. Order and failure semantics belong to the composition and cannot depend on accidental plugin registration order.

## HookSpec

<pre><code class="language-yaml">hook_id: payroll.before_commit.policy
event: before_tool
priority: 200
reads: [principal, intent, tool_digest, resource_scope]
writes: [policy_decision]
idempotency_key: run_id + intent_digest
on_failure: deny
emits: [policy.decided]
owner: security-platform
version: 7
</code></pre>

## Relation to G5

G5 keeps its historical identifier and focuses on deterministic governance enforcement. Hook Composition spans a wider set of responsibilities, so no new collaboration pattern has been added.

## Common failures

- Effective order depends on registration order and remains invisible.
- Retry repeats a notification, quota charge, or external action.
- Policy source, decision, enforcement, and logging live in one handler.
- Failure of a non-critical observation hook blocks the main task.
- Parent and child agents use different hook sets without version evidence.

## Review questions

1. Which event triggers each hook, and what state does it read or write?
2. Are order and conflict rules explicit?
3. Are retry, resume, and duplicate events idempotent?
4. Does failure fail open, fail closed, or escalate?
5. Can a run show the effective hook set and versions?

## Source

The Governance workshop separated policy source, decision, enforcement, and evidence. The Collaboration workshop added stage transitions, cross-agent triggers, and recovery. This topic joins both discussions while retaining G5 as the historical governance entry.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>Hook Composition · Make hidden callbacks a readable control structure</em>, ADPS Topic Study, 26 August 2026.</p><p><a href="https://adpsagent.com/topics/">Topic index</a> · <a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">Collaboration workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>Workshop and case records cited in the article: <a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#topics-hook-composition">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
