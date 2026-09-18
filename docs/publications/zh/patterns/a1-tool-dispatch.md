<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>A1
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>A1 · Tool Dispatch · 工具调度</h1>
<p class="publication-deck">在每一步行动前，根据工具元数据、当前状态和风险规则选择可调用工具。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">行动 Action × 路由 Route（选）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">低到中（取决于候选集、状态刷新和策略检查）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">行动模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">在每一步行动前，根据工具元数据、当前状态和风险规则选择可调用工具。</td>
</tr>
</tbody>
</table>

---

## 问题

工具数量增加后，近义接口和重叠参数会扩大选择空间。LLM 可以填写参数和解释返回值，但一次有效 dispatch 还依赖状态新鲜度、并发安全性、配额和副作用。物流派单若在写入前没有刷新司机状态和路况，就可能反复把任务分给已经不适合接单的司机。

Tool Dispatch 使用工程层契约控制工具选择。每个工具需要提供完整元数据，并配置配额、状态刷新和副作用追踪。

## 坐标说明：行动 × 路由

- **纵轴 · 行动**：工具调用将决策转化为外部动作；工具选择位于行动执行的入口。
- **横轴 · 路由**：它的工作方式是基于当前 intent 和 context，把这一次调用导向最合适的那个工具，是典型的路由结构，而不是链式串联或层级包装。同模块的最简工具集（A5）也落在路由这一侧，但分工不同——A1 解决"怎么挑"，A5 解决"挑之前先砍"。

## 解决方案与机制

Tool Dispatch 的选择质量受工具元数据完整度影响。除了 name、description 和 parameters，生产 schema 还应表达执行特性、来源、权限、渐进披露和生命周期信息。

关键执行特性可包括 `isReadOnly`、`isConcurrencySafe`、`isDestructive`、`requiresFreshState` 和 `requiresApproval`。未知值应进入保守路径：不并行、不跳过审批、不假设状态新鲜。布尔字段无法表达“未声明”时，可使用显式枚举或在注册阶段拒绝不完整 schema。

围绕元数据，还要配三件工程纪律：

<table>
<thead>
<tr>
<th style="text-align: left;">机制</th>
<th style="text-align: left;">作用</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Quota 配额</td>
<td style="text-align: left;">对同一工具、主体或资源设置调用与副作用上限，防止重复动作累积</td>
</tr>
<tr>
<td style="text-align: left;">State refresh 强制</td>
<td style="text-align: left;">写操作前必须先查询刷新状态，避免基于过期数据做写入</td>
</tr>
<tr>
<td style="text-align: left;">Saga 副作用追踪</td>
<td style="text-align: left;">每个 destructive 工具登记 inverse 动作，失败时反向回滚</td>
</tr>
</tbody>
</table>

## 适用场景

- **工具数量多、副作用多、错调代价大三者叠加**：物流派单、客服工单、运维操作。
- **接入 MCP 等外部工具协议**：工具跨越了新的信任边界，需要记录来源和版本，并按风险检查描述、参数、权限与运行行为。
- **工具密集、可用局部程序表达的任务**：例如从多家门店读取库存、筛选缺货项，再为每项查询替代品。模型可以通过 Programmatic Tool Calling 生成一段受限程序，在沙箱内循环或并行调用已注册工具，先汇总结果，再把必要信息交回上下文。调用顺序来自模型生成的程序，并非工程人员预先写死；工具注册、权限、配额和每次调用的准入仍由 A1 控制。

## 四种运行方式的边界

<table>
<thead><tr><th style="text-align: left;">运行方式</th><th style="text-align: left;">如何推进任务</th><th style="text-align: left;">主要边界</th></tr></thead>
<tbody>
<tr><td style="text-align: left;">直接工具调用</td><td style="text-align: left;">模型选择一个工具和参数，取得结果后再决定下一步</td><td style="text-align: left;">每次调用都经过 A1 的候选选择和准入</td></tr>
<tr><td style="text-align: left;"><a href="https://adpsagent.com/zh/concepts/react-loop/">ReAct</a></td><td style="text-align: left;">推理、行动、观察交替进行；新观察直接影响下一轮判断</td><td style="text-align: left;">适合路径尚不确定、需要边做边看的任务，模型往返通常较多</td></tr>
<tr><td style="text-align: left;"><a href="https://adpsagent.com/zh/concepts/programmatic-tool-calling/">Programmatic Tool Calling</a></td><td style="text-align: left;">模型先写受限程序，再由程序循环、分支、并行调用已注册工具</td><td style="text-align: left;">程序负责局部控制流，工具的身份、权限和副作用边界没有改变</td></tr>
<tr><td style="text-align: left;"><a href="https://adpsagent.com/zh/concepts/code-as-action/">CodeAct</a></td><td style="text-align: left;">模型把可执行代码作为行动语言，用代码计算、调用库或组合可用能力</td><td style="text-align: left;">行动空间比已注册工具更宽，需要更严格的沙箱、资源和凭证隔离</td></tr>
</tbody>
</table>

