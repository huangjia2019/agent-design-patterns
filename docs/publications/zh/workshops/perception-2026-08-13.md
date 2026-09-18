<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/workshops/">研讨会</a><span style="margin: 0 0.45rem;">/</span>感知 Perception</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式系列研讨会</p>
<h1>ADPS 设计模式系列研讨会 · 感知模块第一次研讨会</h1>
<p class="publication-deck">信号准入、事件入口、多源与多模态的边界，以及 AI 驱动软件工程中的上下文问题。</p>
<p class="publication-date"><time datetime="2026-08-13">2026-08-13</time></p>
</header>

<table>
<thead>
<tr>
<th style="text-align: left;"></th>
<th style="text-align: left;"></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>主持人</strong></td>
<td style="text-align: left;">黄佳</td>
</tr>
<tr>
<td style="text-align: left;"><strong>核心研讨嘉宾</strong></td>
<td style="text-align: left;">张栋、黄湘龙、李庆丰、黄丞</td>
</tr>
</tbody>
</table>

2026 年 8 月 13 日，ADPS 围绕感知模块组织了第一次专题研讨。会议有两条讨论线。第一条检查 P1–P4 能否解释企业系统中的信号接入、上下文选择、压缩、探索与融合。第二条以 Coding Agent 为现场，讨论 AI 进入软件工程后，需求、架构、测试、评审和组织分工怎样变化。

两条线互有关联，但不应放进同一层目录。感知问题进入本模块总纲与 P1–P4；AI 驱动软件工程横跨记忆、行动、反思和治理，独立进入专题研究。

## 研讨结论

1. 感知范围从决策目标反向设计。可取得的数据不等于本轮都该进入 context。
2. 感知可以分成信号接入、预处理、语义聚合和事件判定四层。最后一层给触发建议，不直接执行业务动作。
3. 多源与多模态需要分开记录。主机、网络、代码和工单是来源；文字、图像、表格和音频是模态。
4. 事件、轮询和流式处理属于接入与触发机制，不能据此给整个任务分配执行拓扑。
5. AI Coding 的主要工程问题已经超出代码生成。可见上下文、验收标准、架构约束、评审容量和长期清理共同决定系统能否持续演进。

## 1. 什么信息有资格影响决策

研讨会将感知定义为决策链的入口。企业系统先要取得信号，再把它整理成模型和下游流程可以使用的结构。工具原本面向人展示的数据，也需要重新设计成 Agent 可读的 schema、状态和回执。

一条可用的感知管线分为四层：信号接入解决协议、权限和容错；预处理完成清洗、去重与归一化；语义聚合把离散信号连到业务实体和历史；事件判定输出分类、分级、置信度和触发建议。

这一结构给感知与决策划了一条线。感知输出结构化事实和标签，业务判断留给后续模块。把阻断规则、修复动作和业务策略全部写进感知层，会使这层难以复用，也无法独立校准。

## 2. 事件、轮询、流式与多源校验

在研发安全场景中，代码提交和工单可以通过事件回调进入系统，批量合规检查适合周期轮询，高吞吐日志适合流式处理。高风险威胁与故障定位常常需要把代码、主机、网络和历史工单放在一起交叉验证。

这些方式可以组合。一条代码审计链可以由提交事件触发，同时使用每日全量扫描校准覆盖，再把多个来源的证据聚合为同一条风险记录。

本场没有把 Event-Driven 增加为新拓扑。事件回答何时启动和怎样传递，任务启动后的控制关系仍由六种执行拓扑描述。

<figure class="workshop-diagram"><img alt="感知从目标和约束反向选择信号，输出结构化事实与触发建议，业务动作留给后续控制。" src="../../assets/images/workshops/perception-funnel-zh.svg"/><figcaption>感知从目标和约束反向选择信号，输出结构化事实与触发建议，业务动作留给后续控制。</figcaption></figure>

## 3. 多源不等于多模态

<p class="workshop-field-note"><strong>熊钰柯用算法上线后的验收说明了差别。</strong>算法本身通过边界检查，只能证明计算部分没有越界；地图上的呈现、设备在高级模式下的行为和最终业务效果还要分层验证。同一套验收设计也不能原样复制到图像识别等另一类任务。</p>

