<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern matrix</a>
<span style="margin: 0 0.45rem;">/</span>White Paper<span style="margin: 0 0.45rem;">/</span>Reasoning
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper · Module Overview</p>
<h1>Reasoning · Compiling Evidence into Reviewable Decisions</h1>
<p class="publication-deck">Reasoning artifacts, effort routing, parallel exploration, hypothesis testing, live interaction, and engineering acceptance.</p>
</header>

Reasoning sits between perception and memory on one side and action on the other. Perception supplies current signals. Memory retrieves prior facts and experience. Reasoning turns them into a decision; action determines how that decision may change an external system.

A production system has to manage more than the final answer. A decision also needs evidence references, alternatives, uncertainty, budget use, a verification method, and a next step. Downstream components can then review, reject, or execute it under control.

<figure class="workshop-diagram"><img alt="A reasoning request is routed into serial, parallel, iterative, or layered reasoning before producing a structured decision" src="../../assets/images/workshops/reasoning-selection-en.svg"/><figcaption>R2 selects resources and a reasoning path. R1, R3, R4, and R5 provide different decision structures. They may be composed; this is not a fixed pipeline.</figcaption></figure>

## The output boundary

“Approve the request” is only a conclusion. A decision that can cross a system boundary must state what supports it, when it remains valid, what is unresolved, and who may authorize the next action.

<pre><code class="language-yaml">decision_id: dec_01K...
goal_ref: goal://incident/482
evidence_refs:
  - log://gateway/482#timeout
  - change://config/917
choice: rollback_recent_configuration
alternatives:
  - keep_observing
  - isolate_single_instance
uncertainty:
  level: medium
  unresolved: database latency has not been excluded
validation:
  before_action: reproduce on canary
  after_action: error rate returns to baseline
authority:
  required: on_call_approval
next_action: prepare_rollback_intent
</code></pre>

This record is still a decision, not an execution command. The Action module must recheck authority, tools, arguments, current state, and acceptance conditions.

## Five patterns, five engineering problems

<table><thead><tr><th>Pattern</th><th>Scope</th><th>Primary artifact</th></tr></thead><tbody>
<tr><td><a href="https://adpsagent.com/patterns/r1-chain-of-thought/">R1 Chain of Thought</a></td><td>Forms a sequential judgment and manages API-visible summaries, evidence, and model metadata</td><td>Reasoning summary, evidence binding, decision record</td></tr>
<tr><td><a href="https://adpsagent.com/patterns/r2-complexity-based-routing/">R2 Complexity-Based Routing</a></td><td>Selects a model, effort level, and fallback path from difficulty, risk, evidence gaps, and service objectives</td><td>RouteDecision, budget, fallback policy</td></tr>
<tr><td><a href="https://adpsagent.com/patterns/r3-parallel-exploration/">R3 Parallel Exploration</a></td><td>Runs isolated candidate paths and aggregates them according to the cost of error</td><td>Branch results, disagreement record, aggregate decision</td></tr>
<tr><td><a href="https://adpsagent.com/patterns/r4-iterative-hypothesis-testing/">R4 Iterative Hypothesis Testing</a></td><td>Updates hypotheses with new evidence until convergence, budget exhaustion, or human escalation</td><td>Hypothesis tree, counter-evidence, exit reason</td></tr>
<tr><td><a href="https://adpsagent.com/patterns/r5-talker-reasoner/">R5 Talker-Reasoner</a></td><td>Separates low-latency interaction from high-cost analysis and hands off structured state</td><td>Task packet, shared state, reasoning result packet</td></tr>
</tbody></table>

## Difficulty and risk are separate decisions

A difficult problem does not automatically justify broader authority. A short request may still trigger a high-risk action. The router should score reasoning difficulty and business risk separately, then set the model tier, number of branches, time budget, and human boundary.

<table><thead><tr><th></th><th>Low risk</th><th>High risk</th></tr></thead><tbody>
<tr><th>Low difficulty</th><td>Rules or a lightweight model; results are easy to recheck</td><td>Computation may be simple, while evidence and approval stay strict</td></tr>
<tr><th>High difficulty</th><td>Deep reasoning or parallel exploration under cost and latency limits</td><td>Deep reasoning, independent verification, explicit human review, and stop rules</td></tr>
</tbody></table>

