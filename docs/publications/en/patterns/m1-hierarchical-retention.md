<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>M1</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>M1 · Hierarchical Retention</h1>
<p class="publication-deck">Organize agent memory by scope, functional type, and access cost, then maintain the active working set through explicit admission, promotion, demotion, and retirement rules.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Memory × Hierarchy</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (multi-tier storage and loading overhead)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Memory patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Organize agent memory by scope, functional type, and access cost, then maintain the active working set through explicit admission, promotion, demotion, and retirement rules.</td>
</tr>
</tbody>
</table>

---

## Problem

An agent may need organization policy, project rules, user preferences, session progress, and recent tool results. These records have different owners, validity periods, access costs, and write controls. Loading all of them at startup increases context use and can displace the goal or current evidence.

Hierarchical retention separates three relationships that are often collapsed into one tree. Scope determines who may see a record, functional type determines how it is used, and access tier determines retrieval cost. The agent assembles only the working set required for the current task and keeps handles to the rest.

## Classification: Memory × Hierarchy

- **Vertical axis · Memory**: The pattern governs records retained across turns, sessions, users, projects, and organizations. It separates current working state from material intended for later tasks.
- **Horizontal axis · Hierarchy**: Scope and policy can inherit from organization to project to user or session, while access tiers move records among hot, warm, and cold paths. Overrides and movement remain explicit and independently versioned.

## Solution and mechanics

1. **Assign scope first**: Use `user / project / team / tenant / organization / session / turn` to determine ownership, visibility, and write authority. Moving content into a hot cache must not widen its scope.
2. **Classify functional type**: Distinguish working, episodic, semantic, procedural, and meta-memory. They serve current work, past events, stable knowledge, verified methods, and system self-records, with different retrieval triggers.
3. **Choose an access tier last**: Place content in hot, warm, or cold storage according to latency, frequency, capacity, and cost. Tiers may use different backends or different indexes, TTLs, and loading policies within one backend.
4. **Assemble a budgeted working set**: Load stable constraints and the active goal at startup, then retrieve session, project, and long-term material on demand. Per-source budgets keep low-priority history from displacing goals, constraints, and current evidence.
5. **Use multiple signals for promotion and demotion**: Hit frequency measures use, not truth. Scoring should include recency, usefulness, reliability, risk, and review status. Security policy and revocation lists require hard-retention rules outside ordinary eviction.
6. **Separate online reads from publication**: A running agent may read live memory and write new material to a candidate store. Promotion into active project, user, or organization memory requires schema, provenance, scope, conflict, and risk checks, followed by a versioned publication step with rollback.

## Applicability

- **Agents reused across sessions, users, and projects**: programming coaches, long-term assistants, and internal enterprise agents need to remember "who this user is, what this project is about, and where the last conversation left off."
- **Multi-tenant SaaS agents**: Tiering by scope naturally provides isolation—user A's preferences do not pollute user B's session, and project X's rules are not carried into project Y. Scenarios that cannot tolerate cross-tenant data leakage, such as finance, healthcare, and contract review, rely on this especially.
- **Enterprise developer agents**: Project instruction files illustrate scoped loading: organization and repository rules can be separated from user preferences and session state. The same principle applies even when the backing store is not a file.

## Known failure modes

- **Flattening separate dimensions into one tree**: Scope, functional type, and access tier answer different questions. A single user/project/session hierarchy couples permission, semantics, and cache movement.
- **No schema on the user tier**: Letting the agent write free text such as “Xiao Li knows decorators” gradually produces multiple phrasings for the same concept and weakens retrieval. High-frequency fields should use a typed schema.
- **Treating hit rate as correctness**: A false memory that is used repeatedly receives a higher score and reinforces itself. Promotion needs provenance, task outcome, and review status.
- **Evicting rare high-risk rules**: Safety policy, compliance constraints, and revocation lists may remain unused for long periods but must be present when needed. Give them a separate retention policy.
- **Designing everything as startup injection**: The user and project tiers suit startup injection, the session tier suits progressive reading, and the ephemeral tier suits real-time assembly. Mixing these access patterns causes old session material to crowd out the current task as the conversation grows.
- **Forcing tiering onto fully stateless scenarios**: Single-shot Q&A and one-off ETL transformations do not need cross-session memory.
- **Allowing runtime writes to overwrite high-level memory**: An unreviewed judgment from one task can propagate across sessions. Automatic writes should enter a candidate store and become active only through an independent publication process.
- **Hard-coding forgetting**: Device signals, compliance records, and long-term preferences have different retention goals. Configure TTL, decay, compaction, archive, and deletion by memory type and policy.
- **Eviction without a reason log**: Compliance (GDPR right-to-be-forgotten) and debugging both require proving "what was deleted, why, and when." Without a log, this cannot be proven.

