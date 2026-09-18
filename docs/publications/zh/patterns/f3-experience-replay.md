<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>F3
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>F3 · Experience Replay · 经验回放</h1>
<p class="publication-deck">从历史 trajectory、人工接管和延迟业务结果中提取经验；新任务开始时检索适用部分，并保留采用与结果证据。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">反思 Reflection × 层级 Hierarchy（分）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">高（存储 + 检索 + 注入的持续投入，回报随时间累积）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">反思模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">从历史 trajectory、人工接管和延迟业务结果中提取经验；新任务开始时检索适用部分，并保留采用与结果证据。</td>
</tr>
</tbody>
</table>

---

## 问题

企业运行多年后，历史工作记录分散在 Slack、Jira、内部 wiki 和邮件中。部分记录包含失败路径、关键变量的发现过程和可复用产物，难以压缩为单一 skill，但可以为后续相似任务提供参考。

Experience Replay 让历史 trajectory 不再只是沉默资产。新任务到来时，系统检索相似的成功、失败或未完成轨迹，把可能有用的部分注入当前 context。它与 Skill Package 的区别在颗粒度：Skill Package 保存经过验证的可调用单位，Experience Replay 保存更宽泛的参考材料。CER 等研究说明这条路线可以在不训练模型的情况下发挥作用，实际收益仍需在目标任务上复现。

## 坐标说明：反思 × 层级

- **纵轴 · 反思**：该模式回看历史任务并提取当前可用的信息，不直接修改本轮输出，也不要求先固化为 skill。
- **横轴 · 层级**：经验按原始 trajectory、lesson、可复用 artifact 和技能候选分层存放，上层经验为当前行动提供约束。

## 解决方案与机制

Experience Replay 包含 Task → Retrieve → Adapt → Execute → Distill → Store 六个阶段。生产实现需要处理以下两项：

1. **multi-level 分层存储**：经验必须分层存，单层要么太散要么太空。AgentRR 给的是双层——low-level（具体 action：调了什么 tool、参数填什么、得到什么 observation，用于 debug）加 high-level（泛化策略：用了什么 approach、应对什么类型问题、什么时候 work，更接近工程师的判断）。Manning 往上延伸成三层抽象阶梯：

<table>
<thead>
<tr>
<th style="text-align: left;">层级</th>
<th style="text-align: left;">内容</th>
<th style="text-align: left;">工程角色</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">L0 Raw traces</td>
<td style="text-align: left;">完整执行 trace</td>
<td style="text-align: left;">ground truth，debug + audit</td>
</tr>
<tr>
<td style="text-align: left;">L1 Per-task reflections</td>
<td style="text-align: left;">单次任务后写的反思文本</td>
<td style="text-align: left;">Reflexion 范式，注入下一轮 prompt</td>
</tr>
<tr>
<td style="text-align: left;">L2 Cross-task heuristics</td>
<td style="text-align: left;">跨任务提炼的通用规律</td>
<td style="text-align: left;">ExpeL 范式，多次 L1 后蒸馏</td>
</tr>
</tbody>
</table>

<ol start="2">
<li><strong>training-free 注入</strong>：重训 LLM 太贵，CER 的做法是把过去 trajectory（裁剪加摘要后）作为 context 注入当前 prompt，让 LLM 在 context window 里 in-context learning，跳过训练阶段。检索时优先 effectiveness 高加 outcome 成功的经验，复用后回写 effectiveness——没用的 lesson 自动 deprecate。</li>
</ol>

研讨会补出了第三项生产要求：**经验的形成和经验的使用要分开**。任务运行时只检索已经发布的经验，避免一条未经验证的局部补丁立刻影响后续任务；离线流程批量分析 trace、人工接管和业务结果，合并重复补丁，补上适用范围，再将通过回放的经验发布到可检索层。

这也解释了反馈延迟的影响。代码任务通常很快得到测试结果，客服建议、运营策略或风险判断可能几天后才知道效果。Experience Replay 要保留 `trajectory_id`、执行版本、当时证据和后到的 outcome label，等结果回来后再更新经验。没有这条关联，系统很容易把“当时看起来合理”误写成“已经验证成功”。

## 在线使用与离线整理

- **在线阶段**：按任务类型、环境版本和风险标签检索经验，做适用性检查，记录哪些经验被采用以及它影响了哪一步。
- **离线阶段**：从一批 trajectory 中找重复失败、局部补丁和稳定做法，结合延迟结果做归因；经过回放和评审后，决定合并、降权、归档或提升为 Skill Package。

在线阶段追求低延迟和可回退，离线阶段追求覆盖、比较和长期一致性。两者混在一起时，每次执行都可能给经验库追加一条临时规则，局部修补越积越多，检索和执行反而越来越慢。

## 适用场景

- **长期运行且任务重复的 Agent**：客服、运维和数据分析等场景会持续积累可复用 experience，收益取决于经验库的覆盖度和质量。
- **组织知识沉淀**：把公司散落在 wiki、文档系统和历史报告中的经验接入当前工作流，通常可先复用现有知识基础设施。
- **失败 trajectory 复用**：失败轨迹也可能包含有效的工具路径、局部产物和边界信息。hindsight relabel 可以把“未完成原目标”重新解释为“完成了某个子目标”，但必须保留原始目标和重标注来源。

