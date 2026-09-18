<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>概率内核与确定性外壳</h1><p class="publication-deck">模型处理开放判断，确定性机制守住生产边界。</p></header>

## 应用背景：模型可以判断意图，不能靠“差不多”转账

用户用自然语言描述一笔复杂付款，模型适合提取目标、识别缺失信息并提出候选步骤。到了收款人身份、金额精度、账户状态、授权额度和幂等提交，这些条件必须得到同样输入时给出同样结果，并留下可复核证据。

## 概念定义

概率内核承担开放理解、规划和候选生成；确定性外壳承担身份、状态、权限、约束、测试、提交和外部回执。内核可以提出动作，外壳决定动作能否获得执行资格，并验证现实世界是否真的改变。

## 工程机制

```
自然语言目标
  → 模型生成结构化 Intent
  → schema / policy / state / authority 校验
  → 受控工具调用
  → 回执与写后读取
  → 结果进入 trace 与后续评测
```

外壳并不要求把全部流程写死。模型仍可以动态选择候选工具和步骤，但只能从带版本的能力中选择，提交前后必须通过可重复的检查。

## 使用边界

创意写作等低风险内容任务可以使用较薄的外壳。会改变资金、数据、权限、生产配置或用户权益的任务需要更厚的外壳。确定性外壳也会出错，因此策略、schema 和校验器本身仍需版本、测试和观测。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-system-boundaries">系统边界与状态</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>工程判断：张栋；外壳表述：黄佳</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将模型的开放判断与身份、状态、权限、测试和外部回执的确定性控制连接起来。</dd></div>
<div><dt>当前地位</dt><dd>跨模块架构概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>定义来源：</strong>ADPS 白皮书研讨与模式整理。</p><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-25">2026-08-25</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-probabilistic-core-deterministic-shell">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
