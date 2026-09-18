<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>Reflection
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书 · 模块总纲</p>
<h1>反思模块 · 从运行反馈到受控修改</h1>
<p class="publication-deck">反馈证据、在线与离线回路、修改权限、正式模式与待研究方向。</p>
</header>

反思可以发生在一次输出之后，也可以发生在一批任务结束之后。它读取产物、执行轨迹和外部结果，对照可检查的标准，决定是否修改当前输出、运行路径或可复用资产，然后再用新的证据确认修改是否有效。

“让模型再想一遍”只是最轻量的实现。缺少证据、停止条件和修改权边界时，额外一轮推理很难证明系统真的变好了。

## 反思合同的四个问题

一条反思回路在上线前应该回答：

1. **什么信号触发检查？** 测试失败、规则不符、用户差评、人工标注，还是模型评分？
2. **什么证据足以判定好坏？** 编译结果、schema、业务规则、专家结论和用户行为的可靠性与到达时间都不同。
3. **这一轮允许改什么？** 改当前答案、当前计划、Skill、记忆、业务规则，还是生产代码？
4. **怎样确认修改后更好？** 原检查项重跑、回归集、对照实验、人工复核和真实业务反馈分别解决不同问题。

四个问题中任何一个没有答案，回路都应先停在观测或建议阶段。

## 观测、评测与反思的分工

<table>
<thead>
<tr>
<th style="text-align: left;">环节</th>
<th style="text-align: left;">产出</th>
<th style="text-align: left;">对系统的影响</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><strong>观测</strong></td>
<td style="text-align: left;">trace、日志、工具调用、状态变化和成本</td>
<td style="text-align: left;">记录发生了什么</td>
</tr>
<tr>
<td style="text-align: left;"><strong>评测</strong></td>
<td style="text-align: left;">通过/不通过、分数、问题类型和证据</td>
<td style="text-align: left;">判定结果或路径是否符合标准</td>
</tr>
<tr>
<td style="text-align: left;"><strong>反思</strong></td>
<td style="text-align: left;">带范围、依据和风险的修改提案</td>
<td style="text-align: left;">尝试改变当前产物、执行路径或可复用资产</td>
</tr>
<tr>
<td style="text-align: left;"><strong>发布与治理</strong></td>
<td style="text-align: left;">审批、版本、灰度、回滚和责任记录</td>
<td style="text-align: left;">决定修改能否获得持久权限</td>
</tr>
</tbody>
</table>

评测给出判断，反思消费这个判断并提出改变。当改变要进入共享 Skill、记忆库、规则库或生产环境时，反思模块需要把权限交给治理门禁。

## 两只时钟：在线与离线

2026-08-12 的 ADPS 反思模块研讨会从多类业务场景中归纳出同一个分界：反思有两只时钟。

<table>
<thead>
<tr>
<th style="text-align: left;"></th>
<th style="text-align: left;"><strong>在线反思</strong></th>
<th style="text-align: left;"><strong>离线反思</strong></th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">目标</td>
<td style="text-align: left;">让当前任务通过验收或安全停下</td>
<td style="text-align: left;">让后续任务少走弯路，修正系统性问题</td>
</tr>
<tr>
<td style="text-align: left;">信号</td>
<td style="text-align: left;">当场可得的测试、规则、工具回执或结构检查</td>
<td style="text-align: left;">多条 trace、Bad Case、专家标注、用户反馈和滞后业务结果</td>
</tr>
<tr>
<td style="text-align: left;">视野</td>
<td style="text-align: left;">当前输出和局部路径</td>
<td style="text-align: left;">跨任务、跨版本和跨团队的整体表现</td>
</tr>
<tr>
<td style="text-align: left;">修改权</td>
<td style="text-align: left;">小，通常限于本轮输出、参数或可回滚变更</td>
<td style="text-align: left;">可提议修改 Skill、Memory、Harness、评测集和流程，发布前需重新验证</td>
</tr>
<tr>
<td style="text-align: left;">时间预算</td>
<td style="text-align: left;">毫秒到分钟级，需明确轮次、延迟和 token 上限</td>
<td style="text-align: left;">小时、天或周级，适合批量对比和人工参与</td>
</tr>
</tbody>
</table>

这是运行方式，不是新的模式坐标。F1 和 F4 经常用于在线回路，但它们的 rubric、失败分类和停止阈值需要离线校准。F2 的加载发生在线，技能的生成、测试、并存评测和发布主要发生在离线。F3 也跨越两边：离线提炼经验，在新任务中按需回放。

## 结果什么时候才到

反思时钟由成功信号的延迟决定。

