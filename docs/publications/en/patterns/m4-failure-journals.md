<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>M4</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>M4 · Failure Journals</h1>
<p class="publication-deck">Separate immutable failure facts, candidate diagnoses, and verified lessons, then recall only applicable and current experience in later tasks.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Memory × Loop (turn)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Medium (structured storage + recall retrieval)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Memory patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Separate immutable failure facts, candidate diagnoses, and verified lessons, then recall only applicable and current experience in later tasks.</td>
</tr>
</tbody>
</table>

---

## Problem

Many agent systems preserve progress but discard the details of failure when a session ends. A later task can then repeat the same error. For example, an agent may write test-environment settings into production configuration and later make the same class of mistake in another project because the conditions and remediation were never retained.

A failure journal makes these events retrievable across tasks. The difficult part is the write path: an error is an observed fact, while root cause and lesson are judgments. The model that just failed may also misdiagnose the failure, so diagnosis and long-term publication cannot be one automatic step.

## Classification: Memory × Loop

- **Vertical axis · Memory**: The journal retains failure events, diagnoses, and reviewed lessons for use in later tasks.
- **Horizontal axis · Loop**: A later task retrieves an applicable lesson, records whether it influenced execution, and writes the new outcome back to evaluation and review. Counterexamples can revise or revoke the lesson.

## Solution and mechanics

A failure journal has three record layers and one recall path:

1. **Failure Event preserves immutable facts**: Store input references, tool calls, errors, system version, permission scope, and the original trace. Later diagnoses link to the event rather than rewriting it.
2. **Candidate Diagnosis preserves a testable explanation**: Store the hypothesized cause, proposed fix, author, confidence information, and applicability. Automatically generated diagnoses default to `candidate` and stay out of active recall.
3. **Verified Lesson publishes reusable experience**: After reproduction, tests, policy checks, or human review, publish a prevention rule, recall condition, valid versions, and invalidation criteria. A later lesson may supersede or revoke it.
4. **Recall at task boundaries**: Before task start, capability entry, or a high-risk tool call, filter by tenant, scope, system version, and failure signature, then rerank by risk and relevance. Only `accepted` and currently applicable lessons are injected.
5. **Write back evidence of use**: Record whether the lesson was retrieved, adopted, and associated with avoiding the repeated failure. A counterexample creates a new candidate diagnosis rather than mutating the old event.

Events, diagnoses, and lessons have different retention policies. Events follow audit requirements, weak candidates may expire quickly, and verified lessons require version and applicability management.

## Applicability

- **Long-running agents with recurring task classes**: The journal is useful when later tasks can retrieve a prior failure under comparable conditions and test whether the lesson prevented recurrence.
- **Multi-tenant SaaS agents**: High-risk failures such as cross-tenant misrouting require special handling—never evicted, force-recalled at the start of every task, alarm triggered on several consecutive records. The task signature uses a two-factor "tenant plus intent" key, so one tenant's failure should not cause another tenant to receive irrelevant reminders.
- **Agents performing high-risk, irreversible operations**: Scenarios where the cost of an error is large and the same mistake cannot be made twice. DevOps, finance, contract processing.

## Known failure modes

- **Applying it to one-off work**: If no later task can reuse the event or lesson, a normal execution trace may be sufficient. Retain a journal when recurrence, risk, or audit value justifies curation.
- **Free text without structured conditions**: A record containing only task, error, and timestamp cannot support reliable filtering by stage, version, tenant, or failure signature. Use constrained fields alongside narrative evidence.
- **Treating the model's explanation as fact**: The same agent generates a root cause and prevention rule immediately after failing, then writes it to long-term memory. A false diagnosis becomes a stable reason to avoid the correct path.
- **Promoting every minor error into a lesson**: Recall noise grows with the archive. Only candidates with sufficient reuse value or risk enter verification.
- **Using semantic similarity without condition filters**: Similar text does not imply the same tenant, tool version, permission, environment, or failure stage. Filter structured conditions before semantic retrieval.
- **Applying old lessons across versions**: The API, schema, or process changes while the historical fix remains active. Lessons need applicable versions and invalidation criteria.
- **Lumping high-risk and ordinary failures together**: A cross-tenant data leak and an API timeout require different treatment. High-risk failures need independent alerting, policy-controlled retention, and forced recall where applicable.

## Verification and metrics

- **Repeat failure rate**: The share of similar tasks that repeat the same failure signature. Compare versions and cohorts rather than database cleanliness alone.
- **Candidate promotion rate and rejection reasons**: Measure which diagnoses become verified lessons and why others fail due to false causes, broad scope, or weak evidence.
- **Recall precision and miss rate**: Test whether a published lesson appears for applicable tasks and stays out of unrelated ones.
- **Lesson adoption and avoided-failure rate**: Record whether the agent used the lesson and whether the same failure signature disappeared, compared with replay without injection.
- **Stale-lesson use rate**: Measure lessons that still influence decisions after supersession, revocation, or version expiry.
- **High-risk failure count**: Monitor tenant-boundary and other safety events independently. There is no acceptable background rate for a boundary violation.

## Reference implementation

```
FailureEvent:
                event_id / task_signature / category / stage / error
                input_refs[] / tool_calls[] / system_version / trace_ref / occurred_at

            CandidateDiagnosis:
                diagnosis_id / event_id / hypothesis / proposed_fix
                proposed_by / confidence / applicability / status(candidate|rejected|verified)

            VerifiedLesson:
                lesson_id / diagnosis_id / prevention_rule / recall_conditions[]
                valid_from / valid_to / applies_to_versions[] / supersedes / review_evidence[]

            recall(task):
                filter accepted lessons by tenant + scope + version + risk
                retrieve by failure signature and semantic relevance
                return lessons + source events + recall trace
```

A production implementation keeps FailureEvent append-only and manages candidate diagnoses and published lessons in separate stores or lifecycle states. Review evidence, publisher, and supersession all enter the audit trail.

## Illustrative scenario

Consider a multi-tenant SaaS support agent that repeatedly encounters tool timeouts, permission failures, and tenant-boundary mistakes. The tool trace and business version first become a FailureEvent. The model's “expired token” explanation enters Candidate Diagnosis only. After reproduction, the system publishes “refresh credentials and revalidate tenant\_id” as a Verified Lesson with an applicable version range. Retrieval filters by tenant, tool version, and intent before ranking. Unknown categories enter `needs_review`. Evaluation covers repeat failures, false recalls, and stale-lesson use.

## Related patterns

- **Procedural Memory (M5)**: M4 retains failure evidence and reviewed prevention rules. M5 retains verified procedures. A failed procedure may create an M4 event and move the corresponding M5 asset to revalidation.
- **Progress Tracking (M3)**: M3 records planned steps and current position. M4 records failure events, diagnoses, and reviewed lessons. A long-running task often needs both records linked by task and checkpoint identifiers.
- **Layered retention (M1)**: The failure journal is a dedicated partition within long-term memory, with retention tiers chosen by risk, access, and policy.
- **Self-Heal Loop (F4)**: F4 attempts bounded repair within the current task. M4 preserves the failure and reviewed lesson for later tasks, including cases where self-heal exhausted its budget.
- **Versioned Memory (candidate)**: Failure events remain immutable while diagnoses and lessons evolve through versions, supersession, and revocation.

## Design conclusion

A failure journal derives its value from publication discipline. Failure events supply evidence, candidate diagnoses remain falsifiable, and only verified lessons travel across tasks. Without that separation, a false lesson propagates more reliably than forgetting.

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>M4 Failure Journals</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-m4-failure-journals">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
