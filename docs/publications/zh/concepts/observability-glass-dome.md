<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>可观测性：活动事件与执行时间线</h1>
<p class="publication-deck">Activity 与 Frame 关联模型、工具、状态变化、耗时和成本。</p>
</header>

![Agent 活动事件与执行时间线](../../assets/images/concepts/observability-glass-dome.png)

## 应用背景：一句“任务完成”无法用来排错

用户看到“薪资组配置完成”，事后却发现两名员工没有被关联。开发者需要沿同一条时间线查到：意图如何识别，调度器选了哪个节点，工具收到什么参数，API 返回什么，状态又是何时被标记为完成。

一般应用日志可以证明进程在运行，却很难还原 Agent 的决策链。这里需要统一的活动事件和可关联的执行帧。

## 概念定义

Agent 可观测性记录一次会话中发生的意图识别、路由、推理、工具调用、状态读写和回复合成。目标是让开发者能够根据结构化事件定位执行偏差，而非只比较用户输入和最终输出。

东方屹腾把会话拆为 Activity，并在 Activity 下记录 Frame。Frame 可包含模型输入输出、工具请求与回执、状态变化、耗时和成本。

## 工程机制

各运行模块发布统一事件：

<pre><code class="language-text">event_id
session_id
activity_type
step_id
started_at / ended_at
input_ref / output_ref
model_or_tool
cost
status
</code></pre>

前端按时间排序显示事件，并允许展开具体 Frame。开发环境可显示完整提示词和回执；生产环境按权限脱敏或关闭调试字段。事件 ID 用于关联叙事、机械状态和任务节点的变化。

可观测性应从第一阶段进入运行时接口。后补日志很难还原模块边界、状态来源和模型当时看到的上下文。

## 案例用法

东方屹腾在接通对话管道后即建设事件时间线。意图识别结果、网关路由、ReAct 轮次和工具调用都以 Activity 展示；每次模型调用的提示词、输出、耗时和成本记录在 Frame 中。

当薪资组配置结果异常时，开发者可以定位到意图误判、推理选择错误、参数来源校验失败或业务回执不符合验收条件，无需反复重放整段会话进行猜测。

## 适用条件

当一次请求跨越多个能力模块，且错误需要定位到具体步骤、输入和状态变化时，应建立活动事件与执行时间线。事件生产方通常由[Orchestrator](https://adpsagent.com/zh/concepts/orchestrator/)统一协调。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：梁博</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将模型、工具、状态变化、耗时和成本整理到同一事件轴。</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-observability-glass-dome">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
