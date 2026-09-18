<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/">模式目录</a><span style="margin: 0 0.45rem;">/</span>横切工程面<span style="margin: 0 0.45rem;">/</span>X1</p>

<header class="publication-head">
<p class="publication-series">ADPS 横切工程面规范</p>
<h1>X1 · Observability · 可观测性</h1>
<p class="publication-deck">以事件、因果、版本、状态差异和外部回执建立 Agent 证据链。</p>
</header>

**事件、因果、版本和外部结果**是 X1 的四个支点。事件保存最小事实，因果关系连接跨 Agent 与工具的调用，版本说明当时实际运行的组件，外部结果确认现实世界是否真的发生变化。缺少其中任何一项，日志都很难支撑复盘、评测和责任归因。

X1 用统一事件、因果标识、版本引用、状态差异和外部回执，把一次运行组织成可以查询、评测和归因的证据链。

## 位置

可观测性贯穿七个认知功能、六种执行拓扑和完整生命周期，不占用双轴矩阵格位。旧编号 G4 仅作为历史入口保留，当前规范编号为 X1。

## 从日志到证据

<table><thead><tr><th>观察面</th><th>需要保留的事实</th><th>用途</th></tr></thead><tbody>
<tr><td>输入与上下文</td><td>来源、版本、准入和丢弃原因</td><td>还原 Agent 当时能看到什么</td></tr>
<tr><td>决策与计划</td><td>目标、步骤、路由、候选和裁决摘要</td><td>分析漂移、路由和计划错误</td></tr>
<tr><td>动作与控制</td><td>工具、参数来源、身份、策略、审批和配额</td><td>审计与调用级归因</td></tr>
<tr><td>状态与结果</td><td>状态差异、外部回执、业务验收与人工修订</td><td>识别假成功和真实影响</td></tr>
<tr><td>运行基础</td><td>模型、提示词、Skill、知识、工具和策略版本</td><td>版本比较与回归定位</td></tr>
</tbody></table>

结构化决策摘要、候选、引用、工具调用和状态变化适合作为运行证据。完整隐式推理既不稳定，也会扩大敏感信息风险。

## 因果与身份链

```
principal → agent → workload → session → run → intent
          → approval → model/tool/sub-agent span → resource → outcome
```

Trace Context 负责跨进程传播，业务对象仍需要稳定 ID。一次重试可以产生新 span，不能因此生成新的业务意图或重复副作用。

## 生命周期中的证据

<table><thead><tr><th>阶段</th><th>重点</th></tr></thead><tbody>
<tr><td>登记与设计</td><td>负责人、能力版本、事件合同、敏感字段与保留周期</td></tr>
<tr><td>评测与灰度</td><td>样本、轨迹、版本差异、拒绝与回滚原因</td></tr>
<tr><td>运行</td><td>调用链、状态变化、外部结果、延迟、成本与策略裁决</td></tr>
<tr><td>复验与演进</td><td>故障簇、修改预测、回归结果、升降级与退役证据</td></tr>
</tbody></table>

## 常见失效

- 记录大量文本，却没有对象 ID、版本和状态差异；
- 把 HTTP 200 或 exit code 0 当成业务成功；
- 跨 Agent、队列和回调断链；
- 采样集中在简单任务；
- 敏感 prompt 和凭证无限留存；
- 把 X2 的评分判断混入 X1 的观测事实。

## 验证

检查 trace 连续性、身份与版本完整度、有副作用动作的外部结果确认、孤儿写操作、证据时延、采样偏差和敏感证据访问。覆盖跨进程、重试、恢复、模型 fallback、schema 升级和 collector 故障。

## 公开实现

[DeerFlow Guardrail](https://adpsagent.com/zh/cases/deerflow-guardrail/)展示身份、授权裁决、RunJournal 与工具执行之间的公开代码路径。业务状态差异和外部结果由接入方补充。

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《X1 · Observability · 可观测性》，ADPS 横切工程面规范 v0.5，2026-08-20。</p>
<p><a href="https://adpsagent.com/zh/topics/observability-driven-evolution/">可观测性专题</a> · <a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>使用边界：</strong>本页定义工程范围与接口，不构成产品认证。具名实践以案例页与公开代码为准。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-20">2026-08-20</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-x1-observability">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
