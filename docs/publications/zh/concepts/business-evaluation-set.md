<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>业务评测集</h1><p class="publication-deck">用业务流程、代表场景、权重和指标判断技术改动是否改善了业务结果。</p></header>

## 应用背景

一套工单 Agent 的字段抽取准确率提高，并不必然缩短工单处理时间。新增澄清步骤可能提升局部正确率，同时增加转人工比例和客户等待。技术回归集能发现能力退化，业务仍需要另一套观察尺度。

## 概念定义

业务评测集由关键业务流程、代表场景、场景权重、指标口径和验收条件组成。它把 Agent 版本放进端到端任务中，观察完成时间、一次解决率、人工接管、错误动作、业务损失或其他领域结果。场景权重来自业务量与风险，不能由模型自行决定。

```
business_evaluation_set:
  business_process: ...
  scenarios:
    - id: ...
      weight: ...
      metric: ...
      data_definition: ...
      acceptance: ...
  owner: ...
  version: ...
  change_log: []
```

## 工程用法

产品、业务和工程团队共同定义样本抽取、指标分母、时间窗口和例外处理。结果按场景分别报告，再按已登记权重汇总。模型或工作流改动通过技术回归后，还要在业务评测集中检查业务流程是否实际改善，以及是否把成本转移给人工岗位或下游系统。

## 与技术评测集的边界

业务评测集不替代结构校验、事实正确性、安全、性能和稳定性测试。技术评测回答组件是否符合规格，业务评测回答整条流程是否得到改善。两套资产可以由不同责任人维护，但发布回执需要同时引用它们的版本和结果。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：李娣娣</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/reasoning-2026-08-26/">推理模块第一次研讨会</a>（<time datetime="2026-08-26">2026-08-26</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将业务流程、代表场景、场景权重、指标口径和版本记录整理为业务层评测资产。</dd></div>
<div><dt>当前地位</dt><dd>X2 下的跨模块概念</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-business-evaluation-set">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
