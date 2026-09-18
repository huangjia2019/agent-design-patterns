<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/topics/">Topics</a><span style="margin:0 0.45rem;">/</span>Agent OS</p>

<header class="publication-head"><p class="publication-series">ADPS Topic Study</p><h1>Agent OS · From analogy to engineering checklist</h1><p class="publication-deck">Use operating-system responsibilities to inspect a multi-agent runtime while keeping the limits of the analogy visible.</p></header>

A multi-agent runtime increasingly resembles a small operating system. It schedules execution units, isolates resources, carries messages, stores state, handles failures, and lets people pause, take over, and resume. The analogy is useful as a completeness check.

## Eight responsibilities

<table>
<thead>
<tr>
<th style="text-align: left;">OS view</th>
<th style="text-align: left;">Question for an agent runtime</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Scheduling</td>
<td style="text-align: left;">Which agent runs, with what priority, budget, and cancellation?</td>
</tr>
<tr>
<td style="text-align: left;">Isolation</td>
<td style="text-align: left;">Are context, tools, credentials, workspace, and failure separated?</td>
</tr>
<tr>
<td style="text-align: left;">Communication</td>
<td style="text-align: left;">Do messages, events, artifacts, and hand-offs have schemas and versions?</td>
</tr>
<tr>
<td style="text-align: left;">Storage</td>
<td style="text-align: left;">How are checkpoints, memory, workspace, and external facts separated?</td>
</tr>
<tr>
<td style="text-align: left;">Identity</td>
<td style="text-align: left;">How does human delegation reach agents, runs, tools, and resources?</td>
</tr>
<tr>
<td style="text-align: left;">Observation</td>
<td style="text-align: left;">How do causal trace, component versions, state deltas, and outcomes connect?</td>
</tr>
<tr>
<td style="text-align: left;">Reclamation</td>
<td style="text-align: left;">When are temporary credentials, locks, queues, tasks, and sandboxes released?</td>
</tr>
<tr>
<td style="text-align: left;">Failure handling</td>
<td style="text-align: left;">How do timeout, retry, compensation, circuit breaking, and takeover combine?</td>
</tr>
</tbody>
</table>

## Where the analogy helps

Operating systems separate the ability to execute from the ability to manage execution over time. A model that calls tools has not necessarily solved fairness, isolation, resource leaks, or failure propagation. The analogy forces those responsibilities into the architecture.

Consider two coding agents changing a client and a service. Scheduling must detect whether both alter the same API contract. Isolation supplies separate worktrees and short-lived credentials. Communication uses a versioned Handoff Contract. Storage retains checkpoints. Cancelling one task must also release its sandbox, leases, and queued callbacks. “Start two agents at once” answers none of those responsibilities.

## Where it distorts

Agent intent and output are probabilistic in ways ordinary processes are not. Agent memory includes selection, trust, forgetting, and versioning rather than only storage. Human-in-the-loop is a business-control and organizational-responsibility problem, not just interrupt handling.

Agent OS is therefore an engineering checklist and research agenda, not a settled product category.

## Minimal runtime surface

<pre><code class="language-text">submit(task, principal, constraints)
spawn(role, task_packet, authority_scope)
handoff(contract)
observe(run_id)
checkpoint(run_id)
cancel(run_id, reason)
reclaim(run_id)
</code></pre>

Names may change; responsibilities remain. Central orchestration, distributed events, and hybrid architectures all need answers.

## Research questions

1. How should agent, workload, run, and tool-invocation identity be layered?
2. Can cross-session resource conflicts be declared and detected before scheduling?
3. How should Handoff Contracts connect to agent protocols?
4. Which versions and external preconditions belong in a long-running checkpoint?
5. How does reclamation cover trial shutdown, owner departure, and retirement?

## Source

This topic grew from cross-layer discussion in the Collaboration and Governance workshops and connects C5 Sub-Agent Isolation, C6 Choreography, X1 Observability, and X3 Security & Identity.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>Agent OS · From analogy to engineering checklist</em>, ADPS Topic Study, 26 August 2026.</p><p><a href="https://adpsagent.com/topics/">Topic index</a> · <a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">Collaboration workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>Workshop and case records cited in the article: <a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#topics-agent-os-engineering">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
