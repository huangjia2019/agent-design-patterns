<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>交接合同</h1><p class="publication-deck">在一次交接中共同转移目标、产物、决定、权限、责任和验收。</p></header>

## 应用背景：完整聊天记录仍然不是一次完整交接

需求 Agent 完成分析后，把数万字对话全部交给实现 Agent。接收方知道讨论过什么，却不知道哪项决定已经确认、哪些方案被否决、自己可以修改哪些资源，以及交付结果由谁验收。上下文很多，责任仍然模糊。

## 概念定义

交接合同是协作节点之间的类型化边界。它传递目标、已有产物、已确认决定、未决问题、权限范围、责任主体、验收条件和下一项必需产物。接收方显式接受或拒绝，发送方的临时权限按策略回收。

## 工程机制

<pre><code class="language-yaml">goal: 保持公共接口兼容并完成服务端修改
artifacts: [spec://417@sha256:...]
decisions:
  - 不修改公共 schema
authority:
  tools: [repo_read, patch_write]
  scope: repo://service-a
acceptance: [unit_tests, contract_tests]
next_required: 可评审补丁与测试证据</code></pre>

合同引用大文件和历史记录，不复制全部内容。若依赖版本、目标范围或权限发生变化，接收方应拒绝旧合同或请求重新签发，而不是静默猜测。

## 使用边界

一次函数调用只需普通参数合同；跨角色、跨 Session、跨团队或跨信任域的交接更需要显式合同。字段可以因领域变化，但目标、产物、决定、权限和验收不应只存在于自然语言聊天中。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-collaboration-runtime">协作与运行时控制</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始问题与建议：王伟；字段结构：ADPS</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将不同团队的 Handoff 协议差异整理为目标、产物、决定、权限和验收字段。</dd></div>
<div><dt>当前地位</dt><dd>研讨会概念</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-handoff-contract">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
