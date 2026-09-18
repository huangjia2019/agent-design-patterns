<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/x1-observability/" style="color: var(--color-text-muted);">X1 可观测性</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>X1 · 可观测性 Observability Harness · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">模型、路由、工具和状态变化统一为语义事件，并按执行时间线关联。</p>
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
<td style="text-align: left;">X1 可观测性 Observability（横切工程面 · 观测与证据）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">G5 钩子流水线 Hook Pipeline</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/x1-observability/">/zh/patterns/x1-observability/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第二章、PPT 7–8 页；第三章 Orchestrator、PPT 12 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">把一次会话中的模型调用、路由、工具执行和状态变化统一为语义事件，并按时间线展示；控制流与界面呈现分开。</td>
</tr>
</tbody>
</table>

---

## 场景约束

一次执行型 Agent 请求会经过意图识别、网关路由、链式推理、ReAct、工具调用、记忆写入和回复合成。若系统只记录用户输入和最终回复，开发者无法判断偏差产生于哪个步骤。

东方屹腾在接通基本对话和附件上传后，即建设运行时事件与时间线，再增加后续能力。这样，每个新增模块都必须同时定义业务接口和观测接口。

本切片讨论的是系统运行过程对开发者和运维人员可见，与 Agent 对外部世界的感知属于不同概念。

## 事件模型

系统使用 Activity 表示有业务语义的运行步骤，Frame 表示步骤中的具体调用和状态变化。

<pre><code class="language-text">Activity
  activity_id
  session_id
  type
  status
  started_at
  ended_at
  frames[]

Frame
  frame_id
  model_or_tool
  input_ref
  output_ref
  state_delta_ref
  latency
  token_or_cost
</code></pre>

Activity 类型包括意图识别、意图网关路由、链式推理、ReAct 轮次、工具调用、审批等待和回复合成。事件使用统一 ID 关联 SessionNarrative、SessionState 和 Workspace 的变化。

## 时间线与权限

Web 界面按时间顺序显示 Activity，并允许展开 Frame。开发环境可以查看模型实际输入、接口输出、耗时和成本；生产环境按角色进行脱敏，只显示必要进度。提示词、业务参数和个人数据不应无差别暴露给终端用户。

用户侧可以看到长任务的阶段进度，并在允许的节点暂停。开发者侧可以查看完整调用链和状态变化。两种视图复用同一事件源，但字段权限不同。

## 控制与呈现分离

Orchestrator 只发布结构化活动事件，不处理 SSE、界面组件或打字机效果。外层 `MessageHandler` 订阅事件，并转换为流式输出。东方屹腾使用 Go 协程和通道实现发布订阅。

这种边界允许控制逻辑和展示逻辑独立演进。新增界面或输出协议不改 Orchestrator，新增能力只需发布符合契约的事件。

## 案例运行

薪资组配置请求的时间线可以依次显示：

<pre><code class="language-text">意图识别
  -&gt; resolve 路由
  -&gt; Skill 召回
  -&gt; 模板匹配工具
  -&gt; 快照任务
  -&gt; 导入任务
  -&gt; 验收与回复
</code></pre>

若结果异常，开发者可以检查意图信号、ReasonContext、工具参数来源、业务回执和节点验收结果。问题定位落到具体 Activity 和 Frame。

## 失效信号

- 只有原始日志，没有稳定的事件类型和关联 ID；
- 模型调用可见，工具和状态变化不可见；
- Orchestrator 同时处理编排和界面渲染；
- 开发视图与生产视图没有权限边界；
- 日志包含未脱敏的薪酬、身份或鉴权数据；
- 失败事件没有输入引用、输出引用或状态差异；
- 审批等待与恢复不在同一调用链中。

## 验证指标

- 运行步骤的语义事件覆盖率；
- Activity 到 Frame、状态变化和业务回执的关联完整率；
- 异常任务的平均定位时间；
- 无关联原始日志占比；
- 开发与生产字段权限测试通过率；
- 单次任务的观测存储成本和保留周期；
- 展示协议变更对 Orchestrator 的代码影响。

## 与白皮书的对应

X1 规范要求通过 Trace 还原完整执行链。东方屹腾以 Activity/Frame 作为事件抽象，以 MessageHandler 和 SSE 作为展示实现。G5 钩子流水线可在执行边界产生事件，X1 负责统一采集、关联和查询。

## 迁移条件

请求跨多个模型、工具和状态模块，且错误需要定位到具体步骤时，应在项目早期建立语义事件时间线。单步内容生成可以先使用平台 Trace，但仍应保留请求、模型版本、成本和错误信息。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 可观测性》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>证据边界：</strong>本页是完整案例的模式切片，记录特定系统约束下的实现选择。案例方提供的实现与效果信息未经过独立审计，不构成通用性能承诺。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>；案例提供：梁博</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-20">2026-08-20</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-x1-observability-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
