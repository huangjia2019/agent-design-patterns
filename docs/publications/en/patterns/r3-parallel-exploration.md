<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>R3</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>R3 · Parallel Exploration</h1>
<p class="publication-deck">Run independent reasoning branches, preserve their evidence, and aggregate only when measured quality gains justify the added cost.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reasoning × Parallel (fan-out)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">High (multiple branches plus aggregation)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reasoning patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Run independent reasoning branches, preserve their evidence, and aggregate only when measured quality gains justify the added cost.</td>
</tr>
</tbody>
</table>

---

## Problem

One reasoning run may omit a relevant feature or settle on a weak hypothesis. Repeating the same configuration can reproduce the same blind spot, while ordinary review sees only the selected result.

Parallel Exploration runs independently configured branches for the same decision and combines their artifacts under an explicit aggregation rule. It uses additional compute when broader evidence, alternative hypotheses, or independent checks justify the cost.

## Classification: Reasoning × Parallel

- **Vertical axis · Reasoning**: R3 runs multiple candidate solutions for the same question. C2 Fan-Out/Gather distributes independent subtasks. Compare the unit of work: R3 branches compete or corroborate on one decision, while C2 branches each produce a different part of the final artifact.
- **Horizontal axis · Parallel**: Branches execute concurrently from a shared task contract without reading one another's intermediate state. A verifier or aggregator combines their typed results.

## Solution and mechanics

A single round of parallel exploration has three stages:

1. **Dispatch**: Replicate the query into N branches and create diversity through prompts, sampling settings, models, or evidence sources. Choose N from task risk, branch correlation, and budget, using local ablation tests to find diminishing returns.
2. **Isolated execution**: Each branch has independent intermediate state and failure handling. Shared evidence may be intentional, but one branch must not copy another branch's conclusion before aggregation.
3. **Aggregation**: use an aggregation strategy to synthesize the N results into one. Majority vote is only one option; the selected rule should encode the cost of different errors.

Choose the aggregation strategy from the output type and the relative cost of false positives, false negatives, and unresolved disagreement:

<table>
<thead>
<tr>
<th style="text-align: left;">Aggregation strategy</th>
<th style="text-align: left;">Suitable scenario</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Majority</td>
<td style="text-align: left;">Enumerable answers, symmetric error cost (math, classification)</td>
</tr>
<tr>
<td style="text-align: left;">Weighted</td>
<td style="text-align: left;">Branches differ in reliability (different models / different compute tiers)</td>
</tr>
<tr>
<td style="text-align: left;">Verifier</td>
<td style="text-align: left;">Open-ended answers (writing, code, planning)</td>
</tr>
<tr>
<td style="text-align: left;">First-Correct</td>
<td style="text-align: left;">A clear success criterion exists (test-driven)</td>
</tr>
<tr>
<td style="text-align: left;">Any-Alarm</td>
<td style="text-align: left;">High-risk with asymmetric error cost (healthcare, finance, security)</td>
</tr>
</tbody>
</table>

## Applicability

- **High-risk judgments with asymmetric error cost**: Medical image triage, financial controls, anti-money-laundering, and vulnerability review may route any predefined high-risk finding to qualified review instead of accepting a majority vote.
- **Large answer spaces where a single chain is unstable**: complex diagnosis, multi-hop reasoning, and tasks that need self-consistency to improve reliability.
- **High-consequence decision points**: A final review before an irreversible commitment may justify multiple evidence paths, while the actual confidence gain must be measured on the target evaluation set.

## Known failure modes

- **Correlated branches**: Identical prompts, evidence, models, or shared intermediate state can produce duplicate conclusions. Measure effective branch diversity and isolate mutable state.
- **Insufficient prompt perturbation**: When multiple branches return nearly identical answers, parallel exploration has degraded into duplicate sampling and the added compute has produced no new evidence. Check whether sampling settings, prompts, models, and evidence sources are genuinely independent.
- **Using majority for asymmetric risk**: A minority high-risk finding can be lost under a vote. Define escalation and abstention rules from the business error model.
- **Incorrect early termination**: An Any-Alarm policy may stop immediately after a qualifying alarm, but it cannot conclude “no alarm” until every required branch completes or the policy records an incomplete result.
- **Overusing parallelism**: Running multiple branches on simple or low-risk tasks adds cost without a decision benefit. Compare against a single-chain baseline.

## Verification and metrics

- **Branch agreement rate**: Interpret agreement together with task difficulty. High agreement may indicate a simple task or insufficient branch independence.
- **Effective N**: Count independent evidence paths or conclusions. Concurrent branches that repeat the same reasoning do not increase effective N. When it stays low, vary prompts, models, or sources before adding branches.
- **Aggregation cost share**: Measure the aggregator's share of total cost and latency. If it dominates, use lighter aggregation or stricter artifacts.
- **Quality gain**: Compare parallel and single-chain runs on the same evaluation set and report cost and latency alongside quality.

## Reference implementation

```
replicate query into N branches:
                each branch → independent runtime → sample at a different temperature → (answer, confidence)
            aggregate(N results, strategy):
                Majority   → the answer with the most votes
                Weighted   → score results with calibrated branch reliability or an external rubric
                Verifier   → hand off to an independent verifier model to score and decide
                Any-Alarm  → if any branch hits a high-risk label, escalate, ignoring the majority
            return final_answer + complete branch trace (per-branch answer / confidence / aggregation strategy / final decision)
```

Evaluate branch diversity, verifier quality, and aggregation rules on the target task set. Respect provider limits, retain each branch trace, and test incomplete, timeout, disagreement, and Any-Alarm paths explicitly.

## Illustrative scenario

Consider a medical-imaging assistant that grades pulmonary nodules. A single chain may miss a suspicious morphology. The revised system uses independent branches with varied prompts or evidence views. Aggregation follows an Any-Alarm rule rather than majority vote: any branch detecting a predefined high-risk sign sends the case to a human second review. Branches run in isolated runtimes and are not terminated early in Any-Alarm scenarios. Accuracy and compute must be reported on an approved clinical evaluation set, with retention governed by the institution's policy.

## Related patterns

- **Complexity-Based Routing (R2)**: R2 can reserve R3 for task classes whose measured quality gain justifies its cost and latency.
- **Chain of Thought (R1)**: Each branch retains its own ordered evidence and decision artifacts under the R1 trace contract.
- **Fan-Out/Gather (C2)**: R3 branches address the same decision with alternative reasoning or evidence. C2 branches produce distinct parts of one deliverable.
- **Iterative Hypothesis Testing (R4)**: R3 evaluates branches concurrently; R4 revises a hypothesis set across evidence-gathering rounds. R4 may use R3 within one round.

## Design conclusion

Parallel Exploration runs independently configured reasoning branches and combines their artifacts under an explicit rule. Verification must cover branch diversity, aggregation errors, incomplete results, cost, and latency against a single-run baseline.

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>R3 Parallel Exploration</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-r3-parallel-exploration">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
