<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>C2
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>C2 · Fan-out / Gather · 扇出聚合</h1>
<p class="publication-deck">Orchestrator 将独立子任务并行分发给 N 个 sub-agent，再由 Aggregator 去重、消解冲突并合并结果。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">协作 Collaboration × 并行 Parallel</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">高（并行 Worker 调用加聚合）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">协作模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">Orchestrator 将独立子任务并行分发给 N 个 sub-agent，再由 Aggregator 去重、消解冲突并合并结果。</td>
</tr>
</tbody>
</table>

---

## 问题

有些任务由单 Agent 顺序执行无法满足业务窗口，例如季报披露前的大批量财务文档扫描。前提是各分片能够独立处理，并且最终结果可以可靠聚合。

扇出聚合将大任务切分为可独立执行的子任务，并行分发给 N 个 sub-agent。token 成本通常随 Worker 数量增加，wall-clock 时间则可以缩短。多个 Worker 的输出可能重叠或冲突，Aggregator 需要执行去重、概念归一和冲突消解。

## 坐标说明：协作 × 并行

- **纵轴 · 协作**：这是把一个任务拆给多个 sub-agent 并行做再汇总，分发的实体是不同的子任务，属于多 agent 协作拓扑。区别于推理模块的并行探索——后者并行的是同一道题的多条解法（推理策略），前者并行的是切给不同 agent 的不同子任务（协作拓扑）。
- **横轴 · 并行**：N 个 sub-agent 同时跑、互不知情，最后统一 gather，是经典的 map-reduce 式并行结构。不是顺序串联，也不是循环迭代。

## 解决方案与机制

一次扇出聚合由三段组成：

1. **切分扇出**：按语义独立性将大任务切成 N 份并行分发。子任务之间不能存在输出依赖；存在顺序依赖时应使用交接链。
2. **隔离执行**：每个 sub-agent 跑在独立 context 里完成自己的子任务，互不通信。隔离强度跟输出冲突可能性成正比——各查不同语料的研究任务用软隔离就够，多 agent 改重叠文件的写代码任务要用物理隔离（独立 Git worktree 或独立容器）。
3. **聚合收回**：用聚合策略把 N 路结果合并。聚合没做对，全套链路就不成立。

Aggregator 至少处理以下五项：

<table>
<thead>
<tr>
<th style="text-align: left;">聚合环节</th>
<th style="text-align: left;">作用</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">去重 dedup</td>
<td style="text-align: left;">多 worker 抓到同一事实时合并，用语义相似度找重复</td>
</tr>
<tr>
<td style="text-align: left;">冲突消解 conflict resolution</td>
<td style="text-align: left;">worker A 说买、worker B 说卖时怎么裁定</td>
</tr>
<tr>
<td style="text-align: left;">跨切整合 integration</td>
<td style="text-align: left;">只在 worker 切片交界处才暴露的问题不能漏</td>
</tr>
<tr>
<td style="text-align: left;">排序 ranking</td>
<td style="text-align: left;">多维度综合排序</td>
</tr>
<tr>
<td style="text-align: left;">溯源 attribution</td>
<td style="text-align: left;">每条结论锚定到原始 source</td>
</tr>
</tbody>
</table>

## 适用场景

- **wall-clock 时间紧迫的批量任务**：季报合规扫描、大规模文档审查、批量投标书评审，总时长是硬瓶颈、子任务彼此独立。
- **可按语义独立切分的研究任务**：跨多个语料源的并行查证，每个 sub-agent 各查一类内容，输出几乎不冲突。
- **多 Agent 并行写代码**：UI、API、数据库和测试由独立 Agent 处理，并用 worktree 隔离文件与提交，最后统一集成验证。

适用条件包括：子任务可独立执行、wall-clock 时间是主要约束，并且业务能够承担 N 倍 token 成本。

## 已知失效方式

