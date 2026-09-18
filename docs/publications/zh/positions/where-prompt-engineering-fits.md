<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/positions/" style="color: var(--color-text-muted);">立场</a>
</p>

# Prompt Engineering 在 Agent 系统中的位置

> ADPS 立场专文  
> 发布：2026-05-30  
> 署名：ADPS 共同体（Agent Design Patterns Society）

## 定义范围

Prompt engineering 设计模型单次调用中的语言条件，包括角色、任务说明、示例、上下文排布、输出格式和工具描述。它直接影响模型如何理解输入、组织推理和表达结果。

Agent 系统还需要管理运行时状态、工具权限、任务进度、失败恢复、审批和证据。这些职责由 Harness 承担。Prompt 进入 Harness，成为一次模型调用的输入；Harness 决定这次调用在什么状态下发生、可以产生哪些副作用，以及结果如何验收。

把两类职责分开后，Prompt engineering 的适用范围会清楚很多。

## 适合放在 Prompt 中的内容

### 角色与任务语义

Prompt 可以说明模型承担的角色、当前任务、术语口径和目标读者。角色描述应服务于可检查的行为，避免只写人格化标签。

### 示例与边界样本

Few-shot 示例适合表达难以完全写成规则的分类口径、格式约定和领域表达。示例集需要覆盖正例、反例和边界情况，并随评测集一起版本化。

### 输出形状

Prompt 可以说明字段含义、缺失值处理和引用要求。JSON Schema、类型检查和业务校验继续在程序侧执行。模型负责形成候选结构，程序负责确认结构能否进入下游。

### 推理与工具使用提示

模型需要知道当前有哪些工具、每个工具解决什么问题，以及何时应请求澄清。工具说明应来自能力注册表，避免在多个 Prompt 中维护互相漂移的副本。

### 软约束

语气、篇幅、解释深度和保守程度可以由 Prompt 调整。安全、权限和资金操作等硬约束必须由运行时控制执行。

## 需要进入 Harness 的职责

### 状态与任务图

规划阶段、执行阶段和等待审批属于显式状态。状态机或任务图保存当前节点、依赖、重试次数和恢复位置。Prompt 可以告诉模型当前状态，不能代替状态存储。

### 工具准入

Tool Registry 定义工具 schema、版本、权限和风险等级。Dispatcher 缩小候选工具，Hook 或 Approval Gate 在调用前后执行政策。自然语言提示只提供操作背景。

### 记忆与上下文

记忆系统决定哪些信息可以写入、何时召回、如何处理过期和冲突。上下文装配器按任务合同选择本轮材料。把完整历史持续追加到 Prompt，会同时放大成本、噪声和过期风险。

### 验证与发布

测试、Eval、业务账本和人工验收提供独立证据。让模型在 Prompt 中给自己的结果打分，只能作为候选信号，不能单独支撑发布、高风险执行或权限升级。

### 停止、重试与恢复

最大步骤数、预算、超时、幂等键、补偿动作和 checkpoint 都需要运行时记录。模型可以提出下一步，执行器负责判断还能否继续。

## 常见越界

<table>
<thead>
<tr>
<th style="text-align: left;">越界方式</th>
<th style="text-align: left;">运行风险</th>
<th style="text-align: left;">工程位置</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">在 Prompt 中描述多 Agent 协作</td>
<td style="text-align: left;">缺少消息、隔离和交接合同</td>
<td style="text-align: left;">协作模式与编排运行时</td>
</tr>
<tr>
<td style="text-align: left;">在 Prompt 中声明禁止高危工具</td>
<td style="text-align: left;">指令可能被绕过</td>
<td style="text-align: left;">工具准入、权限和审批</td>
</tr>
<tr>
<td style="text-align: left;">把全部历史写进 Prompt</td>
<td style="text-align: left;">噪声、过期和成本持续增长</td>
<td style="text-align: left;">记忆分层与上下文装配</td>
</tr>
<tr>
<td style="text-align: left;">让模型维护流程阶段</td>
<td style="text-align: left;">跳步、重复和恢复困难</td>
<td style="text-align: left;">状态机或任务图</td>
</tr>
<tr>
<td style="text-align: left;">让模型自评后直接发布</td>
<td style="text-align: left;">评审与生成同源</td>
<td style="text-align: left;">独立测试、Eval 和人工验收</td>
</tr>
</tbody>
</table>

## 与 ADPS 双轴框架的关系

Prompt engineering 主要作用于需要模型解释、推理、生成或选择工具的局部步骤。执行拓扑仍由 Harness 实现：

- Chain 决定步骤顺序；
- Route 决定候选分支；
- Parallel 决定哪些分支并发；
- Orchestrate 管理任务图与共享状态；
- Loop 定义反馈和停止条件；
- Hierarchy 定义委派、预算与回收。

同一段 Prompt 可以在不同拓扑中复用。拓扑、状态和权限不会因文字写法变化而自动成立。

## Prompt 的工程合同

<pre><code class="language-yaml">prompt_id: payroll_intent_v4
purpose: classify_payroll_request
inputs:
  required: [user_message, tenant_policy]
outputs:
  schema: intent_signal_v2
examples:
  dataset: payroll-intent-boundaries-v3
tools: []
constraints:
  missing_information: ask_clarification
evaluation:
  suite: evals/payroll-intent-v5
  release_gate: no_p0_regression
owner: payroll-agent
</code></pre>

Prompt 作为版本化工件进入代码评审、回归评测和发布记录。团队可以据此回答改了什么、影响哪些任务、由谁验收，以及需要回滚到哪个版本。

## 采用建议

新增一段 Prompt 前，先确定它承担的是语言层工作，还是运行时控制。属于前者时，为它定义输入、输出、示例集和 Eval；属于后者时，把规则落实到状态、代码、权限或验证系统中。

Prompt engineering 保留了重要的模型交互工艺。Harness engineering 将这些工艺放进可运行、可观测和可恢复的系统。

---

ADPS · Agent Design Patterns Society · adpsagent.com

---

<p style="font-size: 0.92rem; color: var(--color-text-muted);">
<a href="https://adpsagent.com/zh/positions/">← 返回全部立场</a>
</p>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 技术立场；论据与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#positions-where-prompt-engineering-fits">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