## Patterns can be nested

A production-incident workflow may use R2 to classify difficulty and risk. A common low-risk case enters R1. Conflicting evidence starts R3 so that independent branches can examine the incident. If the cause remains unclear, R4 advances through hypothesis, evidence collection, and falsification. While the user waits, the R5 Talker reports progress and the Reasoner continues in the background.

The composition needs an explicit convergence point. It waits for required branches, handles timeouts and conflicts, applies exit conditions, and reduces the result to one decision schema. More branches without convergence merely produce more answers.

## Budget, exit, and escalation

<table><thead><tr><th>Control</th><th>Engineering question</th></tr></thead><tbody>
<tr><td>Budget</td><td>How many tokens, model calls, concurrent branches, seconds, and external lookups are allowed?</td></tr>
<tr><td>Evidence</td><td>Which claims require external facts, and are those facts still current?</td></tr>
<tr><td>Disagreement</td><td>When do majority vote, any-alarm, and an independent judge match the cost of error?</td></tr>
<tr><td>Exit</td><td>How does the run stop on sufficient evidence, indistinguishable candidates, budget exhaustion, or a changed user goal?</td></tr>
<tr><td>Escalation</td><td>Which hypotheses, evidence, excluded paths, and open questions accompany a human handoff?</td></tr>
</tbody></table>

## Interfaces with adjacent modules

<table><thead><tr><th>Module</th><th>Input to Reasoning</th><th>Output from Reasoning</th></tr></thead><tbody>
<tr><td>Perception</td><td>Signals, provenance, time, and parsed observations</td><td>Requests for another observation or clarification</td></tr>
<tr><td>Memory</td><td>Versioned, scoped facts, experience, and progress</td><td>Publishable decision summaries and applicability boundaries</td></tr>
<tr><td>Action</td><td>Tool results, business receipts, and current state</td><td>Structured decisions without inherited execution authority</td></tr>
<tr><td>Reflection</td><td>Evaluation results, failure attribution, and delayed outcomes</td><td>Decision records and reproducible acceptance conditions</td></tr>
<tr><td>Governance</td><td>Authority, budget, prohibited operations, and human-review rules</td><td>Risk statements, pending intents, and evidence</td></tr>
</tbody></table>

## Validation

- **Decision quality:** accuracy, false positives, false negatives, and calibration on a business evaluation set.
- **Routing quality:** misrouting and unnecessary escalation against the least costly acceptable path.
- **Convergence quality:** useful falsification, limit exits, human escalation, and repeated evidence gathering.
- **Operating cost:** quality, latency, tokens, concurrency, and external-tool cost reported together.
- **Reviewability:** whether critical conclusions resolve to evidence, versions, rules, and accountable principals.

## Published patterns

- [R1 · Chain of Thought](https://adpsagent.com/patterns/r1-chain-of-thought/)
- [R2 · Complexity-Based Routing](https://adpsagent.com/patterns/r2-complexity-based-routing/)
- [R3 · Parallel Exploration](https://adpsagent.com/patterns/r3-parallel-exploration/)
- [R4 · Iterative Hypothesis Testing](https://adpsagent.com/patterns/r4-iterative-hypothesis-testing/)
- [R5 · Talker-Reasoner (extension)](https://adpsagent.com/patterns/r5-talker-reasoner/)

<section aria-labelledby="reasoning-workshop-link" class="related-case-band">
<p class="related-case-label">Workshop source</p>
<h2 id="reasoning-workshop-link"><a href="https://adpsagent.com/workshops/reasoning-2026-08-26/">First Reasoning Module Workshop</a></h2>
<p>Participants, the public discussion scope, and a reading path through the current patterns.</p>
</section>

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>Reasoning: Compiling Evidence into Reviewable Decisions</em>, Agent Design Pattern White Paper, 2026.</p><p><a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Scope:</strong> This page defines module boundaries and engineering checks. It does not certify a model, product, or enterprise implementation. Scenarios illustrate pattern composition; named cases follow the evidence notes in their engineering case reports.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/reasoning-2026-08-26/">First Reasoning Module Workshop</a> (26 August 2026); published ADPS Reasoning pattern specifications</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-reasoning">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
