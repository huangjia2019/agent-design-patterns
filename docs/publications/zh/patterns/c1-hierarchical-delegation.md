<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>C1
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>C1 · Hierarchical Delegation · 层级委派</h1>
<p class="publication-deck">Supervisor 动态拆分任务，由 N 个独立 Worker 执行，再汇总结构化结果。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">协作 Collaboration × 层级 Hierarchy（分）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">高（多 Worker 调用，加上协调与综合）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">协作模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">Supervisor 动态拆分任务，由 N 个独立 Worker 执行，再汇总结构化结果。</td>
</tr>
</tbody>
</table>

---

## 问题

单个 Agent 同时承担资料检索、正文撰写、配图和报告生成时，长流程中的执行细节会持续占用 context。顺序处理多个子任务后，早期细节可能干扰后续判断。

层级委派由 Supervisor 负责拆分任务、监控进度和合并产出，Worker 在独立 context 中执行专业子任务。Supervisor 只接收结构化结果，不加载各 Worker 的完整轨迹。该模式会增加模型调用和 token 成本，应按任务价值评估。

## 坐标说明：协作 × 层级

- **纵轴 · 协作**：Supervisor 和 Worker 是职责不同的独立 Agent，例如 Researcher、Writer 和 Visualizer。
- **横轴 · 层级**：拓扑是一棵树。Orchestrator 在上，多个 worker 在下，worker 之间不直接通信，要交换信息必须经过 supervisor。这是天然的层级结构，区别于并行的扇出聚合、对抗的评审循环、顺序的交接链。

## 解决方案与机制

一次层级委派由三段组成：

1. **动态拆分**：supervisor 根据具体输入决定拆几个 worker、每个 worker 干什么。研究 AI 行业和研究咖啡行业拆出的子任务结构不一样，拆分必须跟输入相关，不能写死。
2. **隔离执行**：每个 worker 跑在独立 context 里，不继承 supervisor 的 history，只收到自己的 system prompt、具体的 task instruction、自己的 tool set。worker 之间能并行的尽量并行。
3. **中心化综合**：supervisor 只看 worker 返回的结构化 artifact，不看 worker 的 raw trajectory，基于这些精炼摘要做整体判断和最终合并。

Supervisor 和 worker 通常用不同的模型。Supervisor 做拆分和综合，需要深度推理，用强模型；worker 做专门化执行，用更便宜的模型。这和 Plan-and-Execute 把 planner 与 executor 分家是同一套思路，只是从单 agent 内部扩展到了多个 agent 之间。

worker 返回的 artifact 建议至少三层结构：

<table>
<thead>
<tr>
<th style="text-align: left;">字段</th>
<th style="text-align: left;">作用</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">verdict（success / partial / failure）</td>
<td style="text-align: left;">让 supervisor 一眼判断这份产出能不能直接用</td>
</tr>
<tr>
<td style="text-align: left;">ranked findings</td>
<td style="text-align: left;">按重要性排列的工作结论，并保留证据引用</td>
</tr>
<tr>
<td style="text-align: left;">confidence / uncertainty</td>
<td style="text-align: left;">使用经过校准的尺度表达把握程度，不能单独作为仲裁依据</td>
</tr>
</tbody>
</table>

## 适用场景

- **专业分工明确的长流程任务**：行业研究报告生成、投研分析、新药研发流程，每个环节需要不同专业能力。
- **批量同类任务的隔离处理**：合同审阅、简历筛查、文档合规扫描，每份独立交给一个 worker，避免相互污染和 context 爆炸。
- **价值足以覆盖协作开销的任务**：多 Agent 会增加分解、通信和聚合成本。是否值得采用，应在同一任务集上比较单 Agent 与多 Agent 的质量、时延和总 token。

## 已知失效方式

