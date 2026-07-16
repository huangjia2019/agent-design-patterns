# Interface Registry

> **GENERATED FILE — DO NOT EDIT.** Regenerate with `python3 docs/gen_interface_registry.py`.
>
> **Truth for interfaces** = each pattern's `pattern.py` (module docstring contract + public API). This file is a view of it.
> **Truth for coordinates and taxonomy** = the ADPS master control board and the [adpsagent.com](https://adpsagent.com) pattern pages; the coordinates below are a labeled cache synced 2026-07-16, and conflicts resolve toward the ADPS side.
>
> **Citation discipline**: course lectures, whitepapers, and book chapters that quote an interface must pin the commit (`pattern.py@<hash>` in the document header). Interfaces do refactor; a pinned quote stays honest, an unpinned one rots.

Generated 2026-07-16 at HEAD `d7932e8` (working tree has uncommitted changes).

## Summary

| Pattern | Coordinate | Entry point | State |
|:--|:--|:--|:--|
| P1 上下文分诊 Context Triage | 感知 × 路由 | `ContextTriage` | 05-18 |
| P2 语义压缩 Semantic Compaction | 感知 × 链式 | `SemanticCompactor` | 05-18 |
| P3 渐进发现 Progressive Discovery | 感知 × 循环 | `ProgressiveDiscoverer` | 05-18 |
| P4 多模态融合 Multi-Modal Fusion | 感知 × 并行 | `MultiModalFuser` | 05-18 |
| M1 分层保留 Hierarchical Retention | 记忆 × 层级 | `HierarchicalRetention` | 05-18 |
| M2 RAG Retrieval-Augmented Generation | 记忆 × 链式 | `AgenticRAG` | 05-18 |
| M3 进度追踪 Progress Tracking | 记忆 × 编排 | `ProgressTracker` | 05-18 |
| M4 失败日记 Failure Journals | 记忆 × 循环 | `FailureJournal` | 05-18 |
| R1 思维链 Chain-of-Thought | 推理 × 链式 | `CoTManager` | 05-18 |
| R2 复杂度路由 Complexity-Based Routing | 推理 × 路由 | `FallbackChain` | 05-18 |
| R3 并行探索 Parallel Exploration | 推理 × 并行 | `ParallelExploration` | 05-18 |
| R4 迭代假设验证 Iterative Hypothesis Testing | 推理 × 循环 | `IterativeHypothesisLoop` | 05-18 |
| A1 工具调度 Tool Dispatch | 行动 × 路由 | `ToolDispatcher` | 05-19 |
| A2 规划执行 Plan-and-Execute | 行动 × 编排 | `Executor` | 07-16 |
| A3 提示链 Prompt Chaining | 行动 × 链式 | `PromptChain` | 07-16 |
| A4 守卫三明治 Guardrail Sandwich | 行动 × 层级 | `GuardrailSandwich` | 07-16 |
| F1 生成批评 Generator-Critic | 反思 × 链式 | `GeneratorCriticChain` | 07-12 ⚠ dirty |
| F2 技能包 Skill Package | 反思 × 路由 | `SkillLibrary` | 07-12 ⚠ dirty |
| F3 经验回放 Experience Replay | 反思 × 层级 | `ExperienceStore` | 07-12 |
| F4 自愈循环 Self-Heal Loop | 反思 × 循环 | `SelfHealLoop` | 07-12 ⚠ dirty |
| C1 层级委派 Hierarchical Delegation | 协作 × 层级 | `SettlementSupervisor` | 07-01 |
| C2 扇出聚合 Fan-out / Gather | 协作 × 并行 | `FanOutGather` | 07-01 |
| C3 对抗评审 Adversarial Review | 协作 × 循环 | `AdversarialReview` | 07-01 |
| C4 交接链 Handoff Chain | 协作 × 链式 | `HandoffChain` | 07-01 |
| G1 审批门 Approval Gate | 治理 × 路由 | README only | no impl |
| G2 爆炸半径控制 Blast Radius Control | 治理 × 层级 | README only | no impl |
| G3 渐进承诺 Progressive Commitment | 治理 × 链式 | README only | no impl |
| G4 可观测性 Observability Harness | 治理 × 编排 | README only | no impl |

## 感知 Perception

### P1 上下文分诊 Context Triage — `perception/a-context-triage/`

- **Coordinate**: 感知 × 路由
- **State**: `pattern.py` 116 lines · last commit 763ff5d 2026-05-18 · clean · tests: yes
- **Summary**: Context Triage pattern.
- **Public API**: `Priority` *enum*; `ContextItem` *dataclass*; `TriageDecision` *dataclass*; `ContextTriage` *dataclass*(triage, decisions)
- **Contract lines (from docstring)**:
  - token budget, and treat error stack traces as un-droppable invariants.
  - This file is intentionally small (≈ 90 lines). It is not a framework. It is

### P2 语义压缩 Semantic Compaction — `perception/b-semantic-compaction/`

- **Coordinate**: 感知 × 链式
- **State**: `pattern.py` 258 lines · last commit 763ff5d 2026-05-18 · clean · tests: yes
- **Summary**: Semantic Compaction pattern.
- **Public API**: `Turn` *dataclass*; `CompactionAnchor` *dataclass*(to_summary); `CompactionEvent` *dataclass*(compression_ratio, all_errors_preserved); `SemanticCompactor` *class*(should_compact, compact, health_check)
- **Contract lines (from docstring)**:
  - The error trace is special. It is the agent's feedback loop and it must

### P3 渐进发现 Progressive Discovery — `perception/c-progressive-discovery/`

- **Coordinate**: 感知 × 循环
- **State**: `pattern.py` 256 lines · last commit e881812 2026-05-18 · clean · tests: yes
- **Summary**: Progressive Discovery pattern.
- **Public API**: `Phase` *enum*; `Candidate` *dataclass*; `DiscoveryEvent` *dataclass*; `DiscoverySession` *dataclass*(log); `ProgressiveDiscoverer` *class*(discover, health_check)
- **Contract lines (from docstring)**:
  - The pattern's invariant: **at no point do we pre-embed the entire

### P4 多模态融合 Multi-Modal Fusion — `perception/d-multimodal-fusion/`

- **Coordinate**: 感知 × 并行
- **State**: `pattern.py` 274 lines · last commit e881812 2026-05-18 · clean · tests: yes
- **Summary**: Multi-Modal Fusion pattern.
- **Public API**: `ModalityType` *enum*; `ModalityInput` *dataclass*; `FusionEvent` *dataclass*; `FusionResult` *dataclass*; `MultiModalFuser` *class*(fuse, health_check)
- **Contract lines (from docstring)**:
  - **IMAGE**: keep as image only when spatial information is signal (charts,

## 记忆 Memory

### M1 分层保留 Hierarchical Retention — `memory/a-hierarchical-retention/`

- **Coordinate**: 记忆 × 层级
- **State**: `pattern.py` 147 lines · last commit caa2bf0 2026-05-18 · clean · tests: yes
- **Summary**: Hierarchical Retention pattern.
- **Public API**: `Layer` *enum*; `MemoryLayer` *dataclass*(is_expired); `HierarchicalRetention` *class*(write, read, assemble_prompt_context, evict_expired, health_report)
- **Contract lines (from docstring)**:
  - lecture 03-02. The core observation: agent memory is not one thing.
  - The pattern's invariant: **inner layers override outer layers**. When the

### M2 RAG Retrieval-Augmented Generation — `memory/b-rag/`

- **Coordinate**: 记忆 × 链式
- **State**: `pattern.py` 256 lines · last commit caa2bf0 2026-05-18 · clean · tests: yes
- **Summary**: RAG (Retrieval-Augmented Generation) pattern — agentic version.
- **Public API**: `RetrievalMode` *enum*; `RetrievedChunk` *dataclass*; `RetrievalEvent` *dataclass*; `HybridRetriever` *class*(retrieve); `AgenticRAG` *class*(research)
- **Contract lines (from docstring)**:
  - Cheap, fast, fragile. Works well only when the query and the corpus
  - with explicit evidence weighting. The agent does the retrieval rather
  - The pattern's invariant: **the LLM judges retrieval quality on every
  - in the matrix (each step feeds the next), not `memory × single-step`.
- **Note**: Coordinate tension: canonical M2 = 记忆 × 链式 (single cell, fixed 2026-07-09), but this implementation demonstrates the *agentic* variant (`AgenticRAG.research()` is loop-shaped). The loop variant is a teaching footnote on the ADPS side; the coordinate stays 链式.

### M3 进度追踪 Progress Tracking — `memory/c-progress-tracking/`

- **Coordinate**: 记忆 × 编排
- **State**: `pattern.py` 201 lines · last commit caa2bf0 2026-05-18 · clean · tests: yes
- **Summary**: Progress Tracking pattern.
- **Public API**: `TodoStatus` *enum*; `TodoItem` *dataclass*(todo_id); `TodoList` *dataclass*(add, start, complete, request_review, in_progress_item, all_done, pending_count, render); `ProgressTracker` *class*(get_list, evict_if_all_done, context_loss_detected, nudge_message)
- **Contract lines (from docstring)**:
  - list, and nudge it back to that list whenever the conversation drifts.
  - Invariants enforced by `TodoList`:

### M4 失败日记 Failure Journals — `memory/d-failure-journals/`

- **Coordinate**: 记忆 × 循环
- **State**: `pattern.py` 291 lines · last commit caa2bf0 2026-05-18 · clean · tests: yes
- **Summary**: Failure Journals pattern.
- **Public API**: `FailureCategory` *enum*; `FailureEntry` *dataclass*(from_exception, to_dict); `FailureJournal` *class*(record, by_category, high_risk_entries, recall_for_task, render_for_prompt, health_report, export_json)
- **Contract lines (from docstring)**:
  - erasing evidence — and without evidence the model cannot adapt**. (The
  - because the lesson was never written down anywhere the agent can pull
  - `BOUNDARY_LEAK` — config/env/tenant slipped across a boundary that

## 推理 Reasoning

### R1 思维链 Chain-of-Thought — `reasoning/a-chain-of-thought/`

- **Coordinate**: 推理 × 链式
- **State**: `pattern.py` 263 lines · last commit b8dd3a6 2026-05-18 · clean · tests: yes
- **Summary**: Chain-of-Thought pattern.
- **Public API**: `ThinkingEffort` *enum*; `ThinkingBlock` *dataclass*(is_compatible_with); `CoTTrace` *dataclass*(total_thinking_tokens, reasoning_token_ratio, strip_for_fallback); `CoTManager` *class*(create_trace, normalize_tags, estimate_effort, audit_view)
- **Contract lines (from docstring)**:
  - not what this pattern is anymore. In 2026 every frontier model emits
  - when the chain has to cross a model boundary (Claude Code's "thinking
  - The pattern's claim, stated as one sentence: **CoT in 2026 is not a
  - treated as first-class structured data with lifecycle invariants you
  - enforce in the harness, not in the prompt.**

### R2 复杂度路由 Complexity-Based Routing — `reasoning/b-complexity-routing/`

- **Coordinate**: 推理 × 路由
- **State**: `pattern.py` 245 lines · last commit b8dd3a6 2026-05-18 · clean · tests: yes
- **Summary**: Complexity-Based Routing pattern.
- **Public API**: `ComplexityTier` *enum*; `RoutingDecision` *dataclass*; `ComplexityRouter` *class*(route); `FallbackTriggeredError` *class*; `FallbackStep` *dataclass*; `FallbackChain` *class*(run)
- **Module functions**: `length_signal`, `causal_keyword_signal`, `template_query_signal`
- **Contract lines (from docstring)**:
  - not every query needs Opus.** With GPT-4o ~16× the price of
  - `ComplexityRouter` — picks an initial tier from the task shape using
  - `RoutingDecision` with reason; *never* a bare model id, because the
  - The whole point: routing is product economics, not infra plumbing.
  - Make the policy explicit and inspectable.

### R3 并行探索 Parallel Exploration — `reasoning/c-parallel-exploration/`

- **Coordinate**: 推理 × 并行
- **State**: `pattern.py` 201 lines · last commit b8dd3a6 2026-05-18 · clean · tests: yes
- **Summary**: Parallel Exploration pattern.
- **Public API**: `AggregationStrategy` *enum*; `BranchResult` *dataclass*; `ParallelTrace` *dataclass*(total_tokens, branch_agreement_rate, effective_n); `ParallelExploration` *class*(run)
- **Contract lines (from docstring)**:
  - can replay the disagreement, not just the winner.
  - business decision about asymmetric error cost, not an engineering

### R4 迭代假设验证 Iterative Hypothesis Testing — `reasoning/d-iterative-hypothesis/`

- **Coordinate**: 推理 × 循环
- **State**: `pattern.py` 240 lines · last commit b8dd3a6 2026-05-18 · clean · tests: yes
- **Summary**: Iterative Hypothesis Testing pattern.
- **Public API**: `HypothesisStatus` *enum*; `Evidence` *dataclass*; `Hypothesis` *dataclass*(record_evidence); `HypothesisTree` *class*(add, active, confirmed, survivor_count, by_id); `LoopOutcome` *dataclass*; `IterativeHypothesisLoop` *class*(run)
- **Contract lines (from docstring)**:
  - "all strong alternatives have been falsified,"** not "we found

## 行动 Action

### A1 工具调度 Tool Dispatch — `action/a-tool-dispatch/`

- **Coordinate**: 行动 × 路由
- **State**: `pattern.py` 246 lines · last commit 84aa18c 2026-05-19 · clean · tests: yes
- **Summary**: Tool Dispatch pattern.
- **Public API**: `RiskLevel` *enum*; `ToolMetadata` *dataclass*; `DispatchTrace` *dataclass*; `ToolDispatchError` *class*; `ToolDispatcher` *class*(register, dispatch, rollback_session)
- **Contract lines (from docstring)**:
  - Selecting which tool to invoke out of seventeen candidates does not.
  - `is_read_only` and `is_concurrency_safe` default to **False**.
  - tools without rollback simply cannot be registered.
- **Note**: Also carries A5 最简工具集 (Minimal Tool Set), the extension pattern folded into Tool Dispatch on the teaching side. (Numbering rule 2026-07-16: core patterns hold 1-4 per row, extensions start at 5.)

### A2 规划执行 Plan-and-Execute — `action/b-plan-and-execute/`

- **Coordinate**: 行动 × 编排
- **State**: `pattern.py` 326 lines · last commit d7932e8 2026-07-16 · clean · tests: yes
- **Summary**: Plan-and-Execute pattern.
- **Public API**: `StepStatus` *enum*; `PlanStep` *dataclass*; `Plan` *dataclass*(add, validate, ready_steps, is_complete, first_failed); `PlanError` *class*; `Executor` *class*(run)
- **Module functions**: `approve`, `release_blocked`, `replan_local`
- **Contract lines (from docstring)**:
  - first-class durable artifact, not the contents of the model's
  - `Planner` — produces a `Plan` (a DAG of `PlanStep`s with explicit
  - failure triggers *local* replan (not global rewrite).
  - finished, costs balloon. `replan_local` here only touches steps

### A3 提示链 Prompt Chaining — `action/c-prompt-chaining/`

- **Coordinate**: 行动 × 链式
- **State**: `pattern.py` 265 lines · last commit d7932e8 2026-07-16 · clean · tests: yes
- **Summary**: Prompt Chaining pattern.
- **Public API**: `StepResult` *enum*; `ChainStep` *dataclass*; `StepRun` *dataclass*; `ChainTrace` *dataclass*(step_outputs); `PromptChain` *class*(run)
- **Module functions**: `length_gate`, `keys_gate`, `regex_gate`, `any_gate`, `all_gate`
- **Contract lines (from docstring)**:
  - access to all *prior* outputs (not just the immediately previous
  - tolerable* outputs, not perfect ones; the retry budget is the

### A4 守卫三明治 Guardrail Sandwich — `action/d-guardrail-sandwich/`

- **Coordinate**: 行动 × 层级
- **State**: `pattern.py` 406 lines · last commit d7932e8 2026-07-16 · clean · tests: yes
- **Summary**: Guardrail Sandwich pattern.
- **Public API**: `HookPhase` *enum*; `HookResult` *enum*; `GuardrailViolation` *dataclass*; `HookSpec` *dataclass*; `HookOutcome` *dataclass*; `SandwichTrace` *dataclass*; `GuardrailSandwich` *class*(register_tool, add_hook, run)
- **Module functions**: `amount_threshold_hook`, `blocklist_hook`, `output_schema_hook`, `pii_redaction_hook`
- **Contract lines (from docstring)**:
  - for rollback. Both layers are owned by the harness, not the agent;
  - the agent does not get to bypass them by being clever.
  - the tool never runs. On a post-hook violation, the trace is marked
  - as requiring compensation; this class does not execute a saga.
  - its public registry; production deployments must close this at the
  - service or capability boundary.

## 反思 Reflection

### F1 生成批评 Generator-Critic — `reflection/a-generator-critic/`

- **Coordinate**: 反思 × 链式
- **State**: `pattern.py` 192 lines · last commit 5eae0f7 2026-07-12 · **UNCOMMITTED CHANGES** · tests: yes
- **Summary**: Generator-Critic reference interface.
- **Public API**: `Severity` *enum*; `Decision` *enum*; `Issue` *dataclass*(grounded); `Artifact` *dataclass*(revise); `Critique` *dataclass*(blockers, warnings, ungrounded); `AcceptancePolicy` *dataclass*(decide); `ChainResult` *dataclass*(artifact, requires_re_review); `GeneratorCriticChain` *class*(run, review)
- **Contract lines (from docstring)**:
  - The critic reports evidence about the artifact. It does not approve the artifact.
  - pass is explicitly unreviewed and therefore cannot be accepted by the same pass.
  - Repeating review and repair until a deterministic signal turns green belongs to
  - the sibling Self-Heal Loop pattern. An outer workflow may schedule another
  - Generator-Critic pass, but the loop is not hidden inside this interface.

### F2 技能包 Skill Package — `reflection/b-skill-package/`

- **Coordinate**: 反思 × 路由
- **State**: `pattern.py` 196 lines · last commit ab7f5e0 2026-07-12 · **UNCOMMITTED CHANGES** · tests: yes
- **Summary**: Skill Package pattern.
- **Public API**: `SkillStatus` *enum*; `GoldenQuestion` *dataclass*; `Skill` *dataclass*(success_rate); `VerificationReport` *dataclass*; `RouteDecision` *dataclass*; `SkillLibrary` *class*(add, verify, route, record_use, retire)
- **Module functions**: `distill_from_trace`
- **Contract lines (from docstring)**:
  - a skill enters the library only after it passes external verification,
  - and the router only ever routes to verified skills.** The agent saying
  - Router topology, not a chain: at runtime the pattern's core act is one
  - All must pass before the skill is promoted to VERIFIED. Failures keep
  - it in TRIAL, invisible to the router.
  - `SkillLibrary.route` — trigger matching over VERIFIED skills only.
  - No match returns an explicit from-scratch fallback; the router never
  - drops is demoted to TRIAL and must re-verify. That is the staleness
  - guard — policy years change, and last year's skill must not keep its
  - **Discovery mismatch** — triggers too vague, router picks the wrong
  - skill or none. Surfaced by the explicit RouteDecision record.

### F3 经验回放 Experience Replay — `reflection/c-experience-replay/`

- **Coordinate**: 反思 × 层级
- **State**: `pattern.py` 165 lines · last commit 4d30432 2026-07-12 · clean · tests: none
- **Summary**: Experience Replay pattern.
- **Public API**: `Experience` *dataclass*(reuses); `Heuristic` *dataclass*; `ExperienceStore` *class*(record, retrieve, render, feedback, distill, graduation_candidates)
- **Contract lines (from docstring)**:
  - a lesson stays in the replay pool only as long as reuse keeps proving
  - and only the second is a signal. Effectiveness tracking closes that
  - I ran an unrelated check first") stays plausible forever; only reuse

### F4 自愈循环 Self-Heal Loop — `reflection/d-self-heal-loop/`

- **Coordinate**: 反思 × 循环
- **State**: `pattern.py` 246 lines · last commit ff0e955 2026-07-12 · **UNCOMMITTED CHANGES** · tests: yes
- **Summary**: Self-Heal Loop reference implementation.
- **Public API**: `HealStatus` *enum*; `FailureSignal` *dataclass*(signature); `Patch` *dataclass*(fingerprint, touches_tests); `StabilityPolicy` *dataclass*; `HealRound` *dataclass*; `HealTrace` *dataclass*(baseline_restored); `SelfHealLoop` *class*(heal)
- **Module functions**: `propose_guard`

## 协作 Collaboration

### C1 层级委派 Hierarchical Delegation — `collaboration/a-hierarchical-delegation/`

- **Coordinate**: 协作 × 层级
- **State**: `pattern.py` 159 lines · last commit 5a9bfa8 2026-07-01 · clean · tests: yes
- **Summary**: Hierarchical Delegation pattern.
- **Public API**: `Verdict` *enum*; `WorkerSpec` *dataclass*; `SalaryBatchArtifact` *dataclass*; `SafetyBoundary` *class*(must_escalate); `SettlementSupervisor` *class*(decompose, run, synthesize)
- **Contract lines (from docstring)**:
  - context, and only ever sees the workers' structured artifacts — never their raw
  - work. The model is the same as a manager who delegates and reviews but never
  - This file is intentionally small (~130 lines). It is not a framework. It is the
  - a ``WorkerSpec`` (Spec), runs in isolation and returns only an artifact
  - (Budget), and is admitted only through ``SafetyBoundary`` (Gate).
  - **The Manager-Never-Executes rule** (主管不下场) — the supervisor only
  - decomposes / dispatches / synthesizes / gates. It reads artifacts, never a
  - worker's intermediate trace, and workers never talk to each other.

### C2 扇出聚合 Fan-out / Gather — `collaboration/b-fan-out-gather/`

- **Coordinate**: 协作 × 并行
- **State**: `pattern.py` 214 lines · last commit ee22a46 2026-07-01 · clean · tests: yes
- **Summary**: Fan-out-Gather pattern.
- **Public API**: `Strategy` *enum*; `Layer` *enum*; `SourceResult` *dataclass*; `AggregatorPolicy` *dataclass*; `LineItemVerdict` *dataclass*; `Reconciler` *class*(reconcile); `FanOutGather` *class*(run)
- **Contract lines (from docstring)**:
  - Like the sibling patterns this file is small (~150 lines) and is not a framework.
  - real agents into the same shape; the reconciler under test never changes.
  - bound to an *attributable* boundary (one data source), the workers'
  - divergence stops being noise and becomes a locator: agree -> not here;
  - that does not -> human review. Encoded in :meth:`Reconciler.reconcile`.

### C3 对抗评审 Adversarial Review — `collaboration/c-adversarial-review/`

- **Coordinate**: 协作 × 循环
- **State**: `pattern.py` 147 lines · last commit d9fa352 2026-07-01 · clean · tests: yes
- **Summary**: Adversarial Review pattern.
- **Public API**: `Severity` *enum*; `Outcome` *enum*; `Itinerary` *dataclass*; `Objection` *dataclass*; `IndependenceGuard` *class*(check); `ReviewGate` *class*(open_blockers, may_confirm); `AdversarialReview` *class*(run)
- **Contract lines (from docstring)**:
  - purpose only: to attack it. Not to help write it, not to co-sign it — to find the
  - Like the sibling patterns this file is small (~150 lines) and is not a framework.
  - **The Three Isolations of Independence** (独立性三隔离) — a reviewer is only
  - plan, not the planner's private reasoning), *objective* (its job is to find
  - blockers, not to approve), and *identity* (a different agent, not the same one
  - **Objections, never endorsement** (只提异议不背书) — the reviewer returns a list
  - decided by a deterministic :class:`ReviewGate` (zero open blockers), never by the
- **Note**: Interface is single-round (run once, gate decides); the canonical coordinate 协作 × 循环 refers to the review-revise cycle owned by the outer workflow, mirroring how Generator-Critic keeps its loop outside the interface.

### C4 交接链 Handoff Chain — `collaboration/d-handoff-chain/`

- **Coordinate**: 协作 × 链式
- **State**: `pattern.py` 123 lines · last commit 4620664 2026-07-01 · clean · tests: yes
- **Summary**: Handoff Chain pattern.
- **Public API**: `SeamError` *class*; `Baton` *dataclass*; `StageSpec` *dataclass*; `HandoffChain` *class*(run)
- **Module functions**: `trip_chain`
- **Contract lines (from docstring)**:
  - one stage and passing a baton to the next. Not a tree (that is Hierarchical
  - Delegation), not parallel copies (that is Fan-out-Gather) — a line.
  - Like the sibling patterns this file is small (~140 lines) and is not a framework.
  - not three stages downstream where the cause is lost.
  - **Append-only baton** (棒上不回改) — the intent and committed facts are locked once
  - set. A later stage may add, never silently overwrite. A handoff passes values, not
  - a shared mutable scratchpad, so one stage cannot quietly rewrite what an earlier

## 治理 Governance (placeholders)

The four governance patterns are README-only: no `pattern.py`, no interface to register yet. G5 钩子流水线 Hooks Pipeline has no directory (extension pattern, folded into the governance control layer on the teaching side).

- G1 审批门 Approval Gate — 治理 × 路由 — `governance/a-approval-gate/` (README only)
- G2 爆炸半径控制 Blast Radius Control — 治理 × 层级 — `governance/b-blast-radius/` (README only)
- G3 渐进承诺 Progressive Commitment — 治理 × 链式 — `governance/c-progressive-commitment/` (README only)
- G4 可观测性 Observability Harness — 治理 × 编排 — `governance/d-observability-harness/` (README only)

## 组合 Composition

`composition/` holds methodology assets (selection card, six-step methodology, Argus case, checklist benchmark), not patterns; it is intentionally outside this registry's pattern list.
