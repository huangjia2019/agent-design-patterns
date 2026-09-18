<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>F1
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>F1 · Generator-Critic · 生成评审</h1>
<p class="publication-deck">Generator 生成结果，Critic 按证据和 rubric 评审；范围、轮次与成本均受约束，达到发布条件或迭代上限后退出。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">反思 Reflection × 链式 Chain（传）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（包含生成、评审和可能的修订调用）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">反思模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">Generator 生成结果，Critic 按证据和 rubric 评审；范围、轮次与成本均受约束，达到发布条件或迭代上限后退出。</td>
</tr>
</tbody>
</table>

---

## 问题

主观判断密集的任务没有唯一标准答案，写作、设计、代码风格、产品文案和学术摘要都属于这一类。初稿中的问题常常要到复读时才会显现，人类作者也会在收益不再值得继续投入时停止修订。单次生成缺少这一步有意识的回看。

Generator-Critic 把这个流程编码进 Agent：generator 写初稿，critic 按明确标准评审，generator 根据反馈修订，直到通过验收或触及迭代上限。Reflexion、Self-Refine 等研究展示了这条路线的可行性，但实际增益取决于任务、模型、评审标准和停止条件，需要在目标场景上复测。

## 坐标说明：反思 × 链式

- **纵轴 · 反思**：Critic 对当前输出进行评估，可以与 Generator 使用同一模型，也可以接入外部信号。
- **横轴 · 链式**：generate → critique → revise 构成三步线性管道，每一步使用独立 prompt，前一步输出作为后一步输入。F1 从可用输出开始做质量改进；F4 从确定性失败开始执行强制修复循环。

## 解决方案与机制

一个 Generator-Critic 闭环由三段组成：

1. **生成**：generator 产出初稿。这一步用什么模型决定了 critic 要补多少。
2. **评审**：critic 评估当前输出，产出结构化判决（issues 列表 / severity / 一个显式的 no\_changes\_needed 字段）。Reflexion 论文的关键创新是 critic 产出自然语言 reflection 文本而非单纯打分，告诉 generator 哪里错、为什么错、下次怎么改。
3. **改进**：generator 拿着 critique 重写。然后回到第 2 步，直到 critic 通过或迭代触底。

评审结论要说明依据，不能只给一个总分。常见证据源如下，它们各有边界，不能简单排成一条“越来越可靠”的直线：

<table>
<thead>
<tr>
<th style="text-align: left;">证据源</th>
<th style="text-align: left;">长处</th>
<th style="text-align: left;">局限</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">测试、schema、静态检查</td>
<td style="text-align: left;">判据清楚，可重复执行</td>
<td style="text-align: left;">只能覆盖已经编码的规则</td>
</tr>
<tr>
<td style="text-align: left;">规则与专家 rubric</td>
<td style="text-align: left;">能表达业务标准和多维质量</td>
<td style="text-align: left;">标准可能冲突，也会随业务变化</td>
</tr>
<tr>
<td style="text-align: left;">Self-Critic（同模型）</td>
<td style="text-align: left;">成本低，适合快速初筛</td>
<td style="text-align: left;">容易继承 Generator 的盲区</td>
</tr>
<tr>
<td style="text-align: left;">Cross-Model（不同模型）</td>
<td style="text-align: left;">能补充另一种判断路径</td>
<td style="text-align: left;">不等于独立事实，两个模型也可能共同出错</td>
</tr>
<tr>
<td style="text-align: left;">人工判断与业务结果</td>
<td style="text-align: left;">能处理责任、语境和延迟结果</td>
<td style="text-align: left;">成本高，反馈往往来得较晚</td>
</tr>
</tbody>
</table>

生产系统还需要一份 **Reflection Contract**。它至少写清 `subject`、`evidence_refs`、`rubric_version`、`verdict`、`proposed_change`、`scope`、`max_rounds`、`cost_budget` 和 `release_action`。这样一条评审记录才能被复核，也能交给离线流程继续分析。

## 两套反馈时钟

F1 可以出现在任务内，也可以出现在任务完成之后。

- **在线评审**服务当前任务：检查本轮产物，允许有限次修订，目标是让当前结果达到发布条件。它要控制延迟、调用成本和改动范围。
- **离线评审**服务后续任务：汇总生产 trace、人工改稿和业务结果，修订 rubric、grader、prompt 或评测集。它不应在缺少发布门禁时直接改写生产规则。

两者共享同一套证据结构。在线环节留下的判决、轨迹和人工接管原因，进入离线评测集；离线流程验证过的新标准，再按版本发布回在线系统。

## 适用场景

- **内容生成类任务**：写作、翻译、摘要、文案、学术摘要润色——没有客观对错但有明显质量差异，critic 能稳定看出"哪里不够好"。
- **代码风格与可读性优化**：命名、注释、结构调整这类不影响正确性但影响质量的改进。
- **低成本模型承担高频生成**：由低成本模型生成，Critic 负责检查输出是否达到质量阈值。

