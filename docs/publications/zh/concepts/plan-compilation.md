<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/concepts/">概念</a><span style="margin:0 0.45rem;">/</span>概念定义</p>

<header class="publication-head"><p class="publication-series">ADPS Agent 系统 · 工程概念</p><h1>Plan 编译</h1><p class="publication-deck">把推理产出的计划转换为带依赖、类型、权限和验收的可执行结构。</p></header>

## 应用背景：计划读起来合理，执行时才发现根本不能跑

Agent 生成了一份“读取员工资料、计算调整、批量提交、发送通知”的计划。文字顺序通顺，却没有说明提交前必须取得审批，两个步骤同时写同一张表，通知还可能在事务失败前发出。等到 Executor 逐步执行，问题已经进入真实系统。

## 概念定义

Plan 编译把模型生成的结构化计划转换为可执行图，并在执行前完成合法性、依赖、权限、冲突、经济性和验收检查。无法通过的计划返回明确诊断，供模型修订或交给人工，而不是边执行边猜。

## 工程机制

编译器验证步骤类型和参数 schema，补全显式依赖，计算写入冲突域，检查调用者权限与工具版本，并估算重复扫描、串并行选择、调用次数和预算。编译产物固定计划哈希、节点合同、资源键和恢复策略；运行时只能在声明的动态位置内调整。

## 使用边界

低风险探索可以边观察边规划，未必需要完整编译。跨系统写入、批处理、审批、并行任务和长程执行更适合先编译。Plan 编译检查结构是否可执行，不证明模型对业务目标的理解一定正确，仍需上下文合同和外部验收。

<section aria-labelledby="concept-provenance-title" class="concept-provenance">
<h2 id="concept-provenance-title">提出与来源</h2>
<dl>
<div><dt>概念分组</dt><dd><a href="https://adpsagent.com/zh/concepts/#group-planning-execution">规划、执行与写回</a></dd></div>
<div><dt>ADPS 内初始来源</dt><dd>ADPS 内初始提出：茹炳晟；实践补充：王伟、Pylon PENG</dd></div>
<div><dt>首次记录</dt><dd><a href="https://adpsagent.com/zh/workshops/action-2026-08-06/">行动模块第一次研讨会</a>（<time datetime="2026-08-06">2026-08-06</time>）</dd></div>
<div><dt>ADPS 整理</dt><dd>ADPS 将合法性、依赖、权限、冲突和经济性检查整理为计划进入执行前的编译步骤。</dd></div>
<div><dt>当前地位</dt><dd>研讨会概念</dd></div>
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
<p><a href="https://adpsagent.com/zh/chronicle/#concepts-plan-compilation">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