这四种名称描述的层次不同。A1 负责工具注册、候选选择和调用准入；A2 可以把多阶段任务编成计划；ReAct、Programmatic Tool Calling 和 CodeAct 则说明某一步在运行时怎样推进。一次任务里生成的代码只有经过验证、命名、版本化并允许跨任务复用后，才进入 M5 程序性记忆。

## 已知失效方式

- **元数据不足**：只有 name 和 description 时，Agent 无法判断工具的副作用、状态要求和审批条件，容易发生错调。
- **副作用工具没配套**：写数据库、发消息、扣款这类工具没有 quota、没有 state refresh、没有 saga，一次错调就是生产事故。
- **工具堆砌（Tool Stuffing）**：把整个 registry 都发给模型会占用 context 并增加近义工具冲突。应使用渐进披露，让核心工具常驻，其余按需检索加载。
- **工具中毒（Tool Poisoning）**：攻击者可能在外部工具 description 中嵌入指令，使每次加载该工具的 session 都受影响。需要来源白名单、描述检查、最小权限、运行时行为监控和隔离，具体控制按 threat model 组合。

## 验证指标

- **工具选择准确率**：回放历史 query，由规则、人工或 reviewer 判断每一步是否选到合适工具，并按任务类型分析误选原因。
- **副作用可控率**：通过 chaos test 验证错调 destructive 工具时，quota、审批和 saga 能否阻断或回滚。不可逆动作必须有独立的控制指标。
- **工具幻觉率**：记录不存在的工具、错误参数和 schema 校验失败。指标变化时检查 registry、description 和候选集规模。
- **每任务工具调用分布**：结合任务复杂度观察调用数量和重复调用。数量异常只是一条诊断线索，不能单独判断是否 over-tooling。

## 最小实现

```
dispatch(tool_name, args, session):
    工具不存在        → 拒绝（tool_hallucination）
    配额已用满        → 拒绝（quota_exceeded）
    需新鲜状态但已过期 → 拒绝（stale_state_must_refresh）
    需人工审批        → 挂起（awaiting_approval）
    执行 handler:
        成功且 destructive → 登记 saga inverse + 累加 quota + 刷新 state 时间戳
        失败              → 记 trace，交由上层 saga 回滚
    返回 DispatchTrace（工具/参数/触发方/状态/拒因/耗时）
```

生产实现应把未声明的执行属性按高风险处理；quota 同时按任务和业务资源计数，例如派单还要按司机 id 计数；MCP 工具记录来源与版本，并执行相应的描述校验和行为监控。

## 场景化示例

梁博团队的执行型 Agent 将知识检索、技能加载和工具调用分为 `retrieve`、`use_skill` 和 `call_tool` 三类接口。城配派单 Agent 的 dispatch 层增加工具元数据、selection guidance、写操作前状态刷新、单 session 派单配额和 saga 副作用追踪。这个具名实践说明，工具调度的主要工作量落在契约、状态和副作用控制上，效果应以团队授权的生产评测为准。

## 相邻模式

- **最简工具集（A5）**：A1 在给定工具集中选择，A5 控制单次暴露的工具规模。
- **规划-执行（A2）**：A2 决定多阶段任务先做什么、何时验收；某个步骤内部可以用 Programmatic Tool Calling 批量调用工具，每次工具调用仍经过 A1 准入。
- **护栏三明治（A4）**：A4 在 dispatch 前后执行 pre-check 和 post-check，与 A1 的 quota 和 state refresh 形成嵌套控制。
- **复杂度路由（R2）**：思路同源，都是基于 context 做路由，区别在 R2 路由的是推理档位，A1 路由的是工具。

## 工程判断

Tool Dispatch 把工具操作约束编码为元数据和工程契约。生产实现需要覆盖权限、幂等性、状态新鲜度、审批、回滚、限流和审计，不能只依赖名称、描述和参数 schema。

## 企业证据

以下现场记录说明该模式在具体业务约束下如何实现。案例结论只在文中声明的系统边界内成立。

<ul style="list-style: none; margin: 0.5rem 0 1rem 0; padding: 0;">
<li style="margin-bottom: 0.6rem; line-height: 1.55;"><a href="https://adpsagent.com/zh/patterns/a1-tool-dispatch/cases/liangbo/" style="font-weight: 600;">东方屹腾 · 工具调度</a><span style="color: var(--color-text-muted);"> — 工具由行动模块调用，注册时声明机械状态的生产坐标和消费坐标。</span></li>
</ul>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<!-- RELATED-CASE-DEERFLOW:START -->

<section aria-labelledby="related-deerflow-case" class="related-case-band">
<p class="related-case-label">相关开源工程案例</p>
<h2 id="related-deerflow-case"><a href="https://adpsagent.com/zh/cases/deerflow-guardrail/">DeerFlow：从调用前拦截到双层授权</a></h2>
<p>姜宁分享的 Guardrail 演进以五个公开 PR 为证据，展示装配过滤、运行时授权、身份、策略和审计怎样进入同一条工具执行路径。</p>
</section>

<!-- RELATED-CASE-DEERFLOW:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《A1 工具调度》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-a1-tool-dispatch">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