<table>
<thead>
<tr>
<th style="text-align: left;">成功信号</th>
<th style="text-align: left;">常见场景</th>
<th style="text-align: left;">建议回路</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">编译、测试、schema、确定性工具回执</td>
<td style="text-align: left;">代码、配置、结构化写回</td>
<td style="text-align: left;">低风险时可在线修正与复验</td>
</tr>
<tr>
<td style="text-align: left;">稳定规则、引用库、专业检查器</td>
<td style="text-align: left;">政策解读、合规文本、领域查询</td>
<td style="text-align: left;">在线评审可用，规则版本需固定</td>
</tr>
<tr>
<td style="text-align: left;">用户满意度、业务指标、后续人工改动</td>
<td style="text-align: left;">客服、运营、分析建议</td>
<td style="text-align: left;">收集结果后离线分析，不要当场伪造真值</td>
</tr>
<tr>
<td style="text-align: left;">跨部门、跨系统的长反馈链</td>
<td style="text-align: left;">需求到上线、建议到业务动作</td>
<td style="text-align: left;">建立延迟标注和人工归因，先保留不确定性</td>
</tr>
</tbody>
</table>

开放性问题并非一律不能在线检查。可以在线检查引用、格式、明显矛盾和已知风险，对最终业务价值的判定则留到反馈到达之后。

## 反思合同

生产系统需要把反思回路表达为可检查的合同：

<pre><code class="language-yaml">reflection_id: ref_01K2...
scope: artifact              # artifact | trajectory | asset | system
trigger:
  type: test_failure
  ref: trace://run-8842/check-9
evidence:
  - type: deterministic_test
    ref: test://payroll/net-pay-balance
judge:
  policy: reflection-rubric-v4
proposal:
  target: src/payroll/net_pay.py
  allowed_change: diagnosed_files_only
authority:
  mode: auto_in_sandbox      # suggest | auto_in_sandbox | approval_required
budget:
  max_iterations: 3
  max_latency_ms: 90000
verification:
  suite: payroll-regression-v12
  rollback_on_regression: true
retention:
  disposition: candidate_lesson
</code></pre>

一条完整回路是：**触发 → 证据装配 → 诊断 → 修改提案 → 权限门禁 → 执行 → 复验 → 记录**。模型可以参与诊断和提案，测试、规则、人员和业务结果共同决定它有没有权力继续。

## 四个正式模式的职责

<table>
<thead>
<tr>
<th style="text-align: left;">模式</th>
<th style="text-align: left;">主要修改对象</th>
<th style="text-align: left;">反馈特征</th>
<th style="text-align: left;">主要边界</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/f1-generator-critic/"><strong>F1 生成评审</strong></a></td>
<td style="text-align: left;">当前产物</td>
<td style="text-align: left;">规则、引用、专家 rubric 或独立模型</td>
<td style="text-align: left;">评审者本身也要评测，不能用评分代替证据</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/f2-skill-package/"><strong>F2 技能包</strong></a></td>
<td style="text-align: left;">可复用流程与能力资产</td>
<td style="text-align: left;">跨任务成功、失败和并存评测</td>
<td style="text-align: left;">单个 Skill 通过不等于与其他 Skill 组合后仍然通过</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/f3-experience-replay/"><strong>F3 经验回放</strong></a></td>
<td style="text-align: left;">新任务的参考上下文</td>
<td style="text-align: left;">历史轨迹、结果和延迟反馈</td>
<td style="text-align: left;">要保留来源、适用版本和不确定性，防止旧经验产生负迁移</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/f4-self-heal-loop/"><strong>F4 自愈循环</strong></a></td>
<td style="text-align: left;">可回滚的运行状态、配置或代码</td>
<td style="text-align: left;">确定性失败与重跑结果</td>
<td style="text-align: left;">知识缺失、业务逻辑变化和不可逆操作需要转人或离线发布</td>
</tr>
</tbody>
</table>

在线/离线、硬证据/软判断、局部/全局与反馈延迟都是模式选型参数。它们不改变“认知功能 × 执行拓扑”的主框架。

## 生产实现的四层结构

研讨会归纳出一个四层分工：

1. **硬校验层**：编译、测试、schema、业务不变量和系统回执优先。
2. **反思诊断层**：模型阅读证据，识别当前输出、轨迹或资产的可能问题。
3. **记忆与资产层**：候选 lesson、Skill、规则和失败记录经过准入后才跨任务生效。
4. **调度与控制层**：决定是否启动反思、使用哪个评审者、能跑几轮、何时降级或转人。

可自动触发、可终止、可观测、可控制成本，是所有生产回路的共同要求。“可复用”需要更细的处理：当反思结果仅修改本轮产物时，可以明确不保存；当它要跨任务生效时，就必须有准入、版本和退役机制。

## 三个规模化难题

**局部补丁会破坏整体效率。** 一个脱敏后的环境构建 Agent 在长期运行中不断增加局部修复，稳定性上升，整体路径却越来越重。离线反思要能发现重复、冲突和已失效的补丁，不能只把 Bad Case 继续叠加进 prompt。

**Skill 要在组合环境中评测。** 单个 Skill 的触发率和任务成功率只能说明它独立可用。规模扩大后，还要检查误触发、漏触发、重叠、冲突、加载成本，以及新 Skill 是否让已有能力退化。

