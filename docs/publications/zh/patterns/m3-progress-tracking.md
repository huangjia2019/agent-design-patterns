<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>M3
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>M3 · Progress Tracking · 进度追踪</h1>
<p class="publication-deck">在长任务中持续维护目标契约、结构化进度、权威状态引用和 checkpoint，使任务可恢复、可验收且不重复副作用。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">记忆 Memory × 编排 Orchestrate（协）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">低（状态字段读写开销小）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">记忆模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">在长任务中持续维护目标契约、结构化进度、权威状态引用和 checkpoint，使任务可恢复、可验收且不重复副作用。</td>
</tr>
</tbody>
</table>

---

## 问题

LLM 依赖 context window 保持当前任务信息，而长上下文中的中间内容容易获得较低注意力。长时间调试会把原计划挤出有效工作集。例如，Agent 完成部分文件后陷入局部缺陷，随后直接进入测试阶段，遗漏计划中尚未创建的文件。

进度追踪把目标、里程碑、阻塞项和下一步写入外部存储，并在关键决策前重新加载。业务状态仍由数据库、状态机和账本维护；进度记录保存引用和任务叙事，不能凭一段旧摘要决定当前哪个版本有效。

## 坐标说明：记忆 × 编排

- **纵轴 · 记忆**：它给 agent 一份"工作日志",跨 step 保留任务上下文，是记忆最简形式（session memory）——记着"我刚做了什么、现在在做什么、接下来做什么"。
- **横轴 · 编排**：进度追踪跨越所有任务步骤，维护统一 todo 状态，用于步骤选择、中断恢复和遗漏检测，因此属于编排层。

## 解决方案与机制

1. **目标契约 Goal Contract**：在任务台账顶部保存 objective、acceptance、forbidden actions 和 exit conditions。后续压缩可以缩短叙事，不能丢掉验收与禁止动作。
2. **计划与进度分离**：Plan 描述预期步骤，Progress 保存每一步的 `pending / in_progress / blocked / needs_review / completed / failed` 状态、负责人、依赖和下一步。单线程执行器同一分支只允许一个活动步骤；显式并行分支分别维护状态。
3. **只引用权威业务状态**：`state_refs` 指向数据库记录、审批对象、commit 或业务账本。恢复时重新读取这些对象，不能把 checkpoint 中的旧值当作当前真值。
4. **产物式 checkpoint**：里程碑完成后保存可验证 artifact、状态引用、动作回执和 resume cursor。不可逆动作使用 idempotency key 或业务回执证明已经执行。
5. **在风险点重新锚定目标**：工具调用达到阈值、发生失败、切换子任务、恢复会话或准备提交高风险动作时，运行时重新加载 Goal Contract、活动里程碑和禁止动作。
6. **冲突时停机**：历史进度与当前权威状态、验收条件或动作回执冲突时进入 `needs_review`。Agent 不静默选择一个看起来较新的自然语言版本。
7. **分层隔离与归档**：主 Agent 保存里程碑和验收，子 Agent 保存局部步骤并向上返回结构化汇总。任务结束后清空活动视图，完整记录转入审计和回放存储。

## 适用场景

- **多步长任务**：跨多轮且容易因局部调试遗漏原计划的任务，例如代码重构、多文件改造和复杂调试。
- **可恢复的长流程**：任务可能中途崩溃需要 resume 的场景。进度持久化后，第二次会话读 progress、跳过已完成、从中断步恢复，不重做。
- **多周持续推进的任务**：跨数周对同一目标推进的场景（如投资研究对一只股票的判断），需要双层 todo——高层研究计划跨周保持，会话内具体动作做完合并回高层。

## 已知失效方式

- **单次简单任务强行用**：纯对话、单次 Q&A 和可以直接完成的小任务通常不需要 todo。
- **允许多个 in\_progress**：单线程 Agent 同时保留多个进行中步骤会使当前动作不确定。需要并行时，应拆给多个 Agent 或显式建立并行分支。
- **Todo 显示完成，业务状态没有提交**：页面上的 `completed` 只是一条叙事状态。没有数据库版本、动作回执或验收产物，系统不能声称副作用已经发生。
- **用旧 checkpoint 覆盖新状态**：恢复时直接回放快照中的参数，可能重复付款、重复发布或撤销后续人工修改。所有 `state_refs` 都要在恢复时重新解析。
- **目标被压缩成一句“继续处理”**：原始验收、禁止动作和退出条件消失后，Agent 很容易把局部细节当成新目标。
- **把历史决策当成当前决策**：讨论记录和旧版本被召回后，Agent 退回已经废弃的基线。权威状态需要显式的 accepted、superseded 或 revoked 标记。
- **main agent 与 sub-agent 共享一个池**：main agent 查看高层清单时被子 agent 的细节 todos 淹没，注意力被无关粒度争夺。子 agent 应使用独立清单，并向上返回结构化进度。
- **没有框架层重锚和 nudge**：Agent 执行复杂任务却没有更新进度，或在关闭任务前没有验证，运行时仍继续放行。升级条件要与任务风险和执行权限对应。

