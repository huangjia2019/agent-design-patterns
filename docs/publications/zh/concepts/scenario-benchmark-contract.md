<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>场景–Benchmark 契约</h1><p class="publication-deck">用生产场景与对应评测集共同规定能力边界、准入线和换版条件。</p></header>

## 应用背景

同一个客服 Agent 在退款、物流查询和企业合同三类任务上的错误代价完全不同。只写“准确率达到 85%”无法说明样本来自哪里，也无法回答高风险场景是否被平均分掩盖。模型、Prompt、Harness 或工具换版后，旧结果也可能失去效力。

## 概念定义

场景–Benchmark 契约把一组生产场景和对应评测集绑定起来，共同规定能力开发的边界、准入线与持续回归条件。每个场景记录输入来源、预期结果、错误代价、验收阈值和适用版本；上线后的 bad case 回到相应场景，而不是混入一个没有边界的总分。

```
scenario_benchmark_contract:
  scenario_scope: []
  sample_sources: []
  error_costs: {}
  acceptance_thresholds: {}
  bound_versions:
    model: ...
    prompt: ...
    harness: ...
    tools: ...
  production_feedback: []
  owner: ...
```

## 工程用法

团队先从真实任务流中选取场景，再为高风险或高频场景单独设阈值。每次候选版本都运行同一份冻结集，并另报新出现的生产样本。发布回执保存契约版本、组件版本、逐场景结果和例外批准；任一绑定组件或错误代价改变时，触发重新评测。

## 使用边界

这份契约只说明已经覆盖的能力范围，不承诺未覆盖任务上的自动泛化。它也不替代安全、性能和恢复测试。场景边界扩大、业务口径改变或关键组件换版时，需要建立新版本并保留前后差异。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：张栋</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/reasoning-2026-08-26/">推理模块第一次研讨会</a>（<time datetime="2026-08-26">2026-08-26</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将生产场景、样本来源、错误代价、验收阈值和组件版本整理为同一份能力契约。</dd></div>
<div><dt>当前地位</dt><dd>跨模块概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/reasoning-2026-08-26/">推理模块第一次研讨会</a>（<time datetime="2026-08-26">2026-08-26</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-09-04">2026-09-04</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-scenario-benchmark-contract">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