## 已知失效方式

- **冷启动缺少可检索经验**：新库证据不足时，可从经过评审的历史记录和最佳实践中建立 bootstrap 数据，并保留来源和适用版本。
- **陈旧教训漂移**：产品改版后，旧经验可能已经不适用。应绑定系统版本、降低陈旧条目权重，并按明确周期 review 或 deprecate。
- **检索偏差放大**：embedding 相似不等于任务结构相似。"用户增长分析"检索出"用户流失分析"经验，把流失的 funnel 框架硬套到增长上——增长和流失是反向问题。防法是加 task type classifier 粗筛、block 跨类型检索、检索后 LLM 二次审查适用性。
- **无结构全量 dump**：把所有 trajectory 全塞进 vector DB 让 agent 自己挑，没有 multi-level 分层。
- **延迟结果归错任务**：业务结果晚于执行到达，若没有稳定的 `trajectory_id`、版本和时间窗，系统会把后续变化错误归因给某条经验。
- **局部补丁持续堆积**：每次线上失败都追加一条特殊规则，短期见效，长期会增加检索噪声、冲突和延迟。离线流程要定期合并、提升或删除这些补丁。

## 验证指标

- **检索命中率**：召回经验被当前任务采用的比例。偏低时检查 task\_signature、索引和经验粒度。
- **effectiveness 分**：比较经验被采用后的任务结果，并结合多次回放判断。持续无效或产生负迁移的 lesson 应进入 archive。
- **experience store 覆盖和 retrieval count**：冷启动期先看代表性任务是否被记录、检索是否覆盖正确任务族，再观察下游质量变化。
- **质量增量**：与不注入历史经验的回放基线比较，是判断 Experience Replay 是否产生净收益的 lagging indicator。
- **trajectory 与 outcome 对齐率**：有多少延迟业务结果能够回连到当时的任务、版本和证据。
- **负迁移与补丁债务**：统计经验注入后表现下降的任务，以及长期未合并、未验证的局部补丁数量。

## 最小实现

```
# 检索 + 注入 (CER training-free)
past = retrieve(task)                      # top-K, 优先 effectiveness 高 + success
context += render_for_context(past)        # high-level strategy + author metadata
heuristics = get_L2_by_signature(task)     # 跨任务规律
context += render(heuristics)

result = agent.run(task, prior_context=context, trajectory_collector=traj)
record_adoption(task.id, past, result.trajectory)  # 哪条经验影响了哪一步

# 记录事实，暂不直接发布成经验
record_trace(task, traj, immediate_outcome, author_id, runtime_version)
attach_delayed_outcome(task.id, delayed_outcome)  # 结果回来后补写

# 回写 effectiveness (lesson accuracy 反馈环)
for e in past:
    update_effectiveness(e, current_task_succeeded=result.ok)

# 离线合并局部补丁，达到证据门槛并通过回放后再发布 L2
candidate = consolidate_patches(signature, traces, outcomes)
publish_L2(candidate, when=replay_passed and review_approved)
```

生产实现根据检索质量和成本选择 embedding 与摘要模型；保留结果证据而不是只存一个缺少口径的分数；保留 `author_id`、`trajectory_id`、运行版本和来源元数据；`task_signature` 使用语义特征而非不透明 hash。在线检索只读取已发布经验，候选 lesson 和局部补丁留在离线整理区。

## 场景化示例

设想一个数据团队分析“新功能上线后留存未明显提高”的原因。不同分析者重复执行 cohort 分析，却都忽略了同期自然流量变化这一 confounding variable；历史上有一份相似报告，但作者离开后没有进入当前工作流。引入 Experience Replay 后，系统召回该报告及“留存分析需检查时段效应”的 heuristic，同时保留 high-level approach、low-level SQL、作者、数据源和时间范围。成功、失败和中性轨迹分开标记，分析师仍需判断旧经验是否适用于当前产品。重复投入的变化应从项目记录中核验。

## 相邻模式

- **Skill Package（F2）**：Skill Package 保存 verified 可调用单位，Experience Replay 保存范围更宽的参考资产。Agent 可优先匹配 skill，未命中时检索 experience；反复验证成功的 experience 可转为 skill。
- **Failure Journals（记忆模块）**：同源输入。Failure Journals 提供失败 trajectory 库，Experience Replay 提供检索加注入机制，两者配合。AgentHER 之后失败 trajectory 还成了高价值训练原料。
- **Generator-Critic（F1）**：层级递进。Generator-Critic 改单次输出，Experience Replay 让累积经验跨任务复用。

## 工程判断

Experience Replay 把历史轨迹、经验摘要和可复用产物组织成可检索资产。其收益需要通过后续任务的命中率、成功率和人工接管变化来验证。

## 延伸阅读

- [反思模块总纲：从运行反馈到受控修改](https://adpsagent.com/zh/patterns/reflection/)
- [反思模块第一次研讨会（2026-08-12）](https://adpsagent.com/zh/workshops/reflection-2026-08-12/)
- [LangSmith Evaluation：把生产 trace 加入离线评测数据集](https://docs.langchain.com/langsmith/evaluation)

<!-- ADPS-BLUEBOOK-SLOT -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《F3 经验回放》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-f3-experience-replay">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
