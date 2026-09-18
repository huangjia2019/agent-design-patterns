<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>C6</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>C6 · Choreography</h1>
<p class="publication-deck">Participants subscribe to events and publish new events under local rules; no component owns the complete plan. Event contracts define completion, causal trace, timeout, and compensation.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Collaboration × Choreography (candidate topology with distributed control)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">High (multiple agents, event-driven, long call chains, high observability overhead)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Collaboration patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern summary</strong></td>
<td style="text-align: left;">Participants subscribe to events and publish new events under local rules; no component owns the complete plan. Event contracts define completion, causal trace, timeout, and compensation.</td>
</tr>
</tbody>
</table>

---

## Problem

Consider two order flows that both change at runtime. In the first, an orchestrator owns the complete plan. A model may select payment, inventory, or notification agents dynamically, while one interpreter schedules calls and gathers results. The flow is dynamic and control remains centralized.

In the second, no component owns that plan. Payment publishes `PaymentConfirmed`. Inventory subscribes, reserves stock, and publishes `StockReserved`. Delivery and notification subscribe to the new event. Each participant knows its input events, local conditions, and output events; their rules collectively advance the order.

Choreography addresses the second design. Autonomous participants under different team or service boundaries need to evolve independently without making one central flow the entry point for every change. Event contracts reduce direct coupling, while completion, causal tracing, retry, and compensation become explicit engineering obligations.

<figure class="workshop-diagram"><img alt="Control ownership in dynamic orchestration and choreography" src="../../assets/images/workshops/orchestration-vs-choreography-en.svg"/><figcaption>Runtime change is not the criterion. The boundary is who owns the complete plan.</figcaption></figure>

## Classification: Collaboration × Choreography

Choreography belongs to Collaboration because it describes how participants continue one another's work. It remains a candidate topology rather than a seventh core column.

- **Dynamic orchestration** retains an interpreter that owns the complete plan, call order, and result closure. Choreography distributes progression rules among event subscribers.
- **Event-driven infrastructure** handles trigger, queueing, delivery, and replay. Choreography describes where control resides. A centrally orchestrated flow can also begin with an event.
- **Candidate standing** reflects the current evidence base: public agent-engineering examples remain concentrated in collaboration. Cross-domain production cases and failure records are still needed.

## Solution and mechanics

1. **Versioned event contracts** define name, schema, producer, visibility, version, idempotency key, causal identifiers, and sensitive fields. A shared bus does not imply universal read access.
2. **Local subscription rules** state the event condition, state read, allowed action, and emitted event. A participant does not invoke or assume the next participant.
3. **Completion and timeout ownership** identifies terminal events, missing-event detection, and the owner of compensation, human takeover, or a thin saga. Decentralized control does not remove accountability.
4. **Causal evidence** carries `run_id`, `correlation_id`, `causation_id`, principal, and component versions. X1 reconstructs the chain; G2 aggregates budget and impact across it.

## Applicability

- **Participants have clear autonomous boundaries**: payment, inventory, and delivery own local state and release cadence.
- **A new subscriber should not change an existing flow owner**: analytics or notification can subscribe to `StockReserved` under the event contract.
- **Throughput or availability exceeds central step-by-step dispatch**: independent events can be consumed in parallel.
- **The domain accepts eventual consistency and supports compensation**: globally atomic approval or commit normally retains a central gate or transaction coordinator.

A short, fixed flow owned by one team usually favours orchestration. Choreography adds event governance and diagnosis cost; it is not a default upgrade.

## Known failure modes

- **Calling dynamic sub-agents choreography**: if one interpreter owns the plan and gathers results, the design is dynamic orchestration.
- **Event storms and cycles**: A triggers B, which triggers A. Consumers need idempotency, TTL, duplicate detection, quotas, and circuit breakers.
- **No owner of completion**: local success events exist without a terminal condition, timeout owner, or compensation state.
- **Shared schema becomes hidden central coupling**: one field change forces every producer and consumer to upgrade together. Versioning and compatibility require tests.
- **Local limits expand globally**: every participant stays below its own cap while fan-out, retries, and loops exceed the run or tenant budget.

