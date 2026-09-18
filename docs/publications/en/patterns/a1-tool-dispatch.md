<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>A1</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>A1 · Tool Dispatch</h1>
<p class="publication-deck">Before execution, the runtime narrows eligible tools using metadata, permissions, risk, and current state. The model chooses only within that admitted set.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Action × Route</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Low to medium (candidate selection, state refresh, and policy checks)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Action patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Before execution, the runtime narrows eligible tools using metadata, permissions, risk, and current state. The model chooses only within that admitted set.</td>
</tr>
</tbody>
</table>

---

## Problem

As the tool registry grows, overlapping names and stale state make selection harder. A logistics dispatch agent can repeatedly choose the same driver if it does not refresh availability or check the session quota. The individual tool call may be valid while the sequence is operationally wrong.

Tool Dispatch places tool admission in the runtime. Metadata describes each tool's capability, schema, version, cost, permission requirements, and side effects. Dispatch rules apply quotas, state-freshness checks, and trace requirements before a call can proceed.

## Classification: Action × Route

- **Vertical axis · Action**: Tool Dispatch selects the capability that will affect an external system and checks whether the call may proceed.
- **Horizontal axis · Route**: Intent, metadata, permissions, risk, and current state narrow the registry to one admitted call path. Minimal Tool Set (A5) controls which candidates are exposed before this decision.

## Solution and mechanics

Production Tool Dispatch depends on tool metadata that covers identity, schemas, execution behavior, source, progressive disclosure, and lifecycle. A name, description, and parameters are enough to invoke a demo tool, but not enough to govern side effects and state.

Useful execution characteristics include `isReadOnly`, `isConcurrencySafe`, `isDestructive`, `requiresFreshState`, and `requiresApproval`. Unknown values should take the conservative path: no parallel execution, no approval bypass, and no assumption that state is fresh. If booleans cannot represent "undeclared," use explicit enums or reject incomplete schemas at registration.

Runtime admission adds quota, freshness, and side-effect controls around that metadata:

<table>
<thead>
<tr>
<th style="text-align: left;">Mechanism</th>
<th style="text-align: left;">Function</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Quota</td>
<td style="text-align: left;">Caps repeated calls to the same tool or primary parameter within a task, limiting accumulated side effects</td>
</tr>
<tr>
<td style="text-align: left;">Mandatory state refresh</td>
<td style="text-align: left;">Before a write operation, status must first be queried and refreshed, to avoid writing based on stale data</td>
</tr>
<tr>
<td style="text-align: left;">Saga side-effect tracking</td>
<td style="text-align: left;">Each destructive tool registers an inverse action, rolling back in reverse on failure</td>
</tr>
</tbody>
</table>

## Applicability

- **Large registries with side-effecting tools**: Logistics, customer support, and operations need selection plus permission, freshness, quota, and recovery controls.
- **External tool protocols such as MCP**: A new tool crosses a trust boundary. Record its source and version, then review descriptions, parameters, permissions, and runtime behaviour according to risk.
- **Tool-heavy work that can be expressed as a local program**: For example, read inventory from several stores, filter missing items, and query substitutes for each one. With Programmatic Tool Calling, the model writes a bounded program that loops over or parallelizes calls to registered tools inside a sandbox, reduces the results, and returns only the needed information to context. The model-generated program expresses call order; engineers do not predefine that exact sequence. A1 still governs tool registration, authority, quotas, and admission for every call.

## Boundaries between four runtime mechanisms

<table>
<thead><tr><th style="text-align: left;">Mechanism</th><th style="text-align: left;">How work advances</th><th style="text-align: left;">Primary boundary</th></tr></thead>
<tbody>
<tr><td style="text-align: left;">Direct tool calling</td><td style="text-align: left;">The model selects one tool and its arguments, observes the result, and then chooses the next step</td><td style="text-align: left;">A1 selects and admits each call</td></tr>
<tr><td style="text-align: left;"><a href="https://adpsagent.com/concepts/react-loop/">ReAct</a></td><td style="text-align: left;">Reasoning, action, and observation alternate; each observation informs the next decision</td><td style="text-align: left;">Useful when the route is uncertain and work must proceed by inspection, usually with more model round trips</td></tr>
<tr><td style="text-align: left;"><a href="https://adpsagent.com/concepts/programmatic-tool-calling/">Programmatic Tool Calling</a></td><td style="text-align: left;">The model writes a bounded program that loops, branches, or parallelizes calls to registered tools</td><td style="text-align: left;">The program owns local control flow; tool identity, authority, and side-effect boundaries remain in force</td></tr>
<tr><td style="text-align: left;"><a href="https://adpsagent.com/concepts/code-as-action/">CodeAct</a></td><td style="text-align: left;">The model uses executable code as its action language for computation, libraries, and available capabilities</td><td style="text-align: left;">The action space is broader than a registered-tool catalogue and needs stronger isolation for code, resources, and credentials</td></tr>
</tbody>
</table>

