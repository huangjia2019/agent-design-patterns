<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/workshops/">研讨会</a><span style="margin: 0 0.45rem;">/</span>反思 Reflection</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式系列研讨会</p>
<h1>ADPS 设计模式系列研讨会 · 反思模块第一次研讨会</h1>
<p class="publication-deck">在线与离线反思、反馈延迟、评测证据、Skill 演化、归因与自愈边界。</p>
<p class="publication-date"><time datetime="2026-08-12">2026-08-12</time></p>
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
<td style="text-align: left;">张海立、黄佳</td>
</tr>
<tr>
<td style="text-align: left;"><strong>核心研讨嘉宾</strong></td>
<td style="text-align: left;">张栋、周默、王伟、陆钱春、Pylon Peng、李佳奇</td>
</tr>
</tbody>
</table>

2026 年 8 月 12 日，ADPS 组织了反思模块第一次专题研讨。与会者来自研发安全、零售算法、质量评测、通信知识工程、软件研发和旅行服务等场景。讨论从应用内的生成评审展开，逐步进入离线评测、Skill 演化、归因、自愈权限和长反馈链。

## 1. 应用内反思与应用外评测

应用内，评分标准（rubric）和评分器（grader）检查当前产物，修订回路根据检查结果改正输出。应用外，团队用数据集、评估器和运行轨迹比较不同版本，检查新版本是否损坏原有功能，以及评分器是否与人工判断一致。

同一套评分器可以用于这两类工作。评测给出检查结果；反思根据结果提出或执行修改，然后重跑相关任务，确认修改的效果。

