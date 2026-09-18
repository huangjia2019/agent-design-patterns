<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>A4</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>A4 · Guardrail Sandwich</h1>
<p class="publication-deck">Apply policy checks before a high-risk tool call, retain execution evidence, and validate the result afterward, with defined paths for rejection, approval, compensation, and escalation.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Action × Hierarchy</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Cross-cutting (a cross-cutting concern; overhead scales with risk tier)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Action patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Apply policy checks before a high-risk tool call, retain execution evidence, and validate the result afterward, with defined paths for rejection, approval, compensation, and escalation.</td>
</tr>
</tbody>
</table>

---

## Problem

Production agents need admission control before an action and verification afterward. Consider a corporate-transfer agent that misreads the recipient account from an email and submits the payment directly. No control verifies the account, amount, or customer intent before the call, and no post-check validates the receipt or compliance result.

Guardrail Sandwich adds structured pre- and post-action checks around destructive operations. Relevant risks include goal hijacking, tool misuse, parameter misidentification, and sequence-level bypass. Controls should map to the organization's own threat model and compliance obligations.

## Classification: Action × Hierarchy

- **Vertical axis · Action**: What it wraps is the agent's action execution—inserting guards before, during, and after a tool call. This belongs to execution control on the action side.
- **Horizontal axis · Hierarchy**: pre-check → tool call → post-check forms a layered execution boundary, similar to middleware around a request handler. The outer layer admits or rejects the call, and then verifies its result. Plan-and-Execute (A2) separates planning from execution; A4 layers policy enforcement around one execution step.

## Solution and mechanics

A hook can wrap different tools without repeating policy code inside each handler. The lifecycle points most directly related to this pattern are:

- **PreToolUse**: Triggered before a tool call. Depending on the framework contract, it can block, modify parameters, or add context. Typical uses include path allowlists, command denylists, quota checks, and approval gates.
- **PostToolUse**: Triggered after a tool call. It cannot undo an action that has already happened; it can only validate output, prompt the next step, and trigger an audit or saga rollback. Typical use cases are output schema validation, sensitive-data scanning, and side-effect confirmation.

Risk tier, hook order, and rollout policy determine how the checks run:

- **Tier by `risk_level`**: Read-only, ordinary write, destructive, and CRITICAL actions use different guard combinations. High-risk actions add an Approval Gate. The hook configuration file becomes the agent's risk map.
- **Order checks by dependency and cost**: Run local identity and schema checks before network or database checks when policy semantics permit early rejection.
- **Phased rollout**: Begin in monitor mode, move to soft enforcement for clear violations, and enter full enforcement after false-positive and false-negative review. The duration of each phase depends on risk and evidence.

## Applicability

- **Side-effecting actions where a wrong call is costly**: transfers, deleting data, sending messages, calling external APIs. Read operations (read file, search, read-only fetch) need not be sandwiched—every added layer is extra latency overhead.
- **Regulated workflows**: Deterministic constraints such as amount thresholds, dosage bounds, and sanction lists can run before execution; judgment-heavy cases follow the required professional review path.
- **Risk-tiered approval**: Low-risk actions may pass automated checks, while higher-risk actions bind human approval to the exact action intent before execution.

## Known failure modes

- **Sequence-level bypass**: Each action may be allowed in isolation while the sequence exfiltrates data or exceeds scope. Evaluate cumulative action state in addition to single calls.
- **Uniform-check overhead**: Applying every check to every tool adds unnecessary latency. Use different hook sets for low-risk reads and destructive writes.
- **Schema Drift**: The schema validated by the pre-check is inconsistent with what the downstream tool actually expects, so the pre-check passes but the tool fails. The response is to use OpenAPI / JSON Schema as the single source of truth, generating the validation logic on both sides from the same schema.

These failures share an operational cause: hook order, risk classification, and schemas change over time. Treat them as versioned policy assets, test them against representative traces, and review false blocks and missed violations after each release.

## Verification and metrics

- **Block rate**: Observe by rollout phase and sample blocked requests for true violations and false positives.
- **Wrong-action rate**: Track invalid tools, parameters, permissions, and business actions by risk class. High-risk actions do not have an acceptable background error rate.
- **Sandwich latency overhead**: Attribute latency to individual hooks and risk levels. Low-risk reads and high-risk writes should not carry identical checks.
- **Audit completeness**: A trace ID should join PRE, TOOL, and POST records. Retention fields and duration follow applicable policy.

## Reference implementation

```
wrap(tool, ctx):
                for hook in pre_hooks:            # order: cheap first, expensive last
                    verdict = hook(ctx)
                    if verdict.block → short-circuit, return blocked + trace
                    if verdict.modify_args → update ctx.args
                result = tool(**ctx.args)          # execute inside an isolated sandbox
                for hook in post_hooks:
                    verdict = hook(ctx, result)
                    if verdict.rollback → trigger saga inverse, return rolled_back
                    if verdict.modify_result → update result
                return ok + result + full trace (each hook's passed/reason/latency)
```

Wrap every destructive tool. Make retryable hooks idempotent so network failures cannot repeat a transfer, and use `trace_id` to join admission, execution, verification, and compensation records.

## Illustrative scenario

Consider a bank-transfer agent that wraps destructive tools in a sandwich. PRE checks RBAC, amount and risk tiers defined by bank policy, recipient allowlists, and sanctions; TOOL uses an idempotency key and stores the external receipt; POST performs anti-money-laundering checks, reconciles the result, triggers saga compensation where possible, and writes the audit ledger. Legal, risk, and business owners determine hook order. In healthcare, the same structure uses role permissions, dosage policy, medical-history constraints, contraindications, and drug-interaction checks.

## Related patterns

- **Tool Dispatch (A1)**: A1 selects and admits a tool call. A4 applies policy checks and validates the result around high-risk execution.
- **Plan-Execute (A2)**: The approval nodes and compliance checks in an A2 plan are, in practice, often implemented by A4's pre-check.
- **Approval Gate (governance module)**: An Approval Gate binds a human decision to a specific action intent. A4 applies machine-enforced checks around the tool call. Low-risk actions may pass automated checks; higher-risk actions add approval before execution.
- **Failure Journals (memory module)**: Composition bypass and memory poisoning cannot be handled by a single action guard. They also require cross-task failure records and audit evidence.

## Design conclusion

Guardrail Sandwich places checks and constraints before, during, and after an action. Each layer records its result and provides a defined path for rejection, rollback, compensation, or human takeover.

## Open-source implementation

[**DeerFlow Guardrails and Two-Layer Authorization**](https://adpsagent.com/cases/deerflow-guardrail/) traces five public pull requests across assembly filtering, run-time authorization, trusted identity, RBAC, and RunJournal, with explicit boundaries for this pattern.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>A4 Guardrail Sandwich</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-07-18">2026-07-18</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-a4-guardrail-sandwich">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