**归因先于自愈。** 问题可以分为运行时、执行过程、业务结果和体验几类。参数失效、网络抖动和步骤遗漏可能有明确修复路径；专家知识缺失、业务规则变化和团队目标差异无法靠原 Agent 自行补全。

## 研讨中的实现片段

**张栋把规则变更放在开发、评测和生产三层环境中流转。** Bad Case 先进入评测集，模型据此生成候选经验或规则；候选项在 Benchmark 上通过后进入预发布，最后才获得生产权限。线上优先维持稳定路径，新增经验不直接写入正在运行的规则库。

**周默把反思运行时拆为硬校验、模型诊断、记忆沉淀和调度控制四层。** 编译、接口回归和业务规则拥有更高的证据优先级；模型负责解释问题和提出修改；可复用结论进入记忆或 Skill 前要经过准入；调度层限制轮次、token 和延迟。配套指标包括修复成功率、无改进轮次、越修越错的比例、反思开关率和任务延迟。

**Pylon Peng 的日常回放从轨迹中寻找资产变化。** 一条 Skill 因命令参数被删除而失败时，系统先确认是 Agent 误用还是依赖版本变化，再更新操作说明、测试用例和适用版本。候选 Memory、Skill 或 Harness 变更由 `evaluation.json` 一类可执行检查验收，不直接用另一段模型判断代替。

**李佳奇用反馈到达时间区分在线与离线。** 编译、测试和发布日志可以在当前任务中返回，适合当场修正；业务建议需要经过运营动作和用户反馈，真值可能几天后才出现，只能保存当时的版本与轨迹，等待离线归因。他还提出两个规模问题：同类 Skill 增多后需要横向和组合评测；生成与评审使用同一模型时容易保留相同盲区，交叉模型可增加差异性，但仍需规则、测试和原始数据裁决。

## 2026 年的工程进展

截至 2026 年 8 月，主流工具已经把反思依赖的评测部件做成了正式工程接口：

- [LangSmith Evaluation](https://docs.langchain.com/langsmith/evaluation) 区分发布前的离线评测和生产 trace 上的在线评测，并将失败 trace 回收到数据集。[AgentEvals](https://docs.langchain.com/oss/python/langchain/test/evals) 已经直接评估 Agent 的工具调用轨迹。
- Anthropic 在 2026-01 发布的 [Agent 评测方法](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) 中建议组合代码、模型和人工 grader。其 [企业 Skill 治理指南](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/enterprise) 进一步要求触发、独立运行、并存、指令执行和输出质量评测。
- OpenAI 的 [AgentKit](https://openai.com/index/introducing-agentkit/) 将 trace grading、数据集和 grader 纳入 Agent 优化工作流。

这些能力负责看见和判断。判断转成受控修改，并由回归证据确认后，才进入 ADPS 所说的反思回路。

## 暂不增加新编号的方向

**元反思**检查 critic 本身是否漏判、误判或使用了有问题的 rubric。它可以先作为 F1 的高风险配置，不急于单独落牌。

**审议式反思**让多个评审者从不同假设出发展开辩论。它与 F1 生成评审、C3 对抗评审都有重叠，当前还缺少稳定的终止条件和成本证据。

**前瞻性反思**在行动前检查计划、风险和假设。这项职责已分布在 F1、A4 护栏三明治和 G1 审批门中，需要更多独立实践才能判断是否形成新模式。

## 还需要行业回答的问题

- 大规模 Skill 库怎样分离 Agent 质量、Skill 质量与组合效应？
- 多维 rubric 一些指标上升、一些下降时，谁有权定义交换关系？
- 哪些反思结果可以自动修改 Harness，哪些只能生成变更建议？
- 当真实结果几天或几周后才到达，怎样保留当时的轨迹、版本和责任链？
- 如何发现在线回路积累的补丁冲突，并安全地合并、删除或回滚？

## 研讨会记录

本总纲吸收了 2026-08-12 反思模块第一次研讨会的讨论。主持人为张海立、黄佳；核心研讨嘉宾为张栋、周默、王伟、陆钱春、Pylon Peng、李佳奇。本页按主题合并研讨结论，不将脱敏前的企业实践与个人逐条对应。

[阅读完整研讨记录](https://adpsagent.com/zh/workshops/reflection-2026-08-12/) · [白皮书贡献者](https://adpsagent.com/zh/founders/#white-paper-contributors)

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《反思模块：从运行反馈到受控修改》，Agent 设计模式白皮书 v0.3，2026-08-14。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>范围：</strong>本页说明反思子系统的整体设计。F1 至 F4 的问题、机制和验证标准仍以各模式规范为准。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/reflection-2026-08-12/">反思模块第一次研讨会</a>（2026-08-12）；<a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents 动态协作研究</a></dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-12">2026-08-12</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-13">2026-08-13</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-reflection">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