- **子任务有强依赖还硬切**：worker 之间需要交换中间状态、或必须按顺序看才能识别演化轨迹的任务，扇出会把顺序依赖强行拍平成并行，gather 阶段要花大量工作重新建立依赖关系。这种场景应该用交接链。
- **聚合比执行还贵**：aggregation 投入不够时，扇出只是把瓶颈从时长挪到质量。如果业务没有工程精力做去重、冲突消解、跨切整合，就不该开扇出。
- **聚合瓶颈**：worker 数 N 增加时，aggregator 要读完所有 worker 输出，context 撑爆、质量直线下降。N 大时 aggregator 要分层做（先分组 sub-aggregation，再最终综合），把 context 压力压到对数级。
- **切片按职能切而非按冲突切**：按"职能最齐全"切（前端/后端/算法/测试各一组）会导致集成阶段天天解冲突；按"输出冲突最小化"切才对。扇出拓扑应该 mirror 业务团队真实的协作拓扑。
- **隐式 batch 削并发**：应用侧发起多路调用时，provider 可能排队或 batch，实际并发低于配置值。扇出实现需要测量真实吞吐并与 provider 限制对齐。

## 验证指标

- **Worker 完成率**：返回有效 artifact 的 Worker 占比。合规审查还要列出未完成分片，不能用已完成结果掩盖漏评。
- **重复率**：聚合后语义重复条目的占比。持续升高时检查分片边界、归一化和去重策略。
- **加速比**：N 个 Worker 相对顺序基线带来的墙钟时间变化。偏离预期时检查限流、共享依赖和 gather 瓶颈。
- **聚合成本占比**：聚合步骤在总算力和延迟中的占比。过高时可改用更严格的 artifact、分层聚合或确定性去重。

## 最小实现

```
FanoutGather.execute(goal, perspectives, strategy):
    workers = decompose(goal, perspectives)    # 按语义独立性切 N 份
    results = 并行 gather(                       # 信号量控并发 + retry + backoff
        execute_worker(w) for w in workers      # 每个独立 context,失败不阻塞其他
    )
    return aggregate(goal, results, strategy)   # 去重、冲突消解与综合

aggregate(results, strategy):
    concatenate → 简单拼接(仅无重叠时)
    vote        → 多数投票
    synthesize  → 强模型综合,显式消解矛盾 + 去重
    structured  → schema 化结构合并
```

生产实现根据本地质量和成本选择 Worker 与 Aggregator 模型；并发与 provider 限制对齐并在观测后调整；单个 Worker 失败不阻塞其他分支，最终 artifact 必须披露 partial failure；各分支保留完整 trace。

## 场景化示例

设想一个季度合规扫描 Agent。单 Agent 顺序读取全部财务文档无法满足披露前窗口；并行 Worker 虽然缩短墙钟时间，却会产生重复、术语不一致和置信度不可比的问题。gather 阶段因此需要语义去重、概念归一化、证据合并和 needs-review 分类。政府或国企招投标等场景还可能要求 Worker 之间保持独立，trace 和留存期限按适用制度配置。任何 partial failure 都要在最终报告中显式列出。

## 相邻模式

- **并行探索（推理模块 R3）**：结构同源、聚合机制相通，区别在并行的实体。扇出聚合是不同子任务分给不同 Agent（协作拓扑），并行探索是同一道题的多条解法（推理策略）。
- **层级委派（C1）**：同为一对多，但扇出是一对多分量（多个 worker 同时干同一类活的不同部分）、浅协作（fire-and-collect），层级委派是一对多分专业、深协作（supervisor 持续监督）。Anthropic 多 agent research 同时是层级（lead 主管）加扇出（subagents 并行）。
- **对抗评审（C3）**：扇出的 N 个 worker 是互补关系（各看一面拼出全景），对抗评审的 reviewer 是对抗关系（独立审查决策健壮性）。
- **子代理隔离（C5）**：每个并行分支使用独立 context，gather 阶段只读取 reduced 结果。

## 工程判断

扇出聚合用更多 Worker 缩短 wall-clock 时间，同时增加去重、冲突消解和结果合并的成本。Worker 数量扩大前，需要先验证聚合器的容量与质量。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

## 2026-08-25 研讨会修订：写入冲突域与只读聚合

文件分开不等于资源独立。扇出前声明可能写入的文件、编号、配置、领域对象和外部环境；无法确认互斥关系时保持串行。Gatherer 没有写入职责时默认只读。

[协作模块研讨记录](https://adpsagent.com/zh/workshops/collaboration-2026-08-25/)

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《C2 扇出聚合》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-c2-fan-out-gather">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
