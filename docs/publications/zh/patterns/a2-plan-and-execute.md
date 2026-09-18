<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>A2
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>A2 · Plan-and-Execute · 规划-执行</h1>
<p class="publication-deck">先生成包含依赖、资源和审批节点的 plan，再按 plan 调度执行，并在偏离时局部 replan。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">行动 Action × 编排 Orchestrate（协）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（一次规划 + 多次执行，异构模型可显著压成本）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">行动模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">先生成包含依赖、资源和审批节点的 plan，再按 plan 调度执行，并在偏离时局部 replan。</td>
</tr>
</tbody>
</table>

---

## 问题

逐步反应式（ReAct）Agent 在长任务中容易失去全局顺序。招聘 Agent 如果只根据最近一步结果行动，可能跳过背景调查、重复查询薪酬数据，或在候选人状态不满足条件时继续推进。系统缺少一份显式 plan 来保存步骤依赖和审批节点。

Plan-and-Execute 将行动分为 plan 和 execute 两个阶段。规划阶段生成步骤、依赖、资源和人工审批节点；执行阶段由调度器按 plan 推进。宏观顺序保存在可审计、可版本化的计划中。

## 坐标说明：行动 × 编排

- **纵轴 · 行动**：该模式将目标转换为一系列外部动作，并管理动作之间的顺序与依赖。
- **横轴 · 编排**：Plan-and-Execute 的中心是一个编排者——它持有完整 plan，按依赖图调度每一步、维护全局状态与检查点、在偏离时做局部 replan。这跟提示链（A3）的纯链式不同：A3 是前一段输出喂给后一段的线性传递，A2 是一个中心节点统筹多步，独立步骤可并行展开、关键节点落 checkpoint、出错可回退重规划。统筹与回收这一层，正是编排区别于链式的地方。

## 解决方案与机制

实现至少需要职责分离、审批节点和 context reset。Aider architect mode 由 architect 生成 plan，editor 在清空上下文后执行 plan，中间默认由用户确认。

落到工程上有几个关键设计：

- **异构模型**：plan 阶段通常需要更强的全局推理，execute 阶段更结构化且可验证，可以按步骤选择不同模型。具体组合要在同一任务集上比较质量、成本和返工率。
- **plan 是 user-owned artifact**：Claude Code 把 plan 写文件而不是留在 prompt 里。文件天然是审计日志，可以多人 review、版本化、diff，用户从文件读、agent 也从文件读。
- **局部 replan**：plan 与现实冲突时，只修改受影响的后续节点，已 commit 的步骤保持不动。检查频率和 replan 预算由任务长度、外部变化频率和回放结果确定。

ReWOO 等工作展示了减少执行阶段模型往返的一种实现：规划阶段生成带变量依赖的计划，工具执行后再统一综合。它是否比 ReAct 更省 token、更准确，取决于任务结构、工具延迟和评测口径，需要在目标工作流上复测。

## 适用场景

- **目标明确、步骤可枚举、副作用敏感三者叠加**：HR 招聘、信贷审批、运维变更。
- **有硬性流程约束的合规场景**：比如"背景调查必须在发 offer 之前"。这类约束可以编码进 plan validator，规划阶段就拦下违规的 plan。
- **需要崩溃恢复的长任务**：每步写 checkpoint，崩溃后从 checkpoint resume，把 plan-execute 当可恢复事务来设计。

## 已知失效方式

- **plan ossification（计划僵化）**：plan 写好后执行器一路跑，中途某步返回意外结果（候选人撤回、schema 变更、外部 API 改协议），规划器没及时介入，后续步骤全是无效计算。应对是每 N 步把当前子任务和原始目标做一次对齐检查。
- **plan thrashing（计划震荡）**：replan 触发太频繁，每次失败都重写，agent 永远在规划从不执行。应对是设 replan 硬上限加 replan 预算封顶。
- **stale context 悄悄累积**：长任务的 state 用自由格式笔记容易"看起来还能解析但语义已坏"。应对是 state 用 JSON schema 严格化，让 partial corruption 早暴露。
- **cache 友好性被忽略**：每步重写稳定前缀会降低缓存命中并增加成本。结构化更新 plan 或 todo artifact 时，应测量 prefix 稳定性、缓存命中和状态新鲜度。

## 验证指标

- **长任务成功率 / 错误率**：与未拆分的执行基线比较，并按计划错误、执行错误和外部状态变化分类。
- **每任务 LLM 调用次数**：与 ReAct 基线比较，并把 planner、executor、replan 和结果综合分别计数。次数失控通常意味着 replan 震荡或步骤契约过碎。
- **replan 频率**：过高可能表示计划反复震荡，长期为零也可能意味着系统忽略了环境变化。应结合 replan 原因判断。
- **缓存命中率**：观察稳定 system prompt、工具定义和计划前缀能否复用，同时检查缓存是否掩盖过期状态。

## 最小实现

```
plan = planner(goal, context)        # 强模型，一次
若用户不批准 → 返回
while plan 未完成:
    ready = plan 中依赖已满足的步骤   # 拓扑序
    并行执行 ready:
        成功 → 标记 completed，写 checkpoint
        失败 → replan（受限于 MAX_REPLANS）
    每满 N 步 → adaptive replan 检查 plan 是否仍成立
返回 plan + 完整执行 trace
```

生产实现通过依赖注入提供 Planner、Executor 和 Approval；destructive 步骤登记 saga inverse；plan 写入文件并进行版本管理。

## 场景化示例

梁博团队将计划与执行显式分离。规划层把计划写入 Workspace 的 DAG，调度器按依赖关系推进，LLM 只负责单步参数和结果解释。放到招聘流程中，Planner 先生成带依赖的步骤，Executor 只执行当前节点，涉及筛选标准或候选人状态变化的节点进入 Approval Gate。成本、周期和错误变化应由具名团队提供可核验口径后再公开。

## 相邻模式

- **提示链（A3）**：A2 使用完整 plan、DAG 和 replan；A3 采用无 replan 的线性链。生产系统可以由 A2 编排外层任务，在每个子任务内部运行 prompt chain。
- **工具调度（A1）**：A2 的每个执行步骤内部都要做一次 A1 的工具选择。Planner 和 Executor 用异构模型的思路，与 A1 的 Programmatic Tool Calling 同源。
- **护栏三明治（A4）**：plan 里的审批节点和合规校验，落地时常由 A4 的 pre-check 实现。两者都把控制权交还给用户。
- **迭代假设验证（R4）**：R4 是推理端的"边做边调"，A2 是行动端的"先定后调"。A2 的局部 replan 借鉴了 R4 的反馈调整思路。

## 工程判断

Plan-and-Execute 使用任务分解、依赖图、状态机、检查点和补偿机制管理长任务。计划必须可更新、可验证、可中断，并允许用户在关键节点保留控制权。

## 企业证据

以下现场记录说明该模式在具体业务约束下如何实现。案例结论只在文中声明的系统边界内成立。

<ul style="list-style: none; margin: 0.5rem 0 1rem 0; padding: 0;">
<li style="margin-bottom: 0.6rem; line-height: 1.55;"><a href="https://adpsagent.com/zh/patterns/a2-plan-and-execute/cases/liangbo/" style="font-weight: 600;">东方屹腾 · 规划执行</a><span style="color: var(--color-text-muted);"> — 严格步骤依赖写入任务 DAG，由节点状态机调度、验收和恢复。</span></li>
</ul>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《A2 规划执行》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-a2-plan-and-execute">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
