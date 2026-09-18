<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>C5
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>C5 · Sub-Agent Isolation · 子代理隔离</h1>
<p class="publication-deck">子 Agent 在独立 context 中执行，并将结果压缩为 schema artifact 返回主 Agent。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">协作 Collaboration × 层级 Hierarchy（分）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">横切（跨切关注点，叠加在其他协作模式上）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">协作模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">子 Agent 在独立 context 中执行，并将结果压缩为 schema artifact 返回主 Agent。</td>
</tr>
</tbody>
</table>

---

## 问题

如果 sub-agent 将完整工作过程返回主 Agent，批量任务会随条目数量迅速占满主 context。主 Agent 通常只需要 verdict、关键发现、证据和不确定性，而不是每条中间轨迹。

子代理隔离用于控制 multi-agent 系统中的 context pollution。每个 sub-agent 在独立 context 中运行，返回前压缩为结构化 artifact，主 Agent 只消费该 artifact。层级委派和扇出聚合通常依赖这项边界控制。

## 坐标说明：协作 × 层级

- **纵轴 · 协作**：sub-agent 使用独立 context 和权限，主 Agent 与 sub-agent 之间只传递约定结果。
- **横轴 · 层级**：parent agent 调度 sub-agent，sub-agent 在自己的沙箱里跑，是层级加隔离的结构。它跟层级委派共格（都在协作 × 层级交点），但侧重不同——层级委派强调派工，子代理隔离强调隔离加摘要返回。

## 解决方案与机制

子代理隔离包含四项工程要素：

1. **Context 隔离**：sub-agent 启动时不继承 parent 的 history，只收到自己的 system prompt、具体的 task instruction、自己的 tool set。它看不到主 agent 跑过什么、其他 sub-agent 在做什么。
2. **Artifact schema 化返回**：sub-agent 返回结构化 artifact（Pydantic model 或 JSON Schema），字段可包括 verdict（success / partial / failure）、按重要性排列的 findings、citations 和 unresolved questions。主 Agent 可以用确定性代码校验，不必从自由文本中猜测状态。
3. **失败 boundary 隔离**：sub-agent timeout 或抛异常时，主 Agent 收到 `verdict=failure` 的 artifact，而不是未捕获异常。局部失败仍绑定在自己的 branch。
4. **并行互不干扰**：N 个 sub-agent 各跑各的 context，互相看不到中间状态，也不直接通信——要交换信息必须经过主 agent。

## 适用场景

- **子任务产出多、主 agent context 紧的批量任务**：合同审阅、文档扫描、大规模代码检索，每个 sub-agent 处理一份、只回传精炼结论。
- **需要防止任务间相互污染的场景**：每份合同应该被独立 fresh review，不被其他合同的细节 prime（避免 anchoring bias），独立 context 是必需的。
- **数据 scope 不能跨的场景**：一个 sub-agent 看到的敏感数据不能流到另一个 sub-agent 或污染主 agent，隔离 context 提供了天然的数据边界。
- **需要防 prompt 污染的场景**：sub-agent 的试错失败 trace、越界尝试不应该拖累主 agent 或其他 sub-agent 的后续推理。

## 已知失效方式

- **sub-agent 继承主 Agent history**：随着主 Agent 的历史增长，每个新 sub-agent 都会携带与当前任务无关的内容，增加成本和上下文干扰。sub-agent 应从本地 messages 起跑，只接收任务契约中约定的上下文。
- **返回自由文本而非 schema artifact**：自由文本难以用确定性代码 parse，也无法稳定执行 confidence 排序和 verdict 分流。应强制 schema 并拒绝不合规返回。
- **sub-agent 之间直接通信**：为了省事让 sub-agent A 调 sub-agent B，会立刻把层级拓扑变成网状拓扑，cascade failure 风险飙升。要交换信息必须经过主 agent。
- **失败没有 boundary**：sub-agent 抛异常没被捕获，主 agent 收到 raw exception 导致 reasoning loop 被中断、整个任务失败。失败时要返回 schema 化的 failure artifact。
- **简单子任务也套隔离**：当输出很小或主 Agent 确实需要中间细节时，隔离可能增加不必要的开销。应在真实 context 预算下与直接执行比较。

