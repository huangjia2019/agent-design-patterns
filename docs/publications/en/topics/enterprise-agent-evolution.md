<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/topics/">Topics</a><span style="margin:0 0.45rem;">/</span>Enterprise Agent Evolution and Operating Model: Research Agenda</p>

<header class="publication-head">
<p class="publication-series">ADPS Topic Research</p>
<h1>Enterprise Agent Evolution and Operating Model: Research Agenda</h1>
<p class="publication-deck">A research agenda for the concurrent evolution of agent authority, engineering platforms, and organizational responsibility.</p>
</header>

When an agent moves from a personal assistant into a shared workflow and gains authority to change business state, the architecture is only one part of the transition. Review accountability, incident handling, knowledge maintenance, cost management, and team responsibilities also change.

ADPS patterns address local architecture problems, cases document concrete practice, and workshops preserve first-hand practitioner observations. How an enterprise combines these pieces and expands autonomy over time remains less settled. This page therefore starts as a research agenda: it defines the questions and the evidence still needed.

## Three concurrent lines of evolution

| Line | Typical starting point | Questions that follow |
| --- | --- | --- |
| System authority | Read and draft | When may the agent recommend, execute, run a batch, or coordinate other agents? |
| Engineering platform | Individual tool | When are a shared harness, specification repository, test environment, event system, and common governance justified? |
| Operating model | Individual self-review | Who defines acceptance, approves authority, stewards architecture, and owns failures and long-term cost? |

The three lines do not advance automatically in step. A system may support autonomous execution before the organization has defined acceptance ownership or incident response. A platform may also centralize too early, before stable use cases and reusable assets exist.

## From one change to an agent fleet

The payroll example on the home page defines the minimum modelling unit as one business change that can be decided, approved, executed, accepted, and compensated independently. That unit closes one piece of work. The governance lifecycle manages how a capability moves through registration, evaluation, shadow operation, production, revalidation, demotion, and retirement.

![Agent governance lifecycle from registration and evaluation through operation, demotion, and retirement](../../assets/images/patterns/agent-governance-lifecycle-en.svg)

<table>
<thead><tr><th>Management scale</th><th>Payroll example</th><th>Engineering objects</th></tr></thead>
<tbody>
<tr><td>Business change</td><td>Change one employee's transport allowance from 800 to 1000 next month</td><td>Goal, facts, approval, execution, acceptance, compensation</td></tr>
<tr><td>Run</td><td>One request from intake through after-read</td><td>run, Intent, Approval, Execution, evidence chain</td></tr>
<tr><td>Capability version</td><td>Allowance-change capability in payroll agent v7</td><td>Scenario, resource scope, evaluation, autonomy tier</td></tr>
<tr><td>Agent product</td><td>Production payroll-agent instance</td><td>Owner, dependencies, credentials, budget, incident response, retirement</td></tr>
<tr><td>Agent fleet</td><td>Payroll, HR, finance, and compliance agents</td><td>Shared identity, policy format, aggregate limit, causal trace, cross-domain responsibility</td></tr>
</tbody>
</table>

Observability joins facts across the five scales. Evals and tests support release decisions; governance controls changes in authority. Without a clear minimum loop, a platform can accumulate entry points, tools, and logs without establishing who accepts a completed business change.

## Questions before each increase in authority

1. **Business boundary.** Which objects can the agent change, and what are the per-action, daily, and tenant-level impact limits?
2. **Acceptance ownership.** Which role defines success, and which evidence comes from an independent system?
3. **Change authority.** Which parts of code, prompts, skills, tests, specifications, and memory may the agent modify?
4. **Architecture ownership.** Who handles dependency drift, duplication, and stale rules across tasks?
5. **Incident responsibility.** Can execution evidence be replayed, and how do takeover and rollback begin?
6. **Economic boundary.** How are model, tool, review, test, and rework costs considered together?

Technical capability alone does not justify a wider authority boundary. Each level also needs matching acceptance, observability, rollback, and organizational responsibility.

## Intended outputs

- An enterprise autonomy scale that identifies the actions and prerequisites at each level.
- A role and responsibility map across business, engineering platform, security, data, risk, and operations.
- Admission criteria from pilot to production, including evidence, budget, authority, and incident readiness.
- A taxonomy for incidents and slow degradation, separating individual failure, memory contamination, architecture drift, and organizational mismatch.
- Comparative cases showing how the same principles change across industries and risk levels.

## How to use this page now

Enterprises can use the six questions above to review current pilots. Future ADPS workshops and engineering case reports will add evidence. A universal maturity score would require a broader body of observed practice.

## Related material

- [AI-Driven Software Engineering](https://adpsagent.com/topics/ai-driven-software-engineering/)
- [ADPS Pattern Matrix](https://adpsagent.com/patterns/)
- [Governance module and agent lifecycle](https://adpsagent.com/patterns/governance/#payroll-lifecycle)
- [First Governance Module Workshop](https://adpsagent.com/workshops/governance-2026-08-18/)
- [ADPS Enterprise Cases](https://adpsagent.com/cases/)
- [ADPS Workshops](https://adpsagent.com/workshops/)

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>Enterprise Agent Evolution and Operating Model: Research Agenda</em>, ADPS Topic Research, 2026-08-19.</p><p><a href="https://adpsagent.com/topics/">Topic index</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer">Topics synthesize engineering questions that cross several modules. Pattern definitions, attributed cases, and workshop records remain authoritative on their own pages.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>Workshop and case records cited in the article: <a href="https://adpsagent.com/workshops/governance-2026-08-18/">First Governance Module Workshop</a> (<time datetime="2026-08-18">2026-08-18</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-18">2026-08-18</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-14">2026-08-14</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#topics-enterprise-agent-evolution">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
