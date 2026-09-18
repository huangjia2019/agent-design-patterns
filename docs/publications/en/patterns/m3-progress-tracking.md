<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/patterns/" style="color: var(--color-text-muted);">Pattern Matrix</a><span style="margin:0 0.45rem;">/</span>White Paper<span style="margin:0 0.45rem;">/</span>M3</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent Design Pattern White Paper</p>
<h1>M3 · Progress Tracking</h1>
<p class="publication-deck">Maintain a goal contract, structured progress, authoritative state references, and checkpoints across a long task so that work can resume without drifting or repeating side effects.</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>Coordinate</strong></td>
<td style="text-align: left;">Memory × Orchestrate</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Cost</strong></td>
<td style="text-align: left;">Low (reading and writing state fields is cheap)</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Pattern group</strong></td>
<td style="text-align: left;">Memory patterns</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Summary</strong></td>
<td style="text-align: left;">Maintain a goal contract, structured progress, authoritative state references, and checkpoints across a long task so that work can resume without drifting or repeating side effects.</td>
</tr>
</tbody>
</table>

---

## Problem

An LLM relies on the context window to retain current task information, and intermediate material in a long context may receive less attention. During extended debugging, the original plan can leave the effective working set. An agent may complete some files, become absorbed in a local defect, and then move to testing while a planned file remains uncreated.

Progress tracking externalizes the goal, milestones, blockers, and next step, then reloads them before consequential decisions. Databases, state machines, and ledgers remain authoritative for business state. The progress record carries references and task narrative; an old summary cannot decide which operational version is current.

## Classification: Memory × Orchestrate

- **Vertical axis · Memory**: Progress state preserves the goal, current step, completed artifacts, blockers, and recovery position across decisions and sessions.
- **Horizontal axis · Orchestrate**: One coordinator owns the plan state, chooses the next ready step, and updates checkpoints across the task. This differs from a chain in which each step only passes an artifact to its successor.

## Solution and mechanics

1. **Goal Contract**: Keep the objective, acceptance conditions, forbidden actions, and exit conditions at the top of the task ledger. Later compaction may shorten narrative but must preserve acceptance and prohibitions.
2. **Separate plan from progress**: A plan describes expected steps. Progress stores each step's `pending / in_progress / blocked / needs_review / completed / failed` state, owner, dependencies, and next action. A single-threaded branch has one active step; explicit parallel branches maintain separate state.
3. **Reference authoritative business state**: `state_refs` point to database records, approvals, commits, or business ledgers. Resolve them again on resume rather than treating values copied into a checkpoint as current truth.
4. **Create artifact checkpoints**: At each milestone, store verifiable artifacts, state references, action receipts, and a resume cursor. Irreversible actions use idempotency keys or business receipts to prove completion.
5. **Re-anchor at risk boundaries**: Reload the Goal Contract, active milestone, and prohibitions after a tool-call threshold, on failure, at a subtask switch, on resume, and before a high-risk commit.
6. **Stop on conflict**: When progress conflicts with current authoritative state, acceptance criteria, or an action receipt, move to `needs_review`. The agent does not silently choose the most recent-looking prose.
7. **Isolate levels and archive history**: The main agent keeps milestones and acceptance criteria; sub-agents keep local steps and return structured summaries. Completion clears the active view while preserving the event history for audit and replay.

## Applicability

- **Multi-step long tasks**: Tasks spanning many turns and prone to losing planned work during detail-chasing, such as refactoring, multi-file changes, and complex debugging.
- **Recoverable long flows**: Scenarios where a task may crash midway and need to resume. After progress is persisted, the second session reads the progress, skips what is completed, and recovers from the interrupted step without redoing work.
- **Goals advanced over multiple sessions**: Investment research, migration work, and long investigations can retain durable milestones while each session creates bounded local steps and writes completed artifacts back to the task ledger.

## Known failure modes

- **Forcing it onto a simple task**: Plain conversation, one-off Q&A, and work that can be completed directly usually do not need todos.
- **Allowing multiple in\_progress in one serial branch**: The next action becomes ambiguous. Real parallel work needs explicit branches or separate agents with independent state.
- **Marking a todo complete before business state commits**: A UI status is narrative. Without a database version, action receipt, or acceptance artifact, the system cannot claim that a side effect occurred.
- **Restoring stale checkpoint values over current state**: Replaying copied parameters may repeat a payment or publication and overwrite later human changes. Resolve every `state_ref` on resume.
- **Compressing the goal into “continue processing”**: Once acceptance, prohibitions, and exit conditions disappear, a local detail can become the agent's new goal.
- **Treating a historical decision as the current decision**: Retrieved discussion and old versions can pull the agent back to a superseded baseline. Authoritative decisions need accepted, superseded, or revoked status.
- **Main agent and sub-agent sharing one pool**: Detail todos from sub-agents can drown out the main agent's high-level plan. Sub-agents should maintain separate lists and return structured progress upward.
- **No framework-level re-anchor or nudge**: The agent stops updating progress or closes work without verification, and the runtime still allows it to continue. Escalation should reflect task risk and execution authority.

