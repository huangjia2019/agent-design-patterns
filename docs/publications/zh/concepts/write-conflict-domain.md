<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>写入冲突域</h1><p class="publication-deck">识别并行任务可能共同改变的文件、标识、配置、领域对象和外部环境。</p></header>

## 应用背景：两个 Agent 没改同一文件，仍然互相覆盖

两个 Coding Agent 在不同 worktree 中开发不同服务。一个为新需求申请编号 `REQ-417`，另一个也从同一张表取到这个编号；或两者分别修改客户端和服务端，却对公共 API 做出不兼容假设。Git 文件没有冲突，业务写入已经冲突。

## 概念定义

写入冲突域是一组不能无协调并发修改的对象。它可以是文件，也可以是编号空间、公共配置、数据库记录、测试环境、API 合同、部署槽位、云端配额或外部业务资源。冲突域由“共同改变什么”定义，而不只由仓库路径定义。

## 工程机制

调度前，任务声明预计读写集和资源键，例如 `api:customer-v2`、`db:tenant-17/payroll`、`env:uat-3`。调度器据此选择串行、分片、租约或合并策略。运行中发现新的共享对象时，Agent 必须扩大冲突域并重新调度，不能继续假设隔离成立。

## 使用边界

精确静态推断所有写集通常不现实。高风险未知对象应先串行，确认分片规则后再并行。Worktree 仍然适合隔离代码文件，但不能替代领域对象、外部资源和版本合同的冲突检查。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-collaboration-runtime">协作与运行时控制</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>初始问题：唐洪山；实践补充：Pylon PENG、王伟；整理命名：ADPS</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/action-2026-08-06/">行动模块第一次研讨会</a>（<time datetime="2026-08-06">2026-08-06</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将文件冲突扩展到编号、配置、数据库记录、测试环境和外部资源。</dd></div>
<div><dt>当前地位</dt><dd>跨模块概念</dd></div>
</dl>
</section>

<div class="document-citation"><p><strong>定义来源：</strong>ADPS 白皮书研讨与模式整理。</p><p><a href="https://adpsagent.com/zh/concepts/">概念目录</a> · <a href="https://adpsagent.com/zh/workshops/">研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/action-2026-08-06/">行动模块第一次研讨会</a>（<time datetime="2026-08-06">2026-08-06</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-06">2026-08-06</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-write-conflict-domain">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
