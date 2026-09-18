<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>知识编译</h1><p class="publication-deck">把知识源转换成可直接消费、可追溯、可增量更新的运行资产。</p></header>

## 应用背景：文档已经入库，Agent 仍然找不到可用答案

团队把政策、会议记录和故障报告切块后写入向量库。查询“某项津贴从什么时候生效”时，相似段落很多，却没有一条结果同时给出适用地区、有效时间、被替代版本和原文位置。材料被存储了，还没有被整理成适合运行时消费的知识。

## 概念定义

知识编译是记忆写入侧的转换过程：把原始材料整理为摘要、实体、事件、关系、导航结构和原文指针，并生成全文、向量、字段和图关系等索引。它像编译器前端一样保留源位置，同时产出不同检索器可以消费的结构。

## 工程机制

一次编译记录源文件哈希、解析器版本、切分策略、抽取模型、时间与作用域。产物中的每条结论都能回到原文；材料更新时，只重编译受影响的单元并建立覆盖关系。读取侧根据问题选择全文匹配、向量召回、实体查询或导航，而不是让一种相似度搜索承担所有工作。

## 使用边界

知识编译适合更新频率可管理、来源可以版本化的材料。实时余额、审批状态和订单结果仍由权威业务系统提供，不能通过编译后的摘要替代。自动抽取的结论需要准入和抽样审计，避免错误内容进入长期召回。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-context-memory">上下文与记忆</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 研讨会初始引入：张颖峰</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/memory-2026-08-05/">记忆模块第一次研讨会</a>（<time datetime="2026-08-05">2026-08-05</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将其整理为 M2 写入侧机制，并保留这一术语已有公开技术前史的说明。</dd></div>
<div><dt>当前地位</dt><dd>研讨会概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>定义来源：</strong>ADPS 白皮书研讨与模式整理。</p><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/memory-2026-08-05/">记忆模块第一次研讨会</a>（<time datetime="2026-08-05">2026-08-05</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-05">2026-08-05</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-knowledge-compilation">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