研讨会后，白皮书将这条分工写入了[反思模块总纲](https://adpsagent.com/zh/patterns/reflection/)。

<figure class="workshop-diagram"><img alt="即时与延迟反馈通过同一运行标识回链，归因之后才进入修改、评测和发布。" src="../../assets/images/workshops/reflection-dual-clock-zh.svg"/><figcaption>即时与延迟反馈通过同一运行标识回链，归因之后才进入修改、评测和发布。</figcaption></figure>

## 2. 在线反思修当下，离线反思修系统

<p class="workshop-field-note">王伟介绍的环境构建 Agent，每遇到一类失败就增加一个修复补丁。据他的观察，两个月里稳定性提高了，构建时间却从约 5 分钟延长到 30 分钟，个别任务需要一小时。按日汇总运行记录后，团队发现几十条约束中有重复和冲突，需要统一整理。</p>

在线反思跟随当前任务运行，工具报错、参数不符或产物不完整时，系统当场修正。离线反思批量读取一段时间的交互轨迹，寻找多次任务中的重复、冲突和系统性问题。

针对这种积累，离线复盘要检查哪些补丁处理的是同一故障、哪些约束互相冲突，合并或删除后再比较构建成功率与耗时。在线修复则保留修改记录和回滚方式。

## 3. 反馈延迟决定回路长度

<p class="workshop-field-note"><strong>李佳奇对比了代码与业务分析。</strong>代码可以立即获得编译、测试和发布日志；一条经营建议要经过产品、运营、数据分析、供应链和用户行为，几天后才知道是否有效。后者仍然需要反馈回路，只是无法压缩成当前 Session 内的自我修订。</p>

业务结果尚未返回时，可以先检查建议的格式、引用和已知矛盾。后续结果到达，再关联当时的建议与 Agent 版本，由业务人员分析建议是否起作用，以及还有哪些因素影响了结果。

研讨会将“即时/延迟反馈”与“封闭/开放性任务”记录为两个相关但不等价的判断。开放任务也可以包含强硬的局部验收，封闭任务的最终用户体验也可能滞后。

## 4. 反思的证据与停止条件

研讨会讨论了反思流程中的四类实现职责：

1. 硬校验层优先使用机器真值。
2. 模型诊断层分析产物和轨迹。
3. 记忆沉淀层决定什么内容能够跨任务复用。
4. 调度控制层管理启停、轮次、成本、降级和人工接管。

白皮书接受了这个结构，同时对“可复用”作了边界补充：当反思只修改本轮输出时，可以选择不保存；任何跨任务的结论都要进入准入、版本和退役流程。

讨论还涉及元反思、审议式反思和知识完备性检测。这些方向对高风险、缺少确定性真值的任务有启发，当前仍处于探索阶段，研讨会没有将其列为新的正式模式。

## 5. 三层环境把 Bad Case 从线上收回线下

开发、评测和生产需要三层环境。开发环境允许人和 Agent 充分交互，评测环境在 benchmark 上检查新规则和新版本，生产环境使用已验证的流程和资产。

生产中出现 Bad Case 时，团队先保持线上路径稳定，再将失败收入评测集，生成候选规则或知识更新，通过回归后逐级发布。这个流程为在线反思设定了一个实用上限：当修改会影响共享资产或生产策略时，优先转入离线的发布流程。

## 6. 归因是自愈之前的独立工程

<p class="workshop-field-note">陆钱春提出按运行时、执行过程、业务结果和体验治理组织观测。模型调用失败要检查接口和错误记录，步骤缺失要检查执行轨迹，目标未完成则要对照业务要求。缺少领域知识或团队意见不一致时，需要请相应人员补充资料或作出决定。</p>

组织级 Agent 和 Skill 的可靠性治理需要连接事前准入与巡检、运行时健康检查与熔断、事后轨迹审计与整改复测。观测埋点、错误类型和评测方法还可以表达为统一原语，供不同 Agent 与 Skill 共用。

根因至少需要分两类。工具参数失效、步骤缺失或网络波动可能通过重试、修正或降级恢复。专业知识缺失、业务规则不同或各团队期望不一致，已经超出原 Agent 的自愈边界。一个诊断即使找到了现象，也可能是假阳性，或者根本没有可授权的修复方案。

这部分讨论促使 F4 自愈循环收紧了适用条件：需要可识别的失败、可执行的修复、独立复验和可用回滚。根因指向知识、业务决策或责任边界时，循环应转人。

## 7. Skill 演化要同时解决生成、比较和并存

<p class="workshop-field-note">王伟介绍，管理上千个 Skill 时，一个 Skill 单独通过测试，放进包含几十个 Skill 的环境却可能触发错误、抢占路由或与旧流程冲突。因此需要同时测试单个 Skill 和实际使用的组合，区分 Agent 本身、Skill 内容和路由选择造成的影响。</p>

Pylon Peng 介绍了每日反思流程：主 Agent 评测子 Agent 的任务结果，任务结束后由 Hook 收集运行轨迹，再分析是否需要新建或修改 Memory、Skill、规则、子 Agent 和 Harness。当工具参数或业务规则变化时，同步更新 Skill 文档与验证用例，候选修改经过独立评测后再发布。

这类日终批处理为 F2 技能包和 F3 经验回放提供了一个可实施的衔接点，但自动产生的资产仍然要经过评测和发布门禁。

## 8. 交叉评审能打破部分同源盲区

一个脱敏后的 SQL 生成与审查实践最初使用同类模型同时生成和评审，一些问题会穿透审查。将生成与评审分配给不同模型后，问题暴露能力有所改善。

如果两个模型使用同一份有遗漏的评分标准，它们仍可能漏掉同一种错误。交叉评审的结果还需要对照测试、业务规则、原始资料和专家判断检查。

## 9. 关键概念

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
<td style="text-align: left;"><strong>反思合同</strong></td>
<td style="text-align: left;">把触发、证据、评审规则、修改范围、权限、预算、复验与留存写成一份可检查合同</td>
<td style="text-align: left;">已进入反思总纲</td>
</tr>
<tr>
<td style="text-align: left;"><strong>双反馈时钟</strong></td>
<td style="text-align: left;">在线回路处理本轮即时信号，离线回路处理跨任务和延迟反馈</td>
<td style="text-align: left;">运行方式，不新增模式坐标</td>
</tr>
<tr>
<td style="text-align: left;"><strong>补丁债务</strong></td>
<td style="text-align: left;">在线局部修复持续叠加后形成重复、冲突和过长路径</td>
<td style="text-align: left;">F3 离线回放的重要输入</td>
</tr>
<tr>
<td style="text-align: left;"><strong>修改权</strong></td>
<td style="text-align: left;">反思结果可以建议或改变哪些对象，以及何时必须进入发布门禁</td>
<td style="text-align: left;">跨反思与治理的控制字段</td>
</tr>
<tr>
<td style="text-align: left;"><strong>归因先于自愈</strong></td>
<td style="text-align: left;">先确认失败类别、责任边界和可修复对象，再决定是否自动修改</td>
<td style="text-align: left;">已进入 F4 边界</td>
</tr>
</tbody>
</table>

## 10. 白皮书修订

1. 新增[反思模块总纲](https://adpsagent.com/zh/patterns/reflection/)，定义反思与观测、评测、发布治理的边界。
2. **在线反思**与**离线反思**作为运行方式进入总纲，不新增模式编号。
3. **F1 生成评审**增加评审合同、轨迹评审、评审者校准和多维 rubric 交换问题。
4. **F2 技能包**增加候选、独立评测、并存评测、灰度、版本与退役的生命周期。
5. **F3 经验回放**增加离线 trace 挖掘、延迟反馈和局部补丁合并。
6. **F4 自愈循环**区分可修复的运行故障与需要人工补知识、改业务规则的问题。
7. 元反思、审议式反思和前瞻性反思列为待研究方向。

## 11. 后续问题

- 在线回路的修改权限应如何按任务风险分级？
- 如何将一条长反馈链中的业务结果归因到当时的 Agent 版本和轨迹？
- Skill 在独立测试和组合测试中需要哪些共同指标？
- 反思结果修改 Memory、Skill 或 Harness 时，谁拥有准入和回滚权？
- 知识完备性、元反思和审议式反思如何获得可复现的成本与质量证据？

## 相关页面

- [反思模块总纲](https://adpsagent.com/zh/patterns/reflection/)
- [F1 生成评审](https://adpsagent.com/zh/patterns/f1-generator-critic/)
- [F2 技能包](https://adpsagent.com/zh/patterns/f2-skill-package/)
- [F3 经验回放](https://adpsagent.com/zh/patterns/f3-experience-replay/)
- [F4 自愈循环](https://adpsagent.com/zh/patterns/f4-self-heal-loop/)
- [白皮书贡献者](https://adpsagent.com/zh/founders/#white-paper-contributors)

<p class="publication-note publication-note-end">公开稿保留研讨问题与工程细节；涉及内部系统的信息采用脱敏表述。会后采纳的结论见<a href="https://adpsagent.com/zh/patterns/reflection/">反思 Reflection模块总纲</a>与各模式规范。</p>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 设计模式系列研讨会 · 反思模块第一次研讨会；会议日期 <time datetime="2026-08-12">2026-08-12</time></dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-12">2026-08-12</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#workshops-reflection-2026-08-12">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
