<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/">模式矩阵</a><span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>G1</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>G1 · Approval Gate · 审批门</h1>
<p class="publication-deck">固定审批对象，并在暂停恢复后证明执行的仍是获批意图。</p>
</header>

审批门接收准备生效的具体意图：工具不可变版本、规范化参数、资源范围、委托身份和业务前置条件。

## 坐标与边界

**治理 × 路由。**同一个工具会因主体、参数、环境、影响和可逆性不同，进入 deny、allow 或 ask。动作怎样生成属于行动模块；获准后最多能影响多少由 G2 负责。

## 三份记录

<table><thead><tr><th>记录</th><th>内容</th><th>约束</th></tr></thead><tbody>
<tr><td><strong>Intent</strong></td><td>Agent、run、工具摘要、参数、资源、策略版本与前置条件</td><td>实质变化后生成新意图</td></tr>
<tr><td><strong>Approval</strong></td><td>审批人、决定、依据、有效期、可用次数与 Intent 摘要</td><td>只批准一个明确对象</td></tr>
<tr><td><strong>Execution</strong></td><td>执行前复验、幂等键、实际调用、状态差异与外部回执</td><td>证明执行对象与获批对象一致</td></tr>
</tbody></table>

<pre><code class="language-yaml">intent:
  tool_digest: sha256:4ef...
  parameters_ref: artifact://intent/int_01/params
  resource_scope: {tenant: tenant_42, max_records: 20}
  policy_version: payroll-v12
  preconditions: {ledger_version: 417}
approval:
  intent_digest: sha256:93a...
  expires_at: 2026-08-19T09:30:00Z
  max_uses: 1
execution:
  idempotency_key: payrun-2026-08-batch-17
</code></pre>

参数先规范化再计算摘要。字段顺序、默认值、时区和金额精度没有统一时，摘要无法可靠表达“同一个意图”。

## 有序裁决

1. 确定性规则处理硬拒绝、明确放行和必须人审的条件。
2. 模型分类器补充难以穷举的上下文，输出风险与理由，不签发权限。
3. 策略引擎结合身份、参数、资源和环境形成结构化裁决。

冲突顺序必须写进策略。高风险链路在策略服务不可用、无人审批或超时后通常应停止，不能依赖异常分支偶然放行。

## 暂停后怎样恢复

```
DRAFT → EVALUATING → DENIED
                  ↘ ALLOWED → EXECUTING → CONSUMED
                  ↘ PENDING → APPROVED → REVALIDATING → EXECUTING
                                      ↘ EXPIRED / INVALIDATED
```

恢复时检查 Intent 摘要、工具与策略版本、审批有效期、单次消费状态和业务前置条件。日志时间变化通常无关；金额、收款账户、目标资源版本或风险等级变化通常需要重新裁决。具体字段由业务域定义。

## 运行实例

薪酬 Agent 准备提交 18 人付款批次。策略检测到一个刚变更的收款账户，审批界面展示账户差异、总金额、来源账本和风险原因。等待期间又有一笔金额被修正，账本版本变化。恢复时旧批准失效，系统生成新 Intent。新批准被原子消费一次，付款 API 的批次号和状态差异进入 Execution。

## 常见失效

- 只审批工具名或自由文本摘要；
- 批准没有过期、撤销和单次消费；
- 模型风险分直接变成 allow；
- 重试、异步回调或恢复路径绕开审批；
- 审批界面看不到参数来源、资源差异和实际影响。

## 验证

测试参数篡改、策略换版、审批过期、并发消费、重复回调、前置条件变化和审批服务故障。生产观测至少覆盖获批摘要与执行摘要的一致性、旧审批拦截、高风险旁路和低风险误入人审。

## 相邻规范

[G2](https://adpsagent.com/zh/patterns/g2-blast-radius-control/)限制获准动作的最大影响；[G3](https://adpsagent.com/zh/patterns/g3-progressive-commitment/)提供能力级自治档位；[X1](https://adpsagent.com/zh/patterns/x1-observability/)连接 Intent、Approval、Execution 与回执；[G5](https://adpsagent.com/zh/patterns/g5-hooks-pipeline/)提供调用前和恢复前的执行位置。

<!-- RELATED-CASE-DEERFLOW:START -->

<section aria-labelledby="related-deerflow-case" class="related-case-band">
<p class="related-case-label">相关开源工程案例</p>
<h2 id="related-deerflow-case"><a href="https://adpsagent.com/zh/cases/deerflow-guardrail/">DeerFlow：从调用前拦截到双层授权</a></h2>
<p>姜宁分享的 Guardrail 演进以五个公开 PR 为证据，展示装配过滤、运行时授权、身份、策略和审计怎样进入同一条工具执行路径。</p>
</section>

<!-- RELATED-CASE-DEERFLOW:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《G1 · Approval Gate · 审批门》，Agent 设计模式白皮书 v0.4，2026-08-19。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>使用边界：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；运行实例用于说明机制，具名实践另见案例库。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-g1-approval-gate">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