## Verification and metrics

- **Event traceability**: Test whether a complete causal chain can be reconstructed from the correlation-ID event log. A chain that cannot be replayed is not ready for production choreography.
- **Convergence and event storms**: Measure whether a collaboration reaches a terminal event or repeats publication until a circuit breaker fires.
- **Coupling blast surface**: Record which publishers, subscribers, and shared schemas must change when an agent is added or removed. A growing change set indicates that the event contract still carries hidden coupling.
- **End-to-end latency**: Compare against an orchestrated control and separate queueing, retry, and eventual-consistency wait time.

## Reference implementation

```
# Orchestration: one runtime owns the plan, order, and result
            orchestrator.run(task):
                for step in plan(task):
                    result = agents[step].execute()
                    state.update(result)
                return state.result

            # Choreography: participants apply local event rules
            bus = EventBus()

            class ChoreographedAgent:
                subscribes_to = [...]
                def on_event(self, e):
                    if self.should_act(e):
                        out = self.act(e)
                        bus.publish(out,
                            correlation_id=e.correlation_id,
                            causation_id=e.event_id)

            for a in agents:
                bus.subscribe(a.subscribes_to, a.on_event)
            bus.publish(initial_event)
            # A terminal-event policy owns completion, timeout, and compensation.
```

The event bus carries versioned contracts; each subscriber owns a local rule and bounded action; correlation and causation IDs reconstruct the path; a terminal-event policy defines completion, timeout, compensation, and escalation.

## Illustrative scenario

A content risk-control platform may begin with a central orchestrator that calls spam, fraud, policy, and brand detectors in sequence. As detectors and ownership boundaries grow, every new capability requires a shared orchestrator change. In a choreographed design, detection agents subscribe to `content.received` and publish events such as `flag.spam` or `flag.fraud`; a policy agent consumes flags, and an escalation agent publishes `case.opened` for high-risk cases. A new detector joins through the event contract rather than a direct call graph.

Every event carries a correlation ID and can be replayed by case. A thin orchestrated saga remains at the point that defines whether the case is complete, because pure choreography has no central owner of completion. This hybrid preserves decentralized reaction while centralizing the state that requires a single authoritative answer. Event-driven agent runtimes and interoperability protocols provide implementation references, but production claims should come from attributed deployments.

## Related patterns

- **Observability (X1)**: Choreography has no central execution trace. Correlation IDs, event lineage, subscriber outcomes, timeouts, and compensation records are required to reconstruct causality and operate the system.
- **Orchestration**: one component owns the plan and decides which participant runs next. In Choreography, participants react to events under local rules and publish new events. Most production systems combine a centrally controlled path for high-risk work with event-driven collaboration around it.
- **Fan-Out/Gather (C2)**: A fan-out owner creates parallel branches and gathers their results. Choreography has no gather owner; each participant consumes events under local rules and publishes the next event. Use C2 when one task owns completion, and C6 when completion is defined across event participants.
- **Failure Journals (M4)**: Subscriber failures can create immutable failure events and reviewed lessons, while the operational event stream remains a separate system record.
- **Blast-Radius Control (G2) and Approval Gate (G1)**: Aggregate impact across subscribers and retain a central gate for actions that require one authoritative approval or commit.

## Design conclusion

Choreography distributes collaboration control from a central coordinator to each agent's local subscription and publication rules. Events advance the global process. The structure reduces central coupling and requires explicit event contracts, causal tracing, completion criteria, and compensation.

## Workshop revision, 25 August 2026: Dynamic orchestration versus choreography

Model-generated call code and dynamic sub-agent selection remain orchestration when an interpreter owns the plan and gathers results. Choreography requires control distributed across event participants and remains a candidate.

[Collaboration workshop record](https://adpsagent.com/workshops/collaboration-2026-08-25/)

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>C6 Choreography</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-c6-choreography">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
