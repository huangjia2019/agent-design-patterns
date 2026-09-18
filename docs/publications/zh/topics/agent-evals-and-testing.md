<p style="font-size:0.9rem;color:var(--color-text-faint);margin-bottom:1.75rem;"><a href="https://adpsagent.com/zh/topics/">专题</a><span style="margin:0 0.45rem;">/</span>Agent 评测与验证 · 从输出评分到系统验收</p>

<header class="publication-head">
<p class="publication-series">ADPS 专题研究</p>
<h1>Agent 评测与验证 · 从输出评分到系统验收</h1>
<p class="publication-deck">组合确定性测试、轨迹评估、外部验收与生产反馈，建立 Agent 发布证据。</p>
</header>

传统软件测试在 Agent 时代仍然有效。数据结构、权限、工具契约、幂等性和业务账本继续由确定性测试锁住。新增的难题来自概率性输出、多条可行路径、外部工具和延迟结果。一次运行可能换一条轨迹仍能完成任务，也可能文字回答漂亮而外部状态已经写错。

Agent Evals 测量这类不确定行为。它与单元测试、集成测试、沙箱验收、生产监控和人工复核共同构成验证体系。

## 验证为什么是分水岭

近十年的人工智能进展，实践大多走在理论前面。2025 年底以来 Agent 的快速扩散尤其如此：它不是从一套理论推导出来的，而是一个个痛点被逐个解决之后累积出来的结果。补上理论这一课，第一个要回答的问题是，Agent 为什么会在“大模型加 Agent”这类方案里处在中枢位置。

一种能解释这段历史的说法是，分界线在于输出能不能被检验。缺少验证环节时，大模型可以一本正经地一直推理下去，没有任何机制让它停下来认错。在那个阶段，商业上跑得比较顺的多是不需要判定真伪的场景：陪伴与情绪价值不依赖外部事实确认对错，因而不受这一限制，同时也不构成生产力工具。

工具调用和 Agent 出现之后，模型的输出第一次可以被外部世界检验。调用有返回，动作有后果，结果可以和目标状态比对。AI 由此从提供情绪价值转向提供生产力。第一个大规模商业化的生产力场景是 AI 编程，一个重要原因是编程天然自带多层裁判：编译器、类型检查、测试用例和运行结果，都能在很短的时间内给出确定的判定。

