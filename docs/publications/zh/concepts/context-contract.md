<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>上下文合同</h1><p class="publication-deck">规定一类任务允许进入推理窗口的信息、来源、时效与预算。</p></header>

## 应用背景：把整个仓库塞进上下文，仍然可能缺少最关键的信息

一个 Coding Agent 收到了几十个源码文件，却不知道这次修改为什么发生、哪些接口不能动、成功需要通过哪些检查。另一个 Agent 只收到一句“修复登录问题”，连错误日志和复现步骤都没有。两者的问题分别是信息过量和关键证据缺失。

## 概念定义

上下文合同规定某类任务开始前必须具备的信息、允许加载的信息、来源优先级和验收材料。常用结构包括 Why（目标与业务原因）、What（对象、范围与非目标）、How（约束、接口和可用能力）以及 Acceptance（测试、回执或人工裁决）。

## 工程机制

P1 信息在任务开始前必须具备，例如目标对象、权限范围和不可破坏的接口；缺失时进入澄清。P2 信息按步骤加载，例如相邻实现、历史决策和领域材料；它们可以通过检索补充，但必须保留来源、版本和适用范围。合同本身进入版本管理，任务 trace 记录实际加载了哪些条目。

## 使用边界

上下文合同不追求一次性收集全部资料。它通过必需项和按需项控制信息边界，适合需求分析、代码修改、企业知识问答和工具执行。对开放探索任务，Why 与验收可以较宽；涉及写操作时，目标、权限和机械状态必须收紧。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-context-memory">上下文与记忆</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始议题：黄佳；工程实践：黄湘龙；整理命名：ADPS</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/perception-2026-08-13/">感知模块第一次研讨会</a>（<time datetime="2026-08-13">2026-08-13</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将 Why、What、How、验收材料与 P1/P2 的信息边界整理为可测试合同。</dd></div>
<div><dt>当前地位</dt><dd>跨模块概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>定义来源：</strong>ADPS 白皮书研讨与模式整理。</p><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/perception-2026-08-13/">感知模块第一次研讨会</a>（<time datetime="2026-08-13">2026-08-13</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-context-contract">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
