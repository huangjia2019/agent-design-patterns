<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>F2</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>F2 · Skill Package</h1>
<p class="publication-deck">Package a repeatedly successful workflow as a named, loadable, versioned skill, then manage its evaluation, coexistence, release, rollback, and retirement.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Reflection × Route (selected)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium-high (packaging, isolated evaluation, release, and maintenance)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Reflection patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Package a repeatedly successful workflow as a named, loadable, versioned skill, then manage its evaluation, coexistence, release, rollback, and retirement.</td>
</tr>
</tbody>
</table>

---

## Problem

An agent may complete the same kind of task successfully and still start from zero on the next run: it reads the same references, repeats the same trial and error, and rediscovers the same path. Tokens and time are spent on work the system has already learned, because nothing callable was retained after the task finished.

A Skill Package records a verified procedure as a structured asset, usually YAML frontmatter (name, description, triggers), a Markdown body (steps, gotchas, examples), and bundled scripts. When a similar task arrives, the agent routes to the corresponding skill and loads the established path. Generator-Critic revises one output; a Skill Package retains a capability across tasks. The ACT-R cognitive architecture calls this proceduralization: compiling declarative knowledge into procedural skill. Contemporary agent systems often implement the idea with a `SKILL.md`-style package.

## Classification: Reflection × Route

- **Vertical axis · Reflection**: After repeated successful runs, the system extracts a procedure and prepares it for reuse across tasks.
- **Horizontal axis · Route**: Runtime matching selects a skill by task features and triggers. Discovery exposes metadata, Activation loads `SKILL.md`, and Execution loads bundled scripts on demand.

## Solution and mechanics

A Skill Package system consists of two pipelines:

1. **Loading pipeline**: When a task arrives, the agent routes from the skill library to the right skill. Three-stage loading keeps context use under control: startup exposes only a name and short description, activation loads the full `SKILL.md` after a match, and execution loads bundled scripts only when needed. The exact context cost depends on the catalogue and model tokenizer and should be measured locally.
2. **Release pipeline**: A skill may be written by a person or distilled with agent assistance. Both paths move through candidate → safety review → isolated evaluation → coexistence evaluation → canary → release → monitoring → refine, merge, or retire.

Keep critical constraints in the loaded instruction path, use deterministic scripts for operations that can be encoded, include worked examples for judgment points, and review usage evidence for stale or conflicting packages.

Isolated evaluation asks whether a skill can complete its own task. Coexistence evaluation asks whether it still behaves correctly when other skills are available. A skill may pass alone and then steal triggers, lose routing decisions, or interfere with a neighbouring skill. When an outcome degrades, the trace must distinguish the main agent, skill content, trigger description, and host harness.

## Applicability

- **Recurring tasks with a relatively stable flow**: operations runbooks (batch cluster restarts, configuration changes), customer-service triage SOPs, standard sales processes—tasks of the same kind that recur frequently with flows that do not change daily.
- **Enterprise processes that need to be observable and reusable**: structuring the tacit flow in a veteran employee's head into a SKILL.md so that new employees and the agent read and use the same thing, and a sales leader can review and version it.
- **Repeated high-cost procedures**: financial approval and incident-response workflows benefit from a reviewed, versioned procedure when the same controls recur across tasks.

## Known failure modes

- **Packaging an unstable task**: open-domain research, one-off work, rapidly changing workflows, and judgment-heavy tasks may accumulate exceptions faster than reuse value. Package a skill when the task recurs, its procedure is stable enough to test, and inconsistent execution is costly.
- **Unreviewed catalogue growth**: Agent-distilled candidates enter the active library without replay, coexistence tests, or review. Keep candidates separate and promote them through a versioned release path.
- **Stale skills**: Tool, schema, or policy versions change while the skill remains active. Bind certification evidence to dependency versions and move affected skills to revalidation.
- **Description mismatch**: A description that is too broad causes false activation; one that is too narrow causes missed activation. Test descriptions and triggers on labelled eligible and ineligible tasks.
- **Passes in isolation, regresses in combination**: A new skill works alone but conflicts with existing triggers in the production catalogue. Run conflict cases and mixed-skill tasks before release, and retain a known rollback version.
- **Weak attribution**: A failed task is labelled as a “skill failure” without saving route candidates, selected content, model version, and harness version. The team then cannot identify which layer needs repair.

