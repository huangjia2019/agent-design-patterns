<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>双反馈时钟</h1><p class="publication-deck">把任务内即时反馈与跨任务延迟结果分开处理。</p></header>

## 应用背景：当前回复正确，几天后的业务结果仍可能失败

客服 Agent 当场给出一段符合知识库的答复，在线评审判定通过。三天后客户再次来信，说明问题并未解决。Coding Agent 也可能在单元测试通过后提交补丁，直到集成环境或真实用户采用时才暴露兼容问题。两类结果到达的时间不同。

## 概念定义

双反馈时钟把同一任务的即时反馈和延迟反馈分开记录。即时反馈来自格式、规则、测试、工具回执和人工快速评审；延迟反馈来自后续流程、客户复访、业务指标、事故或长期使用。两个时钟共同决定一次运行是否真正成功。

## 工程机制

运行结束时生成可关联的 outcome key，保存 Agent、Prompt、工具、知识和策略版本。即时结果可以关闭当前步骤，但任务在延迟窗口内保持可追踪状态。后续结果到达后，通过 outcome key 回链原 trace，进入经验回放、评测集或规则修订；不能准确归因时标记不确定性。

## 使用边界

能够立即由确定性回执裁决的短事务不必人为延长反馈链。内容建议、客服处理、代码变更和经营决策通常存在延迟结果，需要第二个时钟。采用率和点击率可以提供线索，但不能自动等同于正确。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：李佳奇；整理命名：ADPS</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/reflection-2026-08-12/">反思模块第一次研讨会</a>（<time datetime="2026-08-12">2026-08-12</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将即时结果与跨部门、跨任务的延迟业务结果整理为两个反馈时钟。</dd></div>
<div><dt>当前地位</dt><dd>跨模块概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>定义来源：</strong>ADPS 白皮书研讨与模式整理。</p><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/reflection-2026-08-12/">反思模块第一次研讨会</a>（<time datetime="2026-08-12">2026-08-12</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-12">2026-08-12</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-dual-feedback-clock">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
