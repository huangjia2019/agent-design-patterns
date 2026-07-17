# Interface Registry

> **GENERATED FILE — DO NOT EDIT.** Regenerate with `python3 docs/gen_interface_registry.py`.
>
> **Truth for interfaces** = each pattern's `pattern.py` (module docstring contract + public API). This file is a view of it.
> **Truth for coordinates and taxonomy** = the ADPS master control board and the [adpsagent.com](https://adpsagent.com) pattern pages; the coordinates below are a labeled cache synced 2026-07-16, and conflicts resolve toward the ADPS side.
>
> **Citation discipline**: course lectures, whitepapers, and book chapters that quote an interface must pin the commit (`pattern.py@<hash>` in the document header). Interfaces do refactor; a pinned quote stays honest, an unpinned one rots.

Generated 2026-07-17 at HEAD `a5337b5` (working tree has uncommitted changes).

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
| F1 生成批评 Generator-Critic | 反思 × 链式 | `GeneratorCriticChain` | 07-17 |
| F2 技能包 Skill Package | 反思 × 路由 | `SkillLibrary` | 07-17 |
| F3 经验回放 Experience Replay | 反思 × 层级 | `ExperienceStore` | 07-17 |
| F4 自愈循环 Self-Heal Loop | 反思 × 循环 | `SelfHealLoop` | 07-17 |
| C1 层级委派 Hierarchical Delegation | 协作 × 层级 | `SettlementSupervisor` | 07-17 |
| C2 扇出聚合 Fan-out / Gather | 协作 × 并行 | `FanOutGather` | 07-17 |
| C3 对抗评审 Adversarial Review | 协作 × 循环 | `AdversarialReview` | 07-17 |
| C4 交接链 Handoff Chain | 协作 × 链式 | `HandoffChain` | 07-17 |
| Shared 协作边界契约 Collaboration Boundary Contract | 协作横切接口 | `TaskContract` → `AcceptanceReceipt` | 07-17 |
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
- **State**: `pattern.py` 200 lines · last commit adc1b24 2026-07-17 · clean · tests: yes
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
- **State**: `pattern.py` 211 lines · last commit 27e920b 2026-07-17 · clean · tests: yes
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
- **State**: `pattern.py` 174 lines · last commit f00cc6c 2026-07-17 · clean · tests: yes
- **Summary**: Experience Replay pattern.
- **Public API**: `Experience` *dataclass*(reuses); `Heuristic` *dataclass*; `ExperienceStore` *class*(record, retrieve, render, feedback, distill, graduation_candidates)
- **Contract lines (from docstring)**:
  - a lesson stays in the replay pool only as long as reuse keeps proving
  - and only the second is a signal. Effectiveness tracking closes that
  - I ran an unrelated check first") stays plausible forever; only reuse

### F4 自愈循环 Self-Heal Loop — `reflection/d-self-heal-loop/`

- **Coordinate**: 反思 × 循环
- **State**: `pattern.py` 250 lines · last commit b37d023 2026-07-17 · clean · tests: yes
- **Summary**: Self-Heal Loop reference implementation.
- **Public API**: `HealStatus` *enum*; `FailureSignal` *dataclass*(signature); `Patch` *dataclass*(fingerprint, touches_tests); `StabilityPolicy` *dataclass*; `HealRound` *dataclass*; `HealTrace` *dataclass*(baseline_restored); `SelfHealLoop` *class*(heal)
- **Module functions**: `propose_guard`

## 协作 Collaboration

### C1 层级委派 Hierarchical Delegation — `collaboration/a-hierarchical-delegation/`

- **Coordinate**: 协作 × 层级
- **State**: `pattern.py` 596 lines · last commit 594304a 2026-07-17 · clean · tests: yes
- **Summary**: Hierarchical Delegation pattern.
- **Public API**: `Verdict` *enum*; `SalaryBatchResult` *dataclass*; `BatchAssignment` *dataclass*(batch_id); `SafetyBoundary` *dataclass*(evaluate); `PayrollPortfolioResult` *dataclass*; `PortfolioBoundary` *dataclass*(evaluate); `DelegationSummary` *dataclass*(total, employee_count, auto_approved, human_review); `SettlementSupervisor` *class*(root_contract, decompose, run, synthesize)
- **Module functions**: `batch_fingerprint`, `bind_salary_result`
- **Contract lines (from docstring)**:
  - contracts, dispatches each child through an isolated handoff, and accepts only

### C2 扇出聚合 Fan-out / Gather — `collaboration/b-fan-out-gather/`

- **Coordinate**: 协作 × 并行
- **State**: `pattern.py` 851 lines · last commit 8aa5a33 2026-07-17 · clean · tests: yes
- **Summary**: Fan-out / Gather pattern.
- **Public API**: `Strategy` *enum*; `Layer` *enum*; `ContributionRule` *enum*; `ReconciliationStatus` *enum*; `Tolerance` *dataclass*(matches); `SourceSpec` *dataclass*; `SourceResult` *dataclass*(from_mapping, ok, values); `ConflictResolution` *dataclass*; `LineItemVerdict` *dataclass*(values); `MergedItem` *dataclass*; `ReconciliationReport` *dataclass*(agreed_items, attributable_divergences, to_human, merged, total); `AggregatorPolicy` *dataclass*; `SourceAdmissionPolicy` *dataclass*(evaluate); `Reconciler` *class*(reconcile); `AggregationBoundary` *dataclass*(evaluate); `AggregationRun` *dataclass*(report); `FanOutGather` *class*(handoff_for, run)
- **Module functions**: `bind_source_result`
- **Contract lines (from docstring)**:
  - Every source must return a contract-bound artifact.
  - The gather must apply explicit comparison or contribution semantics.

### C3 对抗评审 Adversarial Review — `collaboration/c-adversarial-review/`

- **Coordinate**: 协作 × 循环
- **State**: `pattern.py` 648 lines · last commit a06e6e3 2026-07-17 · clean · tests: yes
- **Summary**: Adversarial Review pattern.
- **Public API**: `Outcome` *enum*; `Objection` *dataclass*; `ReviewPolicy` *dataclass*; `ReviewRequest` *dataclass*; `ReviewFn` *class*; `ReviseFn` *class*; `ReviewerSpec` *dataclass*; `ReviserSpec` *dataclass*; `ReviewerFailure` *dataclass*; `ReviewReceipt` *dataclass*(blockers, complete); `ReviewPanel` *dataclass*(review); `IndependenceGuard` *dataclass*(evaluate); `ReviewGate` *dataclass*(may_confirm); `ReviewRound` *dataclass*; `ReviewRun` *dataclass*(latest_review); `AdversarialReview` *class*(run)
- **Contract lines (from docstring)**:
  - A candidate artifact crosses a release boundary only after independent reviewers
  - return machine-readable objections against a versioned rubric. Reviewers must
  - return objections, never endorsement. A deterministic gate combines declared
  - This module owns the loop topology: review the current artifact, revise only
  - version. The final round never creates an unreviewed replacement artifact.
- **Note**: The interface owns a bounded review-revise-review loop. Each round produces a ReviewReceipt bound to the current artifact fingerprint and rubric version; the final round cannot create an unreviewed replacement artifact.

### C4 交接链 Handoff Chain — `collaboration/d-handoff-chain/`

- **Coordinate**: 协作 × 链式
- **State**: `pattern.py` 617 lines · last commit a5337b5 2026-07-17 · clean · tests: yes
- **Summary**: Handoff Chain pattern.
- **Public API**: `SeamError` *class*; `FactValue` *dataclass*; `FactRule` *dataclass*; `FactRecord` *dataclass*; `Baton` *dataclass*(facts, fact_record, fingerprint, snapshot_id); `BatonView` *dataclass*; `StageSpec` *dataclass*; `StageDelta` *dataclass*; `StageFn` *class*; `StageBinding` *dataclass*; `StageReceipt` *dataclass*; `ChainRun` *dataclass*; `HandoffChain` *class*(run, advance)
- **Module functions**: `new_baton`
- **Contract lines (from docstring)**:
  - read-only snapshot, consumes declared facts, and returns a typed delta. The chain
  - The shared collaboration boundary remains:
  - The pattern owns five invariants:
  - a stage must receive every fact it declares in ``requires``;
  - a stage must itself deliver every fact it declares in ``provides``;
  - one fact has one declared producer and committed facts are append-only;
  - values cross the seam only after type, evidence, and semantic validation;

### Shared 协作边界契约 Collaboration Boundary Contract

- **Role**: cross-cutting interface shared by C1-C4; not a fifth pattern
- **State**: `boundary_contract.py` 235 lines · last commit 594304a 2026-07-17 · clean
- **Summary**: Shared boundary contract for collaboration patterns.
- **Public API**: `FindingSeverity` *enum*; `AcceptanceDecision` *enum*; `ExecutionBudget` *dataclass*; `TaskContract` *dataclass*(digest); `Finding` *dataclass*; `AcceptanceReceipt` *dataclass*(accepted); `HandoffEnvelope` *dataclass*; `ArtifactEnvelope` *dataclass*(bind)
- **Contract chain**: `TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt`
- **Version invariant**: The contract is immutable and content-addressed. Artifacts and receipts bind to that exact digest, so approval cannot drift to a different task version. This module defines the transport-neutral interface; each pattern still owns how it decomposes, dispatches, aggregates, challenges, or sequences work.

## 治理 Governance (placeholders)

The four governance patterns are README-only: no `pattern.py`, no interface to register yet. G5 钩子流水线 Hooks Pipeline has no directory (extension pattern, folded into the governance control layer on the teaching side).

- G1 审批门 Approval Gate — 治理 × 路由 — `governance/a-approval-gate/` (README only)
- G2 爆炸半径控制 Blast Radius Control — 治理 × 层级 — `governance/b-blast-radius/` (README only)
- G3 渐进承诺 Progressive Commitment — 治理 × 链式 — `governance/c-progressive-commitment/` (README only)
- G4 可观测性 Observability Harness — 治理 × 编排 — `governance/d-observability-harness/` (README only)

## 组合 Composition

`composition/` holds methodology assets (selection card, six-step methodology, Argus case, checklist benchmark), not patterns; it is intentionally outside this registry's pattern list.
