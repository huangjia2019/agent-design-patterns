<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>ReAct 推理—行动循环</h1><p class="publication-deck">在推理与行动之间交替推进，让下一步使用刚获得的外部观察。</p></header>

## 应用背景

客服 Agent 收到“为什么这个订单还没到”时，第一步可以查询订单。若结果显示包裹尚未出库，下一步应读取仓库状态；若已经交给承运商，则应查询物流轨迹。后续动作取决于刚拿到的观察，事先很难写成一条固定链。

## 概念定义

ReAct 让语言模型交替产生推理和任务动作。动作作用于知识库、工具或外部环境，环境返回观察，模型再据此更新判断和后续行动。原始论文关注推理轨迹与行动的交错；生产系统通常保存结构化的决策摘要、动作和观察，不依赖暴露模型的隐藏思维过程。

```
request
  → decide next action
  → call one tool
  → receive typed observation
  → decide again
  → stop, escalate, or act
```

## 工程用法

每轮都要带同一个任务标识，并记录动作、参数来源、观察类型和停止原因。Harness 控制最大轮次、token 与工具预算、允许调用的工具、错误返回格式和人工接管条件。观察结果应先通过 schema 校验，再进入下一轮；工具报错不能被改写成“没有结果”。

## 与程序化工具调用和 CodeAct 的区别

ReAct 在每次观察后重新调用模型，适合需要持续判断的开放路径。程序化工具调用先生成一段局部程序，再由程序循环、并行或筛选已注册工具。CodeAct 的行动空间更宽，允许可执行代码直接承担计算、库调用和工具组合。三者可以嵌套，例如 ReAct 某一轮选择运行一段程序化工具调用。

## 使用边界

步骤和依赖已经稳定时，任务 DAG 或 A2 规划执行通常更容易测试和恢复。ReAct 适合保留必要的运行时判断，不宜承载不可逆动作的全部顺序、权限和验收规则。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-reasoning-action-runtime">推理与行动机制</a></dd></div>
<div><dt>术语来源</dt><dd>外部研究术语：Yao 等</dd></div>
<div><dt>公开来源</dt><dd><a href="https://arxiv.org/abs/2210.03629">ReAct：协同语言模型中的推理与行动，2022</a></dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将 ReAct 作为连接推理与行动的运行机制记录，并明确它不单独占用模式坐标。</dd></div>
<div><dt>当前地位</dt><dd>执行机制概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://arxiv.org/abs/2210.03629">ReAct：协同语言模型中的推理与行动，2022</a></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-react-loop">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
