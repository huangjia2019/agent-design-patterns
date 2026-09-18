<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/topics/">专题</a><span style="margin:0 0.45rem;">/</span>企业 Agent 演进与组织运行 · 研究议程</p>

<header class="publication-head">
<p class="publication-series">ADPS 专题研究</p>
<h1>企业 Agent 演进与组织运行 · 研究议程</h1>
<p class="publication-deck">跟踪 Agent 权限、工程平台与组织责任的同步演进，为后续企业实践建立问题清单。</p>
</header>

当 Agent 从个人辅助工具进入共享工作流，并获得改写业务状态的权限，系统架构、审核责任、事故处理、知识维护、成本管理和团队分工都会随之调整。

ADPS 现有的模式解决局部架构问题，企业案例记录具体实践，研讨会保留专家的一手观察。企业如何组合这些部分、按什么节奏放开自主权，目前还没有足够稳定的结论。本页作为研究议程，记录问题边界和后续需要的证据。

## 三条同时发生的演进线

| 演进线 | 典型起点 | 后续会遇到的问题 |
| --- | --- | --- |
| 系统权限 | 读取与草拟 | 何时可以推荐、执行、批量处理或调度其他 Agent |
| 工程平台 | 个人工具 | 何时需要共享 Harness、规格库、测试环境、事件总线和统一治理 |
| 组织运行 | 个人自审 | 谁定义验收，谁批准权限，谁维护架构，谁对失败和长期成本负责 |

三条线不会自动同步。系统能力可能已经支持自动执行，而团队还没有定义验收责任和事故处置方式。工程平台也可能过早做成统一入口，却缺少稳定场景和可复用资产。

## 从一项变更到 Agent 群体

首页的薪酬示例把最小建模单位定义为一项能够独立判断、审批、执行、验收和补偿的业务变更。这个粒度用来闭合单次工作。治理生命周期继续管理能力怎样完成登记、评测、灰度、运行、复验、降级和退役。

![Agent 从登记、设计、评测、灰度、运行到降级和退役的治理生命周期](../../assets/images/patterns/agent-governance-lifecycle-zh.svg)

<table>
<thead><tr><th>管理尺度</th><th>薪酬示例</th><th>需要固定的工程对象</th></tr></thead>
<tbody>
<tr><td>业务变更</td><td>一名员工的交通津贴 800→1000，下月生效</td><td>目标、事实、审批、执行、验收与补偿</td></tr>
<tr><td>一次运行</td><td>本次请求从受理到写后读取</td><td>run、Intent、Approval、Execution 与证据链</td></tr>
<tr><td>能力版本</td><td>薪酬 Agent v7 的津贴修改能力</td><td>场景、资源范围、评测结果与自治档位</td></tr>
<tr><td>Agent 产品</td><td>薪酬 Agent 的生产实例</td><td>所有者、依赖、凭证、预算、事故响应与退役条件</td></tr>
<tr><td>Agent 群体</td><td>薪酬、HR、财务与合规 Agent 共同工作</td><td>共享身份、策略格式、累计限额、因果 trace 与跨域责任</td></tr>
</tbody>
</table>

可观测性连接五个尺度的事实，Evals 与测试决定能力能否继续发布，治理控制权限如何变化。最小闭环不清楚时，平台很容易只积累入口、工具和日志，仍然无法说明一项业务变更由谁验收。

## 权限扩大的前置条件

1. **业务边界。** Agent 能改变哪些对象，单次、单日和单租户的影响范围是多少？
2. **验收所有权。** 哪个角色定义成功，哪些证据由独立系统产生？
3. **变更权。** Agent 可以改代码、提示词、Skill、测试、规格或记忆中的哪些部分？
4. **架构所有权。** 谁处理跨任务的依赖漂移、重复实现和过期规则？
5. **事故责任。** 执行证据能否重放，人工接管和回退如何启动？
6. **经济边界。** 模型、工具、评审、测试与返工成本如何一起计算？

只有系统能力，不足以支撑权限升级。每一级权限都需要对应的验收、可观测性、回退能力和组织责任。

## 计划产出

- 一套企业 Agent 自主权分级，明确每一级可以执行的动作和前置条件。
- 一张组织角色与责任表，覆盖业务、工程平台、安全、数据、风险和运维。
- 一组从试点到生产的准入条件，包括证据、预算、权限和事故准备。
- 一套事故与长期劣化的分类方法，区分单次失败、记忆污染、架构漂移和组织失配。
- 来自不同行业的对照案例，说明同一套原则在不同风险等级下如何落地。

## 当前用途

这个专题用于收集问题和证据。企业可以用上面六个问题检查当前试点；后续模块研讨会和蓝皮书案例会继续补充实践材料。在行业材料足够丰富之前，本页不给出统一成熟度分数。

## 相关内容

- [AI 驱动的软件工程](https://adpsagent.com/zh/topics/ai-driven-software-engineering/)
- [ADPS 模式矩阵](https://adpsagent.com/zh/patterns/)
- [治理模块与 Agent 生命周期](https://adpsagent.com/zh/patterns/governance/#payroll-lifecycle)
- [治理模块第一次研讨会](https://adpsagent.com/zh/workshops/governance-2026-08-18/)
- [ADPS 企业案例](https://adpsagent.com/zh/cases/)
- [ADPS 研讨会](https://adpsagent.com/zh/workshops/)

<div class="document-citation"><p><strong>引用建议：</strong>ADPS，《企业 Agent 演进与组织运行 · 研究议程》，ADPS 专题研究，2026-08-19。</p><p><a href="https://adpsagent.com/zh/topics/">专题目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer">专题整理跨模块的工程问题。引用的模式定义、具名案例和研讨会记录以各自页面为准。</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>正文关联的研讨会与案例：<a href="https://adpsagent.com/zh/workshops/governance-2026-08-18/">治理模块第一次研讨会</a>（<time datetime="2026-08-18">2026-08-18</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-18">2026-08-18</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-14">2026-08-14</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#topics-enterprise-agent-evolution">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
