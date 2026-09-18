<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>能力认证生命周期：能力如何取得自动运行权</h1>
<p class="publication-deck">能力按 draft、candidate、active 逐步取得运行权，版本漂移后自动失效。</p>
</header>

## 从一条新管线开始

Coding Agent 生成一条新的数据发布管线，并不意味着它可以立刻自动接收生产任务。团队需要先显式运行完整样例，检查真实交付，再决定是否开放自动路由。

## 定义

能力认证生命周期规定生成或修改后的能力怎样取得、保持和失去自动运行权。玄宿案例采用三种状态：

<pre><code class="language-text">draft -&gt; candidate -&gt; active
草稿      已通过首跑      获得自动接单权
</code></pre>

首次完整运行通过证据门后进入 `candidate`；人员确认范围和风险后进入 `active`。代码、模板或关键规则发生版本漂移时，旧认证自动失效，能力退回待认证状态。

## 工程边界

状态必须控制真实运行权限，不能只作为页面标签。认证要绑定具体版本、样例和证据。高风险能力还需要权限、影响范围和回滚能力共同参与准入。

## 来源与谱系

- 初始案例：玄宿科技 GIS 数据发布 Agent，案例提供熊钰柯（Yuke Xiong）。
- 历史近邻：artifact registry、staging/production promotion、model registry、progressive delivery。
- ADPS 整理：把对象扩展为管线、技能、工具封装或 Agent 子流程，并明确自动运行权。
- 定义地位：候选概念。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：熊钰柯</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例</a>（<time datetime="2026-07-30">2026-07-30</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将认证对象扩展到管线、Skill、工具封装与子流程，并明确自动运行权。</dd></div>
<div><dt>当前地位</dt><dd>候选概念</dd></div>
</dl>
</section>

<div class="document-citation">
<p><strong>初始来源：</strong><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例报告</a>；案例提供：熊钰柯（Yuke Xiong）。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例</a>（<time datetime="2026-07-30">2026-07-30</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-07-30">2026-07-30</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-capability-certification-lifecycle">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
