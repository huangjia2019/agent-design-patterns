<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>R1</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>R1 · Chain-of-Thought</h1>
<p class="publication-deck">Manage available reasoning artifacts, evidence, decisions, and model metadata as structured data for replay, audit, and fallback.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reasoning × Chain (canonical)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Variable (reasoning effort, model interface, and retention policy)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reasoning patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern summary</strong></td>
<td style="text-align: left;">Manage available reasoning artifacts, evidence, decisions, and model metadata as structured data for replay, audit, and fallback.</td>
</tr>
</tbody>
</table>

---

## Problem

A model may return a plausible conclusion without exposing the evidence, intermediate decisions, model settings, or fallback path needed to review it. When the result fails, ordinary application logs may show the request and answer but not which sources or decision artifacts influenced the action.

Here, Chain-of-Thought means engineering the reasoning trajectory: storing permitted reasoning artifacts or summaries, preserving input evidence, handling cross-model fallback, and controlling reasoning effort by task complexity. The familiar “Let's think step by step” prompt is only one prompting technique; reasoning APIs expose different structured fields that the runtime must normalize.

## Classification: Reasoning × Chain

- **Vertical axis · Reasoning**: CoT concerns the trajectory from evidence to decision. Depending on the model interface, the system may receive a public rationale, a structured summary, or protected reasoning tokens. The other reasoning patterns build on this trajectory in different ways.
- **Horizontal axis · Chain**: The retained trajectory links input evidence, intermediate decisions, and output in order. Later patterns may branch or iterate, but each branch still needs an ordered evidence-to-decision record.

## Solution and mechanics

CoT is a multi-form engineering category. Its runtime responsibilities include:

1. **Persistence**: Retain the reasoning summaries, evidence references, decisions, and model metadata that the provider and policy allow, indexed by `trace_id`.
2. **Cross-model normalization**: Providers expose public summaries, structured fields, or protected reasoning tokens differently. Normalize available artifacts into one schema and retain provider, model, interface version, and visibility metadata.
3. **Cross-model fallback normalization**: reasoning fields and signatures can be provider-specific. Before a fallback call, remove or transform fields that the target model does not accept, then validate the request against the target schema.
4. **Effort control**: Reasoning effort consumes tokens and latency without guaranteeing better task outcomes. Expose supported effort levels as a per-request setting and select them from task-level evaluation.

One boundary matters: a model's written rationale may be a post-hoc account rather than a faithful record of its internal computation. Treat it as an observability signal, not proof of how the model reached the answer. Critical decisions still need external evidence and verification.

## Applicability

- **Multi-step judgments that require an evidence trail**: Claims review, contract analysis, and credit workflows may need each conclusion linked to source evidence, applicable rules, model version, and approval.
- **Compliance audit-trail scenarios**: Finance, healthcare, and legal workflows may require decision evidence, model metadata, approvals, and retained rationale. The exact record follows applicable policy and provider constraints.
- **Teaching and debugging scenarios**: Show processed reasoning summaries and intermediate evidence when this helps locate an error, without assuming access to private model reasoning.

## Known failure modes

- **Forcing step instructions onto a reasoning model**: Adding a generic “analyze step by step” instruction can increase token use without improving the target task. Test prompting choices on the actual evaluation set.
- **Fallback signature mismatch**: provider-specific reasoning fields or signatures may be invalid when traffic moves to another model. Normalize the message schema before fallback and test the switch path; otherwise the fallback request can fail when the primary model is rate-limited.
- **Writing traces only to log files**: When a reviewer needs the evidence, applicable rules, model version, and final decision for a case, scattered log records are difficult to reconstruct. Use structured traces that are queryable by `trace_id`.
- **Using one effort level for every task**: Template extraction and multi-source risk analysis have different latency and quality needs. Compare effort levels by task class and risk instead of setting one global default.
- **Enabling deep reasoning in latency-sensitive scenarios**: Extended reasoning can violate an interactive response budget. Use a lower effort level, asynchronous execution, or the Talker-Reasoner pattern.

## Verification and metrics

- **Reasoning token share**: Track the share of reasoning tokens by task class. A material rise from the local baseline may indicate over-thinking; a drop should be checked for under-reasoning on difficult tasks.
- **Fallback normalization success rate**: Verify that model-specific reasoning fields are removed or transformed before a fallback call. Any incompatible payload is an operational defect.
- **Trace queryability**: Verify that a historical decision can be reconstructed from its trace ID using retained evidence, model metadata, outputs, and allowed reasoning summaries. Applicable policy defines what may be stored.

## Reference implementation

```
task arrives → choose effort tier by complexity (off / low / medium / high / max)
            model returns retainable summary / structured decision / model metadata → normalize into a unified schema → into structured trace
            if primary model is rate-limited and falls back:
                normalize or remove reasoning fields that the target model does not accept, then validate and send
            dual views for audit retrieval:
                audit view    → permitted reasoning summary + evidence + final decision + fallback chain
                customer view → redacted rationale, no protected reasoning details
            return final_answer + audit trace (indexed by trace_id, retained according to policy)
```

Test prompting and effort settings on the target task set. Keep provider-field normalization versioned, and emit evidence, decisions, model metadata, and fallback transitions as structured events that remain queryable by `trace_id`.

## Illustrative scenario

Bo Liang's execution-oriented agent separates explanatory reasoning from the structured `answer` that downstream programs consume. The runtime stores provider-permitted summaries and evidence in the trace, while the `answer` is a JSON decision object that drives subsequent actions. This keeps audit material separate from the executable control contract.

When JSON parsing fails, the runtime uses a predefined safe fallback instead of crashing or retrying at random. The answer schema is strictly validated, parse failures enter monitoring, and audit retention follows the visibility allowed by the model interface and organizational policy.

## Related patterns

- **Complexity-Based Routing (R2)**: R2 selects a model and effort tier. R1 normalizes and records the resulting evidence-to-decision trajectory.
- **Parallel Exploration (R3)**: Each branch keeps its own ordered trace; the verifier compares branch artifacts and evidence.
- **Iterative Hypothesis Testing (R4)**: Each round records a hypothesis, evidence request, result, and verdict. The next round links to that transition.
- **Talker-Reasoner (R5)**: The Reasoner produces the slower analysis artifact while the Talker maintains the interaction contract.

## Design conclusion

The engineering task is to manage available reasoning artifacts, evidence, decisions, and fallback metadata across their lifecycle. Private model reasoning is not required for an auditable action contract.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>R1 Chain of Thought</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-r1-chain-of-thought">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
