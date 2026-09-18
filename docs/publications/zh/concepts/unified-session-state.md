<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>会话统一状态：三个状态平面</h1>
<p class="publication-deck">SessionNarrative、SessionState 和 Workspace 分别管理语义、参数与调度。</p>
</header>

![会话统一状态的三个平面](../../assets/images/concepts/unified-session-state.png)

## 应用背景：一个任务同时有三种进度

完成一次薪资配置，系统既要记住用户为什么这样设置，也要保存工具返回的 `pay_group_id`，还要知道“关联员工”是否已经完成。这三件事会沿着同一次会话推进，却有不同的结构和校验规则。

把它们塞进一段对话摘要，精确 ID 和任务依赖容易在压缩中丢失；把所有信息放进一张通用状态表，语义记录、业务参数和调度状态又会相互污染。

## 概念定义

会话运行时包含语义、业务参数和任务调度三类状态。三者可以共享会话 ID 和事件时间线，但采用独立的数据模型。

| 状态平面 | 回答的问题 | 数据形态 |
| --- | --- | --- |
| SessionNarrative | 用户要求什么，当前进展如何 | 目标、摘要、经验和上下文投影 |
| SessionState | API 参数来自哪里，是否有效 | Cell、值、作用域和 Provenance |
| Workspace | 哪个任务可以执行，是否完成 | DAG、节点状态和依赖 |

## 工程机制

任务执行完成后，三类副产物分别写入对应平面：

- 业务进展摘要写入 SessionNarrative；
- 接口回执中的参数写入 SessionState；
- 节点状态迁移写入 Workspace。

事件可以关联三次写入，但读取方不同。推理模块读取叙事投影，RunPipeline 读取机械参数，调度器读取任务图。任何模块都不应通过另一平面的数据推断自己的核心状态。

## 案例用法

薪资组快速搭建需要先建快照，再导入模板，失败时回滚。顺序和节点状态由 Workspace 管理；模板匹配产生的 `template_id` 由 SessionState 保存并携带来源；用户目标和完成进展由 SessionNarrative 记录。

早期实现把任务结果、叙事和 API 返回值放在同一上下文中，再让模型挑选下一步参数。长 ID 的复制存在误差，任务进展也会被中间推理稀释。拆分后，参数不再经过模型，调度不再依赖自然语言解释。

## 适用条件

当 Agent 在多步流程中同时维护语义上下文、严格业务参数和可恢复任务状态时，应采用三个平面。上游原则见[控制平面与叙事平面](https://adpsagent.com/zh/concepts/control-narrative-dualism/)，参数坐标见[机械状态平面与 Provenance](https://adpsagent.com/zh/concepts/mechanical-state-plane/)，叙事组织见[锚、账、集](https://adpsagent.com/zh/concepts/anchor-ledger-collection/)。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-system-boundaries">系统边界与状态</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：梁博</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将叙事、机械参数和任务调度的写入权整理为三个状态平面。</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-unified-session-state">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
