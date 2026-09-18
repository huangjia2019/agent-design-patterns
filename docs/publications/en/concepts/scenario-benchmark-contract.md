<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Scenario–Benchmark Contract</h1><p class="publication-deck">Bind production scenarios to evaluation sets, acceptance thresholds, and version-change conditions.</p></header>

## Application context

A support agent faces different failure costs in refunds, delivery enquiries, and enterprise contracts. “85% accuracy” does not identify the sample source or show whether a high-risk scenario was hidden by an average. A model, prompt, harness, or tool change can also invalidate an earlier result.

## Definition

A Scenario–Benchmark Contract binds a set of production scenarios to corresponding evaluation cases. Together they define the capability boundary, release threshold, and regression conditions. Each scenario records input provenance, expected outcomes, error costs, acceptance thresholds, and applicable versions. Production failures return to their scenario rather than disappearing into an unbounded aggregate score.

```
scenario_benchmark_contract:
  scenario_scope: []
  sample_sources: []
  error_costs: {}
  acceptance_thresholds: {}
  bound_versions:
    model: ...
    prompt: ...
    harness: ...
    tools: ...
  production_feedback: []
  owner: ...
```

## Engineering use

The team selects scenarios from real task flows and assigns separate thresholds to high-risk or frequent work. Every candidate version runs against the same frozen set, while newly observed production cases are reported separately. The release receipt records the contract version, component versions, per-scenario results, and approved exceptions. A change to a bound component or error cost triggers re-evaluation.

## Boundary

The contract states the capability range that has evidence. It does not promise automatic generalization to uncovered work, and it does not replace security, performance, or recovery tests. Broader scope, changed business definitions, or a new critical component requires a new version with an explicit diff.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Dong Zhang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/reasoning-2026-08-26/">First Reasoning workshop</a> (<time datetime="2026-08-26">2026-08-26</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS organized production scenarios, sample sources, error costs, acceptance thresholds, and component versions into one capability contract.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/concepts/">Concept catalogue</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/reasoning-2026-08-26/">First Reasoning workshop</a> (<time datetime="2026-08-26">2026-08-26</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-scenario-benchmark-contract">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
