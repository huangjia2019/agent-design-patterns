<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>统一收敛节点</h1><p class="publication-deck">让多条推理分支按同一组证据和裁决规则形成一个可执行结论。</p></header>

## 应用背景

一项合同审查可以同时检查付款条款、数据合规和交付风险。三个分支可能各自给出正确结论，却对“是否允许签署”产生冲突。若分支直接把自然语言结论交给下游，执行层只能临时猜测哪一项优先。

## 概念定义

统一收敛节点接收多条推理分支的候选结论、证据引用、未决项和版本，按同一组标准处理冲突，并产出一个明确状态：接受某个结论、合并兼容部分、要求补证或转交人工。它同时规定谁拥有最终裁决权。

```
convergence:
  candidates: [payment_review, compliance_review, delivery_review]
  required_evidence: []
  comparison_rules: []
  hard_conflicts: []
  decision: accept | request_evidence | escalate
  decision_owner: ...
```

## 工程用法

每个分支输出相同的 typed artifact，至少带 `branch_id`、结论、证据引用、未决问题和生成版本。确定性规则先处理缺失证据、禁止条件和版本冲突；模型评审处理语义比较；高风险或无法消解的冲突交给具名责任人。Trace 保留全部候选和最终取舍，不能只留下收敛后的答案。

## 与并行探索和扇出聚合的边界

R3 并行探索产生独立候选，C2 扇出聚合负责分发和回收，统一收敛节点负责比较和裁决。聚合完成只表示结果已经收齐，不表示冲突已经解决；再调用一次更强模型也不会自动补上证据优先级和责任归属。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-collaboration-runtime">协作与运行时控制</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：张栋</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/reasoning-2026-08-26/">推理模块第一次研讨会</a>（<time datetime="2026-08-26">2026-08-26</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将多条推理分支的候选、证据、冲突处理和最终裁决整理为统一接口。</dd></div>
<div><dt>当前地位</dt><dd>推理模块概念</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-unified-convergence-node">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
