<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>Agent 的三种权力</h1><p class="publication-deck">从信息、裁决和行动三个入口检查 Agent 获得了什么权力。</p></header>

## 应用背景：系统在调用工具之前已经获得了两种权力

审核一个付款 Agent 时，人们往往只看它能否调用转账接口。实际风险更早出现：检索结果决定模型看见哪些收款记录，评测规则决定什么结果可以被判为“通过”，工具权限才决定这项判断能否变成真实转账。三个入口分别改变决策、结论和现实。

## 概念定义

Agent 的工程权力可以沿三条链检查：

- **信息权**：什么信息有资格进入上下文并影响判断；
- **裁决权**：什么规则、评审者或外部证据有资格证明结果正确；
- **行动权**：什么身份和权限有资格改变文件、数据库、账户或其他外部资源。

三种权力可能由不同组件持有。检索器掌握信息入口，评测器或审批人掌握裁决，工具网关掌握行动。设计审查需要把它们分别列出，不能用一张工具权限表代替。

## 工程用法

在薪酬变更中，政策库只提供带版本的规则，不能直接修改员工记录；评测器可以判定参数是否符合政策，不能签发业务授权；执行器只消费已经批准且仍满足前置条件的 Intent。这样，一处组件失误不会同时获得解释规则、宣布合格和执行变更的全部权力。

## 使用边界

这个概念用于威胁建模、职责分离和架构评审。它不要求每种权力都由独立服务承担，但要求系统能指出权力位于哪里、依据是什么、由谁改变，以及证据如何保留。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：黄佳</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理模块第一次研讨会</a>（<time datetime="2026-08-18">2026-08-18</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将信息影响决策、标准裁决结果和权限改变现实世界区分为三种权力。</dd></div>
<div><dt>当前地位</dt><dd>跨模块架构概念</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-three-powers-of-agency">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
