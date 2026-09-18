<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>R2
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>R2 · Complexity-Based Routing · 复杂度路由</h1>
<p class="publication-deck">在查询进入主循环前，根据复杂度和风险选择模型、reasoning effort 与回退路径。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">推理 Reasoning × 路由 Route（选）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（增加一次路由判断，换取按任务分配模型资源）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">推理模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">在查询进入主循环前，根据复杂度和风险选择模型、reasoning effort 与回退路径。</td>
</tr>
</tbody>
</table>

---

## 问题

把能力最强、成本最高的模型作为所有请求的默认选项，会让模板填充和简单查询占用与复杂推理相同的资源。模型价格和能力会持续变化，路由设计应比较当前候选模型在本地任务集上的质量、延迟和成本，而不是依赖一张固定价差表。

复杂度路由按照输入难度和风险分配模型资源。简单查询进入低成本档，复杂或高风险查询进入高能力档。节省幅度取决于真实流量分布和模型组合，需要用生产 trace 回放计算。复杂度路由可以与并行探索（R3）同时使用：前者控制日常请求的资源分配，后者用于高风险决策的多路验证。

## 坐标说明：推理 × 路由

- **纵轴 · 推理**：路由选择 reasoning policy，包括模型能力、effort 和回退策略；它不负责把任务拆给多个 Agent。
- **横轴 · 路由**：按输入的复杂度信号，把不同查询分发到不同的 reasoning depth（模型档 + effort 档）。这是天然的分支选择结构，一个查询进来选一条路走。

## 解决方案与机制

一次复杂度路由由三段组成：

1. **提取信号 + 分类**：从查询里提取复杂度信号（长度、关键词、领域、历史成功率），交给 classifier 判定走哪一档。classifier 可使用规则或低成本模型，路由本身的开销需要纳入总成本和延迟评测。
2. **分档执行**：按照本地评测结果设置多个能力与成本档位，各档共用同一套调用接口。路由既可以选择模型，也可以选择模型的 effort 档位。
3. **升档兜底**：低成本档返回后检查 schema、证据和业务约束，不达标就升档重试。升档链必须有配置上限，到顶仍不合格时应报错或转人工。

生产系统常见三条路由路线，团队可按流量形态和风险选择：

<table>
<thead>
<tr>
<th style="text-align: left;">路线</th>
<th style="text-align: left;">形态</th>
<th style="text-align: left;">取舍</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">模型层内化</td>
<td style="text-align: left;">模型自己决定走快路径还是慢路径</td>
<td style="text-align: left;">省事，但黑盒 + 单厂商绑定</td>
</tr>
<tr>
<td style="text-align: left;">Harness 显式做</td>
<td style="text-align: left;">应用层自己写 classifier + fallback</td>
<td style="text-align: left;">工程量大，但可 log、可审计、可多厂商</td>
</tr>
<tr>
<td style="text-align: left;">第三方 router 服务</td>
<td style="text-align: left;">调中间层 API 自动分发</td>
<td style="text-align: left;">接口最简单，但多一层依赖 + 数据过第三方</td>
</tr>
</tbody>
</table>

需要控制成本、风险和多厂商策略的生产 Agent 通常采用 Harness 显式路由。PoC 和小型项目可以使用模型原生路由或托管路由。

## 适用场景

- **简单请求占多数且成本敏感**：内部 BI 自助查询、客服问答和文档处理通常包含大量简单请求，适合按复杂度分档。
- **多厂商混用场景**：团队同时用 Claude / DeepSeek / 自家微调模型，没法把路由交给单一厂商，必须工程层做。
- **按动作类型分流的专门 Agent**：代码改动用主模型、git 操作用 weak 模型这类，按动作而非按查询复杂度路由，是路由思路的一个变体。

## 已知失效方式

