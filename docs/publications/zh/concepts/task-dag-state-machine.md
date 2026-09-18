<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>任务 DAG 与节点状态机</h1>
<p class="publication-deck">依赖边限定执行顺序，节点状态支持调度、验收和恢复。</p>
</header>

![任务 DAG 与节点状态机](../../assets/images/concepts/task-dag-state-machine.png)

## 应用背景：业务步骤有顺序，每一步还有生命周期

薪酬任务要先创建薪资组，再关联员工，然后计算、审批和提交。“审批”依赖计算结果；审批节点自身又会经历待执行、进行中、等待人工、完成或失败等状态。

只在提示词里写“请按顺序执行”，无法支持并行节点、中断恢复和局部重试。依赖关系与节点状态需要成为程序可读的一等数据。

## 概念定义

任务 DAG 用有向无环图表示步骤依赖，节点状态机记录每个任务的运行状态。二者共同把流程顺序从自然语言说明转换为可调度数据。

节点通常包含 ID、目标、依赖、状态、验收条件和结果引用。下游节点只有在所有依赖节点完成、前置条件通过后才能进入 `ready`。

## 工程机制

规划执行由五类组件组成：

- Planner 生成或局部修订任务图；
- Scheduler 计算可运行节点；
- Executor 执行当前节点；
- Validator 核对业务回执和验收条件；
- Workspace 持久化图、状态迁移和 Checkpoint。

常见状态包括 `pending`、`ready`、`in_progress`、`awaiting_approval`、`completed`、`failed` 和 `blocked`。每次状态转换都应记录触发事件和计划版本。

ReAct 用于任务结构尚不明确的阶段。依赖关系形成后，Orchestrator 把控制权交给规划执行。失败时可以替换受影响子图，保留已经验收的节点。

## 案例用法

薪资组快速搭建要求先创建快照，再导入模板，导入失败时回滚。早期实现把顺序写入 Skill 并交给 ReAct，测试中出现跨步和漏步。任务 DAG 上线后，依赖边限制了可调度顺序，模型不再逐轮决定先后。

同一状态机也支持 HITL。敏感节点进入 `awaiting_approval`，审批通过后回到 `ready`，拒绝后进入 `blocked` 或触发替代计划。

## 适用条件

当流程包含严格先后关系、并行分支、失败恢复或人工审批时，应使用任务 DAG 与状态机。调度状态与其他状态的边界见[会话统一状态](https://adpsagent.com/zh/concepts/unified-session-state/)，审批恢复见[HITL 阻塞与恢复](https://adpsagent.com/zh/concepts/hitl-block-resume/)。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-planning-execution">规划、执行与写回</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：梁博</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将依赖、验收和恢复统一进 Agent 任务合同。</dd></div>
<div><dt>当前地位</dt><dd>继承术语的 Agent 化</dd></div>
</dl>
</section>

<div class="document-citation">
<p><strong>初始来源：</strong><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例报告</a>；案例提供：梁博（Bo Liang）。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-task-dag-state-machine">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
