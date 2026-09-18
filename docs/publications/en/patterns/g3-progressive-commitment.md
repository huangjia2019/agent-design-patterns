<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/">Pattern matrix</a><span style="margin: 0 0.45rem;">/</span>White paper<span style="margin: 0 0.45rem;">/</span>G3</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>G3 · Progressive Commitment</h1>
<p class="publication-deck">Manage promotion, hold, demotion, and retirement by capability, scenario, resource, and version.</p>
</header>

Progressive Commitment governs local, version-bound authority. It records an agent version's authority for a capability, scenario, resource, and environment instead of assigning one global trust score.

## Coordinate and authority unit

**Governance × Chain.** Shadow, recommendation, bounded execution, and expanded scope have evidence prerequisites. Incidents, dependencies, and version changes can move the chain backward.

```
authority_key = (
    agent_version,
    capability,
    scenario,
    resource_scope,
    environment
)
```

Validation and submission by the same payroll agent should have separate grants.

## Autonomy tiers

<table><thead><tr><th>Tier</th><th>Behavior</th><th>Evidence</th></tr></thead><tbody>
<tr><td>Shadow</td><td>Read real input with no business effect</td><td>Baseline, coverage, failure classes</td></tr>
<tr><td>Recommend</td><td>Produce a recommendation or draft</td><td>Adoption, edits, long-tail errors</td></tr>
<tr><td>Bounded Execute</td><td>Automate reversible or low-impact work inside hard limits</td><td>External acceptance, reversal, boundary events, incidents</td></tr>
<tr><td>Expanded Execute</td><td>Expand objects, frequency, or scenarios while retaining hard limits</td><td>Stable window, stratified samples, business outcome</td></tr>
<tr><td>Frozen / Retired</td><td>Stop new effects and preserve audit or rollback</td><td>Incident, expired version, missing owner, ended pilot</td></tr>
</tbody></table>

## Evidence

Task and outcome evidence shows goal completion and downstream use. Process evidence covers planning, tools, memory, and recovery. Foundation evidence covers model, tool, storage, and policy health. An average success rate cannot replace these levels or expose high-risk tails.

## Running example

Payroll agent v7 validates in Shadow and then Recommend. Routine batches are stable while new-hire and cross-region cases remain weak, so only the routine slice receives Bounded Execute. Submission remains reviewed under G1. A payment-tool upgrade freezes the affected validation grant and returns it to Shadow while unrelated capabilities retain their state.

## Disposition, failure, and verification

A review can promote, hold, narrow, demote, or retire. Missing eval coverage, a changed dependency, rising error rates, owner departure, or long inactivity can invalidate authority without an incident.

Reject global agent levels, one-way ladders, easy-sample selection, authority inheritance after material changes, agent-writable grants, and immediate full traffic after promotion. Verify grant granularity, evidence coverage, post-promotion rollback, demotion latency, version inheritance, retirement, and real reduction in human load.

<div class="document-citation">
<p><strong>Suggested citation:</strong>ADPS, <em>G3 · Progressive Commitment</em>, Agent Design Pattern White Paper v0.4, 19 August 2026.</p>
<p><a href="https://adpsagent.com/patterns/">Pattern catalog</a> · <a href="https://adpsagent.com/workshops/governance-2026-08-18/">Governance workshop</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>Scope:</strong>Public review draft. Definitions and classifications are open for discussion and citation; running examples explain mechanisms, while attributed practice appears in the case library.</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-g3-progressive-commitment">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
