<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Programmatic Tool Calling</h1><p class="publication-deck">Let the model write a bounded program that calls registered tools and reduces intermediate results before they enter context.</p></header>

## Application context

A finance agent must identify people in one department whose travel spend exceeded policy. Conventional tool calling retrieves the staff list and then returns every expense and limit result to the model. Calls and context grow with headcount. The work itself is a loop, several parallel reads, and a deterministic aggregation.

## Definition

Programmatic Tool Calling lets the model write a short program that calls registered, explicitly eligible tools inside a bounded execution environment. The program handles loops, conditions, parallelism, aggregation, and error branches. Intermediate data can remain in the runtime while only the necessary result enters model context.

```
members = await get_members("engineering")
expenses = await gather(get_expenses(m.id) for m in members)
limits = await get_limits(unique(m.level for m in members))
print(find_exceeded(members, expenses, limits))
```

The program does not invent `get_expenses`. That tool is already registered. The generated code temporarily composes and processes its calls.

## Engineering use

Only tools explicitly permitted for programmatic callers enter the runtime. The sandbox limits CPU, memory, duration, loops, file access, and network egress. Tool admission still checks the current principal, resource, and Intent. The trace records the generated-code version, every actual tool call, intermediate errors, stdout, and the final result.

## Compared with ReAct and CodeAct

ReAct asks the model to choose again after each observation. Programmatic Tool Calling hands a local control flow to code, reducing model round trips and large intermediate results. CodeAct supplies a broader executable-code action space that can use libraries, computations, and generated helper functions, not only registered tools.

## Position in ADPS

It joins A1 Tool Dispatch and A2 Plan and Execute. A2 chooses the current step. PTC composes several calls inside that step. A1 still governs registration, candidate scope, and per-call admission. A one-run program remains a runtime mechanism. After testing, naming, versioning, and approval for cross-task reuse, it becomes M5 Procedural Memory.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-reasoning-action-runtime">Reasoning and action mechanisms</a></dd></div>
<div><dt>Term origin</dt><dd>External engineering term: Anthropic</dd></div>
<div><dt>Published source</dt><dd><a href="https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling">Anthropic Programmatic Tool Calling documentation</a></dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS places it between A1 Tool Dispatch and A2 Plan and Execute and distinguishes it from ReAct, CodeAct, and M5.</dd></div>
<div><dt>Current standing</dt><dd>Runtime-mechanism concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/concepts/">Concept catalogue</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling">Anthropic Programmatic Tool Calling documentation</a></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-programmatic-tool-calling">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
