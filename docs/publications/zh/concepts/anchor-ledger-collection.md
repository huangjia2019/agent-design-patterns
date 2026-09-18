<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>锚、账、集：叙事状态的数据结构</h1>
<p class="publication-deck">Anchor 保存目标，Ledger 追加事实，Collection 提供当前读取视图。</p>
</header>

![锚、账、集叙事状态结构](../../assets/images/concepts/anchor-ledger-collection.png)

## 应用背景：任务走远之后还要认得起点

一项“为新加坡团队完成下月计薪配置”的任务，会先后经历规则确认、薪资组创建、员工关联和审批。走到后半程时，对话里最新的细节可能是一个员工归属问题，但它不能取代原始交付目标。

长程 Agent 需要一份不随摘要改写的目标、一条可追溯的进展记录，以及一份面向当前步骤的精简视图。三者一起使用，才能同时防止目标漂移和上下文膨胀。

## 概念定义

叙事状态用 Anchor、Ledger 和 Collection 管理长程任务中的目标与进展。

- **锚（Anchor）**保存用户提交的原始目标，在任务生命周期内保持稳定；
- **账（Ledger）**按时间追加关键推理、行动和里程碑摘要；
- **集（Collection）**根据当前步骤从 Ledger 投影出的临时上下文。

Anchor 和 Ledger 是持久化真源，Collection 是按需生成的读取视图。

## 工程机制

每个关键步骤完成后，系统把结构化结果压缩为 Ledger 事件。进入推理边界时，投影器根据当前目标、步骤和权限选择相关事件，生成 Collection，并与 Anchor 一起组装 ReasonContext。

这套结构避免两类问题。只链式传递上一步输出会逐渐稀释原始目标；每次加载全部历史则会增加上下文长度和无关信息。Anchor 固定目标，Ledger 保留事实，Collection 控制当前输入规模。

## 案例用法

用户在新一轮只输入“继续”时，系统不能把这个词当成完整任务。Anchor 提供原始薪资组配置目标，Ledger 提供此前已经完成的模板匹配或快照结果，Collection 只选择当前步骤需要的摘要。推理模块据此恢复任务语义。

API ID 和任务节点状态不写入这套叙事结构作为控制真源。它们分别由 SessionState 和 Workspace 管理。

## 适用条件

当任务链路较长、跨多轮会话，或每个推理步骤只需要历史信息的一部分时，可以采用锚、账、集。相关概念见[会话统一状态](https://adpsagent.com/zh/concepts/unified-session-state/)、[记忆信封](https://adpsagent.com/zh/concepts/memory-envelope/)和[L1/L2/L3 分层记忆](https://adpsagent.com/zh/concepts/layered-memory/)。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-context-memory">上下文与记忆</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：梁博</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 按目标、追加事实和当前读取视图的不同寿命整理三种结构。</dd></div>
<div><dt>当前地位</dt><dd>案例命名</dd></div>
</dl>
</section>

<div class="document-citation">
<p><strong>初始来源：</strong><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例报告</a>；案例提供：梁博（Bo Liang）。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-21">2026-06-21</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-anchor-ledger-collection">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