由此得到一条贯穿本文的判断。一个场景能不能被 Agent 变成生产力，很大程度上取决于它的验证能不能做好；不同阶段会有不同的关键技术成为瓶颈，验证则始终是决定上限的那个变量。[ADPS 反思模块第一次研讨会](https://adpsagent.com/zh/workshops/reflection-2026-08-12/)从另一个方向记录过相近的结论：真值什么时候到达，决定了修正应该闭合在哪一层。

## 概念定义

| 名称 | 主要任务 | 典型产物 |
| --- | --- | --- |
| Test | 对确定性契约作断言 | 通过/失败、差异、错误位置 |
| Eval | 在不确定行为和多次运行上测量能力与回归 | 样本级证据、分数、通过率与失败簇 |
| Monitoring | 观察真实生产流量中的行为 | 运行事件、指标、告警与样本 |
| Acceptance | 由用户或业务规则判定交付是否成立 | 外部回执、可见结果、审批或签收 |

测试和 Eval 的边界可以重叠。一个确定性 grader 既能出现在测试套件中，也能作为 Eval 的评分器。工程上更重要的是说清证据来自哪里，由谁维护，它能支持哪一类发布决策。

## 被测对象

被测对象包括：

- 单个模型或提示词；
- 一个 Skill 或工具适配器；
- 一段路由、规划或工作流；
- 包含状态、权限和恢复机制的 Agent Harness；
- 完整 Agent 产品；
- 多 Agent 系统及其交接、聚合和终止条件。

对象不同，评测数据、执行环境、评分器和发布门都会变。例如，工具适配器主要看 schema、权限和幂等；长程 Agent 还要看目标保持、checkpoint、预算与故障恢复。

## 六个评估切面

| 切面 | 要问的问题 | 证据示例 |
| --- | --- | --- |
| 最终结果 | 外部世界是否达到目标状态 | 数据库事实、业务回执、真实请求结果 |
| 执行轨迹 | 工具、顺序与参数是否合理 | trace、ActionEvent、任务图节点 |
| 单步决策 | 路由、召回、压缩或审批判断是否正确 | 决策标签、候选集、理由与事实对照 |
| 安全与权限 | Agent 是否越界，拒绝和升级是否有效 | 负例、沙箱事件、审批与拒绝记录 |
| 恢复与长程进度 | 中断、重试和交接后能否回到正确任务 | checkpoint、幂等键、目标版本、进度账本 |
| 资源与时效 | 质量改善是否在可接受的延迟和成本内 | 试次分布、token、延迟、工具调用数 |

最终结果是主要裁决依据，轨迹评估用于发现潜在风险和定位失败。对存在多条正确路径的任务，严格匹配一条 golden trajectory 会把有效解法判错。只要结果、权限和必要约束正确，轨迹可以保留一定自由度。

## Agent 测试金字塔

<pre><code class="language-text">               生产影子流量 / 金丝雀 / 业务结果
                    人工与校准后的模型评分
                 轨迹回放、沙箱与故障注入
              工作流、外部验收与系统集成
           工具契约、权限、状态机与幂等性
        schema、解析、函数、规则与确定性组件测试
</code></pre>

下层快、稳定、定位清楚，适合每次提交。上层更接近真实价值，同时运行慢、成本高、方差大。发布门需要组合多层证据，不能把一个综合分数当成全部结论。

## 评分器的优先级

1. 外部事实和确定性断言。
2. 代码、规则、schema 和状态机检查。
3. 业务验收器或独立模拟环境。
4. 经过校准的模型评分器。
5. 专家或真实用户对含糊标准作最终判断。

模型评分器适合语义相关性、风格、完整性和复杂轨迹等难以写成硬规则的项目。它需要与人工判断校准，并定期重新检查偏差。用同一套未校准的模型同时生成、评分和改写标准，会弱化裁决的独立性。

## Eval Contract

<pre><code class="language-yaml">eval_id: gis-publish-regression-v7
system_under_test: gis-agent@v5
task: publish_and_verify_layer
input_fixture: fixtures/s57-small-03
environment: geoserver-sandbox@2.25
allowed_tools: [inspect, publish, verify_get_map]
authority: no_production_write
expected_outcomes:
  - layer_is_queryable
  - get_map_contains_visible_content
forbidden_outcomes:
  - modify_unrelated_workspace
graders:
  - schema_contract
  - external_get_map_probe
trials: 5
release_gate:
  capability: all_required_cases_pass
  regression: no_blocking_case_regresses
evidence: artifacts/evals/gis-v7/
owner: geo-platform
</code></pre>

合同同时记录任务、环境、权限、正负结果、评分器、试次和发布门。随机性较强的任务需要多次 trial，同时保留每次轨迹，否则平均分会掩盖稀有却严重的失败。

## 评测集的生命周期

1. 从规格和业务验收条件生成最初能力集。
2. 将真实失败、bad case 和事故压缩成可重放的回归样本。
3. 补入边界、权限、对抗、空输入和未知输入，同时保留正例与负例。
4. 给数据、环境、评分器和预期结果分别编版。
5. 定期阅读失败轨迹，删除失效样本，拆分过于宽泛的评分项。

能力评测追问系统现在能否完成目标任务，回归评测防止旧能力被新变更损害。两组样本的选择逻辑不同，发布时需要同时运行。

## 三组工程案例

### 外部验收取代内部“成功”

玄宿科技 GIS 数据发布 Agent 曾遇到一类典型假成功：发布接口返回成功，真实 GetMap 仍可能返回 `LayerNotDefined`，且某些错误响应的 HTTP 状态仍是 200。最终验收器从用户一侧发出真实 GetMap 或 GetTile 请求，检查协议结果、内容类型和可见图像。

### 任务图同时承载执行与验收

东方屹腾执行型 Agent 用任务 DAG 和节点状态机管理严格依赖。节点完成要通过验收器，业务 ID 的来源、工具回执和审批事件进入同一时间线。这样既能判断结果，也能定位跳步、漏步和重复执行。

### 同一能力在三种环境中验证

反思模块研讨提出三种环境：基准环境运行稳定样本，日常环境承接真实工作，测试环境允许新 Skill 和新提示词参与。候选能力先与现行版本并存，评测通过后再升级，避免一次经验直接改变全局行为。

## 发布证据流

<pre><code class="language-text">生产失败或新规格
        ↓
复现并固化成样本
        ↓
补入回归集，定义评分器和环境
        ↓
修改候选组件
        ↓
运行能力集 + 回归集 + 负例
        ↓
阅读失败轨迹并复核 grader
        ↓
发布、影子流量或回滚
</code></pre>

新失败应进入回归集，但不是每个线上样本都值得永久保留。团队需要去重、定期退役过期样本，并区分模型波动、环境故障、grader 错误与真实能力缺陷。

## 常见失效方式

- 只测最终文本，不检查外部状态和副作用。
- 只运行一次，将随机成功当成稳定能力。
- 数据集只有正例，没有拒绝、越权、未知输入和恢复场景。
- 用一条 golden trajectory 限定所有正确执行路径。
- 模型评分器没有与人工标注校准，分数变化无法解释。
- Agent 与 grader 在同一次修改中同时变化，旧结果无法比较。
- 仅公布综合分数，不保留样本级失败、轨迹和业务验收证据。

## 后续议题

专题研讨建议带上四件东西：一个真实 bad case，一份 Eval Contract，一条失败轨迹，以及这个样本如何影响发布的记录。这样才能比较不同团队的被测对象、评分口径和权限边界。

## 资料与来源

- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [LangSmith: Trajectory evaluations](https://docs.langchain.com/langsmith/trajectory-evals)
- [LangSmith: Evaluate a complex agent](https://docs.langchain.com/langsmith/evaluate-complex-agent)
- [OpenAI Evals API](https://platform.openai.com/docs/api-reference/evals/)
- [玄宿科技·GIS 数据发布 Agent](https://adpsagent.com/zh/cases/xuanxu-gis-agent/)
- [东方屹腾·执行型 Agent](https://adpsagent.com/zh/cases/liangbo-execution-agent/)
- [ADPS 行动模块第一次研讨会](https://adpsagent.com/zh/workshops/action-2026-08-06/)
- [ADPS 反思模块第一次研讨会](https://adpsagent.com/zh/workshops/reflection-2026-08-12/)
- [ADPS 治理模块第一次研讨会](https://adpsagent.com/zh/workshops/governance-2026-08-18/)
- [治理模块总纲与 Agent 生命周期](https://adpsagent.com/zh/patterns/governance/)

<div class="document-citation"><p><strong>引用建议：</strong>ADPS，《Agent 评测与验证 · 从输出评分到系统验收》，ADPS 专题研究，2026-08-14。</p><p><a href="https://adpsagent.com/zh/topics/">专题目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer">专题整理跨模块的工程问题。引用的模式定义、具名案例和研讨会记录以各自页面为准。</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>正文关联的研讨会与案例：<a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾·执行型 Agent</a>（<time datetime="2026-06-19">2026-06-19</time>）；<a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技·GIS 数据发布 Agent</a>（<time datetime="2026-07-30">2026-07-30</time>）；<a href="https://adpsagent.com/zh/workshops/action-2026-08-06/">ADPS 行动模块第一次研讨会</a>（<time datetime="2026-08-06">2026-08-06</time>）；<a href="https://adpsagent.com/zh/workshops/reflection-2026-08-12/">ADPS 反思模块第一次研讨会</a>（<time datetime="2026-08-12">2026-08-12</time>）</dd></div>
<div><dt>社区贡献</dt><dd>「验证为什么是分水岭」一节由 <a href="https://github.com/wikimatt" rel="noopener" target="_blank">@wikimatt</a> 通过<a href="https://adpsagent.com/zh/contribute/">段落讨论</a>提出，经 ADPS 编辑整理（<time datetime="2026-09-11">2026-09-11</time>）。逐次修订见<a href="https://adpsagent.com/zh/changes/">变更日志</a>。</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-14">2026-08-14</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#topics-agent-evals-and-testing">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
