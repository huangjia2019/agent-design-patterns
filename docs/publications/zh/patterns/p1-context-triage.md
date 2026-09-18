<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>P1
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>P1 · Context Triage · 上下文分诊</h1>
<p class="publication-deck">候选信息超出 context 窗口预算时，按优先级决定加载、压缩、延迟获取或丢弃。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">感知 Perception × 路由 Route（选）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（一次轻量优先级判断，不额外起推理链）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">感知模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">候选信息超出 context 窗口预算时，按优先级决定加载、压缩、延迟获取或丢弃。</td>
</tr>
</tbody>
</table>

---

## 问题

生产级 Agent 通常同时接入代码、会话历史、工具返回和企业知识库。这些候选信息很容易超过模型的有效窗口。按文件名或时间顺序直接截断，可能保留过期材料并删除关键证据，使 Agent 基于不完整输入作出判断。

上下文分诊把候选信息划分为 P0/P1/P2/P3 四级，在单次请求的 token 预算内依次加载，并记录延迟获取和丢弃项。其目标是优先保留影响当前决策的证据。

## 坐标说明：感知 × 路由

- **纵轴 · 感知**：分诊决定 Agent 看什么、不看什么，是感知端的注意力管理。它处理的是信息进入推理之前的环节，不是输出格式的调整，也不是跨会话的记忆。
- **横轴 · 路由**：不同优先级的信息走不同处理路径——高优进 context、中优压成摘要、低优只挂句柄等按需拉取。这是基于信息特征做的一次路由决策，不是链式串联也不是循环迭代。

## 解决方案与机制

一次分诊把候选信息按优先级分层，再用 token 预算来分配各层额度：

<table>
<thead>
<tr>
<th style="text-align: left;">级别</th>
<th style="text-align: left;">典型内容</th>
<th style="text-align: left;">加载策略</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">P0 永远加载</td>
<td style="text-align: left;">system prompt、安全规则、当前任务、业务身份（tenant_id）</td>
<td style="text-align: left;">先预留预算，不能被普通材料挤出</td>
</tr>
<tr>
<td style="text-align: left;">P1 有空间就加载</td>
<td style="text-align: left;">当前文件、最近 tool 结果、错误堆栈</td>
<td style="text-align: left;">按当前任务的重要性加载</td>
</tr>
<tr>
<td style="text-align: left;">P2 压缩后加载</td>
<td style="text-align: left;">历史对话、背景文档</td>
<td style="text-align: left;">先摘要，再按剩余预算加载</td>
</tr>
<tr>
<td style="text-align: left;">P3 只挂句柄</td>
<td style="text-align: left;">可访问但不预加载的资源</td>
<td style="text-align: left;">不预占正文预算，通过工具按需拉取</td>
</tr>
</tbody>
</table>

优先级可以来自人工规则，也可以由算法计算。Claude Code 的 CLAUDE.md hierarchy 属于人工分诊，开发者可将安全规则置于 P0、个人偏好置于 P2；Aider RepoMap 使用 tree-sitter 提取符号并按代码图打分，属于算法分诊。错误堆栈应跨级保护，因为后续修复和回归依赖其中的反馈。每次分诊还需要记录 trace，以区分“候选信息未被发现”和“已发现但被延迟或丢弃”。

## 适用场景

- **多租户 SaaS 客服 Agent**：一个 Agent 服务多家租户，各自知识库合计远超窗口。tenant\_id 必须做成 P0 硬约束，其余知识按四级分诊。
- **面对陌生 codebase 的代码 Agent**：用户每次给一个不同仓库，无法要求每人都写 CLAUDE.md，必须走算法自动符号抽取这条路。
- **长期服务同一团队的工程 Agent**：团队可以用 CLAUDE.md 明确安全规则、项目约束和加载优先级，再由算法补充动态分诊。
- **接入文件系统或知识库的长任务 Agent**：只要候选信息可能超窗，就需要显式分诊。

## 已知失效方式

