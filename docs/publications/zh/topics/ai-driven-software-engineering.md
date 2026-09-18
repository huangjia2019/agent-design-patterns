<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/topics/">专题</a><span style="margin:0 0.45rem;">/</span>AI 驱动的软件工程 · 规格、上下文、执行与反馈</p>

<header class="publication-head">
<p class="publication-series">ADPS 专题研究</p>
<h1>AI 驱动的软件工程 · 规格、上下文、执行与反馈</h1>
<p class="publication-deck">覆盖 AI Coding、SDD 与 Agentic Software Engineering 的规格、上下文、执行、验证与演进。</p>
</header>

AI Coding 已经进入仓库级任务。Agent 可以读取仓库、拆解任务、修改多个文件、运行测试，也可以提交变更。代码生成只是其中一环。工程团队还要给出清晰的工作边界，控制进入本轮判断的上下文，验收产物，并防止局部提速慢慢损害整体架构。

这是一个横跨感知、记忆、推理、行动、反思与治理的问题。ADPS 将它放在“专题”层，用来组织跨模块的工程方法，不为它新增一个模式编号。

## 概念定义

| 名称 | 描述范围 | 在本专题中的用法 |
| --- | --- | --- |
| AI Coding | 用 AI 生成、解释、修改和评审代码 | 指具体工具或开发活动 |
| 规格驱动开发（SDD） | 先将意图、约束和验收条件写成可版本化的规格，再由规格引导计划、实现与校验 | 指一条具体的工程方法 |
| AI 驱动的软件工程 | AI 参与需求、架构、实现、测试、运行和演进的完整工程系统 | ADPS 采用的专题名称 |
| Agentic Software Engineering | Agent 拥有更长的执行链、更完整的工具权限和更高的任务自主性 | 指 AI 驱动软件工程中自主程度较高的形态 |

这些名称有重叠，也还在演化。在 ADPS 文档中，可根据讨论层次选词，无需强行将它们合并为一个行业标签。

## 工程瓶颈的移动

当 Agent 可以较快地写出代码，团队的稀缺能力会向上下游移动：

1. **任务定义。** 要解决的问题、不能违反的约束和可验收的结果，必须足够明确。
2. **上下文管理。** 仓库文件、架构决策、运行日志、历史任务和外部资料不能无差别地进入模型。
3. **验收设计。** 编译通过只是一层证据。用户端行为、数据完整性、性能、安全和运维可见性都可能属于验收范围。
4. **权限边界。** 读取、改写、执行、提交和部署是不同权限，需要分别准入。
5. **架构维护。** 每个局部任务都可以“做完”，仓库仍可能出现重复逻辑、依赖漂移和不必要的代码增长。

因此，评估 AI 软件工程不能只看代码量、PR 数或生成速度。还要看规格是否稳定、证据是否充足、变更是否可追溯，以及后续维护成本是否上升。

## 可操作的五层结构

| 层 | 需要回答的问题 | ADPS 中的对应部分 |
| --- | --- | --- |
| 规格与工作单元 | 这轮要完成什么，边界和验收条件是什么 | Goal Contract、任务分片、计划与推理模式 |
| 上下文 | 哪些信号允许影响本轮判断，历史资产如何召回 | 感知模块、记忆模块 |
| 执行 | 当前步骤如何选工具、控权限、改变外部状态 | 推理模块、行动模块、执行拓扑 |
| 验证 | 哪些证据能证明任务完成，谁有权接受结果 | 外部验收、行动证据链、治理模式 |
| 演进 | 这次经验如何改变规则、测试、Skill 或架构 | 反思模块、版本化记忆、架构维护 |

五层之间通过可版本化产物和运行证据连接。常见产物包括规格、ADR、计划步骤、代码差异、测试结果、ActionEvent、checkpoint 和修复提案。

## 从辅助到受控自主

| 阶段 | Agent 承担的工作 | 团队需要先具备的能力 |
| --- | --- | --- |
| 编码辅助 | 解释代码、生成局部实现、补测试 | 人工选上下文并逐段评审 |
| 规格引导任务 | 按明确规格完成一个可验收切片 | 规格、边界、测试和回退方案可以被检查 |
| Harness 工作流 | 在沙箱中拆解、执行、验证和提交多步变更 | 上下文管理、工具准入、事件记录和外部验收 |
| 受控自主 | 在持续任务队列中工作，处理更长的任务链 | 分级授权、预算、审批门、事故处理和定期架构评审 |