## 已知失效方式

- **有确定性判据时仍使用 LLM Critic**：数学、SQL 和单元测试等任务应优先使用测试或 schema，减少主观评估。
- **critic 未经独立评测**：critic 漏掉关键缺陷或引入噪声意见时，改写反而会退化。应独立评测 critic 的问题召回、误报和改写结果，不能只按模型档位判断它是否合格。
- **critic 强行找问题**：critic prompt 没说明 `no_changes_needed` 是合法结果时，它可能为了完成任务而虚构缺陷。应给出明确的通过条件，并用已经合格的样本测试 phantom issue。
- **同源偏差不设防**：critic 和 generator 是同一个 LLM 时存在 self-enhancement bias，它倾向给自己的输出打高分。高 stake 任务要换 vendor 或加 external grounding。
- **多维 rubric 被压成一个总分**：事实准确、合规、可读性和成本之间可能互相冲突。总分会把关键维度的退化藏起来，应保留逐项判决和阻断项。
- **只评最终答案**：最终答案看似合格，轨迹中却可能出现多余工具调用、错误检索或侥幸命中。高风险任务要同时评结果与 trajectory。
- **迭代不熔断**：不设 max\_iterations 会触发 over-thinking——critic 把上一轮的虚构当依据继续虚构，几轮后 agent 说服自己输出严重有问题。

## 验证指标

- **critic 收敛情况**：记录通过、触顶和人工接管的分布。反复触顶时检查评审标准是否冲突，或 generator 是否具备修正能力。
- **phantom issue 率**：在已由专家确认合格的样本上，统计 critic 虚构问题的情况。
- **critic-vs-expert 一致率**：持续抽样对比专家判断，并按错误类型修订 rubric、prompt 或模型。
- **质量增量**：在同一评测集上比较单次生成与评审循环，同时报告 token、延迟和人工返工。
- **轨迹效率**：记录完成同一验收目标所需的工具调用、失败分支和修订轮次，避免结果变好而执行路径持续膨胀。
- **关键维度回归率**：逐项观察阻断维度，不用平均分掩盖事实性、合规或安全回退。

## 最小实现

```
output = generator(task)
for i in range(MAX_ITERATIONS):       # 按任务风险和评测证据配置
    if external_critic:               # 有 deterministic 信号优先
        critique = external_critic(task, output)
    elif multi_critic:                # 多角色并行 + 仲裁
        critique = merge(critic(task, output, role=r) for r in roles)
    else:
        critique = critic(task, output)
    if critique.no_changes_needed:    # 合法出口, 防 phantom issue
        return output, "converged"
    output = generator(task, previous=output, feedback=critique)
return output, "max_iterations_reached"   # 触底转 HITL
```

生产实现应在 Critic prompt 中允许 `no_changes_needed`；存在 test、schema 或引用库等确定性信号时优先使用 external critic；`max_iterations` 按任务风险和本地评测配置；完整 history、rubric 版本和证据引用留作 Critic 校准数据。在线流程只应用当前任务范围内的修订，grader 与 rubric 的长期变更进入离线评测和发布流程。

## 场景化示例

设想一个论文摘要润色 Agent。第一版让 critic 必须给出若干修改点，结果它会对已合格摘要虚构问题，并把文字改得冗长。后续版本允许输出 `no_changes_needed`，并把学术严谨性、简洁性和术语准确性拆成独立 rubric；术语评审可查询引用数据库；团队持续抽样与专家判断对照。是否值得增加评审循环，应由这组对照样本中的质量增量和额外成本共同决定。

## 相邻模式

- **Self-Heal Loop（F4）**：Generator-Critic 从可用输出开始做质量改进，replay 可选；Self-Heal Loop 从确定性失败开始执行强制循环。
- **Adversarial Review（协作模块）**：升级形态。Generator-Critic 解决当前输出如何修订；Adversarial Review 解决高风险决策如何接受结构独立的审查，需要 model routing、独立 trace 和跨 Agent 编排。是否升级取决于错误代价、独立性要求和成本预算。
- **Skill Package（F2）**：衔接关系。Generator-Critic 改的是当下这次输出，Skill Package 沉淀的是跨任务的成功流程。

## 工程判断

Generator-Critic 将生成与评估拆成独立步骤。Critic 需要明确评价标准，并优先绑定测试、规则、知识源或独立模型等外部依据。

## 延伸阅读

- [反思模块总纲：从运行反馈到受控修改](https://adpsagent.com/zh/patterns/reflection/)
- [反思模块第一次研讨会（2026-08-12）](https://adpsagent.com/zh/workshops/reflection-2026-08-12/)
- [LangSmith Evaluation：离线评测与生产 trace 在线评测](https://docs.langchain.com/langsmith/evaluation)
- [LangChain AgentEvals：结果与 trajectory 评测](https://docs.langchain.com/oss/python/langchain/test/evals)

<!-- ADPS-BLUEBOOK-SLOT -->

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《F1 生成评审》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-f1-generator-critic">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
