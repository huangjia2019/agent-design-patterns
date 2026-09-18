<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>R4</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>R4 · Iterative Hypothesis Testing</h1>
<p class="publication-deck">Test versioned hypotheses against evidence, revise the active set, and stop on confirmation, no progress, or a hard limit.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reasoning × Loop (transition)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">High (cumulative cost over many iterations; must be bounded by circuit breakers and budget caps)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reasoning patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Test versioned hypotheses against evidence, revise the active set, and stop on confirmation, no progress, or a hard limit.</td>
</tr>
</tbody>
</table>

---

## Problem

Some tasks cannot be answered in one reasoning pass. The cause is unknown, evidence arrives step by step, and the first judgment is often wrong. Fault diagnosis is a typical case: a model may rank the actual cause far below a familiar but irrelevant explanation. Committing after one pass amplifies that error. Repeating the same pass does not help because the agent still has the wrong account of the system.

Iterative hypothesis testing maintains a set of hypotheses and updates it after each evidence-gathering step. A retry repeats an operation under the same diagnosis. This pattern changes the diagnosis, evidence request, or experiment before the next round. Parallel Exploration evaluates several branches at once; R4 revises hypotheses across time.

## Classification: Reasoning × Loop

- **Vertical axis · Reasoning**: Each round proposes or updates hypotheses, requests evidence that can distinguish them, and records a verdict.
- **Horizontal axis · Loop**: The next round depends on the previous evidence and verdict. The loop exits on confirmation, falsification of all active hypotheses, no progress, or a configured budget.

## Solution and mechanics

A production implementation separates three responsibilities. They may be stages in one agent or roles assigned to different agents:

1. **Hypothesis generation (Planner)**: List candidate hypotheses from symptoms and historical cases, ranked by prior probability. Select the model and effort setting through local evaluation of hypothesis coverage, missed causes, and cost.
2. **Evidence collection (Generator)**: Given a hypothesis, choose tools that can test it, such as metrics, logs, or sensors. Evidence must come from traceable, reproducible data sources; the model's own impression is not external evidence.
3. **Judgment (Evaluator)**: Decide whether the evidence confirms, falsifies, or leaves the hypothesis unresolved. The Evaluator should search explicitly for counterevidence. Compare prompts and model configurations on replay data instead of assuming that one framing always improves accuracy.

Falsified hypotheses leave the active set, confirmed hypotheses exit, and insufficient evidence creates another evidence request. New evidence that invalidates earlier assumptions rebuilds the active set. When the time, token, or round budget expires without convergence, record the unresolved hypotheses and escalate instead of selecting the highest prior by default.

## Applicability

- **Diagnostic tasks**: Industrial fault localization, medical diagnosis, and safety incident analysis. Evidence must be gathered step by step, and a line of inquiry that fails can be reset and restarted.
- **Complex code debugging**: Each failing test, trace, or controlled change updates the active hypotheses and determines the next diagnostic action.
- **Judgments that require reproducible evidence**: Each verdict can retain the test, source, version, and transition that supported or rejected a hypothesis.

## Known failure modes

- **Using it under a tight response budget**: When latency matters more than iterative diagnosis or the cost of error is low, a single pass may be sufficient.
- **Continuing after the configured limit**: Reaching the cap without convergence calls for reset, task decomposition, better evidence, or human escalation, not an unbounded extra round.
- **The Evaluator only looks for supporting evidence**: This framing amplifies confirmation bias. Record supporting, falsifying, and missing evidence, and prefer tests that distinguish competing hypotheses.
- **Preserving invalid assumptions**: New evidence may invalidate the root framing or only one branch. Record dependency links so the runtime can retire affected hypotheses and rebuild the active set at the correct level.
- **No bounded exit**: Enforce limits for rounds, cost, tokens, elapsed time, and no-progress. On exhaustion, preserve unresolved hypotheses and escalate or decompose the task.

## Verification and metrics

- **Convergence Rate**: The share of cases that reach a verifiable conclusion within budget. Separate failures caused by task size, unavailable evidence, and weak hypotheses.
- **Iterations to convergence**: Track the distribution by task class. Sustained growth indicates low information gain per round or weaker hypothesis generation.
- **Falsification Rate**: Observe whether candidate hypotheses are actually eliminated by counterevidence. A long period with no falsification may indicate confirmation bias.
- **Human-escalation coverage**: Review whether cases with unresolved high-risk hypotheses or exhausted evidence paths reached the required decision owner.

## Reference implementation

```
Task arrives → Planner generates a hypothesis list (ranked by prior probability)
            Loop (limit max_iterations):
                Pick the unvalidated hypothesis with the highest prior
                Generator collects evidence (deterministic data source)
                Evaluator judges (emphasize falsification over confirmation):
                    confirmed   → converge, exit
                    falsified   → prune, continue to the next hypothesis
                    if all hypotheses are falsified → take the new evidence back to the Planner to regenerate
                New evidence invalidates assumptions → retire dependent hypotheses and rebuild the affected set
            Loop ends still without convergence → trigger HITL, attach the full hypothesis tree + evidence + iterations run
            Keep a trace on file throughout (compliance scenarios require long-term retention)
```

For production, evaluate model assignments for each responsibility, enforce a strict evidence schema, attach the hypothesis tree and evidence to human escalation, and retain the trace according to the applicable audit policy.

## Illustrative scenario

Consider a plant alarm whose initial hypotheses focus on common mechanical faults. A field engineer then supplies a new fact: a remote configuration change occurred before the alarm. The system resets the hypothesis tree instead of forcing the fact into the old ranking, and it traces the changed control parameter. Hypothesis generation, evidence collection, and judgment use separate schemas; the evaluator searches for counterevidence; insufficient evidence escalates to a human; and restarting critical equipment always requires approval. Convergence must be evaluated through incident replay and field review.

## Related patterns

- **Parallel Exploration (R3)**: R3 evaluates several hypotheses or solution paths concurrently. R4 updates a hypothesis set over successive evidence-gathering rounds. A system may use R3 inside one R4 round when parallel tests are independent.
- **Chain of Thought (R1)**: Each round retains an ordered evidence request, observation, and verdict trace.
- **Complexity-Based Routing (R2)**: Hypothesis generation, evidence interpretation, and evaluation can use independently selected models and effort levels.
- **Talker-Reasoner (R5)**: A Reasoner may run R4 asynchronously while the Talker remains bound to accepted results in shared state.

## Design conclusion

Exit when evidence meets the confirmation rule, every active hypothesis has been falsified, or a budget or no-progress rule requires escalation. The trace should retain each hypothesis version, its evidence, its verdict, and the reason for the next transition.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>R4 Iterative Hypothesis Testing</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-r4-iterative-hypothesis-testing">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
