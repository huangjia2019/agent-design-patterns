<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>结构写回门禁：在副作用前检查工程不变量</h1>
<p class="publication-deck">候选结构通过范围、类型、引用、完整性和真实增量检查后才能写入。</p>
</header>

## 从“看起来成功”开始

建模 Agent 可以画出一张像样的图，模型库里仍然存在悬空关系、错误归属、重复对象或空变更。等到写回后再让模型点评，工程状态已经被污染。

## 定义

结构写回门禁位于候选计划与正式工程模型库之间。它在产生副作用前检查：

1. 范围存在、唯一且允许写入；
2. 元素、关系和图类型合法；
3. 每条关系的端点形成引用闭包；
4. 用户明确列举的对象完整进入计划；
5. 视图内容是已验收模型结果的子集；
6. 写入产生真实增量，空增量记录为 `NOOP`；
7. 模型库和画布经过唯一写回通道，并生成回执与撤销句柄。

结果使用有限枚举：`APPLIED`、`APPLIED_WITH_WARNINGS`、`BLOCKED`、`NOOP`。

## 工程边界

门禁检查可程序化的不变量，不承担全部建模品质评审。命名、粒度和方案合理性可在写前人审、生成评审或离线评估中处理。

## 来源与谱系

- 初始研究来源：AI4MBSE 建模 Agent 项目，作者袁良锭（Liangding Yuan）；ADPS 依据公开机制归纳。
- 历史近邻：admission controller、database constraint、precondition、transaction validation。
- ADPS 整理：把验证对象换成 Agent 候选结构，并把裁决连到写回回执和结果状态。
- 定义地位：ADPS 重述。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-planning-execution">规划、执行与写回</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始研究实践：袁良锭</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>（<time datetime="2026-08-02">2026-08-02</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将工程不变量检查连到真实写回回执和结果状态。</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-structural-writeback-gate">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
