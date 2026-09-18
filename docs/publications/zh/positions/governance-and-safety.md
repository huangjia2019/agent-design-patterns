<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/positions/" style="color: var(--color-text-muted);">立场</a>
</p>

# 治理与 Safety：运行时控制的工程边界

> ADPS 立场专文  
> 发布：2026-05-30  
> 署名：ADPS 共同体（Agent Design Patterns Society）

## 定义范围

Agent 治理规定系统可以执行哪些动作、在什么条件下执行、由谁承担责任，以及发生偏差后怎样停止、追溯和恢复。Safety 目标需要落实到运行时控制和可检查证据中。

生产系统至少要回答：

- 哪些工具、数据和环境可以访问；
- 哪些动作允许自动执行，哪些需要审批；
- 单次任务、租户和时间窗口内的影响范围；
- 每个判断和副作用留下什么证据；
- 何时停止、回滚、降级或收回自主权。

这些答案进入权限、状态、代码和运维流程，不能只写在 System Prompt 或原则文档中。

## 五类运行时控制

### 1. 工具准入与最小权限

Tool Registry 保存工具的 schema、版本、所有者、风险等级和凭据作用域。运行时根据任务、租户和角色生成最小工具集。未注册、版本不匹配或超出作用域的工具不进入候选。

准入判断应在模型调用之外执行。模型可以建议工具，程序负责验证调用者、资源、参数和权限。

### 2. 高风险动作门禁

审批门处理资金、生产写入、删除、对外发布和不可逆操作。审批材料需要包含动作、对象、数量、来源、预期结果和回滚方案。审批结论与后续工具调用使用同一动作 ID，避免批准 A 后执行 B。

Hook 适合执行确定性规则，例如路径白名单、命令禁用、参数上限和敏感字段检查。模型不需要参与这些判断。

### 3. 影响范围控制

Blast Radius Control 在执行前限制单次动作能够影响的对象、数量、金额、环境和持续时间。常见手段包括：

- 开发、测试和生产环境隔离；
- 只读凭据与短期凭据；
- 单租户、单批次和单资源上限；
- 沙箱、工作目录和网络出口限制；
- 幂等键、事务、补偿动作和 kill switch。

限制需要由下游系统强制执行。提示词中的“谨慎操作”不能替代硬边界。

### 4. 可观测性与审计

每次模型调用、工具调用、审批、状态变化和业务回执进入统一事件链。事件至少关联 run、task、action、tool version、actor、input/output hash 和 policy decision。

审计记录服务于事故还原、发布评测和责任确认。敏感输入可以保存哈希、脱敏摘要或受控引用，避免把可观测性变成新的泄露面。

### 5. 渐进自主

Agent 权限按证据逐级扩大。常见阶段包括影子运行、建议模式、审批后执行、有限自动执行和更大范围自治。升级条件应绑定任务集、错误类型、人工介入、恢复结果和业务验收。

版本变化、领域变化或重大事故会触发降级。自主权是可撤销的运行配置，不是系统一次获得的永久属性。

## 动作风险合同

<pre><code class="language-yaml">action_type: payroll_batch_submit
risk_class: high
subject:
  tenant_id: tenant_42
scope:
  max_records: 200
  environment: production
permissions:
  required_role: payroll_operator
approval:
  required: true
  approver_role: payroll_manager
preconditions:
  - batch_totals_reconciled
  - employee_ids_resolved
  - idempotency_key_present
execution:
  timeout_seconds: 60
  retry: 0
postconditions:
  - receipt_persisted
  - ledger_matches_receipt
recovery:
  mode: manual_compensation
evidence:
  retention_days: 365
</code></pre>

合同把政策翻译成可执行字段。工具调度、门禁、业务账本和审计系统读取同一份定义，减少各层规则互相漂移。

## 控制链

<pre><code class="language-text">任务与身份
    ↓
生成最小工具集和凭据
    ↓
动作提案与参数校验
    ↓
确定性 Hook / 审批门
    ↓
受限环境执行
    ↓
业务回执与后置校验
    ↓
统一事件链、告警与恢复
</code></pre>

任何一层都可能失效，因此后续层仍需限制影响并保留证据。门禁没有通过时不执行；执行结果与预期不符时停止后续步骤；证据链中断时进入人工处置。

## 常见失效

<table>
<thead>
<tr>
<th style="text-align: left;">失效</th>
<th style="text-align: left;">后果</th>
<th style="text-align: left;">修正</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">只在 Prompt 中声明权限</td>
<td style="text-align: left;">指令绕过后仍可调用工具</td>
<td style="text-align: left;">程序侧 allowlist、凭据和 Hook</td>
</tr>
<tr>
<td style="text-align: left;">审批只展示自然语言摘要</td>
<td style="text-align: left;">对象、数量或来源被隐藏</td>
<td style="text-align: left;">展示结构化动作合同和差异</td>
</tr>
<tr>
<td style="text-align: left;">Agent 持有长期生产凭据</td>
<td style="text-align: left;">单次错误跨任务扩散</td>
<td style="text-align: left;">短期凭据、环境隔离和作用域</td>
</tr>
<tr>
<td style="text-align: left;">留下日志但没有关联 ID</td>
<td style="text-align: left;">无法还原判断到副作用</td>
<td style="text-align: left;">统一 run/task/action 事件链</td>
</tr>
<tr>
<td style="text-align: left;">只升级自主权，不定义降级</td>
<td style="text-align: left;">事故后仍沿用原权限</td>
<td style="text-align: left;">可撤销配置和自动降级条件</td>
</tr>
<tr>
<td style="text-align: left;">Agent 可修改评测器和门禁</td>
<td style="text-align: left;">自我验证失去独立性</td>
<td style="text-align: left;">受保护的治理边界和双人审批</td>
</tr>
</tbody>
</table>

## 与 ADPS 模式的关系

- G1 审批门定义高风险动作的人类决策点；
- G2 爆炸半径控制限制错误可影响的范围；
- G3 渐进承诺管理权限和自主权升级；
- X1 可观测性 Harness 建立运行证据；
- G5 Hook 流水线执行模型外的确定性政策。

治理模式会与行动、记忆、协作和反思模式共同出现。模式选型需要落到具体动作、数据、权限和恢复路径上。

## 发布证据

系统进入生产前，建议至少提供：

1. 工具与凭据清单；
2. 高风险动作合同；
3. 审批和 Hook 的回放记录；
4. 影响范围与隔离测试；
5. 一条从提案到业务回执的完整事件链；
6. 停止、回滚和自主权降级演练。

治理的完成标准是控制可以运行、证据可以复核、异常可以处置。

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
<p><a href="https://adpsagent.com/zh/chronicle/#positions-governance-and-safety">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
