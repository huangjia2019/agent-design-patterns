<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/a1-tool-dispatch/" style="color: var(--color-text-muted);">A1 工具调度</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>A1 · 工具调度 · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">工具由行动模块调用，注册时声明机械状态的生产坐标和消费坐标。</p>
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
<td style="text-align: left;">A1 工具调度 Tool Dispatch（行动 × 路由）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">A5 最简工具集 · A2 规划执行</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/a1-tool-dispatch/">/zh/patterns/a1-tool-dispatch/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第三章、PPT 14–15 页；第六章、PPT 22 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">工具由行动模块统一调用；工具注册时声明机械状态的生产坐标和消费坐标；存量 SaaS API 通过网关接入，无需修改原接口。</td>
</tr>
</tbody>
</table>

---

## 场景约束

东方屹腾需要把用户的自然语言请求转换为一组连续的 SaaS API 调用。薪资组配置、算薪、代发和员工入职都包含真实的写操作，工具调度必须同时解决两个问题：

1. 工具调用如何进入可观察、可续作、可检查的运行结构；
2. 下游工具如何取得上游工具产生的准确参数。

第二个问题直接影响业务数据。企业系统中的 `template_id`、员工 ID 和流水号通常是 64 位或 128 位字符串。它们必须来自指定的工具回执，不能由模型根据上下文重新输出。

## 调用边界

Orchestrator 不直接执行工具函数。它根据控制信号把控制权交给行动模块，行动模块在 ReAct 循环中完成调用。每一轮包含：

<pre><code class="language-text">Thought -&gt; Action -&gt; Observation
</code></pre>

三类数据作为 block 追加到 scratchpad。下一轮读取已有 block chain，核对上一轮结果，再决定继续调用、转入规划执行、转人工或结束。

工具、技能和知识检索在这一层具有相同的调用形态。它们都是 `Action` 的候选，由结构化控制信号选中。调用前校验、结果解析、失败处理和目标核对都留在行动模块内，Orchestrator 只管理模式切换和会话级流程。

## 工具注册协议

东方屹腾采用企业管理的封闭工具体系。所有工具由团队注册，Agent 启动时可以建立完整的状态键字典。每个工具在注册时声明：

| 声明项 | 含义 |
| --- | --- |
| 输入参数 | 调用所需的业务参数 |
| 消费坐标 | 参数应从哪个作用域、哪个生产者读取 |
| 输出参数 | 调用成功后产生的业务状态 |
| 生产坐标 | 输出写入哪个作用域和运行层级 |
| 前置条件 | 调用前必须满足的状态或权限 |
| 副作用等级 | 只读、可回滚写入、不可逆写入 |

工具可以同时是机械状态的生产者和消费者。例如，模板匹配工具生产 `template_id`，模板导入工具消费该值。消费者不从叙事上下文解析 ID，而是按注册坐标读取。

## 机械状态与 Provenance

机械状态平面使用 `scope + key` 标识 Cell，并保存当前值及其来源。每次写入都附带 Provenance，至少包含生产工具、调用实例、运行层级和原始回执引用。

<pre><code class="language-go">type Provenance struct {
    ProducerTool string
    RunID        string
    StepID       string
    ReceiptRef   string
}

type Cell struct {
    Scope      string
    Key        string
    Value      any
    Provenance Provenance
}
</code></pre>

工具调用前，RunPipeline 根据消费坐标解析 Cell，并校验来源、作用域和前置条件。缺少参数、来源不匹配或状态过期时立即终止，不向模型请求补值。

完整执行链如下：

<pre><code class="language-text">Skill 声明 SOP
  -&gt; Workspace 确定当前步骤
  -&gt; Tool 声明输入与输出坐标
  -&gt; SessionState 读取 Cell 与 Provenance
  -&gt; RunPipeline 校验并调用 API
  -&gt; 回执解析后写回新的 Cell
</code></pre>

## 存量 API 接入

原有 SaaS API 经网关注册即可进入工具目录。API 的 URL、鉴权和请求结构保持不变；Agent 侧增加工具元数据、状态坐标和调用治理。这样可以复用服务两万多家企业的现有接口矩阵，同时把 Agent 的语义推理与业务参数传递分开。

## 失效信号

- Orchestrator 直接调用工具，绕过行动模块的观察和校验；
- 下游参数从自然语言上下文解析，或由模型重新生成；
- 工具只声明 JSON Schema，没有声明参数来源；
- 同名参数缺少作用域或生产者，无法确定唯一 Cell；
- 写操作没有副作用等级、幂等键或调用后检查；
- 外部工具可以任意热插拔，但系统仍假设状态键可在启动时完整枚举。

## 验证指标

- 工具注册时，输入参数的来源坐标完整率；
- 同一会话内 Cell 坐标的唯一性；
- 写操作参数的 Provenance 覆盖率；
- 多步调用中上游 ID 到下游入参的逐字一致率；
- 缺失、冲突或过期参数的调用前拦截率；
- 工具调用、状态读写与业务回执的事件关联完整率。

## 迁移条件

当多步 API 之间传递数据库 ID、流水号或其他不可重新生成的机械值，并且参数错误会破坏业务数据时，可以采用这套设计。必要条件是工具由组织统一注册，能够声明输入输出坐标并接受调用前校验。

若工具之间主要传递可容忍语义偏差的文本，且错误可以低成本重试，MCP 等开放工具协议通常已经足够，无需引入完整的机械状态平面。

任务级编排复用同一套调用基座，见 [A2 规划执行切片](https://adpsagent.com/zh/patterns/a2-plan-and-execute/cases/liangbo/)。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 工具调度》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>证据边界：</strong>本页是完整案例的模式切片，记录特定系统约束下的实现选择。案例方提供的实现与效果信息未经过独立审计，不构成通用性能承诺。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>；案例提供：梁博</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-a1-tool-dispatch-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
