<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a><span style="margin:0 0.45rem;">/</span><a href="https://adpsagent.com/zh/patterns/r1-chain-of-thought/" style="color: var(--color-text-muted);">R1 思维链</a><span style="margin:0 0.45rem;">/</span>蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 模式实践切片</p>
<h1>R1 · 思维链 · 东方屹腾执行型 Agent</h1>
<p class="publication-deck">每轮推理输出叙事结论和一个可映射到程序动作的下一步控制信号。</p>
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
<td style="text-align: left;">R1 思维链 Chain-of-Thought（推理 × 链式）</td>
</tr>
<tr>
<td style="text-align: left;">结合模式</td>
<td style="text-align: left;">R2 复杂度路由 · A1 工具调度</td>
</tr>
<tr>
<td style="text-align: left;">案例</td>
<td style="text-align: left;">上海东方屹腾科技 · HR/薪酬 SaaS · 服务 2 万+ 企业 · 执行型 Agent</td>
</tr>
<tr>
<td style="text-align: left;">对应白皮书</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/r1-chain-of-thought/">/zh/patterns/r1-chain-of-thought/</a></td>
</tr>
<tr>
<td style="text-align: left;">源</td>
<td style="text-align: left;">梁博 AICon 逐字稿第三章 · PPT 第 13 页</td>
</tr>
<tr>
<td style="text-align: left;">工程结论</td>
<td style="text-align: left;">每轮推理读取 ReasonContext，输出供后续使用的叙事结论和一个可执行的下一步控制信号。</td>
</tr>
</tbody>
</table>

---

## 场景约束

意图网关返回 `resolve`，只说明用户请求需要执行。系统还要判断下一步是检索知识、调用 Skill、进入任务规划、继续推理还是结束。这个判断必须映射到程序已经注册的动作。

固定一次分类调用适合意图识别，无法覆盖会随工具回执变化的事务流程。东方屹腾使用链式推理逐轮处理最新上下文，并设置最大步数和退出信号。

## 输入结构

推理输入由 `ReasonContext` 组装，包含：

- 用户原始目标；
- 意图识别结论；
- 当前任务和关键进展；
- 检索结果或工具观察；
- 相关经验；
- 当前允许选择的动作类型。

`ReasonContext` 从少量字段逐步扩展，字段由真实调用需要决定。机械参数和任务调度状态保持在各自状态平面，不以自然语言复制值。

## 输出契约

每轮输出分为两类：

1. **叙事结论**：对当前输入的分析摘要，写入叙事状态，供规划、行动和最终回复使用；
2. **控制信号**：结构化的下一步动作，交给 Orchestrator。

<pre><code class="language-json">{
  "analysis_summary": "已确认需要从模板库匹配薪资组",
  "next_action": "retrieve_skill",
  "target": "salary_group_template",
  "done": false
}
</code></pre>

有些模型接口支持独立的 reasoning summary 或分析字段；系统只存接口明确返回且允许使用的内容，不依赖模型隐藏推理过程。

## 单步决策

链式推理每轮只决定下一步。工具执行会改变业务状态，后续动作应根据真实回执重新评估。任务结构已经明确时，控制信号可以转入规划执行，由 DAG 维护完整步骤；结构不明确时继续单步推理或 ReAct。

控制信号必须映射到有限动作集合，例如：

<pre><code class="language-text">retrieve_knowledge
retrieve_skill
invoke_action
plan_tasks
continue_reasoning
finish
escalate
</code></pre>

未知动作、Schema 解析失败或达到步数上限时进入确定的兜底分支。

## 案例运行

薪资组请求进入 `resolve` 后，首轮推理可能输出 `retrieve_skill`。Skill 和相关经验加入 ReasonContext 后，下一轮决定匹配模板；收到工具回执后，再判断任务依赖是否已明确并转入规划执行。

每次模型调用的输入引用、输出摘要、控制信号、模型版本和成本进入 Activity/Frame 时间线。

## 失效信号

- 输出只有自然语言，没有程序可消费的动作；
- `next_action` 可以自由生成，无法映射到注册能力；
- 一次生成全部步骤，却不根据工具回执更新；
- ReasonContext 持续累积所有历史；
- 解析失败后无限重试或随机选择动作；
- 系统依赖不可访问的隐藏推理内容。

## 验证指标

- 控制信号 Schema 解析成功率；
- 信号到注册动作的映射成功率；
- 平均推理步数和步数上限触发率；
- 因过早规划导致的 replan 次数；
- 叙事结论到后续决策的引用完整率；
- 解析失败后的安全退出率。

## 与白皮书的对应

R1 白皮书强调推理输出必须进入工程控制流。东方屹腾将叙事结论和结构化动作分离，并由 Orchestrator 消费下一步信号。JSON 解析失败使用预定义回退，不把格式异常传播到行动模块。

## 迁移条件

当任务由多次状态变化驱动、下一步必须根据最新回执决定时，适合使用这种链式推理。一次即可完成的内容生成任务不需要为每轮增加控制信号和 ReasonContext。

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS、梁博，《东方屹腾 · 思维链》，企业 Agent 系统蓝皮书 v0.4，2026-08-02。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-r1-chain-of-thought-cases-liangbo">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
