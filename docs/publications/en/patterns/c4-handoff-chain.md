<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>C4</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>C4 · Handoff Chain</h1>
<p class="publication-deck">Split a long process across agents with bounded responsibilities. Each agent returns a structured HandoffPacket with the state, evidence, open questions, and authority the next agent needs.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Collaboration × Chain (pass)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (each handoff adds validation, persistence, and routing latency)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Collaboration patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Split a long process across agents with bounded responsibilities. Each agent returns a structured HandoffPacket with the state, evidence, open questions, and authority the next agent needs.</td>
</tr>
</tbody>
</table>

---

## Problem

A handoff fails when the next agent receives only the customer's last message. It lacks the customer identity, prior actions, unresolved issue, escalation reason, and permissions carried by the previous agent. The second agent then repeats questions or acts on incomplete state.

The Handoff Chain passes a task sequentially across multiple agents while preserving information, responsibility, and traceability. What moves between agents is the state completed by the previous leg, and that state needs an explicit schema. Human call centers use the same idea in a warm handoff: the outgoing representative briefs the incoming one before transferring responsibility.

## Classification: Collaboration × Chain

- **Vertical axis · Collaboration**: responsibility moves from one agent to the next. Each agent owns a bounded stage and explicitly accepts the transferred state and authority. A routing service may enforce the permitted path, but it does not perform every stage as a supervising agent would.
- **Horizontal axis · Chain**: agents run in a defined sequence because a later stage depends on the state produced by an earlier one. Fan-Out/Gather runs independent workers concurrently; Adversarial Review returns findings to a proposer through a bounded loop.

## Solution and mechanics

A reliable handoff requires three controls:

1. **Responsibility splitting**: each agent owns a bounded leg and receives only the context and authority required for that leg.
2. **Structured packaging**: the previous agent packages current state, evidence, unresolved work, and authority into a schema-defined HandoffPacket. A prompt chain often keeps context within one agent and session. A Handoff Chain crosses agent or session boundaries and therefore requires an explicit transfer schema.
3. **Controlled handover**: before transfer, validate the sender, permitted receiver, packet schema, required evidence, and delegated authority. Cap the number of hops and record who transferred which state to whom.

A HandoffPacket should carry at least a five-layer schema:

<table>
<thead>
<tr>
<th style="text-align: left;">Layer</th>
<th style="text-align: left;">Content</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Goal</td>
<td style="text-align: left;">the requested outcome, current scope, and unresolved problem</td>
</tr>
<tr>
<td style="text-align: left;">Artifacts</td>
<td style="text-align: left;">completed outputs and references, such as knowledge sources checked, scripts run, and ticket IDs</td>
</tr>
<tr>
<td style="text-align: left;">Decisions</td>
<td style="text-align: left;">decisions already made, with rationale, evidence, owner, and version</td>
</tr>
<tr>
<td style="text-align: left;">Rejected Paths</td>
<td style="text-align: left;">approaches already attempted, their results, and reasons not to repeat them</td>
</tr>
<tr>
<td style="text-align: left;">Next Required</td>
<td style="text-align: left;">the next action, acceptance condition, deadline, and required authority</td>
</tr>
</tbody>
</table>

## Applicability

- **Tiered customer support**: a case moves from triage to technical support and then to engineering, with different tools, permissions, SLAs, and escalation authority at each stage.
- **Sequential specialist review**: a case must pass through roles with distinct responsibilities, such as intake, domain review, compliance review, and final approval.
- **Returning control after execution**: an execution agent completes its assigned stage and returns results, unresolved questions, and changed state to the orchestrator for replanning.

This pattern fits work with distinct stages, a meaningful execution order, state that can be represented as a contract, and a defined escalation path. A short task that one agent can complete and verify does not need a handoff chain.

## Known failure modes

- **Cold transfer**: the receiving agent gets only the latest user message and asks for information already captured. Require the packet schema at the transfer boundary and reject incomplete packets before responsibility changes.
- **Loss of decision provenance**: files and outputs arrive, but prior decisions do not include their rationale, evidence, owner, or version. The receiver then repeats work or reverses a decision without knowing its basis. Store decisions as first-class packet fields rather than relying on conversation history.
- **Oscillation loop**: the same pair of agents hands back and forth repeatedly. Set a hard chain-length cap from the role graph and SLA, constrain `can_handoff_to`, record a visited set, and escalate when the cap is reached.
- **Unnecessary handoff**: the current agent transfers work that falls within its responsibility and authority. Check completion status, transfer reason, and receiver capability against routing policy before accepting the handoff.
- **Misuse on short tasks or without clear roles**: Directly completable tasks, general-assistant scenarios, and latency-sensitive conversations may not justify the transfer overhead. Where repeated back-and-forth is likely, keep a supervisor responsible for routing and termination.

