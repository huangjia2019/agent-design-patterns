<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>失败到规则闭环：让事故改变下一次运行</h1>
<p class="publication-deck">事故卡回链规则、默认值、约束或测试，并由后续同类任务验证。</p>
</header>

## 从一张失败卡开始

浏览页模板同时包含 Python `string.Template` 和 JavaScript `${...}`。两套占位符语法冲突，造成图例空白或页面生成失败。若复盘只写“模板有问题”，后续生成仍可能重复同一错误。

## 定义

失败到规则闭环要求事故记录产生可验证的系统变化。失败卡至少保存现象、错误签名、根因、即时处置、防复发动作和来源；防复发动作必须指向规则、默认值、模板约束、测试或生成资产。

<pre><code class="language-text">运行失败 -&gt; 结构化事故卡 -&gt; 人工复核 -&gt; 规则或资产变更
    ^                                      |
    +------------- 同类样例验证 -----------+
</code></pre>

闭环的终点是同类任务行为改变。完成文档、没有资产变更和验证，仍属于事故记录。

## 工程边界

重复、可枚举且可以验证的失败适合规则化。开放问题可以保留人工判断或离线分析。根因未经复现实验证实前，模型可以起草失败卡，不能自行把猜测升级为运行规则。

## 来源与谱系

- 初始案例：玄宿科技 GIS 数据发布 Agent，案例提供熊钰柯（Yuke Xiong）。
- 历史近邻：SRE postmortem、corrective action、failure journal、regression test。
- ADPS 整理：要求事故卡回链运行规则或能力资产，并通过后续样例验证防复发。
- 定义地位：候选概念。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：熊钰柯</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例</a>（<time datetime="2026-07-30">2026-07-30</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 要求失败记录回链规则、测试、默认值或能力资产，并验证防复发。</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-failure-to-rule-loop">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
