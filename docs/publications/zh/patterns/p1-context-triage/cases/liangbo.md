<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/p1-context-triage/" style="color: var(--color-text-muted);">P1 上下文分诊</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>P1 · 上下文分诊 · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">原始目标固定注入；里程碑台账根据当前任务投影为最小上下文。</p>
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
<td style="text-align: left;">P1 上下文分诊 Context Triage（感知 × 路由）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">M3 进度追踪 Progress Tracking</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/p1-context-triage/">/zh/patterns/p1-context-triage/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第六章 · PPT 第 25 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">在关键推理入口，根据当前任务从里程碑台账投影上下文；原始目标固定注入，历史进展按相关性裁剪。</td>
</tr>
</tbody>
</table>

---

## 场景约束

东方屹腾的一次完整任务会跨越意图识别、链式推理、ReAct、任务规划和工具执行，通常包含十余次模型调用。后段推理同时需要用户原始目标和前序进展，但不能加载全部历史。

单向传递“上一步输出”会逐步稀释原始目标。把全部会话和工具结果加入 Prompt，则会增加上下文长度，并使当前步骤需要的信息难以定位。上下文分诊负责在每个关键推理入口决定加载哪些叙事信息。

## 数据来源

叙事状态由三个部分组成：

| 数据 | 职责 | 读取策略 |
| --- | --- | --- |
| Anchor | 保存用户原始目标 | 每次关键推理固定加载 |
| Ledger | 追加关键里程碑摘要 | 持久化，不直接全量注入 |
| Collection | 当前步骤的 Ledger 投影 | 临时生成，用后释放 |

P1 处理的是从 Ledger 到 Collection 的读取决策。Ledger 如何写入和维护属于 [M3 进度追踪](https://adpsagent.com/zh/patterns/m3-progress-tracking/cases/liangbo/)。

## 分诊流程

<pre><code class="language-text">当前任务 + 推理阶段 + 上下文预算
  -&gt; 读取 Anchor
  -&gt; 筛选 Ledger 事件
  -&gt; 按相关性、时效和权限排序
  -&gt; 生成 Collection
  -&gt; 组装 ReasonContext
</code></pre>

Anchor 不参与压缩。Ledger 事件应保留类型、时间、任务节点、摘要和原始事实引用。Collection 根据当前步骤动态生成，同一份 Ledger 在规划、ReAct 和回复合成阶段会产生不同投影。

投影规则可以结合：

- 与当前目标和步骤的语义相关性；
- 事件是否改变任务状态或业务前提；
- 事件时效和来源可信度；
- 当前模型的上下文预算；
- 权限与敏感信息范围。

## 案例运行

用户在上一轮确认薪资组建议，下一轮只输入“继续”。当前输入本身不含完整目标。上下文组装器读取 Anchor 中的薪资组配置目标，再从 Ledger 中选择已完成的模板匹配、用户确认和快照状态摘要，生成当前 Collection。

模板 ID 不从 Collection 传入工具。Collection 只提供“模板已匹配”等语义进展，实际 ID 由机械状态平面读取。

## 失效信号

- Anchor 被摘要覆盖或没有进入后段推理；
- Ledger 已压缩，便被每次全量注入；
- Collection 是固定全局摘要，没有根据步骤变化；
- 投影只按语义相似度，遗漏状态变化和约束；
- 机械参数或任务调度状态把叙事投影当作真源；
- 用户输入“继续”后，任务无法恢复到原始目标。

## 验证指标

- 关键推理入口的 Anchor 注入率；
- Collection 中关键里程碑召回率；
- 无关事件占比和上下文 Token 数；
- 后段计划与原始目标的一致率；
- 因上下文缺失导致的重复执行和错误规划次数；
- 不同投影规则在真实长链路任务上的成功率和成本。

## 与白皮书的对应

P1 白皮书把上下文分诊定义为窗口分配问题：候选信息超过预算时，根据优先级和用途决定加载顺序。东方屹腾的 Anchor 对应固定优先级约束，Collection 对应按当前任务生成的上下文路由结果。

## 迁移条件

当单次任务跨多次模型调用，后段推理依赖原始目标和前序里程碑时，应采用上下文分诊。短链路单轮任务可以直接使用消息历史。若里程碑类型高度开放，需要先建立事件分类和来源元数据，再设计投影规则。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 上下文分诊》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-p1-context-triage-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