## Verification and metrics

- **Chain length in hops**: Track handoff count and cap exhaustion. Configure the maximum from the role graph and business SLA, then escalate when reached.
- **Post-handoff repeat-question rate**: Measure how often the receiving agent asks for information already captured. A high rate indicates that the handoff omitted state or evidence the next role needed.
- **Decision retention rate**: Check whether prior conclusions, reasons, and evidence arrive intact. A low value indicates that the HandoffPacket has degenerated into a raw history dump.
- **SLA attainment by stage**: Measure completion time, queue time, and handoff latency for each stage. A transfer can meet its local SLA while causing the end-to-end case to breach its deadline.

## Reference implementation

```
HandoffChain.execute(request, initial_agent, max_hops):
                current, prev_packet, visited = initial_agent, None, []
                for sequence in 1..max_hops:
                    output = run_agent(current, prev_packet)   # input is a structured packet, not raw history
                    packet = build_packet(prev_packet, output) # cumulatively inherit artifacts/decisions/rejected
                    validate_packet(packet)
                    audit(current, packet)
                    if output.complete: return result
                    next = output.handoff_to
                    if next not in current.can_handoff_to or next in visited:
                        return escalate_to_human()
                    visited.append(current)
                    prev_packet, current = packet, next
                return escalate_to_human()                      # exceeding max_hops escalates to a human

            HandoffPacket: five-layer schema (Goal / Artifacts / Decisions / Rejected Paths / Next Required)
```

Production implementation tiers system prompts and tool permissions by role; `can_handoff_to` lists permitted receivers; `max_hops` follows the role graph and SLA; and the audit log records data and responsibility moving across agents.

## Illustrative scenario

Consider a SaaS support system that passes cases through triage, technical, engineering, and supervisory roles. A first version forwards only the customer's last message, forcing each receiver to ask again for the problem and account context. A stronger HandoffPacket carries the customer's goal, checked knowledge and scripts, decisions with their rationale, rejected paths, and the next required action. Models and tool permissions vary by role, and cap exhaustion sends the case to a human. The same mechanism can return control from an execution agent to an orchestrator when the current decision requires replanning.

## Related patterns

- **Prompt Chaining (A3)**: one agent or workflow executes a sequence of prompt stages under a shared control context. C4 transfers responsibility across agents or sessions and therefore requires an explicit state and authority contract.
- **Hierarchical Delegation (C1)**: a supervisor retains responsibility for assignment, synthesis, and termination. In C4, responsibility moves to the receiving stage; a router may enforce the path without acting as the supervisor.
- **Fan-Out/Gather (C2)**: workers execute independent units concurrently and a gather step combines their outputs. C4 runs stages in order because each stage depends on transferred state.
- **Sub-Agent Isolation (C5)**: C5 defines what a delegated worker can see and do. C4 defines what state, evidence, responsibility, and authority cross from one stage to the next.

## Design conclusion

The Handoff Chain uses a structured contract to pass goals, state, evidence, decisions, and responsibility. A raw conversation dump does not guarantee that the receiver knows the next action or its acceptance condition.

## Workshop revision, 25 August 2026: Handoff Contract

A Handoff Contract transfers the current goal, versioned artifacts, binding decisions, rejected paths, open questions, delegated authority, responsibility, and acceptance conditions. The receiver validates the packet and explicitly accepts or rejects the transfer.

[Collaboration workshop record](https://adpsagent.com/workshops/collaboration-2026-08-25/)

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-handoff-engineering" class="related-case-band">
<p class="related-case-label">Pattern engineering note</p>
<h2 id="related-handoff-engineering"><a href="https://adpsagent.com/patterns/engineering/cross-agent-handoff/">Connecting Two Agents: From Context Reference to Task Handoff</a></h2>
<p>Place this pattern in a frontend finding, backend repair, and frontend retest, then inspect ownership transfer, authority, and acceptance evidence.</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>C4 Handoff Chain</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-c4-handoff-chain">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
