<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>F1</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>F1 · Generator-Critic</h1>
<p class="publication-deck">A Generator produces an output and a Critic reviews it against evidence and a rubric. Scope, rounds, and cost are bounded; the run exits when release criteria or the iteration cap is reached.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reflection × Chain (sequential)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (multiple generation and review calls)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reflection patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">A Generator produces an output and a Critic reviews it against evidence and a rubric. Scope, rounds, and cost are bounded; the run exits when release criteria or the iteration cap is reached.</td>
</tr>
</tbody>
</table>

---

## Problem

Writing, design, code readability, product copy, and academic abstracts combine several quality dimensions that deterministic checks do not fully cover. A first draft may satisfy the schema while still missing evidence, clarity, terminology, or audience requirements.

Generator-Critic separates drafting from review. The critic returns a structured verdict with evidence; the generator revises within a fixed scope and budget. Research systems such as Reflexion and Self-Refine provide prior evidence for language feedback, while production value still depends on the local task set, critic calibration, and acceptance criteria.

## Classification: Reflection × Chain

- **Vertical axis · Reflection**: The Critic examines the current output using a model, rules, tests, retrieved evidence, or human judgment.
- **Horizontal axis · Chain**: Generate → critique → revise is a linear pipeline with an explicit hand-off between stages. The chain may run more than once, but F1 starts with a usable output and applies bounded quality improvement. F4 starts with a verified failure and requires a repair loop.

## Solution and mechanics

A Generator-Critic loop consists of three segments:

1. **Generate**: The generator produces a draft under an output contract. Evaluate this stage independently so the critic is not used to compensate for avoidable generation defects.
2. **Critique**: the critic evaluates the current output and returns a structured verdict with an issue list, severity, evidence, and an explicit `no_changes_needed` field. Reflexion showed how natural-language feedback can carry the error, its cause, and repair guidance in addition to a score.
3. **Revise**: The generator applies accepted findings within the allowed scope. The loop exits on acceptance, no material change, budget exhaustion, or human hand-off.

The verdict should cite its evidence rather than collapse the review into a single score. Common evidence sources have different strengths and limits:

<table>
<thead>
<tr>
<th style="text-align: left;">Evidence source</th>
<th style="text-align: left;">Strength</th>
<th style="text-align: left;">Limitation</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Tests, schemas, static checks</td>
<td style="text-align: left;">Repeatable and unambiguous within their coverage</td>
<td style="text-align: left;">Only checks rules that have been encoded</td>
</tr>
<tr>
<td style="text-align: left;">Rules and expert rubrics</td>
<td style="text-align: left;">Represents business and domain quality</td>
<td style="text-align: left;">Criteria may conflict or change</td>
</tr>
<tr>
<td style="text-align: left;">Self-Critic</td>
<td style="text-align: left;">Low-cost initial screening</td>
<td style="text-align: left;">Inherits blind spots from the Generator</td>
</tr>
<tr>
<td style="text-align: left;">Cross-Model review</td>
<td style="text-align: left;">Adds a different judgment path</td>
<td style="text-align: left;">Two models can still share the same error</td>
</tr>
<tr>
<td style="text-align: left;">Human review and business outcomes</td>
<td style="text-align: left;">Handles accountability, context, and delayed effects</td>
<td style="text-align: left;">Expensive and often slow</td>
</tr>
</tbody>
</table>

A production review also needs a **Reflection Contract**. At minimum, record `subject`, `evidence_refs`, `rubric_version`, `verdict`, `proposed_change`, `scope`, `max_rounds`, `cost_budget`, and `release_action`. This turns a verdict into an auditable input for later offline analysis.

## Two feedback clocks

- **Online review** serves the current task. It checks the artifact, allows a limited number of revisions, and stops at the release condition or budget. Latency and change scope stay small.
- **Offline review** serves future tasks. It studies production traces, human edits, and later business outcomes to revise rubrics, graders, prompts, and evaluation sets. Changes to shared rules follow a versioned release process.

Both clocks use the same evidence structure. Online verdicts and hand-off reasons feed the offline dataset; revised standards return to production only after evaluation and release approval.

## Applicability

- **Content-generation tasks**: Writing, translation, summarization, copywriting, and academic editing can use explicit rubrics for evidence, terminology, audience, style, and completeness.
- **Code style and readability optimization**: Naming, comments, structural adjustments, and similar improvements that do not affect correctness but do affect quality.
- **High-frequency generation with cost constraints**: A lower-cost generator can be paired with a critic, but quality and total cost must be compared with a direct high-capability baseline on the same task set.

## Known failure modes

