<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>M5</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>M5 · Procedural Memory</h1>
<p class="publication-deck">Publish a verified method as a named, triggerable, versioned instruction or executable asset, and recertify it when dependencies change.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Memory × Hierarchy</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (distillation + indexing + lifecycle management)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Memory patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Publish a verified method as a named, triggerable, versioned instruction or executable asset, and recertify it when dependencies change.</td>
</tr>
</tbody>
</table>

---

## Problem

An agent can complete the same class of task repeatedly and still start from scratch each time, rereading references and rediscovering the same sequence. The successful path disappears when execution ends because it was never converted into a reusable process asset.

Procedural memory extracts triggers, steps, tool dependencies, and acceptance checks from a verified run and stores them as a reusable skill. It also gives organizational know-how a machine-readable form that people can review and version.

## Classification: Memory × Hierarchy

- **Vertical axis · Memory**: It retains verified procedures for later tasks, including their triggers, dependencies, steps, acceptance checks, and applicable versions. RAG primarily retrieves declarative evidence; procedural memory retrieves a way of working.
- **Horizontal axis · Hierarchy**: The library can organize atomic skills, composite skills, and workflows into layers. Higher-level procedures reference lower-level capabilities without copying their implementation.

## Solution and mechanics

1. **Three-stage loading**: At startup, load only each skill's name and description (discovery); read the full SKILL.md when a task matches (activation); load scripts and resources on demand during execution. This prevents the whole library from occupying startup context.
2. **Record the source**: Human-authored and agent-distilled skills can share a format, but they enter different review and trust paths. Store authorship, derivation trace, reviewer, and release evidence.
3. **Auto-distillation**: After a complex task succeeds, the agent analyzes the trajectory and writes a candidate skill describing input, tool sequence, and output contract. Triggering should consider complexity, reuse value, and user corrections rather than a fixed tool-call count.
4. **Human- and machine-readable format**: Use markdown plus YAML frontmatter so people can review it, git can diff it, and an agent can load the same source.
5. **Two compilation levels**: Instruction assets use a SKILL.md, runbook, or workflow while preserving agent judgment for exceptions. Executable assets compile stable calculations or operations into code; runtime work is reduced to intent matching, parameter validation, and invocation. This reduces generation variance when the intent space is bounded, while permissions, receipts, and failure handling remain mandatory.
6. **First-run certification**: Exercise a candidate in replay, shadow, or a controlled environment with known success cases, failures, and boundary conditions. Promotion to `active` records reviewer, evidence, and dependency versions.
7. **Lifecycle management**: Track use count, success, human correction, and dependency versions. A trigger, tool schema, or service change moves the asset to `needs_revalidation`. Retirement preserves the reason and a rollback version.

## Applicability

- **Periodic, templated tasks**: The same class of task recurs, has a relatively stable successful path, and has clear entry and exit conditions. Cluster configuration changes, batch restarts, and backup and restore are common examples.
- **Distilling enterprise process**: A law firm's client-tiering logic, a hospital's emergency triage, or a company's refund flow can be written into SKILL.md as a reviewable organizational asset.
- **Procedures with bounded judgment points**: A skill can mark fixed steps, configurable parameters, and conditions that require exploration or human review. This preserves tested structure without treating every case as identical.

## Known failure modes

- **Distilling an open task space**: Open-domain research may reuse tools or checks without having one stable end-to-end procedure. Package only the repeatable parts.
- **Packaging one-off work**: Evaluation, release, and maintenance cost may exceed any reuse benefit.
- **Freezing an unstable workflow**: A skill created while requirements or dependencies are still changing accumulates exceptions and frequent invalidations. Keep it as a candidate until replay shows a stable boundary.
- **Heavily compiling an open task space**: Executable assets need enumerable intents and stable inputs. When request structure keeps changing, return to instruction assets or continued exploration.
- **Packaging an undefined process**: Vague triggers, missing input and output fields, and no release lifecycle produce skills that cannot be routed or verified. Map the procedure and its acceptance conditions before retaining it as procedural memory.
- **Publishing an auto-distilled skill without evaluation**: Keep the asset in candidate state, replay it against known successes and failures, compare it with the current process, and require review appropriate to its risk before activation.
- **Compiling code without its contract**: The procedure runs, but preconditions, permission scope, acceptance, idempotency, and rollback are absent. It produces unexplained side effects faster.
- **Calling an asset after dependencies change**: Tool parameters, data schemas, or policy change while the skill remains active. Dependency versions must participate in certification and invalidation.
- **A library that only grows**: Without a lifecycle, stale, low-success-rate skills keep misleading the agent.

