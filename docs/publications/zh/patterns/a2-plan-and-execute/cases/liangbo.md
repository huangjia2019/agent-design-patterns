<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/a2-plan-and-execute/" style="color: var(--color-text-muted);">A2 规划执行</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>A2 · 规划执行 · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">严格步骤依赖写入任务 DAG，由节点状态机调度、验收和恢复。</p>
</header>

<table>
<thead>
<tr>
<th style="text-align: left;">字段</th>
<th style="text-align: left;">值</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">主模式</td>
<td style="text-align: left;">A2 规划执行 Plan-and-Execute（行动 × 编排）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">A1 工具调度 · G1 审批门 · M3 进度追踪</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/a2-plan-and-execute/">/zh/patterns/a2-plan-and-execute/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第五章 · PPT 16–19 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">把严格步骤依赖写入任务 DAG，由状态机调度、验收和恢复；ReAct 负责探索，规划执行负责已明确的流程。</td>
</tr>
</tbody>
</table>

---

## 场景约束

薪资组快速搭建包含四个连续步骤：

1. 根据用户诉求匹配薪资组模板；
2. 为企业现有薪资组数据建立快照；
3. 快照成功后导入模板；
4. 导入失败时使用快照回滚。

步骤之间存在严格依赖。团队曾把这套顺序写入 Skill，再交给 ReAct 逐步执行。模拟测试中出现过跨步和漏步，说明叙事说明不能代替调度约束。

## 模式边界

ReAct 和规划执行承担不同任务：

| 模式 | 适用状态 | 控制结构 |
| --- | --- | --- |
| ReAct | 目标仍需探索，下一步依赖最新观察 | 带退出条件的循环 |
| 规划执行 | 步骤及依赖已经明确 | DAG 与节点状态机 |

ReAct 在任务结构明确后把控制权交还 Orchestrator。Orchestrator 创建或更新任务图，再进入规划执行。工具失败或新证据改变前提时，执行器可以触发局部 replan，无需重写整个计划。

## 核心数据结构

任务 DAG 保存节点及其依赖。节点至少包含目标、状态、前置依赖、验收条件和执行结果引用。

<pre><code class="language-go">type TaskStatus string

const (
    Pending         TaskStatus = "pending"
    Ready           TaskStatus = "ready"
    InProgress      TaskStatus = "in_progress"
    AwaitingApproval TaskStatus = "awaiting_approval"
    Completed       TaskStatus = "completed"
    Failed          TaskStatus = "failed"
    Blocked         TaskStatus = "blocked"
)

type TaskNode struct {
    ID          string
    Goal        string
    DependsOn   []string
    Status      TaskStatus
    Acceptance  []Criterion
    ResultRef   string
}
</code></pre>

一个节点只有在所有依赖节点均为 `completed`、自身前置条件通过时，才能从 `pending` 进入 `ready`。执行器领取 `ready` 节点后置为 `in_progress`，验收器根据业务回执决定进入 `completed`、`failed` 或 `blocked`。

## 运行组件

- **Planner**：把业务目标转换为任务图，声明依赖和验收条件；
- **Scheduler**：根据依赖和状态选择可运行节点；
- **Executor**：通过 A1 工具调度执行节点；
- **Validator**：核对回执、业务状态和节点验收条件；
- **Workspace**：持久化任务图和状态迁移；
- **Orchestrator**：管理 ReAct、规划执行和人工审批之间的控制权。

独立节点可以并行执行，有依赖的节点按拓扑顺序推进。调度方式与 Airflow、Prefect 等 DAG 系统相近，但节点内容可以由 Agent 在运行中生成或局部修订。

## Checkpoint 与恢复

Checkpoint 至少保存任务图版本、节点状态、已完成结果引用和当前控制权。恢复时，调度器重新计算可运行节点，不依赖模型复述此前步骤。

局部 replan 只替换受失败影响的子图，并保留已验收节点及其业务回执。计划版本写入事件日志，便于追溯“哪个计划产生了这次执行”。

## HITL 接入

敏感节点可以在执行前进入 `awaiting_approval`。审批通过后转为 `ready`，拒绝后转为 `blocked` 或触发替代计划。由于任务状态机已经保存中断点和依赖，HITL 不需要单独维护一套恢复机制。相关设计见 [G1 审批门切片](https://adpsagent.com/zh/patterns/g1-approval-gate/cases/liangbo/)。

## 失效信号

- 计划只是一段文本，没有可执行的节点 ID、依赖和验收条件；
- 计划生成后不再更新，工具失败只能从头重跑；
- 节点完成仅依据模型判断，没有核对业务回执；
- 调度状态、业务参数和叙事摘要混在同一结构中；
- 并行节点共享可变状态，却没有作用域和冲突检测；
- 审批只暂停界面，没有持久化任务节点与恢复位置。

## 验证指标

- 关键步骤依赖覆盖率；
- 跨步、漏步和重复执行次数；
- 节点验收条件的回执覆盖率；
- 失败后局部 replan 的范围与恢复时间；
- Checkpoint 恢复后任务图的一致性；
- 可并行节点的实际并发率；
- 审批恢复后重复副作用次数。

## 迁移条件

任务步骤明确、步骤间有严格依赖，且顺序错误会造成交付失败或数据损坏时，应采用规划执行。任务图、状态机和 Checkpoint 的成本由错误代价来决定。

资料检索、总结和报告生成等松散流程可以使用 ReAct 或提示链。此类任务通常不需要为每一步维护持久化节点状态。

规划执行中的每个节点继续使用 [A1 工具调度切片](https://adpsagent.com/zh/patterns/a1-tool-dispatch/cases/liangbo/) 的注册协议和机械状态坐标。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 规划执行》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>证据边界：</strong>本页是完整案例的模式切片，记录特定系统约束下的实现选择。案例方提供的实现与效果信息未经过独立审计，不构成通用性能承诺。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>；案例提供：梁博</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-a2-plan-and-execute-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