这些阶段是工程能力的递进，不是工具采购清单。旧系统、高流量服务和受监管业务通常需要在较低自主级别停留更长时间。

## 感知模块研讨会的工程线索

2026 年 8 月 13 日的 ADPS 感知模块研讨会给出了几组可以对照的实践：

- 公开项目 OpenLogos 与 RunLogos 将 Why、What、How 和验收条件连成规格链，再将场景切成可独立验收的纵向工作单元。
- 一类大型后端团队记录 token 使用、设计往返和代码修改过程，用这些信号判断 AI 对工作方式的实际影响。
- 新建项目和存量高流量系统采取不同的引入节奏；两者都要把目标和约束写进任务定义。
- AI 生成的 PR 持续增加后，`AGENTS.md` 和 Skills 无法独立承担架构管理，仓库还需要固定的清理、依赖检查和架构评审。
- 游戏开发实践用 ADR、TDD、Task 与每日记录组织正向和反向检查，并根据 UE 蓝图等对象选择文本或视觉输入。
- 一类复杂系统将验收分成算法、地图、运行环境和业务行为等层次。一项变更需经过哪些层次，由它可能改变的外部结果决定。

这些实践没有使用同一套工具，但都在处理同一类问题：如何将人类意图转成 Agent 能执行、团队能验收、仓库能继续维护的工程结构。

## 一条较稳妥的引入路径

1. 选一个边界清楚、失败可回退的任务，先写验收条件。
2. 将规格、约束和架构决策放入仓库，让人和 Agent 读取同一份版本。
3. 为任务定义上下文入口，区分必需信息、按需信息和禁止使用的信息。
4. 先在沙箱内开放最小工具集，记录计划、工具调用、状态变更和验收结果。
5. 用外部行为验收结果，不将 Agent 的完成声明当成最终证据。
6. 定期检查失败是否改变了规格、测试、规则或架构，同时清理重复实现和过期上下文。

## 待继续研究的问题

- 规格应详细到什么程度，才不会把实现细节提前锁死？
- 如何测量 Agent 带来的维护成本、架构漂移和评审负担？
- 长程任务中，哪些状态应进入 checkpoint，哪些应返回仓库或控制平面？
- 当 Agent 可以同时修改代码、测试和规格时，如何保持验收基准的独立性？
- 从个人工具扩展到企业工程系统时，权限、业务责任和架构所有权应如何转移？

最后一个问题已经超出开发工具的范围，将在[企业 Agent 演进与组织运行](https://adpsagent.com/zh/topics/enterprise-agent-evolution/)专题中继续讨论。

## 资料与来源

- [ADPS 感知模块第一次研讨会](https://adpsagent.com/zh/workshops/perception-2026-08-13/)
- [GitHub Spec Kit: Spec-Driven Development](https://github.com/github/spec-kit/blob/main/docs/concepts/sdd.md)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [OpenAI: Harness engineering](https://openai.com/index/harness-engineering/)
- [OpenAI: Running Codex safely](https://openai.com/index/running-codex-safely/)
- [Anthropic: Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

## 既有系统的改造

[可塑软件：在既有业务上增加 Agent 能力](https://adpsagent.com/zh/topics/malleable-software/) 讨论源码受限时的接入方式、业务草案审批及结果核验。

<div class="document-citation"><p><strong>引用建议：</strong>ADPS，《AI 驱动的软件工程 · 规格、上下文、执行与反馈》，ADPS 专题研究，2026-08-14。</p><p><a href="https://adpsagent.com/zh/topics/">专题目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer">专题整理跨模块的工程问题。引用的模式定义、具名案例和研讨会记录以各自页面为准。</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>正文关联的研讨会与案例：<a href="https://adpsagent.com/zh/workshops/perception-2026-08-13/">ADPS 感知模块第一次研讨会</a>（<time datetime="2026-08-13">2026-08-13</time>）</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-14">2026-08-14</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#topics-ai-driven-software-engineering">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
