<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>ReAct Reasoning-Action Loop</h1><p class="publication-deck">Alternate reasoning and action so each next step can use a fresh observation from the environment.</p></header>

## Application context

A support agent receives “Why has this order not arrived?” Its first action may retrieve the order. If the parcel has not left the warehouse, the next action should inspect fulfilment. If a carrier has accepted it, the next action should retrieve tracking events. The latest observation determines the path, so a fixed chain is a poor fit.

## Definition

ReAct interleaves language-model reasoning with task actions. An action queries a knowledge source, tool, or environment; the resulting observation informs the next decision and action. The original paper studies interleaved reasoning traces and actions. Production systems can record structured decision summaries, actions, and observations without relying on disclosure of hidden model reasoning.

```
request
  → decide next action
  → call one tool
  → receive typed observation
  → decide again
  → stop, escalate, or act
```

## Engineering use

Every turn carries the same task identity and records the action, argument provenance, observation type, and stop reason. The harness controls turns, token and tool budgets, eligible tools, error formats, and human takeover. Observations pass schema checks before entering another model turn; a tool error must not be rewritten as an empty result.

## Compared with Programmatic Tool Calling and CodeAct

ReAct invokes the model again after each observation, which suits an open path that needs continuing judgement. Programmatic Tool Calling writes a local program that loops over, runs, or filters registered tools. CodeAct provides a broader executable-code action space for computation, libraries, and tool composition. The mechanisms can nest: one ReAct turn may choose to run a programmatic tool call.

## Boundary

Once steps and dependencies become stable, a task DAG or A2 Plan and Execute is usually easier to test and recover. Use ReAct for choices that depend on fresh observations. Keep the order, authority, and acceptance policy for irreversible actions in explicit runtime controls.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-reasoning-action-runtime">Reasoning and action mechanisms</a></dd></div>
<div><dt>Term origin</dt><dd>External research term: Yao et al.</dd></div>
<div><dt>Published source</dt><dd><a href="https://arxiv.org/abs/2210.03629">ReAct: Synergizing Reasoning and Acting in Language Models, 2022</a></dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS records ReAct as a runtime mechanism joining reasoning and action, without assigning it a separate pattern coordinate.</dd></div>
<div><dt>Current standing</dt><dd>Runtime-mechanism concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/concepts/">Concept catalogue</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://arxiv.org/abs/2210.03629">ReAct: Synergizing Reasoning and Acting in Language Models, 2022</a></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-react-loop">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