## Verification and metrics

- **Working set hit rate**: The share of memory needed for reasoning that is available in the prompt. Establish a local baseline by task class and inspect missing evidence when the rate changes.
- **Per-tier token share** (allocated by budget): whether the tokens each tier loads into the prompt stay within budget. A tier that consistently exceeds its budget needs truncation or to be pushed down to on-demand loading.
- **Cross-tier pollution events**: Track whether incidental session data reaches the user tier or information crosses tenant boundaries. Treat any tenant-isolation violation as a security incident.
- **False-promotion and reviewer-rejection rate**: Sample records moving from candidate to active long-term memory and check for wrong scope, false facts, or low-quality summaries.
- **Stale-memory use rate**: Measure how often a superseded or expired version still affects a decision.
- **High-risk retention completeness**: Periodically inventory hard-retained material and verify that normal decay did not remove it from the usable set.
- **Hit rate and latency by access tier**: Observe retrieval distribution across hot, warm, and cold stores and interpret it with task outcomes.
- **Total startup tokens**: Compare with an unlayered history-loading baseline while verifying that critical information remains visible.

## Reference implementation

```
MemoryRecord:
                id / kind / scope / source / valid_from / valid_to
                supersedes / trust_status / risk / retrieval_keys

            write(candidate):
                validate schema + provenance + scope + sensitive data
                detect conflict and assign candidate|accepted|rejected
                publish an accepted record as a new version

            read(task):
                enforce tenant and scope filters
                exclude expired and superseded versions
                rank by task relevance + usefulness + reliability + risk
                assemble within per-source token budgets

            retire(record):
                decay, archive, revoke, or delete by policy
                append reason + actor + timestamp to the audit log
```

Backend selection serves access behavior; it does not define memory semantics. Even when all records initially share one database, scope, kind, validity, and trust remain independent fields.

## Illustrative scenario

Consider an execution-oriented payroll SaaS agent with three memory tiers. L1 holds the minimum information needed for the current step. L2 holds milestone records such as task status and the action just completed. L3 holds judgments and procedures that may be reused across tasks. The tiers cover the current step, the current task, and cross-task memory. Each has an independent token budget; L1 is assembled at runtime, and writes to L3 pass a trust check so that incidental information from one run does not become long-term memory.

## Related patterns

- **Progress Tracking (M3)**: Current task state changes frequently and belongs on a low-latency path. M3 defines its schema, transitions, checkpoints, and recovery behavior.
- **RAG (M2)**: M1 assembles retained records by scope and access tier. M2 builds and queries evidence indexes over corpora that remain outside the working set.
- **Failure Journals (M4) and Procedural Memory (M5)**: M4 and M5 define specialized long-term assets with their own admission, retrieval, and invalidation rules. M1 supplies their scope and loading controls.
- **Semantic Compaction (P2)**: Compaction reduces admitted session history while preserving recovery evidence. It does not decide whether the result should persist across tasks.
- **Memory Admission (candidate)**: M1 defines tier boundaries; admission decides whether a candidate may enter an active tier.

## Design conclusion

Hierarchical retention manages the agent's working set. Scope preserves isolation, functional type determines use, access tier controls cost, and versioned admission keeps a temporary judgment from becoming a long-term fact.

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-memory-engineering" class="related-case-band">
<p class="related-case-label">Pattern engineering note</p>
<h2 id="related-memory-engineering"><a href="https://adpsagent.com/patterns/engineering/memory-storage-on-kubernetes/">Agent Memory on Kubernetes: Storage Layers and Recovery</a></h2>
<p>Place this pattern in a multi-Pod service and inspect the system of record, version conflicts, retrieval indexes, and recovery path.</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>M1 Hierarchical Retention</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-m1-hierarchical-retention">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