## Verification and metrics

- **Reuse rate**: The share of similar tasks that select an existing skill instead of exploring from scratch. Interpret it together with success and human-correction rates.
- **Skill success rate**: The share of tasks that succeed after calling a skill. A sustained decline from its own baseline may indicate stale infrastructure, triggers, or acceptance checks.
- **Token / time cost**: Compare skill reuse with exploration on comparable tasks while checking output quality and safety.
- **Auto-distillation promotion rate**: The share of generated candidates that pass replay and review. A low rate may indicate weak triggers, unstable workflows, or inadequate candidate quality.
- **Certification validity**: Verify that active assets still match current tools, schemas, policies, and test evidence.
- **Fallback and human-takeover rate**: Check whether executable assets stop safely at boundary conditions instead of improvising.

## Reference implementation

```
Skill = the structured form of a SKILL.md:
                name / description (used for discovery) / body (workflow + best practices)
                triggers[] / preconditions[] / steps[] / failure_handling[]
                mode(instruction|executable) / source(human|agent|refined)
                acceptance[] / permissions[] / idempotency / rollback
                dependency_versions{} / status(candidate|active|needs_revalidation|retired)
                review_evidence[] / use_count / success_rate
            SkillLibrary:
                discover()                    → at startup, return only name + description
                activate(task, top_k)         → match trigger, scope, versions, and preconditions
                certify(candidate, replay_set)→ publish after replay, boundary cases, and review
                mark_used(name, success)      → record the success rate after execution
                distill_from_trajectory(...)  → create a candidate when complexity, success, and reuse criteria hold
                invalidate_on_dependency(...) → move to needs_revalidation after dependency change
                retire(...)                   → leave the active set with reason and rollback version
```

Distillation creates a candidate, not a production capability. Publication validates triggers, input range, permission, acceptance, and fallback, then records dependency versions. Auto-distilled and human-authored skills retain different trust levels.

## Illustrative scenario

Consider an operations team using a DevOps agent for recurring Redis configuration changes, Kubernetes restarts, and PostgreSQL backup and restore. Reviewed runbooks live under `runbooks/`; auto-distilled candidates live under `auto-skills/` and enter a review queue. Triggers use testable keywords or regular expressions, preconditions check access and namespace, and each step is idempotent or includes rollback. Candidate skills run in shadow or replay before human approval. Any time or token reduction must be measured against comparable local tasks.

## Related patterns

- **Skill Package (F2)**: Both patterns may use the same package format and staged loading. M5 governs how procedural knowledge is retained and retrieved; F2 governs how a candidate procedure is evaluated, released, rolled back, and retired.
- **Failure Journals (M4)**: M5 retains verified procedures. M4 preserves failure events and lessons; a failure can invalidate or revise a procedural asset.
- **Layered Retention (M1)**: M1 defines retention scopes and loading precedence. M5 uses those controls for procedural assets and may add atomic, composite, and workflow levels inside the skill library.
- **RAG (M2)**: RAG retrieves declarative evidence and source material. M5 retrieves a verified procedure. A workflow may use both under separate version and permission controls.
- **Approval Gate and Guardrail Sandwich**: Executable procedural memory shortens the reasoning path but does not remove approval, parameter validation, or post-action acceptance for high-risk work.

## Design conclusion

Procedural memory turns one successful run into a reviewable capability asset. Its value comes from stable triggers, explicit contracts, and continued certification; storing the trajectory alone is insufficient.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>M5 Procedural Memory</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-m5-procedural-memory">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
