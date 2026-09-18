<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>持久化意图</h1><p class="publication-deck">让审批等待与恢复执行指向同一个不可变动作。</p></header>

## 应用背景：审批人看到的动作，恢复时可能已经变了

审批人同意“把员工 E-1842 的交通津贴从 800 调到 1000，下月生效”。Agent 暂停数小时后恢复，期间员工状态、当前金额、政策版本或工具版本发生变化。若系统只保存一个“已批准”布尔值，执行器无法证明现在提交的仍是原动作。

## 概念定义

持久化意图是在等待、重试和恢复期间保持稳定的规范化动作记录。它冻结主体、目标资源、期望变化、工具与参数版本、风险、前置条件和恢复策略。审批针对该意图的摘要签发，而不是笼统批准一段会继续变化的对话。

## 工程机制

系统分别保存 Intent、Approval 和 Execution。Approval 绑定意图哈希、审批人、有效期和消费次数；恢复时重新读取可变状态，检查员工是否仍在职、当前值是否仍为 800、政策是否仍适用。前置条件不成立时，旧批准失效并重新审批或终止。

## 使用边界

不跨等待点的只读请求通常不需要持久化意图。涉及审批、异步队列、外部重试或不可逆写入时，它把“当时同意了什么”与“后来实际做了什么”连接起来。意图不能冻结现实世界，因此恢复复验是必要组成部分。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-verification-governance">评测、反思与治理</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：徐一博</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理模块第一次研讨会</a>（<time datetime="2026-08-18">2026-08-18</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将研讨中的 Durable Intent 连接到 G1 审批门，并补充 Intent、Approval、Execution 三段记录。</dd></div>
<div><dt>当前地位</dt><dd>研讨会概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>定义来源：</strong>ADPS 白皮书研讨与模式整理。</p><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理模块第一次研讨会</a>（<time datetime="2026-08-18">2026-08-18</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-18">2026-08-18</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-durable-intent">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
