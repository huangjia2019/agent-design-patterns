<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>R5
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>R5 · Talker-Reasoner · 双模架构</h1>
<p class="publication-deck">将实时交互与深度推理拆分给 Talker 和 Reasoner，并通过共享 belief state 协同。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">推理 Reasoning × 层级 Hierarchy（分）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（Talker 用便宜模型扛大部分对话，Reasoner 才用贵模型）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">推理模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">将实时交互与深度推理拆分给 Talker 和 Reasoner，并通过共享 belief state 协同。</td>
</tr>
</tbody>
</table>

---

## 问题

异步任务可以等待深度推理，实时交互则受首响应和静默时间约束。把完整分析放在同步路径上，往往会让用户等待；只追求即时响应，又可能牺牲判断质量。

Talker-Reasoner 将两类目标拆分给不同 Agent。Talker 负责快速回应和继续收集信息，Reasoner 在后台执行深度分析，两者通过共享 belief state 交换结果。具体延迟目标由渠道和用户研究确定。

## 坐标说明：推理 × 分层

- **纵轴 · 推理**：它把"实时响应"和"深度推理"两种 reasoning modality 分开，是一个双系统的推理架构——对应 Kahneman 的 System 1（快、自动、低耗）和 System 2（慢、刻意、高耗）。这是认知科学在 Agent 上的工程映射，不是单一推理通道。
- **横轴 · 分层**：Talker 在前（快、浅）、Reasoner 在后（慢、深），是分层分工而不是 parallel 竞争。两者职责不同、模型不同、时机不同，Reasoner 的输出通过 belief 影响 Talker 的回答，是上下层协作关系。

## 解决方案与机制

一次双模协同由三段组成：

1. **Talker 快速响应**：使用低延迟模型保持对话、回应情绪并提出澄清问题。它的权限契约限制其在深度分析完成前给出高风险结论。
2. **Reasoner 异步分析**：在后台执行深度分析，完成后把结构化结论写入共享 belief state，不阻塞当前对话。
3. **belief state 协同**：两个 Agent 通过共享 state 通信，写操作加锁以避免 race condition。Reasoner 完成后，Talker 在下一轮将分析结果加入回答。

用户输入在 Reasoner 还在跑时怎么处理，有三种做法可选：QUEUE（排队等 Reasoner 跑完，适合任务场景）、INTERRUPT（立即打断重跑，适合短任务 explore）、PARALLEL（两个 Agent 真并行，Talker 即时回 Reasoner 后台跑，对话场景必须用这个）。把三种做成 config 让产品按场景选。

## 适用场景

- **实时对话**：教育辅导、客服和个人助手需要控制首响应时间，同时保留深度个性化分析。
- **Voice agent**：电话和语音助手需要控制静默时间，并在后台持续分析。
- **需要边聊边收集信息的咨询场景**：Talker 跟用户聊倾向、问 follow-up 的同时，Reasoner 在后台基于已有信息做匹配分析,聊完分析也好了。

## 已知失效方式

- **Talker 越权给出结论**：如果 prompt 未限制 Talker 的建议权限，它可能在 Reasoner 完成前给出冲突结论。Talker 应只负责首响应、澄清和状态通知。
- **Reasoner 没有 timeout 和 cancel**：后台任务可能失控，或在用户换话题后继续分析旧问题。timeout 由渠道预算配置，话题切换时主动 cancel。
- **belief state 不跨 session 持久化**：用户下次回来 Talker 又从零开始，上次 Reasoner 的分析全丢了。要持久化到 Redis / PostgreSQL。
- **结果接入缺少上下文**：Reasoner 完成后直接插入分析，会中断对话连续性。Talker 应结合当前轮次和已收集信息接入结果。
- **异步任务场景硬上双模**：用户提交任务就离开的场景（写文档、批处理），不需要 Talker，直接让 Reasoner 慢慢跑就行，加 Talker 是过度工程。

## 验证指标

- **Talker 响应延迟 p99**：与单体 Agent 的首响应基线比较。Talker 没有改善等待感时，应检查模型选择、工具调用和同步依赖。
- **Talker 越界率**：抽样检查 Talker 是否在深度分析完成前给出具体结论。越界样本应回到 prompt、权限和输出 schema 调整。
- **belief 命中率**：检查后续对话能否读取并正确使用已确认的 belief state，同时防止过期或跨用户状态污染。
- **单 turn 成本**（注意结构）：双模是"两档同时跑"，单 turn 成本比单档贵档还略高（多了 Talker 那部分），但换来延迟大降——这是 cost-latency-quality 三角的另一种 Pareto 选择，要按业务接受度评估。

## 最小实现

```
用户说话 →
    若是首轮：建 belief state，异步触发 Reasoner（非阻塞）
    Talker 快速回应（低延迟模型，权限受限）
    若 Reasoner 已跑完（belief 状态 = updated）→ Talker 把分析自然织进回应
Reasoner 后台（高能力模型）：
    深度分析 → 写 belief state（结构化结论 + 建议）
    带配置化 timeout + cancel（用户换话题时取消）
belief state：跨 session 持久化，写操作加锁
返回 Talker 回应 + 后台维护的 belief
```

生产实现应限制 Talker 的决策权限；Reasoner 异步任务支持 timeout 和 cancel；belief state 持久化到 Redis 供跨 session 使用；共享 state 写操作加锁。

## 场景化示例

设想一个留学咨询 Agent。用户询问两所学校的选择时，Talker 先确认关切点并说明已开始分析；Reasoner 在后台结合成绩、科研经历和兴趣方向形成详细判断，写入 belief state；下一轮由 Talker 根据用户新增信息引用这份判断。在线辅导场景也可采用低成本模型承担 Talker、高能力模型承担 Reasoner，并为师生提供不同粒度的 trace。首响应、最终质量和人工 override 需要在真实会话中分别评估。

## 相邻模式

- **复杂度路由（R2）**：普通路由选择一个模型档位，双模架构同时运行 Talker 和 Reasoner 两个档位。
- **迭代假设验证（R4）**：同在循环列。迭代是单 Agent 跟自己循环验证假设，双模是双 Agent 协同分处理"说"和"想"。
- **思维链（R1）**：Reasoner 运行完整推理链，Talker 只承担低延迟交互。
- **分层记忆模式**：belief state 跨 session 持久化，和记忆模块"User 层 belief 持久化"是同源思路。

## 工程判断

Talker-Reasoner 将低延迟交互与高成本推理分离。Talker 负责澄清和进度反馈，Reasoner 在隔离上下文中完成分析，两者通过结构化任务包与结果包交接。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《R5 双模架构》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-r5-talker-reasoner">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
