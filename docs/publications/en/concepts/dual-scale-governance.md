<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Dual-Scale Governance</h1><p class="publication-deck">Govern the current action and the long-running goal at the same time.</p></header>

## Application context: every action can be legal while the job drifts

A long-running research agent may lawfully read files, search, and edit drafts. Every local check passes. Dozens of turns later, most effort has moved to incidental terminology and formatting while the promised deliverable has not advanced. No action exceeded authority; the goal still drifted.

## Definition

Dual-Scale Governance runs two checks:

- **Action scale** checks the current tool, arguments, identity, resource scope, quota, and preconditions;
- **Goal scale** compares the original goal, current plan, completed artifacts, remaining risk, and external outcome.

The action scale stops one dangerous call. The goal scale stops many locally plausible steps from accumulating into directional drift.

## Engineering use

Runtime events carry both an `action_id` and a `goal_contract_id`. Every call passes action policy. At milestones, cost thresholds, or time windows, the runtime reviews progress against the goal contract. Missing progress, invalidated assumptions, or cost divergence causes pause, replanning, or human takeover rather than another local patch.

## Boundary

Short transactions often need only action governance. Work that crosses hours, sessions, people, or systems needs the goal scale. Review frequency should follow risk and irreversibility; a full global review on every step would be unnecessarily expensive.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Jia Huang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/governance-2026-08-18/">First Governance workshop</a> (<time datetime="2026-08-18">2026-08-18</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS separates per-action compliance from long-horizon goal drift as two concurrent governance scales.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module governance concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/concepts/">Concept catalogue</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/governance-2026-08-18/">First Governance workshop</a> (<time datetime="2026-08-18">2026-08-18</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-18">2026-08-18</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-dual-scale-governance">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
