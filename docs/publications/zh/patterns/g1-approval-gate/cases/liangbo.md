<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/g1-approval-gate/" style="color: var(--color-text-muted);">G1 审批门</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>G1 · 审批门 · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">敏感节点执行前等待审批，通过后重新校验并从原任务节点恢复。</p>
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
<td style="text-align: left;">G1 审批门 Approval Gate（治理 × 路由）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">A2 规划执行 · X1 可观测性</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/g1-approval-gate/">/zh/patterns/g1-approval-gate/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第五章末 · PPT 第 19 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">敏感节点在执行前进入等待审批状态；审批通过后重新校验上下文，并从原任务节点恢复。</td>
</tr>
</tbody>
</table>

---

## 场景约束

东方屹腾的 Agent 可以修改薪资项和社保配置，并连接银行与税务接口。代发、申报和批量数据修改等操作具有高错误成本，需要在最终写入前获得人工授权。

审批门包含两个不同的问题：

1. 哪些任务或工具必须暂停；
2. 审批后如何恢复同一条执行流，而非从头重跑。

## 两种续作

| 形态 | 运行方式 | 所需状态 |
| --- | --- | --- |
| 叙事续作 | 当前会话结束，用户在后续会话确认 | 原始目标与进展摘要 |
| 执行流恢复 | 当前任务节点暂停，收到审批事件后继续 | 任务图、节点状态、业务参数和幂等记录 |

内容修改等任务可以采用叙事续作。代发、报税和终端命令等操作通常需要执行流恢复。

## 状态机接入

东方屹腾复用规划执行的任务 DAG 和节点状态机。敏感节点在执行前由 `ready` 转为 `awaiting_approval`。审批通过后重新校验，再返回 `ready`；拒绝或超时后进入 `blocked`、`cancelled` 或替代流程。

下游依赖节点在审批完成前保持不可调度。无依赖的并行分支可以继续运行，具体由任务图决定。

审批规则使用声明式配置，至少包括：

- 任务或工具标识；
- 风险等级与触发条件；
- 所需审批角色；
- 超时和拒绝策略；
- 参数摘要与展示字段；
- 审批后的再次校验要求。

## 恢复校验

审批通过不等于立即调用工具。恢复前需要检查：

1. 任务图版本和依赖是否仍有效；
2. SessionState 中的参数是否过期或被覆盖；
3. 用户权限和审批主体是否匹配；
4. 相同幂等键是否已经成功执行；
5. 外部系统状态是否发生变化。

通过检查后，调度器重新计算可运行节点，并从原阻塞点继续。

## 案例运行

薪资代发节点进入 `awaiting_approval` 后，界面显示任务、金额摘要、参数来源和待审批原因。审批事件写入统一时间线。批准后，系统核对代发批次、权限和幂等记录，再执行工具；依赖该节点的后续查询或报税任务随后才可调度。

## 失效信号

- 界面显示暂停，后台任务仍继续；
- 审批通过后从头重跑全部任务；
- 下游节点在上游等待审批时被调度；
- 所有写操作都要求审批，审批人形成机械放行；
- 审批规则写死在工具代码中；
- 审批后不重新检查参数、权限和幂等状态；
- 审批记录没有关联任务版本和执行事件。

## 验证指标

- 高风险操作的审批覆盖率；
- 误拦截率和审批通过率；
- 审批等待时长与超时率；
- 恢复后重复副作用次数；
- 下游节点提前运行次数；
- 审批记录到任务、参数和业务回执的关联完整率。

## 与白皮书的对应

G1 白皮书要求在高风险动作前设置显式准入点，并保存审批证据。东方屹腾用规划执行状态机表达阻塞和恢复，用 X1 时间线展示等待、批准和继续执行的全过程。

## 迁移条件

Agent 执行不可逆、敏感或受监管操作时，应采用执行流审批。系统需要先具备可持久化的任务节点、状态机和幂等机制。只涉及内容确认的场景可以使用较轻的叙事续作。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 审批门》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>证据边界：</strong>本页是完整案例的模式切片，记录特定系统约束下的实现选择。案例方提供的实现与效果信息未经过独立审计，不构成通用性能承诺。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>；案例提供：梁博</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-07-30">2026-07-30</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-g1-approval-gate-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
