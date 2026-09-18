<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/topics/">Topics</a><span style="margin:0 0.45rem;">/</span>AI-Driven Software Engineering: Specifications, Context, Execution, and Feedback</p>

<header class="publication-head">
<p class="publication-series">ADPS Topic Research</p>
<h1>AI-Driven Software Engineering: Specifications, Context, Execution, and Feedback</h1>
<p class="publication-deck">An engineering framework for AI coding, SDD, and agentic software engineering across specifications, context, execution, verification, and evolution.</p>
</header>

AI coding now extends well beyond completion inside an editor. An agent can inspect a repository, break down work, change several files, run tests, and prepare a commit. Code generation is one step in that process. Engineering teams therefore face a broader set of questions: how to define a bounded unit of work, control which context can affect a decision, verify an outcome, and prevent local delivery speed from degrading the architecture over time.

These questions span perception, memory, reasoning, action, reflection, and governance. ADPS treats them as a cross-cutting topic rather than assigning another pattern number.

## Terminology

| Term | Primary scope | Use in this topic |
| --- | --- | --- |
| AI coding | Using AI to generate, explain, modify, or review code | A tool or development activity |
| Spec-driven development (SDD) | Versioning intent, constraints, and acceptance criteria as specifications that guide planning, implementation, and verification | A specific engineering method |
| AI-driven software engineering | AI participation across requirements, architecture, implementation, testing, operation, and evolution | The ADPS topic name |
| Agentic software engineering | Longer execution chains, broader tool access, and greater task autonomy | A higher-autonomy form of AI-driven software engineering |

The terms overlap and continue to evolve. ADPS uses each at the level where it is useful and does not present this vocabulary as an industry standard.

## The bottleneck is moving

As agents produce code more quickly, scarce engineering capacity moves upstream and downstream:

1. **Task definition.** The problem, constraints, and observable acceptance conditions must be explicit enough to guide execution.
2. **Context management.** Repository files, architecture decisions, runtime logs, previous work, and external material should not enter the model indiscriminately.
3. **Acceptance design.** Compilation is one class of evidence. User-visible behaviour, data integrity, performance, security, and operability may also matter.
4. **Authority boundaries.** Read, write, execute, commit, and deploy permissions require separate admission decisions.
5. **Architecture stewardship.** Every local task may pass while the repository accumulates duplication, dependency drift, and unnecessary code growth.

AI software engineering therefore cannot be evaluated only by lines of code, pull-request volume, or generation speed. Specifications, evidence, traceability, review load, and downstream maintenance cost also matter.

## A five-layer engineering structure

| Layer | Question | ADPS connection |
| --- | --- | --- |
| Specification and unit of work | What is this run meant to finish, within which boundaries and acceptance criteria? | Goal Contract, task slicing, planning and reasoning patterns |
| Context | Which signals may affect this decision, and how are prior assets recalled? | Perception and memory modules |
| Execution | How does the current step select tools, control authority, and change external state? | Reasoning, action, and execution topologies |
| Verification | What evidence proves completion, and who may accept it? | External acceptance, action evidence, and governance patterns |
| Evolution | How does this result change rules, tests, skills, memory, or architecture? | Reflection, versioned memory, and architecture stewardship |

Versioned artifacts and runtime evidence connect these layers. Typical artifacts include specifications, architecture decision records, plan steps, code diffs, test results, action events, checkpoints, and repair proposals.

## From assistance to managed autonomy

| Stage | Agent work | Required team capability |
| --- | --- | --- |
| Coding assistance | Explain code, generate local changes, add tests | A person selects context and reviews each change |
| Specification-guided task | Deliver one independently acceptable slice from an explicit specification | Inspectable constraints, tests, rollback, and acceptance criteria |
| Harnessed workflow | Plan, execute, verify, and prepare a multi-step change in a sandbox | Context control, tool admission, event records, and external acceptance |
| Managed autonomy | Work from a continuing queue across longer task chains | Tiered authority, budgets, approval gates, incident handling, and periodic architecture review |

These stages describe engineering capability, not a procurement checklist. Legacy systems, high-traffic services, and regulated work usually remain at lower autonomy levels for longer.

## Evidence from the Perception workshop

The first ADPS Perception workshop on 13 August 2026 surfaced several comparable practices:

- The public OpenLogos and RunLogos projects connect Why, What, How, and acceptance criteria in a specification chain, then slice scenarios into vertically complete units of work.
- One class of large backend teams records token use, design iterations, and code changes to observe how AI changes actual engineering work.
- Greenfield projects and high-traffic brownfield systems use different adoption paths, while both place goals and constraints in the task definition.
- As AI-produced pull requests grow, `AGENTS.md` and skills do not carry architecture stewardship on their own. Repositories still need scheduled cleanup, dependency checks, and architecture review.
- A game-development practice uses ADRs, TDD, task files, and daily records for forward and reverse checks, selecting text or visual input for artefacts such as Unreal Engine Blueprints.
- One class of complex systems separates acceptance into algorithm, map, runtime-environment, and business-behaviour layers. The applicable layers follow the external outcomes a change can affect.

The teams use different tools, but they address the same engineering problem: turning human intent into work an agent can execute, a team can verify, and a repository can sustain.

## A conservative adoption path

1. Choose a bounded task with a clear rollback path and write the acceptance criteria first.
2. Keep specifications, constraints, and architecture decisions in the repository so people and agents read the same version.
3. Define the context ingress for that task: required, on-demand, and prohibited information.
4. Begin with a minimal tool set in a sandbox and record plans, calls, state changes, and verification results.
5. Verify external behaviour instead of accepting the agent's completion claim as final evidence.
6. Review whether failures changed specifications, tests, rules, or architecture, and remove duplicated implementation and stale context.

## Open questions

- How detailed should a specification be before it starts fixing implementation decisions too early?
- How should teams measure review burden, maintenance cost, and architecture drift caused by agent-produced changes?
- Which long-running task state belongs in checkpoints, the repository, or the control plane?
- When an agent can change code, tests, and specifications together, how can acceptance criteria remain independent?
- As an individual tool becomes an enterprise engineering system, how should authority, business accountability, and architecture ownership move?

The last question is continued in [Enterprise Agent Evolution and Operating Model](https://adpsagent.com/topics/enterprise-agent-evolution/).

## Sources

- [First ADPS Perception Module Workshop](https://adpsagent.com/workshops/perception-2026-08-13/)
- [GitHub Spec Kit: Spec-Driven Development](https://github.com/github/spec-kit/blob/main/docs/concepts/sdd.md)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/)
- [OpenAI: Running Codex safely](https://openai.com/index/running-codex-safely/)
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## Extending existing systems

[Malleable Software: Adding Agents to Existing Business Systems](https://adpsagent.com/topics/malleable-software/) examines integration without source access, approval of business drafts, and verification of external results.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>AI-Driven Software Engineering: Specifications, Context, Execution, and Feedback</em>, ADPS Topic Research, 2026-08-14.</p><p><a href="https://adpsagent.com/topics/">Topic index</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer">Topics synthesize engineering questions that cross several modules. Pattern definitions, attributed cases, and workshop records remain authoritative on their own pages.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>Workshop and case records cited in the article: <a href="https://adpsagent.com/workshops/perception-2026-08-13/">First ADPS Perception Module Workshop</a> (<time datetime="2026-08-13">2026-08-13</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-14">2026-08-14</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#topics-ai-driven-software-engineering">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
