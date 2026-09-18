<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>C4
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>C4 · Handoff Chain · 交接链</h1>
<p class="publication-deck">将长流程拆给 N 个职责明确的 Agent，并通过结构化 HandoffPacket 顺序传递状态与责任。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">协作 Collaboration × 链式 Chain（传）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（每次交接加一次 LLM 调用）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">协作模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">将长流程拆给 N 个职责明确的 Agent，并通过结构化 HandoffPacket 顺序传递状态与责任。</td>
</tr>
</tbody>
</table>

---

## 问题

多 Agent 系统如果在交接时只传递用户最后一句话，接收方将缺少客户身份、已完成动作、既有决策和待处理问题，容易重复提问或重复执行。

交接链在多个 Agent 之间顺序传递目标、状态、证据、决策和下一步责任。跨 Agent、跨 session 的状态需要显式 schema。客服中心的 warm handoff 采用同类做法：转接前由当前客服向接收方说明已知信息和处理进度。

## 坐标说明：协作 × 链式

- **纵轴 · 协作**：上一个 Agent 的输出成为下一个 Agent 的输入，各 Agent 是职责明确的 peer，不依赖 Supervisor 持有全局状态。
- **横轴 · 链式**：N 个 agent 严格按顺序传递，不并行也不循环。区别于扇出聚合的 N 个 worker 同时干，也区别于对抗评审的来回辩论。顺序敏感是它的硬特征。

## 解决方案与机制

一次交接包含以下三项：

1. **职责切分**：长流程拆成 N 个职责清晰的 Agent，每个 Agent 只处理约定环节。
2. **结构化打包**：当前 Agent 将关键状态打包为 HandoffPacket。单 Agent 多 prompt 可以自然延续 context，交接链跨 Agent 和 session，需要显式 state schema。
3. **受控移交**：交接前有权限闸判断这次交接合不合理，有链长上限防止无限传递，每次交接落 audit log。

HandoffPacket 建议至少五层 schema：

<table>
<thead>
<tr>
<th style="text-align: left;">层</th>
<th style="text-align: left;">内容</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Goal</td>
<td style="text-align: left;">客户根本诉求 + 当前未解决的具体问题</td>
</tr>
<tr>
<td style="text-align: left;">Artifacts</td>
<td style="text-align: left;">已完成的产出（查过的 KB、跑过的脚本、抄过的 ticket）</td>
</tr>
<tr>
<td style="text-align: left;">Decisions</td>
<td style="text-align: left;">决策包含 what / why / evidence</td>
</tr>
<tr>
<td style="text-align: left;">Rejected Paths</td>
<td style="text-align: left;">已尝试失败的方向，下一棒不要重复</td>
</tr>
<tr>
<td style="text-align: left;">Next Required</td>
<td style="text-align: left;">显式的下一步动作，不允许"看着办"</td>
</tr>
</tbody>
</table>

## 适用场景

- **分级客户支持**：L1 分诊、L2 技术、L3 工程、Director 升级，模型逐级增强、工具权限逐级放开、SLA 逐级升级。
- **专业分工的审批流程**：医疗的分诊护士到全科到专科到主任、法律的 paralegal 到 associate 到 partner、销售的 SDR 到 AE 到 CSM 到 VP。
- **执行型 agent 的控制权回交**：当一个 agent 完成自己职责需要把控制权交还给上层时（详见企业落地一例）。

四个条件要同时满足：专业分工明确、顺序可定、state 可结构化、SLA 升级机制是业务核心。

## 已知失效方式

- **冷转接**：只传"用户最后一句话"给下一棒，下一棒没拿到任何前面的上下文。识别信号是客户在交接后立刻被问已回答过的问题、情绪从 calm 转 frustrated 的转折点跟交接时点重合。修法是 HandoffPacket 必须含至少五层 schema。
- **决策溯源丢失**：Artifacts 都传过去了，但决策的 why 没传——下一棒看着一堆产出却不知道前任凭什么走这条路，于是重走流程或推翻前任决策。"Artifacts survive handoff, decisions don't"，除非给 decisions 单独留一个 schema 字段。
- **震荡循环**：同一对 Agent 反复来回交接，L2 退回 L1，L1 又交给 L2。修法是配置链长硬上限、显式约束 `can_handoff_to`、记录 visited set，并在触顶时转人工。
- **过度交接**：LLM 默认有 over-handoff 倾向，碰到稍微难的事就想踢给下一个 agent。可以在交接前加一道 classifier 审视"这次交接合理吗，是不是该自己做完"。
- **短任务或无清晰角色误用**：可以直接完成的短任务、单 Agent 通用助理和延迟敏感的实时对话通常不适合交接链。Loop 风险高时可改用层级委派，由 Supervisor 持有全局状态。

