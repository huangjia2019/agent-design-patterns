<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>HITL：阻塞、审批与恢复</h1>
<p class="publication-deck">敏感节点暂停并保存状态，审批后重新校验并继续执行。</p>
</header>

![HITL 阻塞审批与恢复](../../assets/images/concepts/hitl-block-resume.png)

## 应用背景：等人确认不等于结束任务

薪资计算完成后，Agent 应在真正提交前停下，给审批人展示批次、人数、金额和异常项。审批可能在几小时后才到达，期间网页会断开，业务数据也可能发生变化。

这不是在工具调用前弹出一个确认框就结束。系统要把任务持久化为“等待审批”，记住待执行动作与参数来源，收到授权后再校验一次执行条件。

## 概念定义

人在回路（HITL）在敏感任务开始前暂停执行，等待授权，并在审批后从保存的状态恢复。删除数据、薪资代发和税务申报等操作应由策略明确标记。

恢复对象分为两类：

- **叙事续作**：本轮结束，用户在后续会话确认，系统根据目标和进展重新进入流程；
- **执行流恢复**：当前任务节点暂停，审批事件到达后从同一节点继续。

第二类需要持久化任务状态、依赖、参数来源和幂等信息。

## 工程机制

敏感节点在执行前进入 `awaiting_approval`，并生成审批记录。记录至少包含任务、工具、参数摘要、风险级别、发起人和超时策略。

审批通过后，系统重新检查：

1. 任务版本和前置依赖是否仍有效；
2. 机械状态参数是否过期或被覆盖；
3. 权限和审批主体是否匹配；
4. 写操作是否已有相同幂等键的成功记录。

通过检查后节点转为 `ready`，拒绝或超时则进入 `blocked`、`cancelled` 或替代流程。

## 案例用法

东方屹腾在规划执行阶段已经建立任务 DAG、状态机、调度器和执行器。代发、申报等敏感工具通过声明式策略进入等待审批状态。审批后沿用原任务图恢复，不需要为每个工具单独实现暂停逻辑。

状态机也维护下游节点。上游审批未完成时，下游保持不可调度，避免界面暂停但后台仍继续执行。

## 适用条件

当 Agent 会执行不可逆、敏感或高风险操作时，应配置 HITL。执行流恢复依赖[任务 DAG 与状态机](https://adpsagent.com/zh/concepts/task-dag-state-machine/)，恢复所需的叙事、参数和调度状态见[会话统一状态](https://adpsagent.com/zh/concepts/unified-session-state/)。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：梁博</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将人工审批整理为可持久化运行状态，并补充恢复前复验。</dd></div>
<div><dt>当前地位</dt><dd>ADPS 重述</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-hitl-block-resume">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