## 验证指标

- **计划遗漏率**：长任务中原计划步骤被跳过的比例。它需要通过回放或任务审计计算，是判断进度追踪是否有效的首要指标。
- **目标与验收覆盖率**：每个活动步骤是否能回到 Goal Contract 中的一项目标或验收条件，任务关闭时是否逐项提供证据。
- **目标漂移事件**：活动步骤与原始 objective、forbidden actions 或当前里程碑失去关系的次数。
- **验证步骤覆盖率**：适用任务在关闭前是否包含验证动作。应按任务风险设定要求，并记录 nudge 是否真正改变了行为。
- **resume 成功率**：中断后能否从持久化进度恢复，且不重复已完成的不可逆动作。
- **重复副作用事件**：恢复、重试或并发情况下，同一业务动作因缺少幂等证明而执行多次的次数。
- **状态引用新鲜度**：恢复和高风险动作前，`state_refs` 是否重新解析到当前版本。
- **单 in\_progress 合规率**：单线程执行器任意时刻只能有一个活动步骤。违反这一不变量说明状态机或并发边界存在缺陷。

## 最小实现

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
    snapshot active view without replacing authoritative business state
```

进度事件采用 append-only 记录，活动视图可以重建。高风险动作前后写入统一 trace，checkpoint 只保存业务对象引用和回执，不复制一份可能过期的机械状态。

## 场景化示例

设想一个买方研究 Agent 持续更新某只股票的判断。Goal Contract 保存研究对象、交付物、证据日期要求和不得绕过投资经理审批的约束。每个会话只维护本轮可完成的具体步骤，完成后把报告、数据快照和评审结论写入 artifact refs。持仓和审批状态来自业务系统，进度账只保存指针。恢复会话时先刷新这些引用；研究结论与当前持仓或审批冲突时进入 `needs_review`，不会沿旧 checkpoint 自动继续。

## 相邻模式

- **分层保留（M1）**：Todo list 位于高频更新的会话层，并在每轮决策前加载当前活动项和必要的上层目标。
- **失败日记（M4）**：进度追踪保存任务步骤状态，失败日记保存失败现象、原因和处理结果。
- **Plan-and-Execute（推理模块）**：Plan 描述预期步骤，进度追踪维护这些步骤的运行时状态。
- **Hooks Pipeline（治理模块）**：框架层的 nudge 和持久化挂点天然契合 hook 机制，可用 PreToolUse / PostToolUse hook 实现。
- **可观测性（X1）**：ProgressState 解释 Agent 认为自己做到哪，统一 trace 和动作回执证明系统实际发生了什么。

## 工程判断

进度追踪把长任务的目标、过程和恢复位置外置。Goal Contract 防止方向漂移，权威状态引用防止旧摘要冒充真值，产物与回执防止恢复时重复副作用。

## 企业证据

以下现场记录说明该模式在具体业务约束下如何实现。案例结论只在文中声明的系统边界内成立。

<ul style="list-style: none; margin: 0.5rem 0 1rem 0; padding: 0;">
<li style="margin-bottom: 0.6rem; line-height: 1.55;"><a href="https://adpsagent.com/zh/patterns/m3-progress-tracking/cases/liangbo/" style="font-weight: 600;">东方屹腾 · 进度追踪</a><span style="color: var(--color-text-muted);"> — Anchor 固定目标，Ledger 追加关键进展，Collection 提供当前步骤的读取视图。</span></li>
</ul>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-memory-engineering" class="related-case-band">
<p class="related-case-label">模式工程实现</p>
<h2 id="related-memory-engineering"><a href="https://adpsagent.com/zh/patterns/engineering/memory-storage-on-kubernetes/">K8s 中的 Agent 记忆：存储分层与恢复验证</a></h2>
<p>把本模式放进多 Pod 服务，检查权威存储、版本冲突、检索索引和恢复路径。</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《M3 进度追踪》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">参考实现</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>文档状态：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；场景化示例用于说明机制，不代表已经核验的企业案例。具名实践另见<a href="https://adpsagent.com/zh/cases/">案例库</a>。ADPS 欢迎业界提交带来源、测量口径和发布授权的案例。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-m3-progress-tracking">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
