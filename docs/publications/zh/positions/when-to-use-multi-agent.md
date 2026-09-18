<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/positions/" style="color: var(--color-text-muted);">立场</a>
</p>

# 多 Agent：采用条件与工程边界

> ADPS 立场专文 · 第 1 篇  
> 发布：2026-05-30  
> 署名：ADPS 共同体（Agent Design Patterns Society）

## 问题范围

多 Agent 描述多个具有独立运行边界的 Agent 共同完成任务。角色名称、不同提示词或连续的多次模型调用，并不足以构成多 Agent 系统。

工程上需要检查四个边界：

1. **上下文边界**：每个 Agent 读取哪些信息，内部过程是否会污染其他角色。
2. **工具与权限边界**：各 Agent 能调用哪些工具，是否使用不同凭据和作用域。
3. **状态与失败边界**：一个 Agent 失败时，其他 Agent 能否继续、重试或独立回滚。
4. **交接边界**：跨 Agent 传递的是结构化工件、证据和状态，还是整段对话。

如果这些边界都不存在，系统更接近单 Agent 的分步调用。此时增加角色只会增加调度、上下文复制和故障定位成本。

## 采用原则

单 Agent、明确工具集和可观测 Harness 应作为比较基线。多 Agent 的采用需要结构性理由，并通过同一任务集比较质量、延迟、成本和故障恢复。

常见的结构性理由包括：

- 子任务可以真正并行，分支之间没有运行期依赖；
- 不同角色必须隔离信息、权限或工具；
- 任务需要独立失败域，局部失败不能拖垮整个运行；
- 高风险产物需要独立评审，且评审方拥有不同证据或判断标准。

“角色更多”“协作更像组织”或“演示效果更丰富”不属于采用条件。

## 适合多 Agent 的结构

### 并行探索

Planner 将任务拆成相互独立的分支，多个 Worker 并行产生工件，Aggregator 在所有分支结束后汇总。任务 DAG 中可并行的叶子节点应当没有数据依赖；存在依赖的部分继续使用链式或编排拓扑。

验收重点包括：

- 每个分支有清楚的输入、输出和截止条件；
- 分支结果可以单独重试和丢弃；
- 汇总阶段能识别冲突、重复和缺失；
- 并行节省的墙钟时间高于额外调度成本。

### 独立评审

Generator 产生候选工件，Critic 使用明确 rubric、原始证据或确定性检查进行评审。不同模型可以增加视角差异，但不能自动提供独立性。上下文、证据源、权限和责任人仍需分离。

评审结论应包含问题位置、依据、严重度和处置建议。只有“同意 / 不同意”或一个综合分数，无法支持修复与追责。

### 层级委派

父 Agent 控制目标、预算和最终验收，子 Agent 在受限作用域内处理局部任务。子 Agent 返回结构化结果，不把完整内部对话写回父 Agent 的上下文。

这种结构适用于大仓库检索、跨领域资料收集和权限分区任务。委派合同至少需要目标、允许工具、资源预算、交付格式、失败状态和回收条件。

## 不适合多 Agent 的结构

### 线性任务的角色化拆分

一条严格顺序的任务链被拆成多个角色后，每一步仍要等待前一步，无法获得并行收益。状态在角色之间反复序列化，反而增加丢失和误读的机会。此类任务通常由单 Agent 配合 Chain、Plan and Execute 或 Prompt Chaining 更容易控制。

### 共享全部上下文与状态

多个角色读取同一份上下文、共享同一工具面，并在同一状态对象上连续写入时，隔离收益基本不存在。应先判断这些角色是否只是同一运行时中的不同阶段。

### 缺少可比较的单 Agent 基线

没有基线，就无法判断多 Agent 带来的变化来自并行、隔离、模型差异，还是提示词和工具设计。基线至少记录任务完成率、关键失败类型、延迟、成本、人工介入和恢复结果。

## 最小隔离合同

<pre><code class="language-yaml">agent_role: repository_reviewer
task_scope:
  repository: payroll-service
  paths: ["src/payroll/**"]
context:
  include: ["change.patch", "acceptance.md"]
  exclude: ["generator_scratchpad"]
tools:
  allow: ["read_file", "search_code", "run_tests"]
  deny: ["write_file", "deploy", "database_write"]
budget:
  max_steps: 12
  max_duration_seconds: 180
handoff:
  schema: review_finding_v1
  required: ["location", "evidence", "severity", "recommendation"]
failure:
  retry: 1
  on_timeout: return_partial
</code></pre>

这份合同让“独立角色”成为运行时事实。缺少作用域、工具、预算和交接约束时，角色设定仍停留在提示词层。

## 决策表

<table>
<thead>
<tr>
<th style="text-align: left;">维度</th>
<th style="text-align: left;">单 Agent 更合适</th>
<th style="text-align: left;">多 Agent 候选</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">任务依赖</td>
<td style="text-align: left;">强顺序依赖或频繁共享状态</td>
<td style="text-align: left;">存在无依赖并行分支</td>
</tr>
<tr>
<td style="text-align: left;">上下文</td>
<td style="text-align: left;">信息可以共同读取</td>
<td style="text-align: left;">信息隔离能减少干扰或泄露</td>
</tr>
<tr>
<td style="text-align: left;">权限</td>
<td style="text-align: left;">使用同一工具和凭据</td>
<td style="text-align: left;">需要分权、最小权限或独立审批</td>
</tr>
<tr>
<td style="text-align: left;">失败恢复</td>
<td style="text-align: left;">整体重试成本低</td>
<td style="text-align: left;">需要局部重试和独立失败域</td>
</tr>
<tr>
<td style="text-align: left;">评审证据</td>
<td style="text-align: left;">同一证据足以验收</td>
<td style="text-align: left;">需要独立证据源或专业判断</td>
</tr>
<tr>
<td style="text-align: left;">运行基础</td>
<td style="text-align: left;">基线和追踪尚不完整</td>
<td style="text-align: left;">已能比较每个分支的质量与成本</td>
</tr>
</tbody>
</table>

这张表不用于机械计分。任何候选方案都应回到任务 DAG、隔离合同和对照实验中验证。

## 与 ADPS 模式的关系

多 Agent 不是单独的执行拓扑。它常由协作模式与并行、层级、路由或编排拓扑组合形成：

- C1 层级委派定义父子责任和验收；
- C2 扇出汇聚处理独立并行分支；
- C3 对抗评审建立生成与评审的证据边界；
- C4 接力链定义跨角色交接；
- C5 子 Agent 隔离约束上下文、工具和失败域；
- C6 编舞研究缺少中央编排者时的事件协作，目前仍作为候选模式评审。

模式名称只说明结构。生产可用性仍取决于状态管理、可观测性、权限控制、停止条件和回归评测。

## 证据要求

公开讨论多 Agent 方案时，建议同时提供：

1. 单 Agent 基线；
2. 任务 DAG 与可并行分支；
3. 子 Agent 隔离合同；
4. 端到端轨迹和失败恢复记录；
5. 相同任务集上的质量、延迟、成本与人工介入对比。

ADPS 将继续收集可复核的行业案例。缺少原始记录的百分比、倍数和匿名故事不作为模式有效性的证据。

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
<p><a href="https://adpsagent.com/zh/chronicle/#positions-when-to-use-multi-agent">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
