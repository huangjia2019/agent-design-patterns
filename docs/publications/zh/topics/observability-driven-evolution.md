<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/topics/">专题</a><span style="margin:0 0.45rem;">/</span>可观测性驱动的 Agent 演进 · 从运行时间线到可验证变更</p>

<header class="publication-head">
<p class="publication-series">ADPS 专题研究</p>
<h1>可观测性驱动的 Agent 演进 · 从运行时间线到可验证变更</h1>
<p class="publication-deck">用运行轨迹、组件版本、外部结果和变更证据支撑 Agent 调试、发布与演进。</p>
</header>

Agent 运行失败时，一个最终答案和几行应用日志很难说明问题。工程师需要知道它当时看到了什么，选了哪个工具，改变了哪些状态，又根据什么宣布完成。当团队开始调整提示词、工具、Skill、记忆或执行结构时，还要回答更难的问题：这次修改是否真的改善了后续任务，有没有引入新的回归。

这些问题横跨感知、记忆、推理、行动、反思、协作与治理。v0.5 将可观测性定义为 X1 横切工程面；本专题继续讨论证据如何支撑 Agent 调试、评测、发布与演进。

## 感知与可观测性的边界

感知处理 Agent 能从外部世界读到哪些信号。可观测性处理工程团队能否还原 Agent 的运行过程和变更效果。前者为推理提供输入，后者为调试、评审、发布和追责提供证据。

可观测性至少要支持三类查询：

1. 一次运行中发生了什么？
2. 哪个组件、版本或决策导致了结果？
3. 修改之后，后续结果是否改善，回归是否可接受？

## 四个可观测面

| 可观测面 | 需要记录的东西 | 它支持的决策 |
| --- | --- | --- |
| 运行与轨迹 | 输入引用、路由、模型调用、工具参数、状态变化、延迟与成本 | 问题发生在哪一步 |
| 结果与业务事实 | 业务账本、外部回执、验收探针、人工复核 | 任务是否在消费端完成 |
| 组件与配置 | 提示词、工具、中间件、Skill、子 Agent、记忆、模型与数据版本 | 问题来自哪个可编辑部分 |
| 决策与变更 | 修改动机、预期效果、差异、评测结果、审批和回滚点 | 这次变更是否应当保留 |

只有运行 trace，团队可以调试单次任务，却难以管理演进。加入组件版本、变更预测与后续评测后，每次修改才有可检查的前因后果。

## 变更流程中的证据

<pre><code class="language-text">埋点与版本化
      ↓
采集运行事件与外部结果
      ↓
按任务、版本和因果链聚合
      ↓
定位候选组件并提出可验证的修改
      ↓
运行能力评测与回归评测
      ↓
审批发布或回滚
</code></pre>

变更进入流程前，需要形成可验证合同。合同说明修改哪个组件、预期改善哪类任务、不能损害哪些回归项，并将结论指向确定性证据和评测结果。

## 工程实践

### Activity / Frame 运行时间线

东方屹腾执行型 Agent 在项目早期就建立了统一时间线。`Activity` 表示具有业务语义的步骤，`Frame` 保存其中的模型调用、工具事件和状态变化。意图识别、路由、ReAct 轮次、审批等待和业务回执可以按同一个 `run_id` 查询。

这套设计同时服务三个角色：开发者查找错误发生的 Frame，业务人员查看进度和回执，运维人员查看延迟、费用和失败分布。生产界面按角色脱敏，不把调试提示词和业务数据直接暴露给终端用户。

### 组件、经验与决策可观测

复旦大学 2026 年的 Agentic Harness Engineering 研究将自动演进的关键拆成三部分：

- 组件可观测：系统提示词、工具说明与实现、中间件、Skill、子 Agent 配置和长期记忆都是文件级、可比较、可回退的对象。
- 经验可观测：运行轨迹、错误、评测和环境状态形成可下钻的证据库，不只保留一句总结。
- 决策可观测：每次编辑携带一个预测，下一轮任务用结果检验预测。

该研究还提醒了一个边界：Agent 能够根据轨迹提出修复，却不一定能预见变更对其他任务的损害。评测器、执行环境和回滚通道因此应由受保护的治理边界管理，不能跟着 Agent 一起自由改写。