企业安全系统更常见的是多源融合：主机、网络、代码和工单可能都是文本或结构化记录。游戏开发中则有模态选择问题：虚幻引擎蓝图既可以按图读取，也可以转成脚本式结构；表示方式取决于任务、解析工具和 token 成本。

研讨会后，P4 增加来源与模态两个字段。来源决定权限、时效和交叉核验，模态决定解析器和表示方式。P4 暂时保留“多模态融合”的名称，后续再根据案例决定是否扩大命名。

## 4. 目标与约束共同构成上下文

<p class="workshop-field-note"><strong>黄湘龙把软件上下文拆成 Why、What、How 与验收。</strong>Why 说明服务谁、解决什么问题；What 固定场景和产品行为；How 承载架构、时序、API 与数据库；验收用例在编码前形成。Agent 因而拿到的是一组可核对的工程图纸，而不是不断变长的口头补充。</p>

Coding Agent 的输入需要同时包含目标与约束。目标说明要完成什么，测试、接口、设计规范和业务规则说明怎样判断做得好不好。上下文过少，Agent 无法完成任务；上下文过多，注意力会被无关材料分散。

算法研发中还出现了分层验收问题。算法本身通过测试，还不能证明地图呈现、设备行为或最终业务结果正确。不同任务需要自己的分层验收，无法把一套检查器原样搬到所有算法和产品中。

这部分讨论进入了感知总纲中的 Context Contract，也连接到行动模块的 Action Contract 与反思模块的评测证据。

## 5. 从 SDD 到 AI 驱动的软件工程

<p class="workshop-field-note"><strong>现场的争论落在存量系统上。</strong>姜宁提醒，大型旧仓库即使通过 PR 持续演进，也会累积架构侵蚀，Agent 还可能加快这种侵蚀；黄丞补充了 ADR、测试、任务记录和反向写回，让已经发生的实现决定重新进入可读上下文。新项目可以从规格建链，旧项目还要先恢复架构边界。</p>

公开项目 OpenLogos 与 RunLogos 展示了一条规格化路径。OpenLogos 使用 Why、What、How 和验收材料组织软件上下文，RunLogos 将提案、文档、计划、垂直切片、编码、评审、验证、部署和归档放进流程引擎。每个切片都需要独立验收，评审循环设置轮次、问题数量、证据和停止条件。

一组脱敏后的大型后端研发实践保留了产品、研发和测试的现有职责，在技术方案、代码实现和 Code Review 中逐步引入 Agent，并统计使用情况、token、方案往返轮次和落地后的代码修改量。近期目标是减少人工介入轮次，不预设全流程已经无人化。

新项目和存量项目需要不同的引入方式。新项目可以从规范、设计和测试开始建立完整链路；面对高流量存量系统，团队更适合从边缘模块逐步进入核心，并保留更严格的人工与测试门禁。

开源协作中还出现了另一个约束：代码生成速度超过维护者评审能力后，问题会转向架构一致性。不同贡献者使用不同 Coding Agent，`AGENTS.md` 和 Skill 可以表达部分规则，仍无法防止局部代码慢慢堆成架构债务。周期性清理、重构和架构守护因此成为必要工作。

游戏项目的做法则用 ADR、TDD 与 Task 区分长期架构选择、一次变化和当期执行。日报和任务记录帮助成员在中断后恢复，需求和程序实践双向更新，代码、测试、构建与日志则形成正向开发和逆向排障两条路径。