## Verification and metrics

- **Skill hit rate**: the proportion of eligible tasks that recall the correct skill. Calibrate descriptions and triggers against a labelled task set.
- **Skill success rate**: the proportion of tasks that succeed after calling a given skill, compared with the general-flow baseline. A sustained decline should trigger review or rollback.
- **Library health**: track whether task quality, precision of activation, and maintenance burden change as the catalogue grows.
- **Loading token share**: measure catalogue, activation, and execution context separately. Set a local budget that leaves enough room for the task itself.
- **Coexistence regression rate**: Compare false activation, missed activation, task success, and context cost before and after a skill joins the active catalogue.
- **Release and rollback evidence**: Record the evaluations a candidate passed, its canary period, approval, and whether rollback returns the system to a known state.

## Reference implementation

```
# Stage 1 Discovery: load only name + description at startup
            catalog = [{"name": s.name, "desc": s.description} for s in library]

            # Stage 2 Activation: load the full SKILL.md after a task matches
            matched = top_k(task, library, k=activation_k)   # tune on labelled tasks

            # Stage 3 Execution: load bundled scripts on demand, track success rate
            result = run(matched_skill, task)
            mark_used(matched_skill, success=result.ok)

            # Retention: Hermes-style automatic distillation (multiple filters)
            if distillation_policy.accepts(task, trace, outcome):
                skill = distill(task, tool_calls)   # enters probation, not direct production

            # Release: evaluate alone and with the active catalogue
            ISOLATED_EVAL(skill, held_out_tasks)
            COEXISTENCE_EVAL(skill, active_library, conflict_cases)
            PROMOTE(replay_passed and coexistence_passed and approval_granted)

            # Runtime attribution
            record_route(candidates, selected_skill, skill_version, harness_version, outcome)

            # Lifecycle
            REFINE(sufficient_usage_evidence and quality_declining)
            ROLLBACK(blocking_regression)
            EVICT(no_effective_use and review_approved)
```

Use staged loading to control context. A self-distilled skill stays in probation until replay and review pass. Isolated and coexistence evaluations are both release gates. Every activation records routing and version evidence; a blocking regression rolls back to the previous stable version.

## Illustrative scenario

Consider a B2B sales team whose strongest salesperson follows a repeatable but undocumented process: researching the account before contact, using a consistent discovery structure, selecting objection-handling material, and sending a decision checklist before signature. The team can package this process as a human-authored `SKILL.md`, with scripts for deterministic checks and examples for judgment-heavy steps. Agent-distilled variations stay in a lower-trust namespace, customer-facing changes require review, and promotion depends on replay against historical opportunities. The example demonstrates lifecycle and trust controls. Any claim about improved conversion or onboarding speed would require the company's own records and publication approval.

## Related patterns

- **Procedural Memory (M5)**: Both patterns may use the same runtime package format. F2 focuses on evaluating and releasing a procedure after reflection; M5 focuses on retaining and retrieving procedural knowledge. One released asset can participate in both mechanisms.
- **Generator-Critic (F1)**: F1 reviews and revises an artifact within one task. F2 packages a procedure for reuse across tasks after it has passed evaluation.
- **Experience Replay (F3)**: F2 holds verified callable procedures; F3 holds broader reference assets that still require adaptation. A runtime can route to a skill first and retrieve experience when no skill matches.
- **RAG (M2)**: RAG retrieves declarative evidence and domain knowledge. A Skill Package supplies a tested procedure for acting on that material. Many enterprise workflows need both.

## Engineering judgment

A Skill Package turns a verified procedure, its tools, and its boundary conditions into a versioned runtime asset. Its value depends on routing quality and lifecycle discipline as much as on the instructions inside the package.

## Further reading

- [Reflection module: Make feedback change the system](https://adpsagent.com/patterns/reflection/)
- [First Reflection workshop, 12 August 2026](https://adpsagent.com/workshops/reflection-2026-08-12/)
- [Claude Enterprise Skills: testing and lifecycle guidance](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise)

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>F2 Skill Package</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-f2-skill-package">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
