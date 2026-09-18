<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/concepts/">Concepts</a><span style="margin:0 0.45rem;">/</span>Definition</p>

<header class="publication-head"><p class="publication-series">ADPS Agent Systems · Engineering Concept</p><h1>Write-Conflict Domain</h1><p class="publication-deck">Identify files, identifiers, configuration, domain objects, and environments that concurrent tasks may jointly mutate.</p></header>

## Application context: two agents can overwrite each other without touching one file

Two coding agents work in separate worktrees on different services. Both allocate `REQ-417` from the same identifier table, or one changes a client while the other changes a server under incompatible assumptions about the public API. Git reports no file conflict; the business writes still conflict.

## Definition

A Write-Conflict Domain is a set of objects that cannot be mutated concurrently without coordination. It may contain files, identifier spaces, shared configuration, database rows, test environments, API contracts, deployment slots, cloud quotas, or external business resources. The domain is defined by what the tasks jointly change, not only by repository paths.

## Engineering mechanism

Before scheduling, each task declares an expected read/write set and resource keys such as `api:customer-v2`, `db:tenant-17/payroll`, or `env:uat-3`. The scheduler chooses serialization, sharding, leases, or merge rules. Discovery of a new shared object expands the domain and triggers rescheduling instead of allowing the agent to continue under a false isolation assumption.

## Boundary

Perfect static inference of every write set is rarely practical. Unknown high-risk objects should begin serially and move to parallel execution only after a partition rule is known. Worktrees remain useful for source files but cannot replace conflict checks over domain objects, external resources, and versioned contracts.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-collaboration-runtime">Collaboration and runtime control</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial problem: Hongshan Tang; practice discussed by Pylon Peng and Wei Wang; name formalized by ADPS</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/workshops/action-2026-08-06/">First Action workshop</a> (<time datetime="2026-08-06">2026-08-06</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS extended file conflicts to identifiers, configuration, database records, test environments, and external resources.</dd></div>
<div><dt>Current standing</dt><dd>Cross-module concept</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Definition source:</strong> ADPS White Paper workshops and pattern development.</p><p><a href="https://adpsagent.com/concepts/">Concept index</a> · <a href="https://adpsagent.com/workshops/">Workshops</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/workshops/action-2026-08-06/">First Action workshop</a> (<time datetime="2026-08-06">2026-08-06</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-08-06">2026-08-06</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-write-conflict-domain">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
