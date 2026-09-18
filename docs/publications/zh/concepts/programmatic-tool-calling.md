<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>程序化工具调用</h1><p class="publication-deck">让模型生成一段受限程序，批量调用已注册工具并在进入上下文前处理结果。</p></header>

## 应用背景

财务 Agent 要找出一个部门中超出差旅额度的员工。普通工具调用会先取员工列表，再逐人查询费用和额度；每次结果都回到模型，调用次数和上下文随人数增长。这个步骤实际需要一段循环、若干并行查询和一次确定性汇总。

## 概念定义

程序化工具调用让模型写一段短程序，在受限执行环境中调用已经注册并明确准入的工具。程序处理循环、条件、并行、聚合和错误分支，中间数据可以留在执行环境，最终只把必要结果送回模型。

```
members = await get_members("engineering")
expenses = await gather(get_expenses(m.id) for m in members)
limits = await get_limits(unique(m.level for m in members))
print(find_exceeded(members, expenses, limits))
```

上例没有临时发明 `get_expenses`。这些工具已经注册；临时生成的是调用和处理它们的程序。

## 工程用法

只有显式允许被代码调用的工具进入运行环境。沙箱限制 CPU、内存、执行时长、循环次数、文件读写和网络出口；工具权限仍按当前主体、资源和 Intent 检查。Trace 要同时记录生成代码版本、每次实际工具调用、中间错误、stdout 和最终返回。

## 与 ReAct 和 CodeAct 的区别

ReAct 每取得一次观察，模型就再次决定下一步。程序化工具调用把一段局部控制流交给代码，因此能减少模型往返和大批中间结果。CodeAct 把可执行代码作为更通用的行动空间，可以使用库、计算和动态生成的辅助函数，不限于调用注册工具。

## 在 ADPS 中的位置

它连接 A1 工具调度和 A2 规划执行：A2 确定当前步骤，PTC 在步骤内部组合多次工具调用，A1 仍负责工具注册、候选范围和每次准入。程序只服务当前运行时，它还是执行机制；经过测试、命名、版本化并允许跨任务调用后，才成为 M5 程序性记忆。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-reasoning-action-runtime">推理与行动机制</a></dd></div>
<div><dt>术语来源</dt><dd>外部工程术语：Anthropic</dd></div>
<div><dt>公开来源</dt><dd><a href="https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling">Anthropic Programmatic Tool Calling 文档</a></dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将其放在 A1 工具调度与 A2 规划执行的交界，并补充与 ReAct、CodeAct 和 M5 的边界。</dd></div>
<div><dt>当前地位</dt><dd>执行机制概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling">Anthropic Programmatic Tool Calling 文档</a></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-programmatic-tool-calling">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
