<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>双尺度治理</h1><p class="publication-deck">同时约束当前动作与长程目标，避免每一步合规却逐渐偏离任务。</p></header>

## 应用背景：每一步都合法，任务仍然可能走偏

一个长程研究 Agent 可以合法读取文件、调用搜索和修改草稿，局部检查全部通过。数十轮以后，它却把主要时间花在无关术语和格式细节上，原定交付物没有推进。动作没有越权，目标已经漂移。

## 概念定义

双尺度治理同时运行两组检查：

- **动作尺度**检查当前工具、参数、身份、资源范围、配额和前置条件；
- **目标尺度**比较原始目标、当前计划、已完成产物、剩余风险和外部结果。

动作尺度阻止一次危险调用，目标尺度阻止许多看似合理的小步骤累积成方向偏移。

## 工程用法

运行时事件同时记录 `action_id` 与 `goal_contract_id`。每次工具调用通过动作策略；到达里程碑、成本阈值或时间窗口时，系统根据目标契约复核进展。若产物没有推进、假设已失效或成本偏离，系统暂停、重规划或交还人工，而不是继续增加局部补丁。

## 使用边界

短事务通常只需要动作治理。跨小时、跨会话、跨人员或跨系统的任务需要目标尺度。目标复核的频率应随风险和不可逆程度调整，不能把每一步都变成昂贵的全局重评。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：黄佳</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理模块第一次研讨会</a>（<time datetime="2026-08-18">2026-08-18</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将单步动作合规与长程目标漂移分为两个同时运行的治理尺度。</dd></div>
<div><dt>当前地位</dt><dd>跨模块治理概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理模块第一次研讨会</a>（<time datetime="2026-08-18">2026-08-18</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-18">2026-08-18</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-dual-scale-governance">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
