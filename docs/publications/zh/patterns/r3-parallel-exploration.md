<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>R3
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>R3 · Parallel Exploration · 并行探索</h1>
<p class="publication-deck">对同一查询运行 N 条相互隔离的推理链，并按错误代价选择聚合策略。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">推理 Reasoning × 并行 Parallel（撒）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">高（多分支执行加聚合）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">推理模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">对同一查询运行 N 条相互隔离的推理链，并按错误代价选择聚合策略。</td>
</tr>
</tbody>
</table>

---

## 问题

单条推理链有"侥幸偏差"：同一个提示、同一个模型，不同采样得到的答案不一定一致。一条链刚好走偏，整个结论就错了，而且每一步看上去都对——错误藏在"这一次恰好没抓到的那个特征"里，事后复盘很难发现。

并行探索同时运行多条独立推理链，再聚合为单一结果。它适用于错误代价足以覆盖额外计算的场景，可以与复杂度路由（R2）组合：普通请求按复杂度分档，高风险节点再启动并行分支。质量增益与计算开销都要在同一评测集上报告。

## 坐标说明：推理 × 并行

- **纵轴 · 推理**：并行的实体是*同一个推理任务的多条候选路径*（多个 candidate solution），属于推理策略层，而不是把任务拆给多个 Agent。这是它和协作模块"扇出聚合（C2）"的根本区别——后者并行的是子任务，前者并行的是同一道题的多个解法。
- **横轴 · 并行**：N 条分支同时跑、互不知情，最后统一聚合，是天然的并行结构，不是链式串联，也不是循环迭代。

## 解决方案与机制

一次并行探索由三段组成：

1. **分发**：把同一个查询复制成 N 条分支，通过不同提示、采样参数、模型或证据源制造多样性。N 由任务风险、分支相关性和成本预算决定，应通过本地消融实验寻找拐点。
2. **隔离执行**：每条分支跑在独立的执行环境里（独立的模型客户端、独立的中间状态、独立的错误恢复）。分支之间串扰会让"独立采样"退化成"链式错误传染"，准确度不升反降。
3. **聚合**：按业务错误代价选择多数投票、Any-Alarm、加权评分或模型评审，将 N 个结果合成为一个。

聚合策略的选择取决于业务"错的代价分布"：

<table>
<thead>
<tr>
<th style="text-align: left;">聚合策略</th>
<th style="text-align: left;">适用场景</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">多数投票 Majority</td>
<td style="text-align: left;">答案可枚举、错误代价对称（数学、分类）</td>
</tr>
<tr>
<td style="text-align: left;">加权投票 Weighted</td>
<td style="text-align: left;">不同分支可信度不同（不同模型 / 不同算力档）</td>
</tr>
<tr>
<td style="text-align: left;">评委裁定 Verifier</td>
<td style="text-align: left;">开放式答案（写作、代码、规划）</td>
</tr>
<tr>
<td style="text-align: left;">第一个达标 First-Correct</td>
<td style="text-align: left;">有明确成功判据（测试驱动）</td>
</tr>
<tr>
<td style="text-align: left;">任一警报即升级 Any-Alarm</td>
<td style="text-align: left;">高风险且错误代价不对称（医疗、金融、安全）</td>
</tr>
</tbody>
</table>

## 适用场景

- **高风险、错误代价不对称的判断**：医疗影像分诊、金融风控、反洗钱、安全漏洞审查。这类场景"漏判"远比"误判"贵，配合 Any-Alarm 聚合即可把不对称代价表达进系统。
- **答案空间大、单链不稳的推理**：复杂诊断、多跳推理、需要 self-consistency 提升可靠性的任务。
- **关键的一次性决策**：不可逆业务承诺前的最终复核等节点，可以使用 N 倍算力换取更高可靠性。

## 已知失效方式

- **分支不独立**：N 条分支共享执行环境，相互污染缓冲区或 retry，"伪独立"导致准确度反降。必须给每条分支独立的运行时。
- **提示扰动不足**：多个分支跑出几乎一样的答案时，并行探索退化成重复采样，相应的计算也没有换来新的证据。应检查采样参数、提示差异、模型与证据源是否真正独立。
- **盲目默认多数投票**：在错误代价不对称的场景用 Majority，会把少数分支的真实警报投没——医疗里这等于漏诊。
- **该收齐却早终止**：Any-Alarm 必须等所有分支返回，不能用"高置信度早终止"省钱，否则会漏掉警报信号。早终止只适用于对称代价场景。
- **低风险任务使用过多分支**：单链已经满足要求时，增加分支只会带来额外开销。应与单链基线比较后再决定是否启用。

## 验证指标

- **分支一致率**：观察各分支结论的一致程度，并结合任务难度解释。高度一致可能表示任务简单，也可能表示分支缺少真正独立性。
- **有效 N**：N 条分支产生多少种独立证据路径或结论。有效 N 长期偏低时，应先改变提示、模型或数据源，而不是继续增加分支。
- **聚合成本占比**：聚合步骤在总成本和延迟中的占比。相对本地基线过高时，改用更轻的聚合器或更严格的分支 artifact。
- **质量增量**：在同一评测集上比较并行与单链，并同时报告成本和延迟。没有稳定增益时，应关闭并行或修正分支独立性。

## 最小实现

```
对 query 复制 N 条分支：
    每条分支 → 独立运行时 → 不同 temperature 采样 → (answer, confidence)
聚合(N 个结果, 策略):
    Majority   → 票数最多的答案
    Weighted   → 按 confidence 加权后最高的答案
    Verifier   → 交给独立评委模型打分裁定
    Any-Alarm  → 任一分支命中高风险标签即升级，无视多数
返回 final_answer + 完整分支 trace（每路答案/置信度/聚合策略/最终决策）
```

生产实现应通过提示、采样参数、模型或证据源差异形成分支多样性；评委模型需在目标任务上评测；并发调用复用连接池并遵守 provider 限制；Any-Alarm 模式禁止早终止。

## 场景化示例

设想一个医疗影像辅助 Agent 对肺结节给出分级建议。单链可能遗漏某种可疑形态。系统改为多路独立评估，并让分支使用不同提示或证据视角；聚合器不采用简单多数票，而是执行 Any-Alarm 规则：任一路发现预先定义的高风险形态，就进入人工二次评审。各分支使用独立运行时，禁止在其他分支尚未完成时提前结束；trace 按机构的医疗数据与审计政策留存。准确率与资源开销必须在经审批的临床评测集上报告。

## 相邻模式

- **复杂度路由（R2）**：日常请求按复杂度路由，高风险决策可以启动并行探索。
- **思维链（R1）**：并行的每一条分支内部通常就是一条思维链；并行是在 R1 之上叠加的"多采样"。
- **扇出聚合（C2）**：结构同源、聚合机制相通，区别在并行的实体——R3 是同一道题的多条解法（推理策略），C2 是不同子任务分给不同 Agent（协作拓扑）。
- **迭代假设验证（R4）**：对偶关系。并行是空间维度同时开 N 条线，迭代是时间维度一条线跑多次。

## 工程判断

并行探索的聚合策略需要反映业务对不同错误的代价。多数投票、any-alarm 和 verifier-judge 对应不同的容错假设，不能互相替代。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《R3 并行探索》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-r3-parallel-exploration">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
