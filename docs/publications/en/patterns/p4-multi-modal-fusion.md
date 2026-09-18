<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>P4</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>P4 · Multi-Modal Fusion</h1>
<p class="publication-deck">Convert each modality into the representation required by downstream checks, process independent channels in parallel, and preserve provenance in the fused artifact.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Perception × Parallel (fan-out)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">High (cost grows with specialist processing paths and vision calls)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Perception patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern summary</strong></td>
<td style="text-align: left;">Convert each modality into the representation required by downstream checks, process independent channels in parallel, and preserve provenance in the fused artifact.</td>
</tr>
</tbody>
</table>

---

## Problem

Enterprise input often mixes PDFs, charts, tables, scanned pages, and logs. Sending an entire report to a vision model can produce a magnitude error in a chart. Converting everything to plain OCR text removes the spatial relationships in bars, axes, and legends, leaving only a low-information statement such as “the chart shows market share.”

Multi-modal fusion decides how each segment should enter the context: vision input, extracted text, structured data, or no input at all. This decision happens before the agent reasons over the material. A poor representation cannot be repaired by better selection, compaction, or exploration downstream.

## Classification: Perception × Parallel

- **Vertical axis · Perception**: Fusion converts PDFs, images, audio, logs, and structured data into representations that downstream checks can consume while preserving source references.
- **Horizontal axis · Parallel**: Independent modality processors can run concurrently, after which a fuser joins their typed artifacts. The gather step records how each claim maps back to its source.

## Solution and mechanics

Choose each representation from the signal the next check needs. Preserve images for spatial evidence, use Markdown or JSON for document structure, keep timestamped transcripts with audio references for speech, and filter logs into typed events. Fusion then joins those artifacts while retaining source references.

<table>
<thead>
<tr>
<th style="text-align: left;">Input type</th>
<th style="text-align: left;">Default handling</th>
<th style="text-align: left;">Cost comparison</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Architecture diagrams, flowcharts</td>
<td style="text-align: left;">Keep the source image when layout matters; optionally convert to Mermaid for search and editing</td>
<td style="text-align: left;">Structured forms are easier to query and revise; the image preserves visual layout</td>
</tr>
<tr>
<td style="text-align: left;">Tables, structured data</td>
<td style="text-align: left;">Convert to GitHub Flavored Markdown or typed records</td>
<td style="text-align: left;">Cell values remain exact and do not depend on visual parsing</td>
</tr>
<tr>
<td style="text-align: left;">Charts, heatmaps</td>
<td style="text-align: left;">Keep the image as evidence; extract required values into typed records and retain coordinates or labels</td>
<td style="text-align: left;">Verify numeric values against source data, tables, or a reviewed chart-extraction result</td>
</tr>
<tr>
<td style="text-align: left;">Long logs (&gt;&gt; window)</td>
<td style="text-align: left;">Three-layer pipeline</td>
<td style="text-align: left;">See below</td>
</tr>
</tbody>
</table>

Vision cost depends on model, resolution, and detail settings, so a fixed cross-provider table is misleading. Benchmark representative documents with the models and settings actually used, recording token use, latency, extraction quality, and cache behavior. Long logs can follow a three-stage pipeline: filter irrelevant content with grep, awk, or jq; have a sub-agent produce a structured summary; then place only the JSON artifact and a pointer to the raw log in the main context.

## Applicability

- **Financial research report analysis**: PDF tables + analyst text + market-size charts. None of the channels is complete on its own; they must be assembled before a judgment can be made.
- **Insurance claims**: Accident photos + claim report text + structured policy data combined.
- **Operations incident response**: Monitoring screenshots + long log fragments + configuration files. Long logs must go through the three-layer pipeline.
- **Mixed structured and unstructured input**: Use fusion when different channels contribute distinct evidence. If they repeat the same information, select the most reliable representation instead of processing every channel.

## Known failure modes

- **Misreading figures**: A chart-reading error can propagate through later turns. Cross-check extracted values against text, tables, or source data; route mismatches to human review; and preserve the figure source and extraction method with downstream claims.
- **Image input cost grows inside a loop**: Re-sending the full image at every step multiplies cost. Set limits for spend, tokens, elapsed time, and recursion depth; use thumbnails or cropped regions by default; and cache stable input.
- **Sub-agent loops and lost findings**: A truncated handoff can leave a downstream agent with incomplete instructions, causing repeated requests back to the sender. Store the complete finding in a state store and pass a pointer ID; require every sub-agent to declare a budget and termination condition before it starts. This illustrates the failure mechanism and is not presented as a verified enterprise incident with a specific loss figure.
- **One-size-fits-all truncation threshold**: Retention should follow each tool's information distribution. Shell output often needs both the command context near the beginning and the error stack near the end; file reads may need the beginning, the end, or relevant excerpts depending on file type. A fixed ratio can discard decisive evidence.

## Verification and metrics

- **Token share by modality**: Track image, table, text, and log usage separately. A sudden change from the local baseline should trigger inspection of conversion paths, duplicate submission, and cache behavior.
- **Budget enforcement in the agent loop**: Record triggers and interceptions for spend, tokens, elapsed time, and recursion depth. A budget that is missing or enforced only after a call is a runtime defect.
- **Secondary extraction rate on the chart path**: Of the charts that go through vision, how many do a chart→CSV extraction before computing. Taking a vision-output number directly for reasoning is a high-risk signal.

## Reference implementation

```
fuse(inputs):                       # inputs are multiple heterogeneous channels
                for each channel, dispatch by form:
                    TEXT   → straight into content
                    IMAGE  → base64 through vision (take this path only when spatial info is the signal)
                    TABLE  → convert to markdown (structure is the primary signal)
                    PDF    → extract TOC + locate key pages + key figures through vision + tables to md + drop decorative images
                    LOG    → bash pre-filter → sub-agent summary → structured JSON back to main context
                    AUDIO  → STT to text
                merge into unified content blocks, return + a trace (per channel: modality / tokens_out / method)
            health_check: watch token share by form, alert early on anomalous forms
```

Define small interfaces for OCR, speech-to-text, PDF extraction, log filtering, and specialist agents. Environment-specific implementations can then change without rewriting the fusion flow. Load optional multimedia libraries only on the path that needs them, and return a typed capability error when a dependency is unavailable.

## Illustrative scenario

Consider a research-report agent evolving through three implementations. The first sends the whole PDF to vision and misreads the magnitude of a chart. The second converts everything to OCR text and loses spatial relationships. The third extracts the table of contents, locates relevant pages, keeps key figures as images, converts tables to markdown, drops decorative material, and cross-checks chart values against text and tables. The lesson is to choose a representation for each modality and retain the provenance needed to verify it.

## Related patterns

- **Context Triage (P1), Semantic Compaction (P2), Progressive Discovery (P3)**: Fusion determines the representation. Triage selects among represented sources, compaction reduces admitted material, and discovery acquires missing evidence.
- **Fan-Out/Gather (C2)**: Independent modality processors may use C2, with one gather step producing the fused artifact and provenance map.
- **Layered Retention (M1)**: Large source artifacts can remain in external storage while the context carries a versioned pointer and a bounded extraction. Cross-session retention still requires memory admission.

## Design conclusion

Measure fusion through extraction error, missing cross-modal links, context cost, and acceptance failures by modality. The fused artifact should preserve the evidence required by downstream checks without copying every source in full.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>P4 Multi-Modal Fusion</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-p4-multi-modal-fusion">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