- **Using an LLM where a deterministic check exists**: For mathematics, SQL, schemas, and unit tests, run the check directly and use the model to explain or repair the failure.
- **An unvalidated critic**: A critic that misses important defects or introduces noisy objections can degrade the output. Evaluate critic recall, false alarms, and revision outcomes independently of the generator's model tier.
- **A critic that forces problems into existence**: If the critic prompt does not state that "no changes needed is a valid option," it may invent problems to fill the quota. Treat an unchanged result as a legitimate verdict, then measure false alarms on a reviewed set of already-qualified outputs.
- **Correlated generator and critic errors**: Shared models, prompts, or evidence can preserve the same blind spot. Add deterministic checks, independent evidence, a differently configured reviewer, or qualified human review according to risk.
- **Collapsing a multidimensional rubric into one score**: Accuracy, compliance, readability, and cost can move in different directions. Keep per-dimension verdicts and blocking criteria visible.
- **Reviewing only the final answer**: A plausible answer may hide unnecessary tool calls, incorrect retrieval, or a lucky result. High-risk work needs both outcome and trajectory evaluation.
- **No bounded exit**: An unconstrained critic can keep producing low-value or false findings. Set round, cost, latency, and no-material-change limits, then preserve the unresolved verdict for hand-off.

## Verification and metrics

- **Critic convergence rate**: Track how often the loop reaches an accepted result before the configured cap. Repeated exhaustion points to a weak generator, an unstable rubric, or an incapable critic.
- **Phantom-issue rate**: Measure how often the critic flags an output that expert review already considers acceptable. Use this to calibrate the rubric and the `no_changes_needed` exit.
- **Critic-vs-expert agreement rate**: Compare a representative sample of critic verdicts with expert judgment. Set an acceptance threshold from the risk of the task and the cost of human review.
- **Quality increment**: Compare the final output with the single-generation baseline on a fixed evaluation set, and report the gain together with token cost and latency.
- **Trajectory efficiency**: Track tool calls, failed branches, and revision rounds needed to meet the same acceptance criteria.
- **Critical-dimension regression**: Report regressions in blocking dimensions separately instead of hiding them inside an average score.

## Reference implementation

```
output = generator(task)
            for i in range(MAX_ITERATIONS):       # configure from task risk and evaluation evidence
                if external_critic:               # prefer a deterministic signal when present
                    critique = external_critic(task, output)
                elif multi_critic:                # multiple roles in parallel + arbitration
                    critique = merge(critic(task, output, role=r) for r in roles)
                else:
                    critique = critic(task, output)
                if critique.no_changes_needed:    # valid exit, guards against phantom issues
                    return output, "converged"
                output = generator(task, previous=output, feedback=critique)
            return output, "max_iterations_reached"   # hand off to HITL when bottomed out
```

The Critic prompt should allow `no_changes_needed`. Prefer tests, schemas, and citation checks when they apply. Configure `max_iterations` from local evaluation and task risk, and retain the full history, rubric version, and evidence references for calibration. Online review may revise the current artifact; durable changes to graders and rubrics go through offline evaluation and release.

## Illustrative scenario

Consider an agent that polishes academic abstracts. A critic instructed to find a fixed number of problems may rewrite an already concise abstract into a verbose one, because it has no valid way to say that the draft is acceptable. A stronger design permits `no_changes_needed`, separates academic rigor, concision, and terminology into explicit rubrics, and grounds terminology or citations in an external database. The team then compares critic verdicts with editor review on a fixed sample and decides whether the quality gain justifies the added cost. This is an illustrative design scenario; any claimed production result would need an attributed case and a documented measurement method.

## Related patterns

- **Self-Heal Loop (F4)**: Generator-Critic improves a usable output and may stop after one review. Self-Heal starts from a verified failure and runs a bounded repair loop with rollback and hand-off.
- **Adversarial Review (C3)**: F1 generates and revises an artifact through a bounded feedback loop; generator and critic may share a model or runtime. C3 introduces independent review roles, evidence, and traces when the decision requires separation of duties or stronger challenge.
- **Skill Package (F2)**: F1 revises the current artifact. Repeatedly successful and reviewed procedures may later become F2 candidates.

## Engineering judgment

Generator-Critic separates generation from evaluation. The Critic needs explicit criteria and should use tests, rules, source evidence, independent models, or human judgment according to the task.

## Further reading

- [Reflection module: Make feedback change the system](https://adpsagent.com/patterns/reflection/)
- [First Reflection workshop, 12 August 2026](https://adpsagent.com/workshops/reflection-2026-08-12/)
- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation)
- [LangChain AgentEvals](https://docs.langchain.com/oss/python/langchain/test/evals)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">Related open-source framework case</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/cases/deepagents-dynamic-orchestration/">Deep Agents: From Fixed Graphs to Code-Generated Collaboration</a></h2>
<p>Haili Zhang's workshop research, checked against public documentation and source code, connects hierarchical delegation, fan-out/gather, subagent isolation, independent verification, evaluation, and observability.</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>F1 Generator-Critic</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-f1-generator-critic">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