- **优先级误判**：把关键文件标成 P3 后，Agent 会在推理中途重新检索，既增加调用开销，也提高级联错误风险。拿不准时可暂时升级，并通过重读记录校准规则。
- **分诊过激**：为省 token 把 budget 卡得太死，关键依赖链全被挂起，Agent 反复"我需要再读一下这个文件"，重读率（re-read ratio）飙升——省下的 token 又被重读耗回去。
- **P3 句柄命名含混**：`doc://manual-page` 这种名字让 Agent 不知道该不该取。句柄名要自带“是什么”信号，可采用“层级 + 主题 + 时间”的结构。
- **跨租户串数据**：P3 句柄取错租户的数据塞进 context 就是数据泄露事件。带租户前缀的资源在加载时必须强制校验与 P0 tenant\_id 一致。
- **trace 被采样掉**：低比例随机采样可能漏掉持续发生在少数租户上的边界问题。涉及租户隔离和安全决策的分诊 trace 应完整保留，并用结构化字段控制存储量。

## 验证指标

- **重读率 re-read ratio**：Agent 推理中途重新读取已挂起材料的比例。相对自身基线持续上升，通常说明分诊过激或句柄描述不清。
- **dropped\_count 的长尾分布**：均值会掩盖少量请求中大量材料被丢弃的问题，应结合任务类型和失败 trace 检查长尾。
- **P3 命中率 p3\_hit\_rate**：P3 句柄中实际被取用的比例。长期偏低时应缩小句柄池，长期偏高时应检查是否把常用材料错降到 P3。阈值需依据本地任务分布校准。

## 最小实现

```
对候选信息按优先级排序（P0 > P1 > P2 > P3，错误堆栈额外加分）：
    逐条塞入：
        P3            → 进句柄池，不预加载
        其余 + 未超预算 → 进 context，累加 token
        其余 + 超预算   → 丢弃（但错误堆栈强制保留）
返回 (进 context 的, 挂句柄的, 一条 TriageDecision)
TriageDecision 留下：时间戳 / 预算 / selected / deferred / dropped / tokens_used
```

生产实现应使用真实 tokenizer，避免 `len // 4` 对中文造成较大误差；错误识别规则需要按业务领域扩展；TriageDecision 应写入 ELK、Datadog 等可观测系统，并持续监测 dropped\_count。

## 场景化示例

设想一个贷款评审 Agent 同时收到当前财报、抵押物估值、历史登记材料和往来说明。若系统按文件名截断，当前估值可能被删除，过期登记材料却留在 context 中。四级分诊会优先保护当前财报、抵押物估值和“异常/缺失”标记，历史材料按时效降级，并为未加载内容保留可追溯句柄。这里要检查的是输入选择是否完整，而不是先讨论模型的推理能力。

## 相邻模式

- **语义压缩（P2）**：互补且常配合。分诊管"哪些信息进 context"（未来 token），压缩管"已经进的怎么压不丢关键"（过去 token），P2 级"压缩后加载"正是两者的衔接点。
- **渐进发现（P3）**：分诊的 P3 句柄可作为渐进发现按需获取的对象；前者筛选已有候选，后者主动搜索未知信息。
- **分层记忆（Memory 模块）**：共用同一套句柄命名规范，但 TTL 不同。代码、文档类句柄永远指向当前版本归分诊管；用户偏好、对话状态类有版本演化归记忆管。建议把 P3 句柄分 `immutable://` 和 `versioned://` 两类标记。

## 工程判断

上下文分诊把 context window 作为受限资源管理。优先级、预算和 trace 共同保证关键材料不会在截断或压缩时被淘汰。

## 企业证据

以下现场记录说明该模式在具体业务约束下如何实现。案例结论只在文中声明的系统边界内成立。

<ul style="list-style: none; margin: 0.5rem 0 1rem 0; padding: 0;">
<li style="margin-bottom: 0.6rem; line-height: 1.55;"><a href="https://adpsagent.com/zh/patterns/p1-context-triage/cases/liangbo/" style="font-weight: 600;">东方屹腾 · 上下文分诊</a><span style="color: var(--color-text-muted);"> — 原始目标固定注入；里程碑台账根据当前任务投影为最小上下文。</span></li>
</ul>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《P1 上下文分诊》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-p1-context-triage">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
