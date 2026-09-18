<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>CodeAct: Code as Action</h1><p class="publication-deck">Use executable code as the agent's action language for computation, libraries, and tool composition.</p></header>

## Application context

A data-analysis agent reads tables, cleans fields, computes statistics, produces charts, and revises its logic after an error. Wrapping every operation as a separate JSON tool causes the registry to keep growing and requires repeated model calls to compose simple operations.

## Definition

CodeAct uses executable Python as a unified action space. The model can call available functions and libraries, create local variables and helpers, and revise an earlier action after the interpreter returns a result or error. The original research concerns code as an action during a run, not the durable storage of that code.

## Boundary with Programmatic Tool Calling

Both mechanisms ask the model to write code. Programmatic Tool Calling centres on registered tools: code batches their calls and reduces intermediate results while each tool remains explicitly admitted. CodeAct is more general. Its code can compute directly, use runtime libraries, and create temporary operations. It therefore tends to expose a broader capability and attack surface.

## Engineering use

The runtime isolates files, processes, networks, and credentials and sets time and resource limits. Code, dependencies, input digest, execution output, and errors enter the trace. External writes still pass through A1 Tool Dispatch, A4 Guardrail Sandwich, and governance controls; expressing an action as code does not bypass authority.

## Boundary with M5 Procedural Memory

Code generated and executed for one task is CodeAct. It becomes M5 Procedural Memory only after repeated validation, naming, versioning, dependency and trigger declarations, and approval for later runs. Saving a script that happened to work once does not create a reusable capability.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-reasoning-action-runtime">Reasoning and action mechanisms</a></dd></div>
<div><dt>Term origin</dt><dd>External research term: Wang et al.</dd></div>
<div><dt>Published source</dt><dd><a href="https://arxiv.org/abs/2402.01030">Executable Code Actions Elicit Better LLM Agents, ICML 2024</a></dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS separates one-run code actions from validated, reusable M5 Procedural Memory.</dd></div>
<div><dt>Current standing</dt><dd>Runtime-mechanism concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/concepts/">Concept catalogue</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://arxiv.org/abs/2402.01030">Executable Code Actions Elicit Better LLM Agents, ICML 2024</a></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-code-as-action">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
