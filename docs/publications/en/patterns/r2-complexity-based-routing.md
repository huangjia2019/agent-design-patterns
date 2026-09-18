<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>R2</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>R2 · Complexity-Based Routing</h1>
<p class="publication-deck">Route each request to a model and effort tier using task complexity, risk, and acceptance evidence. Record the decision and escalate when the selected tier fails its checks.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reasoning × Route (selection)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (one routing decision in exchange for task-specific model allocation)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reasoning patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Route each request to a model and effort tier using task complexity, risk, and acceptance evidence. Record the decision and escalate when the selected tier fails its checks.</td>
</tr>
</tbody>
</table>

---

## Problem

Using the most capable and expensive model for every request allocates the same resources to template filling and complex analysis. Prices and model capabilities change, so routing should compare current candidates on a local task set rather than rely on a fixed price-ratio table.

Complexity-based routing assigns model resources from task difficulty and risk. Simple requests use a lower-cost tier; difficult or high-risk requests use a more capable tier. Savings depend on the traffic distribution and model mix and should be calculated from replayed production traces. The pattern can coexist with parallel exploration: routing allocates routine requests, while parallel branches add verification for selected decisions.

## Classification: Reasoning × Route

- **Vertical axis · Reasoning**: The router selects a model, effort level, or reasoning policy for the current request. It does not decompose the request among multiple agents.
- **Horizontal axis · Route**: Complexity, risk, domain, and historical outcomes choose one initial execution tier, with explicit escalation if its acceptance checks fail.

## Solution and mechanics

A single complexity-based routing pass consists of three stages:

1. **Extract signals + classify**: Derive complexity signals from the query, domain, and historical outcomes, then use rules or a lower-cost model to choose a tier. Include the classifier's own cost and latency in the evaluation.
2. **Tiered execution**: Define capability and cost tiers from local evaluation results while keeping a shared call interface. Routing may select both a model and its effort setting.
3. **Escalation fallback**: After a lower-cost tier answers, check its schema, evidence, and business constraints. If it falls short, escalate and retry. The chain needs a configured ceiling; failure at the top should raise an error or hand off to a human.

Production systems commonly use three routing approaches:

<table>
<thead>
<tr>
<th style="text-align: left;">Control location</th>
<th style="text-align: left;">Form</th>
<th style="text-align: left;">Trade-off</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Internalized in the model</td>
<td style="text-align: left;">The model or provider selects an internal reasoning path</td>
<td style="text-align: left;">Low integration effort; limited routing trace and portability</td>
</tr>
<tr>
<td style="text-align: left;">Explicit in the harness</td>
<td style="text-align: left;">The application owns classification, acceptance, and fallback</td>
<td style="text-align: left;">More implementation work; explicit trace and multi-provider control</td>
</tr>
<tr>
<td style="text-align: left;">Third-party router service</td>
<td style="text-align: left;">A routing service selects the target model</td>
<td style="text-align: left;">Common interface; additional dependency and data-processing boundary</td>
</tr>
</tbody>
</table>

Choose the control location from the evidence and governance needed. An explicit harness supports local replay, policy overrides, and provider comparison. Provider-managed or third-party routing may fit when its trace, data boundary, and fallback behavior meet the product's requirements.

## Applicability

- **Mixed request difficulty under a cost or latency budget**: internal BI, customer support, and document processing often combine routine requests with a smaller set of high-risk or multi-step cases. Routing allocates different model and effort tiers while preserving acceptance thresholds.
- **Multi-vendor mixed scenarios**: a team using Claude / DeepSeek / its own fine-tuned model at the same time cannot hand routing to a single vendor and must do it at the engineering layer.
- **Specialized agents that split by action type**: code changes may use the primary model while routine Git operations use a lower-cost model. This routes by action type instead of query complexity.

## Known failure modes

- **Classifier built only on fixed rules**: Keyword matching may misroute unseen query forms. Add uncertainty-based escalation or a lower-cost model, and compare the cost of false downgrades on a replay set.
- **Acceptability check looks only at length**: checking only whether the output is long enough lets through results that violate the schema, exceed numeric bounds, or cite the wrong source data. Do schema-aware validation.
- **Escalation costs more than the target tier**: A lower tier followed by escalation can exceed the direct cost and latency of the final tier. Review request classes with repeated escalation and adjust their initial route.
- **High-risk queries also go to the low tier**: Finance, privacy, or compliance queries may need a reliable tier even when syntactically simple. Encode risk overrides outside the model.
- **Routing without meaningful alternatives**: If every request uses the same model, effort level, and control path, the router adds latency without changing execution. Add routing only when evaluated alternatives produce a useful cost, latency, or quality trade-off.

## Verification and metrics

- **Per-query cost distribution**: Break cost down by routing tier and task class. When the high-capability tier changes materially, distinguish harder traffic from classifier error.
- **Routing accuracy**: Use labels, human review, or a stronger reviewer to judge whether the selected tier met the task requirement. Track unsafe downgrades separately.
- **Fallback rate**: The share of lower-tier results that escalate. Changes call for inspection of thresholds, model capability, and input distribution.
- **Routing decision time**: Measure the classifier's contribution to total latency. If it becomes material, use rule prefilters, caching, or asynchronous features.

## Reference implementation

```
Query comes in → extract complexity signals (length / keywords / domain / history)
            classifier (rules or evaluated classifier model) → choose tier + confidence
            High-risk query (finance / privacy / compliance) → apply policy override to an approved tier
            Execute:
                selected tier runs → result acceptable? → return
                              not acceptable → escalate (schema validation + cost estimate)
                escalation chain reaches its configured ceiling; still failing at the top → raise error / hand off to human
            Emit a trace on every routing decision (query summary / tier / signals / confidence / actual cost / whether escalated)
```

Evaluate rules and classifier models on the same routing set. Make acceptance checks schema-aware, cap the total cost and latency of fallback, and review request classes that repeatedly escalate so they can start at a more suitable tier.

## Illustrative scenario

Consider an internal BI agent serving product, growth, and finance teams. Trace review shows that some requests fill SQL templates or add grouping, while others require multi-step attribution or causal analysis. The first version uses the most capable model for all of them and cannot explain whether resources are being spent on difficult work.

The revised system assigns tiers to template queries, aggregation, attribution, and high-complexity analysis; combines a rule prefilter with a lower-cost classifier; estimates total cost before escalation; forces finance, privacy, and compliance requests through risk-based overrides; and retains every routing trace for replay. Cost and quality changes are calculated from those traces rather than assumed from an industry percentage.

## Related patterns

- **Parallel exploration (R3)**: complementary. Routing picks one tier at a single point in time to save money; parallelism opens N lines at once to buy quality. Within the same agent, everyday work goes through routing and critical decisions start parallelism.
- **Chain of thought (R1)**: the tier that routing selects already contains the CoT effort tier. Routing is the version of CoT effort control raised from a single call to the task level.
- **Dual-mode architecture (R5)**: dual-mode is the architectural extreme of routing—ordinary routing is "pick one tier and run," dual-mode is "run two tiers at once," pushing "tier selection" all the way to "splitting the agent."
- **Failure journal / guard-type patterns**: forcing high-risk queries through the most reliable tier shares the same protective reasoning as "some boundaries cannot be skimped on."

## Design conclusion

Complexity-based routing places token cost, latency, and answer quality on a Pareto frontier. The business SLA determines which point on that curve a request should use. This makes routing a product-economics decision with measurable trade-offs, rather than a fixed model preference.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>R2 Complexity-Based Routing</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-r2-complexity-based-routing">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