These labels describe different layers. A1 governs tool registration, candidate selection, and call admission. A2 can schedule a multi-stage plan. ReAct, Programmatic Tool Calling, and CodeAct describe how a step proceeds at runtime. Code generated in one run becomes M5 Procedural Memory only after validation, naming, versioning, and approval for reuse across tasks.

## Known failure modes

- **Metadata too thin**: Name and description do not express permissions, freshness, idempotency, approval, side effects, or result contracts. The runtime cannot distinguish two semantically similar tools safely.
- **Side-effect tools without supporting controls**: Database writes, messages, and payments need appropriate quotas, current-state checks, idempotency, receipts, and compensation or escalation paths.
- **Tool stuffing**: Sending a large registry to the model consumes context and increases ambiguity. Keep core tools resident and retrieve extended tools on demand.
- **Tool poisoning**: An attacker can place hidden instructions in an external tool description. Defenses include allowlisting, description scanning, sandboxing, behavior monitoring, and least privilege, selected from the system's threat model.

## Verification and metrics

- **Tool selection accuracy**: Replay historical queries and judge whether each step selected a suitable tool, grouping errors by task class.
- **Side-effect controllability**: Use chaos tests to verify that quotas, approvals, and saga compensation stop or reverse a destructive mis-dispatch.
- **Tool hallucination rate**: Track nonexistent tools, invalid parameters, and schema failures. Investigate changes in registry quality and candidate-set size.
- **Tools per task**: Analyze the call distribution together with task complexity and repeated calls; the count alone does not establish over-tooling.

## Reference implementation

```
dispatch(tool_name, args, session):
                tool does not exist        → reject (tool_hallucination)
                quota exhausted            → reject (quota_exceeded)
                fresh state required but stale → reject (stale_state_must_refresh)
                approval required          → suspend (awaiting_approval)
                run handler:
                    success and destructive → register saga inverse + increment quota + refresh state timestamp
                    failure                → record trace, hand off to upper-layer saga rollback
                return DispatchTrace (tool / parameters / trigger / status / rejection reason / latency)
```

Treat undeclared execution properties conservatively. Count quota at the business-resource level, such as driver ID, as well as at task level. External tools retain source and version metadata and pass registration and runtime monitoring.

## Illustrative scenario

Bo Liang's execution-oriented agent separates knowledge retrieval, skill loading, and tool calls into `retrieve`, `use_skill`, and `call_tool`. In an intra-city dispatch scenario, the dispatch layer adds richer metadata, selection guidance, mandatory state refresh before writes, a per-session driver quota, and saga side-effect tracking. The implementation places most Tool Dispatch work in contracts, state, and side-effect control. Any outcome figure should be published only with the team's approved evaluation method.

## Related patterns

- **Minimal Tool Set (A5)**: A5 limits per-decision exposure; A1 selects and admits a call from the resulting candidate set.
- **Plan-and-Execute (A2)**: A2 decides stage order and acceptance points. A step may use Programmatic Tool Calling to batch several tool calls, while A1 still admits each call.
- **Guardrail Sandwich (A4)**: A1 handles candidate selection and call admission. A4 adds policy checks and result validation around high-risk execution.
- **Complexity-Based Routing (R2)**: R2 routes a request to a model and effort tier. A1 routes an approved action intent to a tool.

## Design conclusion

Tool Dispatch encodes permission, idempotency, state freshness, approval, rollback, rate limits, and audit behavior as metadata and runtime contracts. Tool choice cannot rely on name, description, and parameter schema alone.

<!-- RELATED-CASE-DEERFLOW:START -->

<section aria-labelledby="related-deerflow-case" class="related-case-band">
<p class="related-case-label">Related open-source engineering case</p>
<h2 id="related-deerflow-case"><a href="https://adpsagent.com/cases/deerflow-guardrail/">DeerFlow: From Pre-Call Interception to Two-Layer Authorization</a></h2>
<p>The Guardrail evolution shared by Willem Jiang uses five public pull requests to connect assembly filtering, runtime authorization, identity, policy, and audit in one tool-execution path.</p>
</section>

<!-- RELATED-CASE-DEERFLOW:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>A1 Tool Dispatch</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-a1-tool-dispatch">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