- **Worker 未隔离**：Supervisor 接收完整执行过程而非 schema artifact，context 会被子任务细节占满。Worker 应返回压缩后的结构化结果。
- **Worker 之间直接通信**：Worker A 直接调用 Worker B 会将树结构变为网状结构，增加 cascade failure 风险。信息交换应经过 Supervisor。
- **Worker 失败没有边界**：Worker 异常未被捕获时，Supervisor 会收到 raw exception 并中断任务。每个 Worker 需要 timeout、异常包裹和 failure artifact。
- **并行 worker 数量过多**：Worker 增多后，Supervisor 需要比较和综合更多 artifact。并发和 fan-out 上限应由 provider 容量、artifact 体量和综合质量共同决定。
- **Collaboration Light 场景误用**：同一个 Agent 仅切换多个 prompt 时，不需要层级委派。该模式要求多个具有专业分工的 Agent。

## 验证指标

- **协作开销占比**：Supervisor 与 Worker 通信消耗的 token 和时间占比。相对本地基线过高时，应压缩 artifact、减少往返或改用轻量 channel。
- **worker 失败级联率**：一个 Worker 失败是否拖垮其他分支或 Supervisor。高风险任务应优先验证隔离与部分失败处理。
- **artifact 合规率**：Worker 返回是否符合 schema。自由文本绕过 schema 会触发重派、人工修正和额外延迟。
- **多 Agent 成本倍数**：与单 Agent 基线比较总 token、模型费用和墙钟时间。成本超过任务价值时应退回单 Agent 或缩小委派范围。

## 最小实现

```
SupervisorAgent.execute(task):
    plan = decompose(task)              # 动态拆分,跟输入相关
    artifacts = 并行 gather(            # 并发上限作为配置
        IsolatedSubAgent(worker).execute(subtask)
        for worker, subtask in plan
    )
    return synthesize(task, artifacts)  # 只看 artifact,不看 raw trajectory

IsolatedSubAgent.execute(subtask):
    本地 messages = [system_prompt, subtask]   # 不继承 parent history
    try: raw = wait_for(llm(messages, tools), timeout)  # 失败 boundary
    except: return Artifact(verdict="failure", ...)
    return reduce_to_artifact(raw)      # 强制压缩成 verdict/findings/confidence
```

生产实现为每个 Worker 创建独立 context；强制返回 schema artifact；使用 timeout 和异常包裹隔离失败；通过信号量控制并发，Worker 之间不共享 state。

## 场景化示例

设想一个律所的合同审阅 Agent。第一版让每个 sub-agent 返回完整分析，主 Agent 很快被长文本淹没。第二版为每份合同分配独立 Worker，并强制返回固定 schema：`contract_id`、`risk_level`、`top_concerns`、`recommendation` 和防篡改的 `contract_hash`。高风险合同进入律师评审队列；Worker 超时或失败时返回 failure artifact；portfolio report 写入文件供审计。实际吞吐与质量需要在律所授权的合同集上评测。

## 相邻模式

- **子代理隔离（C5）**：层级委派负责派工，子代理隔离负责 Worker context、schema artifact 和失败边界，两者通常配套使用。
- **扇出聚合（C2）**：同为一对多，但分工逻辑不同。层级委派是一对多分专业（每个 worker 干不同的事），扇出聚合是一对多分量（多个 worker 同时干同一类活的不同部分）。
- **交接链（C4）**：层级委派由 Supervisor 持有全局状态；交接链在职责对等的 Agent 之间顺序传递状态。
- **Plan-and-Execute（行动模块）**：层级委派是它在多 agent 层的扩展，把"一个 agent 内 plan-execute 分家"扩展成"多个 agent 分家"。

## 工程判断

层级委派同时划分任务和信息范围。Supervisor 接收下一层的结构化结果，不继承所有 Worker 的原始轨迹，以控制上下文规模和责任边界。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

## 2026-08-25 研讨会修订：任务级身份与生产冻结

委派应同时缩小任务、上下文与权限。Worker 使用任务级身份或短时凭证，不能继承发起人的全部权限。测试、预发布和生产逐步固定 Supervisor、Worker、模型、工具与策略版本。

[协作模块研讨记录](https://adpsagent.com/zh/workshops/collaboration-2026-08-25/)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《C1 层级委派》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-c1-hierarchical-delegation">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