这些材料已经超出感知模块，完整综合见[AI 驱动的软件工程专题](https://adpsagent.com/zh/topics/ai-driven-software-engineering/)。

## 6. 三个反模式

研讨会归纳了三类已经出现的失效方式：

- **感知万能论**：默认数据源越多越智能，结果是核心信号被淹没，延迟和成本上升。
- **感知决策耦合**：清洗与业务动作写在同一层，规则变化牵动整条链。
- **静态感知**：上线后不再复盘漏报、误报和延迟，业务与架构变化逐渐扩大盲区。

研讨会还补充了输入安全。外部工具、文档、网页、图片和日志可能携带恶意指令或错误上下文。来源、作用域、数据与指令边界需要在感知侧留下明确记录。

## 7. 关键概念

<table>
<thead>
<tr>
<th style="text-align: left;">概念</th>
<th style="text-align: left;">本场定义</th>
<th style="text-align: left;">当前地位</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>感知漏斗</strong></td>
<td style="text-align: left;">信号接入、预处理、语义聚合、事件判定四层运行结构</td>
<td style="text-align: left;">模块级参考结构</td>
</tr>
<tr>
<td style="text-align: left;"><strong>Context Contract</strong></td>
<td style="text-align: left;">记录目标、必看材料、延迟句柄、时效、来源、冲突规则与缺失项</td>
<td style="text-align: left;">已进入感知总纲</td>
</tr>
<tr>
<td style="text-align: left;"><strong>来源—模态双字段</strong></td>
<td style="text-align: left;">分开记录数据来自哪里和采用什么表示，分别服务权限核验与解析选择</td>
<td style="text-align: left;">已进入 P4 修订</td>
</tr>
<tr>
<td style="text-align: left;"><strong>可验收垂直切片</strong></td>
<td style="text-align: left;">一份需求切成可独立实现、运行和验收的端到端工作单元</td>
<td style="text-align: left;">AI 驱动软件工程专题概念</td>
</tr>
<tr>
<td style="text-align: left;"><strong>架构可读性</strong></td>
<td style="text-align: left;">把架构边界做成 Agent 可以发现、检查和执行的仓库资产</td>
<td style="text-align: left;">专题研究方向</td>
</tr>
</tbody>
</table>

这些名称用于整理本场讨论。除 Context Contract 外，其余暂不新增模式编号。

## 8. 白皮书修订

1. 新增[感知模块总纲](https://adpsagent.com/zh/patterns/perception/)，写入四层漏斗、触发机制、来源与模态、决策边界及输入安全。
2. **P1 上下文分诊**增加目标反向约束、缺失项记录和输入作用域。
3. **P2 语义压缩**继续保护错误、已否决方案和业务数字，并把架构决策列为 Coding Agent 的保护信息。
4. **P3 渐进发现**增加存量代码库中的局部逆向发现与架构约束检索。
5. **P4 多模态融合**区分多源与多模态，增加来源、时效、转换血缘和交叉核验。
6. AI Coding、SDD、测试、架构守护和团队演进进入专题研究，不在 P1–P4 中增加新编号。

## 9. 后续问题

- 感知漏斗的层间合同怎样形成可复用 schema。
- P4 是否需要改名，以及多源冲突应如何保留不确定性。
- 存量项目怎样把架构边界从说明文档转成 Agent 可执行的检查。
- AI 代码产量超过人工评审容量后，哪些评审可以自动化，哪些仍需人判断。
- 新项目和存量项目分别需要什么样的自治门槛与质量证据。

## 相关页面

- [感知模块总纲](https://adpsagent.com/zh/patterns/perception/)
- [P1 上下文分诊](https://adpsagent.com/zh/patterns/p1-context-triage/)
- [P2 语义压缩](https://adpsagent.com/zh/patterns/p2-semantic-compaction/)
- [P3 渐进发现](https://adpsagent.com/zh/patterns/p3-progressive-discovery/)
- [P4 多模态融合](https://adpsagent.com/zh/patterns/p4-multi-modal-fusion/)
- [AI 驱动的软件工程专题](https://adpsagent.com/zh/topics/ai-driven-software-engineering/)
- [白皮书贡献者](https://adpsagent.com/zh/founders/#white-paper-contributors)

<p class="publication-note publication-note-end">公开稿保留研讨问题与工程细节；涉及内部系统的信息采用脱敏表述。会后采纳的结论见<a href="https://adpsagent.com/zh/patterns/perception/">感知 Perception模块总纲</a>与各模式规范。</p>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 设计模式系列研讨会 · 感知模块第一次研讨会；会议日期 <time datetime="2026-08-13">2026-08-13</time></dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-14">2026-08-14</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#workshops-perception-2026-08-13">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
