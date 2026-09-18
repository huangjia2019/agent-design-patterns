<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>P2
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>P2 · Semantic Compaction · 语义压缩</h1>
<p class="publication-deck">context 接近容量上限时，分级压缩历史信息，并保留后续推理所需的证据、决策和错误反馈。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">感知 Perception × 链式 Chain（传）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（摘要用便宜模型即可，按阈值触发）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">感知模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">context 接近容量上限时，分级压缩历史信息，并保留后续推理所需的证据、决策和错误反馈。</td>
</tr>
</tbody>
</table>

---

## 问题

长任务持续交互后，context 会逐步接近容量上限。一段包含连接池配置、队列深度和调用位置的 stack trace 如果被压缩为 “a database error occurred”，定位信息以及已排除的重试方案都会丢失，Agent 可能再次执行已经否决的处理路径。

语义压缩采用三级级联：先清理冗长的 tool 结果，再摘要早期对话，最后执行深度压缩。各级按 context 占用阈值触发，适用于单个 session 内的容量管理。压缩后仍需保留下一阶段推理所依赖的事实和决策。

## 坐标说明：感知 × 链式

- **纵轴 · 感知**：压缩处理已经进入窗口的输入历史，决定当前 context 保留哪些证据。跨会话存储属于记忆模块，问题求解属于推理模块。
- **横轴 · 链式**：三层压缩是级联结构，每层接前一层的输出，原文经清理、摘要、再压缩一路传下来，一层比一层紧。流在 chain 上的是被压缩的历史。

## 解决方案与机制

压缩按 context 占用从轻到重分层触发，错误堆栈跨整个流程受保护：

<table>
<thead>
<tr>
<th style="text-align: left;">层级</th>
<th style="text-align: left;">动作</th>
<th style="text-align: left;">典型压缩比</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Level 1 截断</td>
<td style="text-align: left;">清理冗长 tool 输出（保留指针，标注可重取）</td>
<td style="text-align: left;">轻度</td>
</tr>
<tr>
<td style="text-align: left;">Level 2 摘要</td>
<td style="text-align: left;">把老对话合并进持久 anchor，不重新生成完整摘要</td>
<td style="text-align: left;">中度</td>
</tr>
<tr>
<td style="text-align: left;">Level 3 深压</td>
<td style="text-align: left;">老错误压成清单但保留关键参数，近期证据完整保留</td>
<td style="text-align: left;">深度</td>
</tr>
</tbody>
</table>

触发阈值和持久 anchor 直接影响压缩质量。阈值应根据所用模型、工具输出形态和本地长任务评测确定，并在推理质量开始下降前留出余量。持久 anchor 采用增量合并，避免同一段历史被反复摘要。anchor 至少维护意图、已做改动、已做决策、已排除方案和下一步，其中“已排除方案”用于阻止 Agent 重复尝试已经否决的路径。

## 适用场景

- **长会话客服 Agent**：用户报告难以稳定复现的间歇性故障，Agent 一边对话一边调用内部工具，并可能跨班次排查。anchor 可直接导出为二线工程师的交接单。
- **多步调试与代码 Agent**：tool 输出经常包含长日志、数据查询或 API 响应，适合保留“做过什么”，并将已消费的原始输出替换为可重取指针。
- **研究助手、数据分析、咨询顾问类长 session Agent**：当 context 占用持续增长并开始影响任务质量时，应按本地评测触发压缩。

## 已知失效方式

- **摘要丢关键信息**：把带有行号、连接池配置和队列深度的错误压成 “a database error occurred”，定位依据就消失了。摘要 prompt 应明确保留业务数字、文件路径、函数名和错误码。
- **错误边界压缩**：在 Agent 活跃推理中段触发压缩，比如刚把 bug 缩到两个候选文件正要决策，压缩一来推理上下文丢失，从头来过。只压已完成、Agent 已 move on 的对话段。
- **反复压缩导致漂移**：反复摘要同一段内容会逐步放大偏差。系统应记录摘要血缘并限制重复压缩；仍无法控制容量时，转人工或开启带交接包的新 session。
- **过晚才压缩**：等窗口几乎耗尽再处理，可能已经经历了一段低质量推理。触发点应通过长任务回放评测确定。
- **永远不该压错误堆栈**：错误堆栈是 Agent 的反馈回路，丢了等于失忆。它必须跨整个压缩流程受特殊保护。

## 验证指标

- **Level 3 触发率**：观察最激进压缩层级在各类任务中的占比。某类 session 反复进入 Level 3，说明预算、交接或提前退场策略需要调整。
- **平均压缩比**：记录 after/before，并与下游任务质量一起看。压得更小不等于更好；需要用回放评测确认关键事实和已排除方案仍可恢复。
- **关键证据保留率**：检查错误堆栈、测试结果、文件路径和业务参数是否仍存在。安全相关证据缺失应直接触发告警。

## 最小实现

```
should_compact(total, budget, threshold): total / budget >= threshold
compact(turns, target):
    切分：老的可压 | 受保护（近期证据 + 所有错误堆栈）
    Level 1：清理冗长 tool 输出 → 够了就返回
    Level 2：老 turns 摘要合并进 anchor（intent/changes/decisions/excluded/next）→ 够了就返回
    Level 3：老错误压成清单但留关键参数，近期证据完整保留
每次压缩落一条 CompactionEvent（level / 前后 token / 保留的错误堆栈数）
```

摘要 prompt 应明确要求保留“已排除方案”，并以追加方式记录新决策。摘要任务可以使用成本较低的模型。

## 场景化示例

设想一个企业客户报告 API 在高峰时段间歇性失败，重试后又能恢复。客服 Agent 跨班次调用日志检索、指标查询和配置比对工具，原始输出不断堆积。系统先清理已经消费过的冗长 tool 输出，同时写入 anchor，记录故障现象、已做诊断和已排除方案；容量继续增长时，再把早期对话增量合并进 anchor。问题仍未收敛时，系统导出 anchor 和证据指针，交给二线工程师继续处理。

二线接到一份可继续工作的交接包，其中包括当前症状、已排除路径、支持与反驳各假设的证据，以及尚未验证的下一步。深度压缩在这里也是退场信号。压缩阈值应依据 session 的实际分布和回放质量来定，不能从工单等级直接推断。

## 相邻模式

- **上下文分诊（P1）**：互补。分诊管未来 token（哪些进），压缩管过去 token（已经进的怎么压不丢关键），P1 的"P2 级压缩后加载"正是两者衔接点。
- **渐进发现（P3）**：分诊管理待进入窗口的信息，压缩管理窗口中的历史信息，渐进发现负责主动获取未知信息。
- **分层记忆（Memory 模块）**：压缩管理单个 session 的窗口容量；跨 session 保留用户历史和任务事实属于记忆模块的职责。

## 工程判断

压缩策略决定后续推理可以使用哪些证据。错误堆栈、测试结果和被否决方案一旦被删除，后续回归与修复就会失去依据。

<!-- ADPS-BLUEBOOK-SLOT -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《P2 语义压缩》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-p2-semantic-compaction">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
