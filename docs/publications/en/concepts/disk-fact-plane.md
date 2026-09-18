<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>Disk Fact Plane: Connect Runtime Stages through External Contracts</h1><p class="publication-deck">Keep stage facts, progress, and acceptance evidence in recoverable external contracts.</p>
</header>

## Start with recovery

A map dataset has passed validation, processing, and publication when the process stops. Recovery needs precise answers: what completed, where the artifacts are, and which stage can resume. In-memory objects and terminal logs do not provide a stable contract.

## Definition

A disk fact plane stores stage facts, execution state, and acceptance evidence in versioned files. Processes exchange paths and references instead of depending on unrecoverable shared memory.

In the Xuanxu case, `metadata.json` holds dataset and artifact facts, `run-state.json` holds stage progress and the resume point, and `verify_report.json` holds external acceptance evidence. Each fact has one authoritative writer. The console is a projection over these files.

## Boundary

The implementation fits a single host or controlled shared storage. Multi-host, multi-tenant concurrent writes require transactional storage, locking, and isolation. The durable concept is an external, versioned, recoverable fact contract; disk is the carrier used in this case.

## Provenance

- Initial case: Xuanxu Technology GIS publishing agent, contributed by Yuke Xiong.
- Lineage: file-based IPC, single source of truth, append-only state, and materialized projections.
- ADPS contribution: separate stage facts, runtime state, and acceptance evidence with one-writer ownership.
- Definition status: case-coined concept.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-system-boundaries">System boundaries and state</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Yuke Xiong</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu GIS publishing-agent case</a> (<time datetime="2026-07-30">2026-07-30</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS separated stage facts, runtime state, and acceptance evidence, then added a single-writer constraint.</dd></div>
<div><dt>Current standing</dt><dd>Case-derived name</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>Initial source:</strong> <a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu Technology GIS publishing-agent case</a>; contributed by Yuke Xiong.</p><p><a href="https://adpsagent.com/concepts/">Concept registry</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd><a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu GIS publishing-agent case</a> (<time datetime="2026-07-30">2026-07-30</time>)</dd></div>
<div><dt>Source date</dt><dd><time datetime="2026-07-30">2026-07-30</time></dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#concepts-disk-fact-plane">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
