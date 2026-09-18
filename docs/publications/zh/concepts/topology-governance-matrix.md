<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>拓扑治理矩阵</h1><p class="publication-deck">用身份、权限、防护与溯源检查串行、并行和路由结构。</p></header>

## 应用背景：画出并行分支，还没有回答谁能看什么

一个负责人把 800 份简历分给多个 Worker 并行核验。运行图说明了怎样分片和汇总，却没有说明 Worker 以谁的身份工作、能读取哪些字段、是否可以写回，以及汇总者如何追溯每条结论。若所有 Worker 直接继承负责人的长期 Token，并行会把最大权限同时复制到全部分支。

## 概念定义

拓扑治理矩阵把串行、并行和路由等运行结构，与身份、权限、防护和溯源四个控制维度交叉检查。前者说明控制如何展开，后者判断这种展开是否具备生产条件。

## 工程机制

<table><thead><tr><th>结构</th><th>需要额外回答的问题</th></tr></thead><tbody><tr><td>串行</td><td>每一跳代表谁，交接后哪些临时权限必须回收，错误怎样阻止继续下传</td></tr><tr><td>并行</td><td>分片是否隔离，聚合者是否默认只读，子链路怎样归入同一 trace</td></tr><tr><td>路由</td><td>路由依据是否留证，高风险分支是否收紧权限，未知类型怎样兜底</td></tr></tbody></table>

有效权限通常取用户授权、任务范围、Agent 职责、工具能力和资源边界的交集。矩阵应在设计评审、部署检查和事故复盘中使用同一组字段。

## 使用边界

矩阵是一张检查表，不代替 IAM、策略引擎或观测系统。它的价值在于暴露“图画完了但控制没有设计”的空白，并让不同拓扑使用可比较的生产准入问题。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-collaboration-runtime">协作与运行时控制</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：张栋</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/collaboration-2026-08-25/">协作模块第一次研讨会</a>（<time datetime="2026-08-25">2026-08-25</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 按公开口径整理身份、权限、防护和溯源四层检查表。</dd></div>
<div><dt>当前地位</dt><dd>研讨会概念</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-topology-governance-matrix">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