## 验证指标

- **主 Agent context 占用**：所有 sub-agent artifact 占主 context 的比例。应为主 Agent 的聚合、冲突判断和最终推理预留空间。
- **artifact 合规率**：sub-agent 返回是否符合 schema。自由文本绕过 schema 会触发重派、人工修正和延迟。
- **失败级联率**：一个 sub-agent 失败是否拖垮其他分支。通过进程、context、工具权限和错误边界分别验证隔离效果。
- **artifact 压缩比**：raw trajectory 与 reduce 后 artifact 的体量关系，还要配合关键信息保留率一起看。

## 最小实现

```
IsolatedSubAgent.execute(task):
    local_context = [system_prompt, task]      # 不传入 parent history → Context 隔离
    try:
        raw = run_loop(task, local_context)     # 独立 LLM call + 独立 tool set
    except: return Artifact(verdict="failure")  # 失败 boundary
    return reduce_to_artifact(raw)              # 强制压成 verdict/findings/citations

SupervisorWithSubAgents.execute(task):
    artifacts = 并行 gather(                     # N 个并行,各自独立 context → 互不干扰
        sub.execute(dispatch_subtask(task, sub)) for sub in sub_agents
    )
    return synthesize_from_artifacts(artifacts) # 主 agent 只看 artifact 不看 raw trajectory
```

生产实现使用本地 messages 隔离 context；通过 reduce\_to\_artifact 返回 schema；使用 try/except 和 timeout 建立失败边界；并行 gather 中保持各分支 context 独立。

## 场景化示例

设想一个律所的合同审阅 Agent。第一版让 sub-agent 返回每份合同的完整分析，主 context 被 trajectory 淹没。第二版为每份合同创建独立 sub-agent，强制返回 `verdict`、`top_concerns`、`recommendation` 和证据指针；单个分支失败不影响其他合同；低 confidence artifact 转人工。Claude Code Task tool 可作为产品实现参考：每个任务使用独立 context、独立 LLM call 和独立 tool set，只向主 Agent 返回最终 artifact。实际吞吐、漏评率和压缩损失需要用授权合同集验证。

## 相邻模式

- **层级委派（C1）**：层级委派负责 Supervisor 与 Worker 的派工关系，子代理隔离负责 Worker context、schema artifact 和失败边界。
- **扇出聚合（C2）**：扇出的每个并行 branch 都依赖隔离——独立 context，gather 阶段只看 reduced 结果。隔离是扇出能跑通大规模并行的工程基础。
- **Hierarchical Retention（记忆模块）**：同源思想。信息按层级分发、越上层越精简，子代理隔离是这个作用域分层原则在多 agent 协作层的落地。
- **上下文分诊（感知模块）**：同源思路。主 agent 不预加载子 agent 的中间状态，需要时按需取（通常不需要，artifact 就够），类似延迟加载。

## 工程判断

子代理隔离限制每个 Worker 的上下文、工具、凭证、预算和工作区。主 Agent 只接收可验证 artifact，局部失败因此不会直接污染主任务。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

## 2026-08-25 研讨会修订：跨 Session 隔离

隔离范围扩展到 worktree、需求编号、共享配置、测试数据库、部署环境和外部配额。调度器在并行前检查写入冲突域，并记录锁、租约、冲突策略与释放条件。

[协作模块研讨记录](https://adpsagent.com/zh/workshops/collaboration-2026-08-25/)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-handoff-engineering" class="related-case-band">
<p class="related-case-label">模式工程实现</p>
<h2 id="related-handoff-engineering"><a href="https://adpsagent.com/zh/patterns/engineering/cross-agent-handoff/">两个 Agent 怎样接上：从上下文引用到任务交接</a></h2>
<p>把本模式放进一次前端发现、后端修复和前端复测，检查责任转移、权限边界与验收证据。</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《C5 子代理隔离》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-c5-sub-agent-isolation">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
