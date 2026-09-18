<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Handoff Contract</h1><p class="publication-deck">Transfer goal, artifacts, decisions, authority, responsibility, and acceptance together.</p></header>

## Application context: a complete chat history is still an incomplete hand-off

A requirements agent forwards tens of thousands of words to an implementation agent. The receiver can see what was discussed but cannot tell which decision is final, which paths were rejected, which resources it may change, or who will accept the result. Context volume increased; responsibility did not become clear.

## Definition

A Handoff Contract is a typed boundary between collaboration stages. It carries the goal, existing artifacts, accepted decisions, open questions, authority scope, accountable owner, acceptance criteria, and the next required artifact. The receiver explicitly accepts or rejects it, and temporary authority from the previous leg is reclaimed by policy.

## Engineering mechanism

<pre><code class="language-yaml">goal: preserve public API compatibility
artifacts: [spec://417@sha256:...]
decisions:
  - do not change the public schema
authority:
  tools: [repo_read, patch_write]
  scope: repo://service-a
acceptance: [unit_tests, contract_tests]
next_required: reviewable patch and test evidence</code></pre>

The contract references large artifacts and history rather than copying them. A changed dependency, scope, or authority causes rejection or reissue instead of silent guessing.

## Boundary

An ordinary function call needs only an argument contract. Explicit hand-off becomes important across roles, sessions, teams, or trust domains. Domain fields may vary, but goal, artifacts, decisions, authority, and acceptance should not exist only in conversation.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-collaboration-runtime">Collaboration and runtime control</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial problem and proposal: Wei Wang; field structure: ADPS</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS organized differing handoff protocols around goal, artifacts, decisions, authority, and acceptance.</dd></div>
<div><dt>Current standing</dt><dd>Workshop concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/collaboration-2026-08-25/">First Collaboration workshop</a> (<time datetime="2026-08-25">2026-08-25</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-handoff-contract">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
