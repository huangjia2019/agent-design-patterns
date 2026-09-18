<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Business Evaluation Set</h1><p class="publication-deck">Judge technical changes against business processes, representative scenarios, weights, and outcome measures.</p></header>

## Application context

Higher field-extraction accuracy in a service-ticket agent does not necessarily shorten ticket resolution. An added clarification step may improve local correctness while increasing human hand-offs and customer waiting time. Technical regression detects capability loss; the business needs a separate measurement layer.

## Definition

A Business Evaluation Set combines a critical business process, representative scenarios, scenario weights, metric definitions, and acceptance conditions. It runs an agent version through end-to-end work and observes completion time, first-contact resolution, human takeover, incorrect actions, business loss, or other domain outcomes. Weights come from business volume and risk; the model does not choose them.

```
business_evaluation_set:
  business_process: ...
  scenarios:
    - id: ...
      weight: ...
      metric: ...
      data_definition: ...
      acceptance: ...
  owner: ...
  version: ...
  change_log: []
```

## Engineering use

Product, business, and engineering owners agree on sampling, metric denominators, time windows, and exception handling. Results are reported per scenario before aggregation under registered weights. After a model or workflow change passes technical regression, the business set checks whether it improved the process or merely shifted cost to human teams and downstream systems.

## Boundary with technical evaluation

A Business Evaluation Set does not replace structural, factual, security, performance, or reliability tests. Technical evaluation asks whether a component meets its specification. Business evaluation asks whether the end-to-end process improved. Different owners may maintain the two assets, but a release receipt references both versions and results.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>First proposed within ADPS by Didi Li</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/reasoning-2026-08-26/">First Reasoning workshop</a> (<time datetime="2026-08-26">2026-08-26</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS organized business processes, representative scenarios, scenario weights, metric definitions, and versions into a business-level evaluation asset.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module concept under X2</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-business-evaluation-set">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
