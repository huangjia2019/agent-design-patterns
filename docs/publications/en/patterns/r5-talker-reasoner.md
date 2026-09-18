<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>R5</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>R5 · Talker-Reasoner · Dual-Process Architecture</h1>
<p class="publication-deck">Keep live conversation responsive while a separate Reasoner updates versioned shared state under timeout and stale-result controls.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reasoning × Hierarchy</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (interactive and asynchronous paths can use independently evaluated models and budgets)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reasoning patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Keep live conversation responsive while a separate Reasoner updates versioned shared state under timeout and stale-result controls.</td>
</tr>
</tbody>
</table>

---

## Problem

Many reasoning patterns assume the user can wait. That may be acceptable in an asynchronous task but not in a live conversation or voice interface. The engineering problem is the period of silence while deep analysis runs.

Talker-Reasoner assigns interaction and deep analysis to separate agents. The Talker meets the product's first-response budget and gathers clarification; the Reasoner runs in the background; both coordinate through a shared belief state.

## Classification: Reasoning × Hierarchy

- **Vertical axis · Reasoning**: The pattern separates an interaction response from a slower analysis job. The two paths have different output contracts, latency budgets, and permissions.
- **Horizontal axis · Hierarchy**: The Talker owns the live turn; the Reasoner supplies a versioned analysis artifact through shared state. The Talker cannot present unaccepted background work as a conclusion.

## Solution and mechanics

A single dual-process round consists of three parts:

1. **Talker responds within the interaction budget**: The interactive path acknowledges the request and gathers clarification. Its output schema prevents unverified recommendations before analysis completes.
2. **Reasoner runs asynchronously**: A separately evaluated model performs the slower analysis and writes a structured result to shared state without blocking the live turn.
3. **Belief-state coordination**: the two agents communicate through shared state, with locks or version checks preventing overlapping writes. The Talker reads accepted reasoning at defined turn boundaries and incorporates it into the next response.

Define how new input affects an active Reasoner job. `QUEUE` waits for the current job, `INTERRUPT` cancels it and starts again with the new state, and `PARALLEL` permits concurrent jobs with version checks. Select the policy by product semantics and cap outstanding work.

## Applicability

- **Real-time conversation**: Tutoring, customer service, and personal assistants where first response and deep analysis have different latency budgets.
- **Voice agents**: Phone and voice assistants where prolonged silence breaks the interaction.
- **Advisory sessions with progressive clarification**: The Talker gathers preferences while the Reasoner analyzes the accepted information snapshot. New answers either update, cancel, or queue the background job under the configured policy.

## Known failure modes

- **Talker overreach**: The interactive path gives a concrete recommendation before accepted analysis is available. Constrain its schema, evidence access, and permissions, then measure violations in session review.
- **The Reasoner has no timeout or cancel**: A background task can continue after the user changes topic. Add a configured timeout and active cancellation tied to the conversation state.
- **Unpersisted belief state**: A later session cannot recover an accepted analysis or identify that it is stale. Persist the state with user, topic, source-version, and validity boundaries.
- **Unversioned handoff into conversation**: The Talker inserts an analysis produced from an earlier preference snapshot. Bind each result to the input version and accept it only at a defined turn boundary.
- **Using two paths for a purely asynchronous task**: Document generation and batch processing may need only a job status and final result. Do not add a Talker unless the product has a live interaction requirement.

## Verification and metrics

- **Talker response latency p99**: Compare with the single-agent first-response baseline and the product's interaction budget.
- **Talker overreach rate**: Sample whether the Talker gives concrete conclusions before the Reasoner finishes. Fix violations in the output schema, prompt, or permissions.
- **Belief hit rate**: Verify that later turns retrieve and correctly use confirmed belief state without stale or cross-user contamination.
- **Cost and cancelled work**: Measure interactive calls, Reasoner jobs, cancellations, and stale results per completed task. Compare them with first-response latency and final acceptance quality.

## Reference implementation

```
User speaks →
                If first turn: create belief state, asynchronously trigger Reasoner (non-blocking)
                Talker replies within interaction_budget (bounded schema, no unverified recommendation)
                If an accepted Reasoner result matches the input version → Talker may use it
            Reasoner in background (model selected by analysis evaluation):
                Deep analysis → write belief state (structured conclusions + recommendations)
                With configured timeout + cancel when the user changes topic
            belief state: persisted across sessions, writes take a lock
            Return Talker reply + the background-maintained belief
```

Enforce the Talker contract in schema and permissions, not only in its prompt. Give Reasoner jobs timeout and cancellation, persist belief state in a suitable store, and use locks or optimistic version checks for shared-state writes.

## Illustrative scenario

Consider a study-abroad advisory agent. When a user asks which school fits better, the Talker first acknowledges the comparison and asks what outcome matters most. The Reasoner evaluates grades, research experience, and interests in the background and writes its conclusion to the belief state. On the next turn, the Talker incorporates the result alongside the user's new preference. A tutoring system can use the same split with separate teacher and student trace views. First-response latency, final quality, and human override should be measured independently on real sessions.

## Related patterns

- **Complexity-Based Routing (R2)**: R2 selects one execution tier for a request. R5 keeps an interactive path active while a separate analysis job runs.
- **Iterative Hypothesis Testing (R4)**: The Reasoner may use R4 internally, while the Talker remains bound to accepted shared state.
- **Chain of Thought (R1)**: R1 defines the reasoning artifacts and evidence trace produced by the Reasoner.
- **Layered Retention (M1)**: Shared belief state needs user, topic, version, validity, and cross-session retention boundaries.

## Design conclusion

Talker-Reasoner separates two response obligations. The Talker maintains the real-time interaction with short, bounded replies. The Reasoner works on the slower analysis and returns a considered result when ready. The Talker's message is a valid interaction in its own right, not an unfinished draft of the Reasoner's answer.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>R5 Talker-Reasoner</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-r5-talker-reasoner">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
