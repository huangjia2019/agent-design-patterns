<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>推理资产化：把低频判断固化为运行资产</h1>
<p class="publication-deck">设计期形成可审阅、可认证的能力资产，运行期消费指定版本。</p>
</header>

## 从 GIS 发布任务开始

地图数据发布需要反复执行同一类格式识别、处理、样式生成和服务发布。运行时每次重新让模型选择接口和机械参数，会把名称、坐标和范围重新暴露给概率偏差。玄宿科技把开放判断移到管线设计期，运行时只消费已认证管线。

## 定义

推理资产化把低频、开放、可审阅的判断放在设计期，并把结论固化为带输入合同、版本、验证记录、状态和失效信号的能力资产。运行期读取认证过的管线、规则、模板或技能包，不重复做同一类开放推理。

<pre><code class="language-text">设计期：知识 + 样例 + 模型 + 人工审阅 -&gt; 版本化能力资产
运行期：输入签名 -&gt; 已认证资产 -&gt; 确定性执行 -&gt; 外部验收
</code></pre>

缓存一次回答不构成推理资产化。缓存缺少能力边界、认证证据和版本漂移处理。

## 适用条件

这项设计适合任务类型可枚举、正确性可离线验证、运行偏差代价较高且流程会重复发生的场景。开放意图持续变化时，可以保留稳定资产，同时在入口增加语义收敛；机械参数仍由工具和事实合同产生。

## 来源与谱系

- 初始案例：玄宿科技 GIS 数据发布 Agent，案例提供熊钰柯（Yuke Xiong）。
- 历史近邻：partial evaluation、program specialization、build-time staging、制品化交付。
- ADPS 整理：加入模型生成、人工审阅、认证版本与运行权。
- 定义地位：案例命名。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-planning-execution">规划、执行与写回</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始实践：熊钰柯</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技 GIS 数据发布 Agent 案例</a>（<time datetime="2026-07-30">2026-07-30</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 补入模型生成、人工审阅、认证版本和运行权。</dd></div>
<div><dt>当前地位</dt><dd>案例命名</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-reasoning-assetization">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
