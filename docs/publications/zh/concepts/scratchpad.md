<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>草稿纸看板：Agent 的短期工作面</h1>
<p class="publication-deck">用结构化字段保存当前目标、步骤、观察、阻塞、证据和下一动作。</p>
</header>

## 从一个长程任务开始

Agent 连续工作几十轮后，完整聊天记录会越来越长。当前目标、刚完成的步骤、阻塞原因和下一动作散落在历史消息里，恢复时很难迅速定位。草稿纸看板把本轮仍在使用的信息放到一个短寿命工作面上。

## 定义

草稿纸看板记录一次任务运行中的当前目标、已确认计划、当前步骤、最近观察、阻塞、证据引用和下一动作。模型与 Orchestrator 都可以读取；每个字段有明确写入者；任务结束后压缩、归档或丢弃。

<pre><code class="language-text">ScratchpadBoard = {
  goal,
  accepted_plan,
  current_step,
  recent_observations,
  blockers,
  evidence_refs,
  next_action,
  revision
}
</code></pre>

Thought、Action 和 Observation 可以作为其中的轨迹字段。工具回执、业务 ID 和审批结果仍进入各自的事实平面，草稿纸不充当机械参数的权威来源。

## 工程边界

草稿纸适合任务结构仍在探索、下一步依赖最新观察的阶段。依赖关系稳定后，应把严格顺序迁入任务 DAG，把业务参数迁入机械状态平面，把跨任务经验迁入长期记忆。

完整聊天记录直接充当草稿纸会带来两个问题：读取面持续膨胀，写入权也不清楚。工程化实现需要固定字段、修订号、大小上限和结束策略。

## 来源与谱系

- 初始案例：东方屹腾执行型 Agent，案例提供梁博（Bo Liang）。
- 历史近邻：HEARSAY-II Blackboard、ReAct 轨迹、CoALA working memory、任务看板与 checkpoint。
- ADPS 整理：把短期推理轨迹扩展为模型、运行时和人工审核共享的可检查工作面。
- 定义地位：ADPS 重述。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-context-memory">上下文与记忆</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：梁博</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将短期推理轨迹整理为模型、运行时和人工审核共享的工作面。</dd></div>
<div><dt>当前地位</dt><dd>ADPS 重述</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-scratchpad">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
