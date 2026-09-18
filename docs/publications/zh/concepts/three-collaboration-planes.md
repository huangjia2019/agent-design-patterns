<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>三类协作关系</h1><p class="publication-deck">同时审查 Agent-Agent、Human-Agent 与 Agent 环境中的 Human-Human。</p></header>

## 应用背景：Agent 之间交接成功，团队仍可能失忆

需求 Agent 把规格交给编码 Agent，编码 Agent 再把补丁交给评审 Agent，机器链路看起来完整。与此同时，产品、架构和测试人员在会议里决定“不修改公共 schema，并在下一版本补兼容层”。如果这项决定只留在聊天中，下一轮 Agent 仍可能重新提出已经否决的方案。

## 概念定义

Agent 系统中的协作至少包含三个平面：Agent-Agent 负责拆分、并行、交接和复核；Human-Agent 负责表达意图、补充证据、批准、接管和验收；Human-Human 负责团队决定、责任延续和组织规则。第三个平面发生在人之间，但会直接改变 Agent 后续可以做出的判断。

## 工程机制

三个平面通过版本化产物连接。Agent 交接使用 Handoff Contract；人与 Agent 的澄清、审批和接管进入可恢复的运行事件；会影响后续工作的团队决定进入 RFC、ADR、runbook 或项目规则，并保留来源和适用范围。原始会议和聊天无需整段入库，只提取会改变目标、约束、权限或验收的决定。

## 使用边界

三类关系不是三套独立系统。它们用于检查协作图是否遗漏了人和组织。低风险、短时任务可以只保留轻量记录；长程任务和多人项目需要把三个平面的关键决定接入同一条证据链。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-collaboration-runtime">协作与运行时控制</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：王伟</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将 Agent-Agent、Human-Agent 和 Agent 环境中的 Human-Human 关系整理为统一设计视角。</dd></div>
<div><dt>当前地位</dt><dd>跨模块概念</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-three-collaboration-planes">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
