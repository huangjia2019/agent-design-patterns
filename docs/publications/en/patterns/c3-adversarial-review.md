<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>C3</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>C3 · Adversarial Review</h1>
<p class="publication-deck">Separate proposal, review, and adjudication roles; give reviewers independent evidence and a shared rubric before release.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Collaboration × Loop (debate)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">High (multiple independent roles, review rounds, and audit traces)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Collaboration patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Assign one agent to produce a proposal and one or more separately configured reviewers to challenge it. Define reviewer duties, evidence sources, decision authority, and exit conditions before the review begins.</td>
</tr>
</tbody>
</table>

---

## Problem

Several prompts against the same model and evidence do not by themselves establish an independent review. Separation may require different organizational roles, evidence sources, runtimes, models, permissions, and decision authority, depending on the applicable policy.

Adversarial review addresses how a high-stakes decision receives structurally independent scrutiny. In financial credit, medical assistance, legal assessment, and regulatory workflows, the required form of independence comes from the applicable policy and the reviewing organization; using several prompts or vendors does not by itself prove compliance. Compared with single-agent Generator-Critic, this pattern also needs model routing, separated context and evidence, independent traces, and an explicit adjudication contract.

## Classification: Collaboration × Loop

- **Vertical axis · Collaboration**: One agent proposes a solution and another is assigned to test it. Independence may come from model family, context, evidence source, runtime, review instructions, organizational ownership, or a combination of these controls. A vendor difference is one possible signal, not a sufficient condition.
- **Horizontal axis · Loop**: A proposal, challenge, response, and adjudication can repeat within a bounded review budget. Each round preserves findings, evidence, accepted changes, and unresolved disagreement.

## Solution and mechanics

A single adversarial review consists of three roles and one loop:

1. **Proponent proposes**: the generator agent produces the initial solution.
2. **Critic reviews**: An independently configured reviewer tests the proposal against assigned failure hypotheses, evidence, and rubric. `no_issues_found` is valid only when the trace shows adequate coverage.
3. **Proponent revises**: the solution is revised based on the issues the critic raised, and the next round begins.
4. **Decision owner adjudicates**: A configured judge, policy rule, or qualified person issues `approve / conditional / reject / needs_more_evidence` under an explicit authority contract.

Each role writes a separate trace into the audit log. Review rounds need a hard ceiling based on risk and budget. The critic must be capable of testing the generator's subtle errors, and the judge needs the evidence contract required to settle disputes. Cross-family routing can reduce some shared blind spots. Independence also depends on context, data sources, runtime separation, and human accountability.

## Applicability

- **Workflows with separation-of-duties requirements**: Credit, medical assistance, legal assessment, and regulatory processes may require independent evidence and accountable review before release.
- **Critical decisions where errors are costly**: Use it when expected loss, regulatory responsibility, or safety risk justifies independent review overhead.
- **Known correlated reviewer failures**: When replay shows that self-review misses a defect class, introduce different evidence, review duties, deterministic checks, models, or human expertise and measure the change.
- **Model-combination trade-offs**: A mid-tier generator plus an independent critic may outperform a single expensive call on some tasks, but that comparison must be run on the target evaluation set.

## Known failure modes

- **Correlated blind spots**: changing vendors does not guarantee independent errors; generator and critic models may still share training sources, evaluation weaknesses, or prompt assumptions. For high-risk cases, diversify evidence and review duties, add deterministic checks where possible, and retain a qualified human decision owner.
- **Context growth across rounds**: Cost and latency rise when every call carries the full discussion. Give each reviewer the task, current draft, assigned checks, and required evidence. Give the decision owner a structured record of findings, responses, and unresolved issues.
- **Critic agrees by default**: A reviewer may accept the proposal without testing its assigned failure hypotheses. Track review coverage and confirmed findings, and sample verdicts with qualified reviewers. A critic that never finds substantive issues and one that continually invents them are both miscalibrated.
- **Insufficient reviewer diversity**: when every reviewer uses the same role, prompt, and evidence, additional agents tend to repeat the same judgment. Give reviewers distinct failure hypotheses, evidence sources, or review duties, and measure whether disagreement reveals defects that one reviewer misses.
- **Misuse on simple tasks**: Low-risk writing polish and tasks with deterministic verification usually do not justify multi-agent adversarial review. Tests, schemas, or a single calibrated critic are more direct.