## Verification and metrics

- **Plan-omission rate**: The share of long tasks that skip an item from the original plan. Compute it from replay or task audits rather than UI state alone.
- **Goal and acceptance coverage**: Each active step should map to the Goal Contract, and task closure should supply evidence for every acceptance condition.
- **Goal-drift events**: Count active steps that no longer relate to the objective, prohibitions, or active milestone.
- **Verification-step coverage**: Whether applicable tasks include verification before closing. Set the requirement by task risk and record whether the nudge changes behavior.
- **Resume success rate**: Whether recovery continues from persisted progress without repeating completed irreversible actions.
- **Duplicate side-effect events**: Count business actions repeated during resume, retry, or concurrency because no idempotency proof was available.
- **State-reference freshness**: Verify that `state_refs` are resolved to current versions on resume and before high-risk actions.
- **Single-in\_progress compliance**: A single-threaded executor must have only one active item. A violation exposes a state-machine or concurrency-boundary defect.

## Reference implementation

```
GoalContract:
                goal_id / objective / acceptance[] / forbidden[] / exit_conditions[]

            PlanStep:
                step_id / title / owner_id / depends_on[]
                status(pending|in_progress|blocked|needs_review|completed|failed)
                acceptance[] / artifact_refs[] / action_receipts[]

            ProgressState:
                active_milestone / current_step / blocked_by / next_step
                state_refs[] / decision_refs[] / checkpoint_ref / resume_cursor

            before_decision():
                reload GoalContract + active milestone + current state_refs
                stop on version, receipt, or acceptance conflict

            checkpoint():
                append progress event + artifact hashes + action receipts
                snapshot the active view without replacing authoritative business state
```

Store progress events append-only and rebuild the active view from them. High-risk actions share one trace before and after execution. A checkpoint stores references and receipts, not a second copy of mechanical state that can become stale.

## Illustrative scenario

Consider an investment-research agent that updates a view on one company over an extended period. Its Goal Contract stores the research subject, deliverables, evidence-date requirements, and the rule that portfolio-manager approval cannot be bypassed. Each session keeps only steps that can be completed in that run, then writes reports, data snapshots, and review decisions to artifact references. Position and approval state come from business systems, while the progress ledger stores pointers. Resume refreshes those references; a conflict between the research conclusion and current position or approval state enters `needs_review` instead of continuing from an old checkpoint.

## Related patterns

- **Layered Retention (M1)**: Progress tracking is the hottest layer within the hierarchy. The runtime loads the active item and enough of the higher-level goal for each decision.
- **Failure Journals (M4)**: M3 records expected work and current position. M4 preserves failure events, candidate diagnoses, and verified lessons. Link both to the same task, step, and trace identifiers.
- **Plan-and-Execute (A2)**: A2 creates and schedules the plan. M3 persists the changing execution state, artifacts, blockers, and resume cursor for that plan.
- **Hooks Pipeline (G4 legacy entry, now X1)**: Runtime hooks can persist progress after tool calls and reload the Goal Contract before risk boundaries. Hook behavior must remain idempotent and observable.
- **Observability (X1)**: ProgressState explains where the agent believes it is; unified traces and action receipts prove what the system actually did.

## Design conclusion

Progress tracking externalizes the direction, execution state, and recovery position of long work. The Goal Contract limits drift, authoritative references prevent stale prose from becoming truth, and artifacts plus receipts prevent repeated side effects after resume.

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-memory-engineering" class="related-case-band">
<p class="related-case-label">Pattern engineering note</p>
<h2 id="related-memory-engineering"><a href="https://adpsagent.com/patterns/engineering/memory-storage-on-kubernetes/">Agent Memory on Kubernetes: Storage Layers and Recovery</a></h2>
<p>Place this pattern in a multi-Pod service and inspect the system of record, version conflicts, retrieval indexes, and recovery path.</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation"><p><strong>Suggested citation:</strong> ADPS, <em>M3 Progress Tracking</em>, Agent Design Pattern White Paper v0.3, 2026-07-13. <a href="https://adpsagent.com/patterns/">Catalog</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">runnable code catalog</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>Document status:</strong> This is a public review draft. Illustrative scenarios explain the mechanism and are not presented as verified enterprise cases. See the <a href="https://adpsagent.com/cases/">case library</a> for attributed practice. ADPS welcomes case contributions with sources, measurement methods, and publication approval.</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">Chronicle</h2>
<dl>
<div><dt>Recorded source</dt><dd>ADPS pattern white paper; prior work and references are listed in the article</dd></div>
<div><dt>First published on ADPS</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/chronicle/#patterns-m3-progress-tracking">View in the ADPS Chronicle</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