## 最小事件合同

<pre><code class="language-json">{
  "run_id": "run-20260814-0042",
  "task_id": "publish-map-17",
  "goal_version": "goal-v3",
  "component_versions": {
    "prompt": "sha256:...",
    "toolset": "registry-v12",
    "skill": "gis-publish-v5"
  },
  "event_type": "tool_result",
  "input_ref": "artifact://plan/step-4",
  "tool": "verify_get_map",
  "state_delta": {"verification": "failed"},
  "evidence_ref": "artifact://receipts/getmap-17",
  "latency_ms": 842,
  "cost_usd": 0.01
}
</code></pre>

变更记录可在这组字段上再加 `decision_id`、`predicted_effect`、`observed_effect` 和 `rollback_ref`。每个字段都应服务一个实际查询；对调试和评审没有用的信息，不必为了“完整”全量采集。

## 与 ADPS 模块的关系

| 模块 | 在证据流程中的作用 |
| --- | --- |
| 感知 | 保留输入来源、选择与压缩决策 |
| 行动 | 产生语义化 ActionEvent、业务账本、外部回执与 checkpoint |
| 反思 | 使用轨迹、错误和延迟反馈提出修改候选 |
| 记忆 | 保存经过验证的经验、版本与来源 |
| 治理 | 管理发布门、可见性、预算、回滚和审计 |

X1 给出统一的可观测合同，其证据同时服务长程任务、评测、反思、记忆与治理生命周期。

## 常见失效方式

- 日志只有文本，没有任务、步骤、状态和证据的语义关联。
- 仅保留最终回答，无法还原工具参数、中间状态和外部结果。
- 轨迹没有绑定提示词、模型、工具集和 Skill 版本，同一错误无法复现。
- 仪表盘只显示 token、延迟和成本，没有外部验收与业务结果。
- 自动演进可以修改 Agent，也可以修改用来判定它的评测器。
- 事件采集很全，却没有固定的评审人、修复入口和回归流程。

## 后续议题

后续研讨可以围绕三类实物展开：一条真实任务的事件时间线，一次从错误证据到组件修改的差异，一份包含能力与回归结果的发布记录。只讲平台产品和指标名称，很难触及具体的工程分歧。

## 资料与来源

- [X1 可观测性](https://adpsagent.com/zh/patterns/x1-observability/)
- [治理模块总纲与 Agent 生命周期](https://adpsagent.com/zh/patterns/governance/)
- [ADPS 治理模块第一次研讨会](https://adpsagent.com/zh/workshops/governance-2026-08-18/)
- [DeerFlow Guardrail 代码与架构演进](https://adpsagent.com/zh/cases/deerflow-guardrail/)
- [东方屹腾·执行型 Agent 案例](https://adpsagent.com/zh/cases/liangbo-execution-agent/)
- [复旦大学：Agentic Harness Engineering](https://arxiv.org/html/2604.25850v4)
- [ADPS 行动模块第一次研讨会](https://adpsagent.com/zh/workshops/action-2026-08-06/)
- [ADPS 反思模块第一次研讨会](https://adpsagent.com/zh/workshops/reflection-2026-08-12/)

<div class="document-citation"><p><strong>引用建议：</strong>ADPS，《可观测性驱动的 Agent 演进 · 从运行时间线到可验证变更》，ADPS 专题研究，2026-08-14。</p><p><a href="https://adpsagent.com/zh/topics/">专题目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer">专题整理跨模块的工程问题。引用的模式定义、具名案例和研讨会记录以各自页面为准。</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>正文关联的研讨会与案例：<a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾·执行型 Agent 案例</a>（<time datetime="2026-06-19">2026-06-19</time>）；<a href="https://adpsagent.com/zh/workshops/action-2026-08-06/">ADPS 行动模块第一次研讨会</a>（<time datetime="2026-08-06">2026-08-06</time>）；<a href="https://adpsagent.com/zh/workshops/reflection-2026-08-12/">ADPS 反思模块第一次研讨会</a>（<time datetime="2026-08-12">2026-08-12</time>）；<a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">ADPS 治理模块第一次研讨会</a>（<time datetime="2026-08-18">2026-08-18</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-14">2026-08-14</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#topics-observability-driven-evolution">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
