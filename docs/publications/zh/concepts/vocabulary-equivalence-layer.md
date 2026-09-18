<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/concepts/" style="color: var(--color-text-muted);">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 工程概念</p>
<h1>词表等价层：对齐规划词表与宿主元模型</h1>
<p class="publication-deck">以版本化映射对齐规划词表、领域类型和宿主元模型。</p>
</header>

## 从一次类型误杀开始

这个问题出现在 Agent 需要写入既有工程工具的场景。用户和规划器使用领域语言，宿主系统却已经有固定的类型系统、枚举和版本。两边讲的可能是同一个业务对象，字面名称却不一样。

例如，用户要在 SysML 模型中创建“系统参与者”，规划器输出 `SystemActor`，建模工具可能按 UML 元模型存为 `uml:Actor`，写回 API 又只返回归一化后的 `Actor`。若验收代码直接比较字符串，这次合法写入会被判定为类型错误。

同类情况也存在于 CRM 的“客户 / 账户 / 联系人”、GIS 的“图层 / 要素类 / 发布服务”，以及云 IAM 的“用户 / 主体 / 服务账号”之间。系统需要的是一层可测试的语义等价关系，不是散落在提示词和适配器里的别名判断。

## 定义

词表等价层显式映射规划词表、规范领域类型、宿主元模型类型和写回返回类型。

<pre><code class="language-text">planning type
  -&gt; canonical domain type
  -&gt; host metamodel type
  -&gt; returned write-back type
</code></pre>

映射处理别名、继承、兼容类型、图类型差异和宿主版本。规划器、验证器和写入器引用同一份映射资产，并在日志中保留原始值与每次转换。

## 工程边界

映射需要版本、单元测试和宿主升级回归。它解决确定性语义适配，不替代开放领域知识检索。转换记录缺失时，适配器 bug 很容易被误判为模型幻觉。

## 来源与谱系

- 初始研究来源：AI4MBSE 建模 Agent 项目，作者袁良锭（Liangding Yuan）；名称由 ADPS 归纳。
- 历史近邻：Adapter、Anti-Corruption Layer、schema mapping、canonical data model。
- ADPS 整理：将映射作为按图类型和宿主版本选择的可测试运行资产。
- 定义地位：ADPS 重述。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-planning-execution">规划、执行与写回</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始研究实践：袁良锭</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>（<time datetime="2026-08-02">2026-08-02</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将词表映射整理为按图类型和宿主版本选择的可测试运行资产。</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-vocabulary-equivalence-layer">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
