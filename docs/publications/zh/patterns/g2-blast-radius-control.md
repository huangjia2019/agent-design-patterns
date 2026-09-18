<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/">模式矩阵</a><span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>G2</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>G2 · Blast Radius Control · 爆炸半径控制</h1>
<p class="publication-deck">用硬边界与动态自治范围限制一次动作、一段运行和一组 Agent 的最大影响。</p>
</header>

爆炸半径控制假设审批、模型和工具都会出错，提前规定一次错误最多能改变多少资源、消耗多少预算、传播到多少下游。

## 坐标与边界

**治理 × 层级。**身份包住能力，能力包住资源，资源再受数量、速率、时间、成本、并发和网络上限约束。多层防线只有在凭证、进程和配置入口真正分离时才具有独立价值。

## Hard Envelope 与 Autonomy Envelope

<table><thead><tr><th>边界</th><th>内容</th><th>变更权</th></tr></thead><tbody>
<tr><td><strong>Hard Envelope</strong></td><td>租户隔离、生产凭证、绝对金额、禁止工具与数据类别</td><td>独立管理面或明确人工流程</td></tr>
<tr><td><strong>Autonomy Envelope</strong></td><td>批量、频率、对象集合、工具、并发和自动化档位</td><td>在硬边界内随证据和场景收放</td></tr>
</tbody></table>

```
effective_scope = intersect(
    hard_envelope,
    principal_scope,
    task_scope,
    capability_scope,
    current_context_scope,
    evidence_based_scope
)
```

每次委派只能保持或缩小范围。子 Agent 不得取得父 Agent 没有的工具、资源、预算或时长。

## 需要聚合的维度

数量、速率、成本和并发不能只按单个工具计算。十个子 Agent 各自低于 100 条，整个 run 仍可能写入 1000 条。限额至少要在 action、run、principal、tenant 和 fleet 中选择合适层级聚合。

<table><thead><tr><th>维度</th><th>控制例子</th></tr></thead><tbody>
<tr><td>资源与数据</td><td>租户、账户、环境、对象集合、字段和用途</td></tr>
<tr><td>数量与速率</td><td>每次、每批、每个 run、每个租户和时间窗口</td></tr>
<tr><td>成本与时间</td><td>token、云资源、外部采购、凭证有效期和任务时长</td></tr>
<tr><td>并发与传播</td><td>子 Agent 数、调用深度、并发写入和下游接收者</td></tr>
<tr><td>恢复</td><td>dry-run、延迟提交、checkpoint、幂等、补偿和熔断</td></tr>
</tbody></table>

## 运行实例

一批 18 人的薪酬付款已经通过 G1。G2 仍限定单租户、单次 20 条、run 累计 40 条、一个并发写入、Intent 金额上限和更高一级的基础设施绝对上限。重试创建第二批时，幂等键与 run 级限额同时阻断；目标账户换成其他租户时，资源边界先行拒绝。

## 多 Agent 与编舞

中心编排可直接累计预算；编舞需要共享的 run、principal、委托链和剩余额度。局部 Agent 限额会在扇出、重试和循环中被放大，因此还要限制子 Agent 数量、委派深度和跨域传播。

## 常见失效

- 把沙箱当成完整业务边界；
- 用 per-tool 限额替代 run 或 tenant 总额；
- Agent 可以改写自己的硬上限；
- 停止开关与 Agent 共用凭证；
- 只在正常路径限界，重试与恢复绕过；
- POST 才发现不可逆越界。

## 验证

通过故障注入测量最坏对象数、金额、成本和传播范围；演练熔断时延；验证并发、重试和子 Agent 下的累计口径；确认 Agent 无权修改 limiter、kill switch 和证据。

## 相邻规范

[A5](https://adpsagent.com/zh/patterns/a5-minimal-tool-set/)缩小能力面，[C5](https://adpsagent.com/zh/patterns/c5-sub-agent-isolation/)隔离子 Agent，[G3](https://adpsagent.com/zh/patterns/g3-progressive-commitment/)只在硬边界内调整自治范围。

<!-- RELATED-CASE-DEERFLOW:START -->

<section aria-labelledby="related-deerflow-case" class="related-case-band">
<p class="related-case-label">相关开源工程案例</p>
<h2 id="related-deerflow-case"><a href="https://adpsagent.com/zh/cases/deerflow-guardrail/">DeerFlow：从调用前拦截到双层授权</a></h2>
<p>姜宁分享的 Guardrail 演进以五个公开 PR 为证据，展示装配过滤、运行时授权、身份、策略和审计怎样进入同一条工具执行路径。</p>
</section>

<!-- RELATED-CASE-DEERFLOW:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《G2 · Blast Radius Control · 爆炸半径控制》，Agent 设计模式白皮书 v0.4，2026-08-19。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-g2-blast-radius-control">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
