<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/concepts/" style="color: var(--color-text-muted);">Concepts</a><span style="margin:0 0.45rem;">/</span>Concept</p>

<header class="publication-head">
<p class="publication-series">ADPS Engineering Concept Registry</p>
<h1>External Acceptance Probe: Let the User-Side Result Decide Success</h1><p class="publication-deck">Test the result from the user side and let that evidence decide success.</p>
</header>

## Start with a false HTTP 200

GeoServer can return a `ServiceException` with HTTP status 200. The publication call appears successful while the user receives an empty map. A process exit code or status code alone records a business failure as success.

## Definition

An external acceptance probe performs the same action a consumer would perform from outside the system boundary. It checks status, content, and the usable result. Internal receipts remain process evidence; the probe decides whether the task commits, retries, or fails.

The Xuanxu probe issues real WMS or WMTS requests, inspects content type and exception bodies, checks that a screenshot contains non-transparent map content, and writes the result to `verify_report.json`.

## Boundary

The probe must cover the real delivery path, not an internal shortcut. Visual checks need calibrated thresholds and known-good samples. Complex cartographic quality may still require expert sampling.

## Provenance

- Initial case: Xuanxu Technology GIS publishing agent, contributed by Yuke Xiong.
- Lineage: end-to-end tests, synthetic probes, and health endpoint monitoring.
- ADPS contribution: the probe receipt directly controls the agent task state.
- Definition status: ADPS restatement.

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">Proposal and provenance</h2>
<dl>
<div><dt>Concept group</dt><dd><a href="https://adpsagent.com/concepts/#group-verification-governance">Evaluation, reflection, and governance</a></dd></div>
<div><dt>Initial source within ADPS</dt><dd>Initial practice: Yuke Xiong</dd></div>
<div><dt>First recorded in</dt><dd><a href="https://adpsagent.com/cases/xuanxu-gis-agent/">Xuanxu GIS publishing-agent case</a> (<time datetime="2026-07-30">2026-07-30</time>)</dd></div>
<div><dt>ADPS editorial work</dt><dd>ADPS connected a user-side probe receipt to the task state machine so observable results decide success.</dd></div>
<div><dt>Current standing</dt><dd>ADPS restatement</dd></div>
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
<p><a href="https://adpsagent.com/chronicle/#concepts-external-acceptance-probe">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
