<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>单图事务：一次提交一个可验证建模增量</h1>
<p class="publication-deck">一种图、一个已解析范围、一次写入和一份回执构成提交边界。</p>
</header>

## 从“完成整个系统模型”开始

“完成闸机系统模型”可能涉及需求图、用例图、块定义图、内部块图和状态图。这个目标没有稳定的单次完成定义，前一张图的偏差还会继续传到后一张图。

## 定义

单图事务把一种图、一个已解析挂载位置、一次写入和一份验收回执组成一个 Unit of Work。

<pre><code class="language-text">一次用户操作 = 一种图类型 + 一个 scope_ref + 一个 WriteSet + 一份回执
</code></pre>

该边界限定本轮允许修改的工程范围、写回前的不变量、实际变更统计和撤销所需的完整变更集。更大的目标由多个可验收事务逐步完成。

## 工程边界

单图事务不保证跨图一致性。上层计划仍需管理多张图之间的依赖、版本和验收顺序。宿主工具缺少原子事务时，适配器需要前态快照、补偿步骤和明确的部分失败状态。

## 来源与谱系

- 初始研究来源：AI4MBSE 建模 Agent 项目，作者袁良锭（Liangding Yuan）；名称由 ADPS 归纳。
- 历史近邻：Unit of Work、Command、transaction boundary。
- ADPS 整理：把图类型、工程范围、候选结构、回执和撤销合成 Agent 写回边界。
- 定义地位：候选概念。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-planning-execution">规划、执行与写回</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始研究实践：袁良锭</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>（<time datetime="2026-08-02">2026-08-02</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将图类型、工程范围、候选结构、回执和撤销合成一次写回边界。</dd></div>
<div><dt>当前地位</dt><dd>候选概念</dd></div>
</dl>
</section>

<div class="document-citation">
<p><strong>初始来源：</strong><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>；作者：袁良锭（Liangding Yuan）。</p>
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>（<time datetime="2026-08-02">2026-08-02</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-one-diagram-unit-of-work">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
