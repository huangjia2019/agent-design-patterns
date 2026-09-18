<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>CodeAct：代码即行动</h1><p class="publication-deck">把可执行代码作为 Agent 的行动语言，用同一空间完成计算、库调用与工具组合。</p></header>

## 应用背景

数据分析 Agent 既要读取表格，又要清洗字段、计算统计量、绘图，并根据报错修改处理逻辑。若每个动作都预先包装成 JSON 工具，工具数量会不断增加，跨工具组合也要多次回到模型。

## 概念定义

CodeAct 把可执行 Python 代码作为统一行动空间。模型可以调用已有函数与软件库、创建局部变量和辅助函数，并根据解释器返回的结果或错误，在下一轮修改此前的行动。原始研究关注代码在单次运行中承担行动；代码的持久化和复用属于另一个问题。

## 与程序化工具调用的边界

两者都让模型写代码。程序化工具调用的中心是已注册工具：代码负责批量调用与压缩中间结果，工具仍经过明确准入。CodeAct 的代码行动更一般，可以直接计算、使用运行环境中的库，并形成新的临时操作。因此 CodeAct 的能力面和攻击面通常都更大。

## 工程用法

运行环境需要隔离文件、进程、网络和凭证，并设置资源与时间上限。代码、依赖、输入摘要、执行结果和错误必须进入 trace；涉及外部写入时，仍需通过 A1 工具调度、A4 护栏和治理机制，不能因为动作以代码表达就绕过权限。

## 与 M5 程序性记忆的边界

一次任务中生成并运行的代码属于 CodeAct。只有当方法经过重复验证，被命名、版本化、声明依赖与触发条件，并获得后续任务的运行许可时，它才成为 M5 程序性记忆。保存一个偶然成功的脚本，并不等于形成了可复用能力。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-reasoning-action-runtime">推理与行动机制</a></dd></div>
<div><dt>术语来源</dt><dd>外部研究术语：Wang 等</dd></div>
<div><dt>公开来源</dt><dd><a href="https://arxiv.org/abs/2402.01030">Executable Code Actions Elicit Better LLM Agents，ICML 2024</a></dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将一次性代码行动与经过认证、可跨任务复用的 M5 程序性记忆分开。</dd></div>
<div><dt>当前地位</dt><dd>执行机制概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://arxiv.org/abs/2402.01030">Executable Code Actions Elicit Better LLM Agents，ICML 2024</a></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-code-as-action">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