- **classifier 只用固定规则**：关键词匹配对未见查询形态泛化较差，可能把复杂查询错判到低能力档。可以增加低成本模型分类或不确定性升档，并用回放集比较误路由成本。
- **acceptable 校验只看长度**：只检查输出够不够长，放过了 schema 不符、数值越界、引错源数据的结果。要做 schema-aware 校验。
- **fallback 比直接走贵档更贵**：便宜档先跑一遍不达标再升贵档，总成本反而高于一开始就走贵档。fallback rate 一高就得查 classifier 是不是失准了。
- **高风险查询进入低成本档**：财务、隐私和合规查询即使形式简单，也应由风险规则强制进入高可靠档。
- **单模型团队硬上路由**：只用一个模型、或任务永远同一类、或便宜模型已经够用的场景，路由没有意义。

## 验证指标

- **每查询成本分布**：按路由档位和任务类型观察成本长尾。高能力档占比变化时，区分业务输入变难与 classifier 误路由。
- **路由准确率**：使用人工标注或强 reviewer 判断所选档位是否满足任务要求，并单独统计高风险任务的降档错误。
- **升档率 Fallback Rate**：低成本档触发升档的比例。指标变化时检查分档规则、模型能力和输入分布，并重算成本与质量。
- **路由决策时间**：观察 classifier 给总延迟增加的开销。路由判断过重时，可改用规则预筛、缓存或异步特征。

## 最小实现

```
查询进来 → 提取复杂度信号（长度 / 关键词 / 领域 / 历史）
classifier（便宜模型或规则）→ 选定档位 + 置信度
高风险查询（财务 / 隐私 / 合规）→ 强制最贵档，跳过分流
执行：
    便宜档跑 → 结果可接受？→ 返回
              不可接受 → 升档（schema 校验 + 成本估算）
    升档链达到配置上限，仍不合格 → 报错 / 转人工
每次路由决策打 trace（查询摘要 / 档位 / 信号 / 置信度 / 实际成本 / 是否升档）
```

生产实现可使用低成本模型完成 classifier；acceptable 校验需要识别 schema；fallback 链设置成本上限；反复升档的查询类型可直接调整默认档位。

## 场景化示例

设想一个内部数据分析 Agent 同时服务产品、增长和财务团队。生产 trace 显示，部分请求只是 SQL 模板填充或增加分组，另一些需要多步归因或因果分析。第一版全部使用最高能力模型，无法解释资源是否花在了真正困难的任务上。

改造后，系统按模板查询、聚合分析、归因分析和高复杂度推理分档；classifier 使用规则预筛加低成本模型判断；升档前估算本次调用的总成本；财务、隐私和合规查询按风险规则强制进入高能力档；每次路由保留 trace，并定期回放误路由样本。实际节省和质量变化由这批 trace 计算，不预设行业通用比例。

## 相邻模式

- **并行探索（R3）**：路由在单个时间点选择一档，并行探索同时运行 N 个候选分支。日常请求可使用路由，高风险节点再启动并行验证。
- **思维链（R1）**：路由选的档位里就含 CoT 的 effort 档，路由是 CoT effort 控制从单次调用上升到任务级的版本。
- **双模架构（R5）**：普通路由选择单一档位；双模架构同时运行 Talker 和 Reasoner 两个档位。
- **失败日记 / 护栏类模式**：高风险查询强制走最稳档，和"有些边界不能省钱"的防护思路同源。

## 工程判断

复杂度路由在 token、延迟和质量之间选择满足业务 SLA 的运行点。路由策略属于产品成本与服务等级设计，需要用真实流量持续校准。

## 企业证据

以下现场记录说明该模式在具体业务约束下如何实现。案例结论只在文中声明的系统边界内成立。

<ul style="list-style: none; margin: 0.5rem 0 1rem 0; padding: 0;">
<li style="margin-bottom: 0.6rem; line-height: 1.55;"><a href="https://adpsagent.com/zh/patterns/r2-complexity-based-routing/cases/liangbo/" style="font-weight: 600;">东方屹腾 · 复杂度路由</a><span style="color: var(--color-text-muted);"> — 入口分类器生成有限控制信号，意图网关按成本和风险选择执行链。</span></li>
</ul>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《R2 复杂度路由》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">参考实现</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>文档状态：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；场景化示例用于说明机制，不代表已经核验的企业案例。具名实践另见<a href="https://adpsagent.com/zh/cases/">案例库</a>。ADPS 欢迎业界提交带来源、测量口径和发布授权的案例。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-r2-complexity-based-routing">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
