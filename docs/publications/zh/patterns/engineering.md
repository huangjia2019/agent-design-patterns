<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/patterns/">模式矩阵</a><span style="margin:0 0.45rem;">/</span>模式工程实现</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书 · 工程实现</p>
<h1>模式工程实现</h1>
<p class="publication-deck">从具体工程问题进入模式：环境、状态、接口、失败与验证。</p>
</header>

模式规范描述一类反复出现的问题、机制和边界；模式工程实现把这些规范放进一个具体环境，继续追问数据存在哪里、状态怎样转移、接口如何设计、失败后怎样恢复。

这一类文章与蓝皮书不同。蓝皮书记录具名项目的演进、产物和结果；模式工程实现从一个真实工程问题出发，可以组合多个模式，但不把尚未实证的方案写成企业成果。它也不同于横切专题：专题讨论跨越多个模块的方法，工程实现通常由一个模块统领，并回链到相关模式。

## 从问题到模式

在 K8s 场景中，用户偏好已经写入 Markdown，下一次请求却落到另一个 Pod。工程链要继续追踪写入提交、版本冲突、索引同步、启动装配和跨 Pod 恢复。M1、M2、M3 分别解释保留层级、检索入口和任务连续性，X1 与 X3 补上观测证据和租户边界。

在前后端 Agent 协作场景中，前端复现接口超时，后端会话已经掌握事务与日志上下文。工程链从问题发现经过任务认领、修复、部署和复测，最后由可核验结果关闭。C4 负责交接顺序，C5 保留双方的局部上下文与权限边界；只有需要中央负责人或并行排查时，才继续引入 C1 或 C2。

模式名称提供检索入口，工程链负责说明这些机制在系统里落在哪里、失败时会留下什么证据。后续文章也沿用这个写法。

## 记忆

### [K8s 中的 Agent 记忆：存储分层与恢复验证](https://adpsagent.com/zh/patterns/engineering/memory-storage-on-kubernetes/)

同一用户的下一轮请求落到另一个 Pod 后，Markdown 记忆为什么会消失？文章区分内容表示、运行工作区、权威存储和检索入口，并给出版本冲突、索引同步、租户隔离和跨 Pod 恢复测试。

关联规范：M1 分层保留、M2 RAG、M3 进度追踪、X1 可观测性、X3 安全与身份。

## 协作

### [两个 Agent 怎样接上：从上下文引用到任务交接](https://adpsagent.com/zh/patterns/engineering/cross-agent-handoff/)

前端 Agent 发现后端问题以后，怎样把责任和证据交给已经掌握后端上下文的 Agent？文章区分消息、项目事实和局部工作上下文，给出任务状态机、Handoff Contract、协作控制面和交接验收测试。

关联规范：C4 交接链、C5 子 Agent 隔离；需要中央负责人或并行排查时再加入 C1 层级委派、C2 扇出聚合。

## 收录要求

一篇模式工程实现应保留下列信息：

1. 具体环境、参与者和故障现象；
2. 需要移动或持久化的数据、状态、权限与证据；
3. 接口、数据结构或运行顺序；
4. 正常路径之外的失败测试；
5. 与模式规范的对应关系，以及没有解决的部分。

产品名称可以作为已核对的实现例子，不用产品清单代替架构说明。

<div class="document-citation">
<p><strong>引用与许可：</strong>ADPS，模式工程实现，2026-09-13。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式矩阵</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式工程实现目录</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-09-13">2026-09-13</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#pattern-engineering-notes-20260913">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
