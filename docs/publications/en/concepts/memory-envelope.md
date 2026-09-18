<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Memory Envelope</h1><p class="publication-deck">Assemble a versioned context package for one model call.</p>
</header>

![Memory envelope assembled for one reasoning step](../../assets/images/concepts/memory-envelope.png)

## Application context

A reasoning step that decides how to associate employees needs the task goal, current plan node, relevant policy, created payroll-group identifier, and unresolved exceptions. It does not need every tool response and discussion from earlier stages. Passing the full history raises cost and lets recent detail displace the original goal.

## Definition

A Memory Envelope is the versioned context package assembled for one model call. It combines the stable Anchor, current progress, selected evidence, exact state references, recalled experience, and the output contract expected from this step.

## Engineering mechanism

<pre><code class="language-yaml">goal: ref://anchor/17
step: associate-employees
progress: ref://workspace/node-4
facts: [ref://state/pay-group-id]
evidence: [ref://policy/sg-payroll@v8]
experience: [ref://lesson/bulk-association@v3]
output_schema: AssociationDecision</code></pre>

The runtime records the envelope hash and source versions with the model call. A later replay can therefore reconstruct what the model was allowed to see without storing a hidden, mutable prompt.

## Boundary

The envelope is a read package, not the system of record. It points to authoritative values and artifacts. Selection policy may use relevance and priority, but permissions, validity, and task scope filter candidates before ranking.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-context-memory">Context and memory</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Bo Liang</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>The implementation structure is ReasonContext; ADPS supplied the name Memory Envelope.</dd></div>
<div><dt>Current standing</dt><dd>Case-derived name</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Initial source:</strong> <a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng Execution Agent case report</a>; contributed by Bo Liang.</p><p><a href="https://adpsagent.com/concepts/">Concept registry</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/cases/liangbo-execution-agent/">Dongfang Yiteng execution-agent case</a> (<time datetime="2026-06-19">2026-06-19</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-memory-envelope">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