## 验证指标

- **链长跳数**：观察交接次数和触顶情况。最大跳数由角色图和业务 SLA 配置，触顶后强制转人工。
- **交接后重复提问率**：客户在交接后被问已回答过问题的比例，是冷转接的直接症状。
- **决策保留率**：检查上一棒的结论、理由和证据是否完整进入下一棒。偏低说明 HandoffPacket 退化为 raw history dump。
- **SLA 达成率**（按分级核算）：各级 agent 在自己 SLA 窗口内完成的比例，配合 sentiment carry over 监控升级链路里的客户情绪变化。

## 最小实现

```
HandoffChain.execute(request, initial_agent, max_hops):
    current, prev_packet = initial_agent, None
    for sequence in 1..max_hops:
        output = run_agent(current, prev_packet)   # 输入是结构化 packet 不是 raw history
        packet = build_packet(prev_packet, output) # 累积式继承 artifacts/decisions/rejected
        audit(packet)
        if output.complete: return result
        next = output.handoff_to
        if next not in current.can_handoff_to:      # 权限闸:防越级 + 防 oscillation
            return escalate_to_human()
        prev_packet, current = packet, next
    return escalate_to_human()                      # 超 max_hops 升人工

HandoffPacket: Goal / Artifacts / Decisions / Rejected Paths / Next Required
```

生产实现按 Agent 角色分级 system prompt 和 tool 权限；`can_handoff_to` 列出允许的接收方；`max_hops` 根据角色图设置，超过后强制转人工；audit log 记录跨 Agent 数据流转。

## 场景化示例

设想一个 SaaS 客户支持系统按分诊、技术、工程和主管角色逐级处理。第一版每次交接只传客户最后一句话，下一棒只能重新询问问题和账户信息。改造后，HandoffPacket 包含客户诉求、已查询的 KB 和脚本、带 why 的决策、已排除方向和下一步动作；模型和工具权限随角色调整；链长触顶后转人工。执行型 Agent 也可通过 handoff 回交控制权：当 ReAct Agent 识别到需要整体计划，或 Skill 契约声明 `PlanExecute`，就把控制权交回 Orchestrator。

## 相邻模式

- **Prompt Chaining（行动模块）**：Prompt Chaining 在单 Agent 内串联 prompt，context 自然延续；交接链跨 Agent 和 session，需要显式 state schema。
- **层级委派（C1）**：交接链没有主管、每一棒都是 peer，层级委派有 supervisor 作为稳定锚点。Loop 风险高时回到层级委派让 supervisor 当锚点反而更稳。
- **扇出聚合（C2）**：交接链是 N 个 agent 顺序干，扇出是 N 个 worker 同时干。
- **子代理隔离（C5）**：交接链关注跨棒的 state 显式传递，子代理隔离关注 sub-agent 的 context 边界，两者关注点不同但都涉及 agent 间的信息流设计。

## 工程判断

交接链用结构化 schema 传递目标、状态、证据、决策和责任。直接转交完整对话历史无法保证接收方获得明确的下一步与验收条件。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

## 2026-08-25 研讨会修订：交接合同

Handoff Contract 同时传递当前目标、带版本产物、已定决定、否决路径、未决问题、权限、责任和验收。接收方显式接受或拒绝，交接后回收上一段临时权限。

[协作模块研讨记录](https://adpsagent.com/zh/workshops/collaboration-2026-08-25/)

<!-- PATTERN-ENGINEERING-RELATED:START -->

<section aria-labelledby="related-handoff-engineering" class="related-case-band">
<p class="related-case-label">模式工程实现</p>
<h2 id="related-handoff-engineering"><a href="https://adpsagent.com/zh/patterns/engineering/cross-agent-handoff/">两个 Agent 怎样接上：从上下文引用到任务交接</a></h2>
<p>把本模式放进一次前端发现、后端修复和前端复测，检查责任转移、权限边界与验收证据。</p>
</section>

<!-- PATTERN-ENGINEERING-RELATED:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《C4 交接链》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-c4-handoff-chain">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
