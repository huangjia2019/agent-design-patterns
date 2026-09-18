<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>P3
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>P3 · Progressive Discovery · 渐进发现</h1>
<p class="publication-deck">Agent 面对未知信息空间时，通过广扫、精读和深追逐轮缩小检索范围。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">感知 Perception × 循环 Loop（转）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（需要多次搜索、读取与评估）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">感知模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">Agent 面对未知信息空间时，通过广扫、精读和深追逐轮缩小检索范围。</td>
</tr>
</tbody>
</table>

---

## 问题

面对大型遗留 codebase、未建立索引的合同或长事故日志时，Agent 往往不知道相关代码的名称或证据所在位置。全量载入会超出窗口；RAG 也可能漏召回，例如相关变量名为 `merge_user_state`，注释中没有 “order”，语义查询难以建立关联。

渐进发现先通过广扫获得候选，再根据已有发现调整下一轮查询，直到证据充分、连续没有新发现或预算耗尽。该模式管理当前 session 对未知空间的主动探索。

## 坐标说明：感知 × 循环

- **纵轴 · 感知**：渐进发现分阶段获取信息，并决定下一步读取对象，位于推理之前的输入侧。
- **横轴 · 循环**：每轮使用前一轮结果调整检索条件，终止条件为证据充分、预算耗尽或连续无新增发现。分诊通常是单次路由，压缩采用线性级联，渐进发现则重复执行检索与评估。

## 解决方案与机制

一次发现走 forage-focus-deepen 三阶段，广度递减、深度递增：

<table>
<thead>
<tr>
<th style="text-align: left;">阶段</th>
<th style="text-align: left;">动作</th>
<th style="text-align: left;">工具与代价</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Forage 广扫</td>
<td style="text-align: left;">扫陌生空间获得候选，只看文件名、路径和匹配行上下文</td>
<td style="text-align: left;">grep / glob / find，低成本广覆盖</td>
</tr>
<tr>
<td style="text-align: left;">Focus 精读</td>
<td style="text-align: left;">从候选中选择最相关的对象完整读取，查看依赖关系和调用链</td>
<td style="text-align: left;">read，缩小范围后投入主要预算</td>
</tr>
<tr>
<td style="text-align: left;">Deepen 深追</td>
<td style="text-align: left;">沿可疑链继续检查被引用函数、测试或历史 commit</td>
<td style="text-align: left;">read，只追高信号路径</td>
</tr>
</tbody>
</table>

工具层应提供 grep、read、glob 等原子操作，使 Agent 能根据已读内容调整下一次查询。最大循环数、单轮预算和候选数量都是可配置上限，应根据仓库规模、任务风险和本地回放结果确定。达到上限仍无结果时，应修改关键词、切换检索手段或转人工处理。首轮 forage 可先由轻量模型把任务描述转换为一组精确关键词；后续轮次依据新增证据更新关键词。

## 适用场景

- **陌生 codebase 的 bug 根因定位**：原作者离开、文档稀疏，没人知道某条 pipeline 经过哪些文件。Agent 需要先找到入口，再沿调用关系逐步缩小范围。
- **运维事故响应**：接到告警后从 metric 反推关键词，按时间窗口裁剪日志，三阶段定位故障源，给值班工程师初判报告和"第一步该做什么"建议。
- **合同条款风险扫描、研究文献综述**：任何符合"接到任务→不知道相关信息在哪→探索定位"模式的场景。
- **隐私敏感且可直接搜索的 codebase**：grep + read 让代码留在受控文件系统中，不必先复制到向量库。

## 已知失效方式

- **Forage 关键词太宽**：任务“用户登录变慢了”只被写成 `["login", "slow"]`，会返回大量候选。结合组件名、错误字段和调用入口生成更窄的查询，能减少无关读取。
- **Focus 阶段挑错文件**：scorer 算分错把测试文件排在生产文件前，Agent 读了一堆 spec 文件，关键的 `services/auth.rb` 没读到。给 scorer 带业务权重：生产文件 > 测试文件、最近修改 > 旧代码、核心目录 > 边缘目录。
- **Deepen 死胡同**：沿依赖追进第三方库后没有新增信号。应为 Deepen 设置范围和跳数上限，除非现有证据明确指向外部依赖。
- **Discovery 与 RAG 结果冲突**：两条检索路径可能返回重叠或矛盾的结果。应按数据时效、权限边界和索引覆盖率设置优先级，并保留各自的来源信息。

## 验证指标

- **找到答案的循环数 cycles\_to\_success**：按任务类型观察收敛需要多少轮。相对基线持续上升时，检查关键词生成、工具可用性和候选排序。
- **forage/focus 预算比**：Forage 应保持广而轻，Focus 承担主要阅读预算。比例偏移时，结合候选数量和最终命中情况判断查询过宽还是过窄。
- **零信号率 zero\_signal\_rate**：达到停止条件仍未找到有效信号的 session 占比。该指标上升时，应检查索引时效、读取权限、scorer 和任务描述质量。

## 最小实现

```
discover(task, keywords):
    循环 至多 max_cycles：
        Forage：对每个 keyword 跑 grep → 汇总候选 → 按 task 相关性打分 → 留 top_k
        若 cycle_tokens 超 budget → 停
        Focus：挑 focus_k 个对象完整 read，记下依赖关系
        Deepen：从已读内容抽依赖（import / 函数引用），在 deepen_budget 内深追
        若信号足够 → 成功，跳出
        否则 → 用已发现内容 refine keywords，再来一轮
    每阶段落一条 DiscoveryEvent（phase / keyword / 候选数 / files_read / tokens / wall_time）
```

grep、read 和 scorer 通过依赖注入接入，使同一流程可运行于本地文件系统、MCP server 或外部索引引擎。

## 场景化示例

设想一个电商系统的订单确认邮件偶尔混入其他客户的条目。语义检索没有召回相关代码，因为实现中没有出现 “order” 这个业务词。Agent 先用 `grep "send.*confirm"` 广扫发送入口，再精读邮件任务与缓存调用链，最后沿 `Cache.get_user` 深追，发现 cache key 缺少租户维度。这个问题依赖代码调用关系，直接遍历文件结构比只依赖语义召回更有效。

## 相邻模式

- **上下文分诊（P1）**：分诊产生的 P3 句柄可作为渐进发现按需获取的入口。分诊筛选已有候选，渐进发现主动选择查询和读取对象。
- **语义压缩（P2）**：把探索交给 sub-agent、主 Agent 只接收摘要，可以减少探索过程对主 context 的占用。
- **程序性记忆（Memory 模块）**：可将本次得到的 final\_files 跨 session 保存。后续同类任务先检索记忆，未命中时再启动渐进发现。

## 工程判断

渐进发现通过多轮检索逐步缩小范围。每轮都要更新查询依据，并在证据足够、预算耗尽或连续无新增发现时停止。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《P3 渐进发现》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-p3-progressive-discovery">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
