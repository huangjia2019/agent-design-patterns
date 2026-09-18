<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/m3-progress-tracking/" style="color: var(--color-text-muted);">M3 进度追踪</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>M3 · 进度追踪 · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">Anchor 固定目标，Ledger 追加关键进展，Collection 提供当前步骤的读取视图。</p>
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
<td style="text-align: left;">M3 进度追踪 Progress Tracking（记忆 × 编排）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">P1 上下文分诊 · M1 分层保留</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/m3-progress-tracking/">/zh/patterns/m3-progress-tracking/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第六章 · PPT 第 25 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">Anchor 固定原始目标，Ledger 追加关键进展，Collection 为当前推理提供按需投影。</td>
</tr>
</tbody>
</table>

---

## 场景约束

东方屹腾的长程任务跨越多个能力边界和十余次模型调用。后续步骤需要持续回答两个问题：用户最初要求什么，系统已经完成什么。

若每一步只继承上一轮叙事输出，原始目标会被中间分析逐步稀释。若完整携带历史，Prompt 会持续增长。进度追踪需要把目标和里程碑外置为可持续读写的状态。

## 状态结构

<pre><code class="language-text">SessionNarrative
  Anchor: 原始目标
  Ledger: 追加式里程碑事件
  Collection: 当前步骤的临时投影
</code></pre>

Anchor 在任务创建时写入，后续不由摘要覆盖。Ledger 只记录关键变化，例如意图确认、模板匹配完成、快照创建成功、审批等待和任务失败。每条事件保留：

<pre><code class="language-text">event_id
task_id
event_type
summary
artifact_ref
created_at
producer
</code></pre>

Collection 由上下文分诊模块在关键推理入口生成，不是新的持久化真源。

## 写入规则

Ledger 采用追加写，历史事件不原地改写。需要纠正时追加更正事件，并引用被更正条目。摘要应说明发生了什么、产生了什么结果、哪些约束仍有效，同时保留指向原始 Artifact 或业务回执的引用。

机械参数不以 Ledger 摘要为调用真源，任务节点状态也不从摘要推断。它们分别写入 SessionState 和 Workspace。

## 案例运行

用户提出薪资组配置目标后，系统写入 Anchor。模板匹配、快照和导入等关键结果依次写入 Ledger。若用户在新一轮只输入“继续”，上下文组装器仍可读取 Anchor，并从 Ledger 选择尚未完成任务所需的里程碑。

这套状态也支持中断恢复。恢复过程先读取任务图确定可执行节点，再读取 Anchor 和相关 Ledger 事件恢复语义；API 参数从机械状态平面读取。

## 失效信号

- 目标只存在于首轮消息，没有独立 Anchor；
- 每个内部推理片段都写入 Ledger，导致事件失去里程碑粒度；
- Ledger 摘要没有原始证据引用；
- 历史事件被覆盖，无法还原进展；
- Collection 被持久化后当作完整事实；
- 任务调度和业务参数从自然语言摘要中推断。

## 验证指标

- 后段推理的 Anchor 可用率；
- 关键里程碑写入完整率；
- Ledger 事件到 Artifact 或回执的引用完整率；
- 用户输入“继续”后的正确恢复率；
- 因目标漂移导致的错误规划次数；
- 每个任务的 Ledger 规模和摘要压缩比。

## 与白皮书的对应

M3 白皮书把进度追踪定义为 Agent 的外置工作记忆。东方屹腾的 SessionNarrative 提供了具体实现：Anchor 保存目标，Ledger 保存进展，Collection 提供当前读取视图。P1 负责读取侧的投影，M3 负责状态的写入、持久化和恢复。

## 迁移条件

当任务跨多轮、多模块或可中断恢复时，应显式维护进度状态。单轮短任务可以直接使用消息历史。若系统尚未区分叙事、机械和调度状态，应先建立状态边界，再引入 Anchor、Ledger 和 Collection。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 进度追踪》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-m3-progress-tracking-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
