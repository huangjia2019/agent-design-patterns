<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>C3
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>C3 · Adversarial Review · 对抗评审</h1>
<p class="publication-deck">由 Generator 提案、独立 Critic 审查、Judge 裁决，并通过模型、上下文或数据来源隔离形成结构独立性。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">协作 Collaboration × 循环 Loop（转）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">高（多个独立角色、评审轮次和审计 trace）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">协作模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">由 Generator 提案、独立 Critic 审查、Judge 裁决，并通过模型、上下文或数据来源隔离形成结构独立性。</td>
</tr>
</tbody>
</table>

---

## 问题

同一个 LLM 使用三段不同 prompt，不构成结构独立的审查。各角色仍共享模型训练数据、对齐偏差和先验。

对抗评审用于需要 audit-grade 独立审查的高风险决策。金融授信、医疗诊断、法律评估和监管合规中的独立性需要由模型、上下文、激励或数据来源实际体现。与单 Agent Generator-Critic 相比，它还需要 model routing、独立 trace 和跨 vendor 计费记录。

## 坐标说明：协作 × 循环

- **纵轴 · 协作**：两个或多个独立 Agent 使用不同角色和对抗激励。Critic 需要与 Generator 形成可验证的结构差异。
- **横轴 · 循环**：Proponent 提案、Critic 反对、Proponent 修正，直到 Judge 收敛或预算耗尽。

## 解决方案与机制

一次对抗评审由三个角色和一个循环组成：

1. **proponent 提议**：generator agent 产出初始方案。
2. **critic 反对**：独立 critic agent 专门找问题，prompt 明示"找问题不是确认，找不到 issue 反而要重审"。critic 找不到问题在高 stake 场景是可疑信号，不是通过信号。
3. **proponent 修正**：根据 critic 提出的 issue 修订方案，进入下一轮。
4. **judge 裁定**：judge agent 综合双方论证，给出最终裁决（approve / conditional / reject）。

各角色分别写入独立 trace，评审轮次按任务风险与成本预算设置硬上限。Critic 需要具备识别 Generator 细微错误的能力，Judge 需要明确的证据与裁决契约。跨 family routing 可以减少部分共同盲区，独立性还取决于 context、数据源、运行时和人工责任是否分离。

## 适用场景

- **有 audit-grade 独立性要求的合规场景**：金融授信、医疗诊断辅助、法律评估、监管合规，这些场景独立审查是上线门票。
- **错误代价很高的关键决策**：当错误损失、监管责任或安全风险足以覆盖独立评审成本时，可以采用对抗评审。
- **generator 输出与 critic 训练数据共享偏差的场景**：单模型自评在这些场景几乎无效，必须引入跨 family 的独立视角。
- **模型组合的工程取舍**：中档模型配合独立 critic 有时优于单次高能力模型调用，但必须在目标任务集上验证。

## 已知失效方式

- **模型共谋**：名义上跨 vendor，但 critic 和 generator 底层共享同一批 web 训练语料，"独立训练"是字面独立不是实质独立，两者在某些 corner case 上有共同盲区。vendor 独立不等于训练数据独立。关键场景要选不同 region、不同语言语料预训练的模型，或加第三家 critic，或接合规人审做最终防线。
- **成本级联**：每轮 context 都累积完整历史时，成本和延迟会快速上升。critic 每轮只读取任务、当前 draft 和必要证据，judge 在最终裁决时读取结构化 debate log。
- **谄媚崩塌**：critic 可能倾向认同 generator，名义上有对抗却没有实质分歧。应监控 `issues_per_turn`、phantom issue 和专家一致性，不能用“总能找出问题”替代有效评审。
- **角色 prompt 不够多样**：所有 agent 用同一个 role prompt 时，多 agent 反而比单 agent 更差。工程重点不是堆 agent 数量，是设计 role 多样性。
- **简单任务误用**：低风险写作润色或已有确定性验证的任务，通常不需要多 Agent 对抗；测试和规则往往是更直接的 critic。

## 验证指标

- **独立性证据**：记录模型、提示、数据源、运行时和组织角色的差异。不同 vendor 只是证据之一，不能自动证明认知独立。
- **critic 发现率 issues\_per\_turn**：结合 phantom issue 和专家抽查分析。长期没有有效 issue 可能是谄媚，持续制造 issue 也可能是标准失调。
- **辩论轮数**：观察收敛分布和触顶样本。反复无法收敛时，应调整 judge、证据契约或退出该模式。
- **单笔决策成本**（按业务核算）：跨 family 三 agent 的真实 token 成本，要监控每轮 spend，超阈值降级到 single-critic mode。

## 最小实现

```
AdversarialReview.review(task):
    校验 independence_policy               # 模型、数据源、角色或运行时独立性
    proposition = proponent(task)
    for round in 1..MAX_ROUNDS:
        verdict = critic(task, current)    # 用不同 vendor 的 model
        if requires_second_review(verdict): continue
        if not verdict.issues: break
        current = proponent(task, current, verdict.issues) # 修正
    return judge(task, debate_log)         # 综合双方,落 audit log

CritiqueVerdict:
    issues: list           # 显式优于隐式
    severity: minor/major/critical
    no_issues_found: bool  # 注意:这是 RED FLAG 不是 PASS
```

生产实现应记录 agent vendor、模型版本、数据源和运行时；Critic 首轮找不到问题时可触发复审；MAX\_ROUNDS 按任务风险与成本预算配置；compliance attestation 写入 audit log，留存期限按适用政策确定。

## 场景化示例

设想一个银行贷款决策辅助系统。第一版由同一模型分别扮演信贷分析、风险评估和合规审查，角色 prompt 不足以证明独立性。后续版本让 Generator、Critic 和 Judge 使用不同模型或独立证据源，各自保留 trace，并把最终裁决与人工审批写入 audit log。它能否满足审计要求，取决于银行和审计方认可的独立性证据，不能由“用了多个模型”直接推出。

## 相邻模式

- **Generator-Critic（反思模块）**：同源不同 scale。前者是单 agent 自我审视（同一模型加不同 prompt），后者是多 agent 独立审查（独立 agent 加对抗激励加结构独立）。错代价、监管要求、成本预算这三件事是从前者升级到后者的判断点。
- **扇出聚合（C2）**：扇出的 Worker 是互补关系，对抗评审中的 Critic 使用对抗激励。
- **并行探索（推理模块 R3）**：并行探索运行多个候选推理分支，但不要求对抗角色。
- **N-version programming（经典工程谱系）**：两者都使用独立实现、独立运行和聚合裁决。

## 工程判断

对抗评审通过独立角色、不同信息源和明确裁决规则组织分歧。独立性属于结构要求，需要在模型、上下文、激励或数据来源中实际体现。

<!-- ADPS-BLUEBOOK-SLOT -->

## 2026-08-25 研讨会修订：评审—执行反馈

评审结果要带上依据、风险、适用条件和复验要求。执行阶段发现的新约束进入证据链并返回后续评审，避免独立角色之间形成新的信息断层。

[协作模块研讨记录](https://adpsagent.com/zh/workshops/collaboration-2026-08-25/)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《C3 对抗评审》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-c3-adversarial-review">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