## Verification and metrics

- **Independence evidence**: Record differences in models, prompts, evidence sources, runtime, and organizational roles. Vendor diversity is only one piece of evidence.
- **Critic discovery rate (`issues_per_turn`)**: Analyze it together with phantom issues and expert sampling. Persistently empty or persistently fabricated findings both signal poor calibration.
- **Debate rounds**: Observe the convergence distribution and cap exhaustion. Repeated non-convergence calls for a better judge, evidence contract, or exit from the pattern.
- **Cost per decision**: Measure the real token, latency, and review cost of the chosen configuration and compare it with the risk budget.

## Reference implementation

```
AdversarialReview.review(task):
                check_independence_policy()            # context, evidence, runtime, model, or role
                current = proponent(task)
                for round in 1..MAX_ROUNDS:            # configured risk and cost ceiling
                    verdict = critic(task, current, review_contract)
                    append_trace(current, verdict)
                    if verdict.no_issues_found and requires_second_review(verdict):
                        verdict = second_critic(task, current, review_contract)
                        append_trace(current, verdict)
                    if verdict.no_issues_found: break
                    current = proponent(task, current, verdict.issues)
                return judge(task, current, debate_log) # rule, qualified person, or judge agent

            CritiqueVerdict:
                issues: list           # explicit beats implicit
                severity: minor/major/critical
                no_issues_found: bool  # valid only when supported by the review trace
```

Production implementation should record model versions, prompts, evidence sources, and runtime identity; define when an empty critic verdict requires a second review; configure `MAX_ROUNDS` from task risk and cost; and retain compliance attestations according to the applicable policy.

## Illustrative scenario

Consider a bank's loan-decision assistance system. A first version asks one model to play credit analyst, risk reviewer, and compliance reviewer. Different role prompts do not establish structural independence. A later design separates the generator, critic, and judge by model or evidence source, retains each trace, and writes the final ruling and human approval into the audit record. Whether this satisfies an audit depends on the bank's policy and the auditor's accepted evidence; it cannot be inferred from the number of models alone.

## Related patterns

- **Generator-Critic (F1)**: F1 generates and revises an artifact through a bounded feedback loop and may share a model or runtime. C3 adds independent review roles, evidence, and traces when separation of duties or stronger challenge is required.
- **Fan-out/Gather (C2)**: workers process separate units or viewpoints and a gather step combines their outputs. C3 assigns reviewers to challenge the same proposal against distinct checks.
- **Parallel Exploration (R3)**: branches develop alternative hypotheses or solutions for later selection or aggregation. C3 starts with a proposal and searches for defects, unsupported claims, and policy violations.
- **N-version programming**: independent implementations of one specification are compared or voted on to reduce common-mode software failures. It is a useful precedent when several agents independently implement the same task; a proposal-and-critique loop has different control flow and should not be treated as equivalent.

## Design conclusion

Adversarial review organizes disagreement through independent roles, evidence, and an explicit ruling rule. Independence is a structural claim that the system must demonstrate, not a label earned by adding another prompt.

## Workshop revision, 25 August 2026: Review-execution feedback

A review result carries evidence, risks, applicability conditions, and revalidation requirements. Constraints discovered during execution return through the evidence chain so role separation does not create a new information gap.

[Collaboration workshop record](https://adpsagent.com/workshops/collaboration-2026-08-25/)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>C3 Adversarial Review</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-c3-adversarial-review">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
