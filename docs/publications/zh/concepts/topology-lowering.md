<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>拓扑降阶</h1><p class="publication-deck">把高层协作语义编译为串行、并行和路由等运行原语。</p></header>

## 应用背景：设计图与运行图讲的是两件事

一个代码审查团队在设计上包含任务负责人、多个扫描 Worker、独立评审者和最终裁决者。落到常见工作流框架以后，它可能只剩“路由到多个节点、并行执行、汇总结果、条件回路”几类边。若团队只保存这张运行图，几个月后很难解释哪个节点代表委派、谁有最终裁决权，以及某个失败应由谁收口。

## 概念定义

拓扑降阶是把层级委派、对抗评审、交接链等高层协作设计，编译为运行时支持的串行、并行、路由和循环原语。降阶只改变执行表示，不删除角色、责任、权限和验收语义。

## 工程机制

编译前的设计节点保存 `pattern`、`role`、`owner`、`authority` 和 `acceptance`。运行节点保存对这些字段的引用，并在 trace 中记录当前节点来自哪一个设计决策。这样，层级委派即使执行成“路由—并行—汇总”，最终负责人和 Worker 的权限仍然不同；对抗评审即使执行成一条条件回路，生成、评审和裁决也不会被合并成一个角色。

## 使用边界

拓扑降阶适合框架原语少于设计语言的系统。它不能反向证明所有协作模式都只是三种底层边：相同运行图可能承载完全不同的责任结构。审查时应同时查看设计图、编译映射和运行证据。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-collaboration-runtime">协作与运行时控制</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>工程判断：张栋；整理命名：ADPS</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>张栋提出串行、并行、路由是常见运行原语；ADPS 补入高层责任语义的保留规则。</dd></div>
<div><dt>当前地位</dt><dd>模块级方法概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>定义来源：</strong>ADPS 白皮书研讨与模式整理。</p><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-topology-lowering">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
