<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>类型化中间表示链：逐步收敛自然语言结构</h1>
<p class="publication-deck">自然语言逐段收敛为可验证、带类型和稳定引用的候选结构。</p>
</header>

## 从一张用例图开始

用户要求在“闸机控制”包下建立一张用例图。一次调用同时生成对象、关系和画布时，关系可能引用不存在的名称，视图也可能漏掉已经创建的元素。失败后只能整份重做。

## 定义

类型化中间表示链把自然语言意图逐步收敛为可验证的数据结构。AI4MBSE 建模 Agent 项目可以还原为：

<pre><code class="language-text">ModelingJob -&gt; ElementPlan -&gt; RelationPlan -&gt; ViewPlan -&gt; WriteSet
</code></pre>

每一段读取已验收的上游结果，输出带类型、稳定引用和来源的候选结构。验证器检查良构性，写入器只消费通过门禁的 `WriteSet`，不再重新理解自然语言。

## 工程边界

序列化成 JSON 并不自动形成类型化 IR。字段类型、允许值、引用规则和阶段不变量必须由 schema 或验证器执行。阶段可以由多个 Agent、一个 Agent 的多次调用或普通函数完成，进程数量不影响概念成立。

## 来源与谱系

- 初始研究来源：AI4MBSE 建模 Agent 项目，作者袁良锭（Liangding Yuan）；契约名称由 ADPS 依据公开机制还原。
- 历史近邻：compiler IR、typed AST、semantic analysis、database referential integrity。
- ADPS 整理：模型起草候选 IR，程序验收阶段合同，写入器消费已验证结果。
- 定义地位：ADPS 重述。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-planning-execution">规划、执行与写回</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始研究实践：袁良锭</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>（<time datetime="2026-08-02">2026-08-02</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 依据公开机制还原阶段合同，并明确候选 IR、验证器和写入器的职责。</dd></div>
<div><dt>当前地位</dt><dd>ADPS 重述</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-typed-ir-chain">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
