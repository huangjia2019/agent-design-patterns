<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/cases/" style="color: var(--color-text-muted);">案例库</a><span style="margin:0 0.45rem;">/</span>完整蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 系统蓝皮书 · 项目报告 03</p>
<h1>AI4MBSE 建模 Agent：让自然语言取得工程模型写入资格</h1>
<p class="publication-deck">元素、关系和视图分段规划，程序解析工程范围并在写回前检查结构事实。</p>
</header>

<!-- CASE-V06-ROUTE-ark-mbse-agent-True:START -->

<section aria-labelledby="case-route-mbse" class="case-route">
<p class="case-route-kicker">贯穿任务</p>
<h2 id="case-route-mbse">一句建模指令，怎样取得工程模型写入资格</h2>
<ol class="case-route-list">
<li><span class="case-step-no">01</span><strong>任务</strong><p>在指定包中创建一张用例图，复用已有参与者，补齐用例、关系和画布呈现。</p></li>
<li><span class="case-step-no">02</span><strong>第一处分叉</strong><p>业务名称无法唯一落到工程包；继续生成会把正确结构写进错误范围。</p></li>
<li><span class="case-step-no">03</span><strong>架构修改</strong><p>范围解析、三段类型化计划、七项写回门禁和唯一适配器共同控制副作用。</p></li>
<li><span class="case-step-no">04</span><strong>重新验收</strong><p>实际增量、结果枚举、回执和撤销句柄共同说明这次写回发生了什么。</p></li>
</ol>
</section>

<!-- CASE-V06-ROUTE-ark-mbse-agent-True:END -->

## 项目概览

<table>
<thead>
<tr>
<th style="text-align: left;">项目</th>
<th style="text-align: left;">项目信息</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">项目目标</td>
<td style="text-align: left;">用户用自然语言提出建模要求，系统在 MagicDraw、Cameo 等工具中创建或修改一张 SysML 图</td>
</tr>
<tr>
<td style="text-align: left;">核心风险点</td>
<td style="text-align: left;">画布视觉显示正常时，模型库中仍可能存在错误归属、悬空关系、重复元素或空变更假成功</td>
</tr>
<tr>
<td style="text-align: left;">技术方案</td>
<td style="text-align: left;">把元素、关系和视图拆成三份有类型的计划，程序解析挂载位置并在写回前检查结构不变量</td>
</tr>
<tr>
<td style="text-align: left;">最小写回单元</td>
<td style="text-align: left;">一种图类型、一个已解析位置、一份变更回执和一个撤销句柄</td>
</tr>
<tr>
<td style="text-align: left;">当前验证依据</td>
<td style="text-align: left;">宿主工具实验截图、意图日志、关系写回日志和项目复盘记录</td>
</tr>
<tr>
<td style="text-align: left;">适用场景</td>
<td style="text-align: left;">模型写入正式工程库前，类型、引用和写入范围可由程序校验的建模任务</td>
</tr>
</tbody>
</table>

## 1. MBSE 中的模型与图

SysML 用于描述复杂系统的组成、行为、需求和关系。MagicDraw、Cameo 一类工具既保存工程模型库，也显示各种图。图是模型的一种视图，只呈现模型的一部分。

例如，一张块定义图可以显示“闸机控制器”和“读卡器”。模型库还要保存这两个元素的稳定标识、所属包、类型和关系端点。画布上的方框位置正常，并不能证明关系端点有效，也不能证明元素写进了正确的包。

AI4MBSE 是袁良锭发起并在 mbse.ltd 持续记录的建模 Agent 项目，研究正式工程模型中的写入问题。一次错误写回可能被后续设计、仿真、评审和文档继续引用，因此验收要同时检查模型库和画布。

本文用一句简化指令贯穿后续设计：

> 在“闸机控制”包中创建一张用例图，包含“刷卡进入”“扫码进入”和“管理员放行”。

系统需要先回答三个问题：用户要创建什么图，写到哪个已有位置，明确点名的三个用例是否都进入最终计划。

## 2. 一次生成为什么容易留下结构错误

项目早期的验证方案让模型一次输出元素、关系和视图。这个路径调用少，失败却难定位。

- 元素名称合理，所属包可能不存在。
- 关系读起来通顺，端点 ID 可能指向未创建元素。
- 模型库已经写入三个对象，画布只显示两个。
- 用户点名三个用例，计划只生成两个，系统仍返回成功。

整份输出出错后只能整体重做，修复时模型还可能改动原本正确的部分。研究原型因此把主链路按建模语义拆成元素、关系和视图三个阶段，使每一段都能单独验收。

## 3. 三份计划怎样接起来

入口将用户语言收敛成一张作业单，至少记录操作类型、图类型和工程范围。

<figure>
<img alt="建模作业意图卡，包含操作、图类型和范围" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-a1-intent-card.jpg"/>
<figcaption>作业单固定本轮要做什么。范围尚未解析时，后续元素规划不会启动。</figcaption>
</figure>

三阶段只接收已经验收的上游结果。

<table>
<thead>
<tr>
<th style="text-align: left;">阶段</th>
<th style="text-align: left;">输入</th>
<th style="text-align: left;">产出</th>
<th style="text-align: left;">不能越界做什么</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">元素规划</td>
<td style="text-align: left;">用户摘要、已解析范围、类型白名单、邻近可复用元素</td>
<td style="text-align: left;"><code>ElementPlan</code></td>
<td style="text-align: left;">不生成关系和布局</td>
</tr>
<tr>
<td style="text-align: left;">关系规划</td>
<td style="text-align: left;"><code>ElementPlan</code>、关系白名单、业务摘要</td>
<td style="text-align: left;"><code>RelationPlan</code></td>
<td style="text-align: left;">不创建计划外元素，不改稳定标识</td>
</tr>
<tr>
<td style="text-align: left;">视图规划</td>
<td style="text-align: left;">已验收元素、关系和当前图规则</td>
<td style="text-align: left;"><code>ViewPlan</code></td>
<td style="text-align: left;">不重新发明模型结构</td>
</tr>
</tbody>
</table>

按研究机制整理，一次作业可以表示成下面的结构。

<pre><code class="language-text">ModelingJob
  action: chat | create | modify
  diagram_type: use_case | bdd | ibd | state | ...
  scope_ref: stable project reference | pending
  stage: intent | elements | relations | view | validated | applied
  element_plan: typed elements with stable references
  relation_plan: typed edges whose endpoints resolve
  view_plan: projection over accepted model objects
  outcome: applied | applied_with_warnings | blocked | noop
  writeback_receipt: state delta + rollback handle
</code></pre>

ADPS 将这三份计划称为类型化中间表示链。名称可以先放在一边，工程上的重点是：下游不再读取一段自由文本，而是读取字段、类型和引用都能检查的上游结果。

三阶段既可以由三个独立 Agent 执行，也可以由一个进程中的三个函数完成。真正产生价值的是输入边界、失败隔离和数据契约，不是 Agent 数量。

## 4. 一次只处理一张图

“完成闸机系统模型”没有稳定边界。它可能同时包含需求图、用例图、块定义图、内部块图和状态图。前面的偏差还会传播到后面的图。

本研究将单次操作限制为：

> 一种图类型 + 一个已解析的挂载位置。

这条约束同时确定本轮可以修改什么、写回前验收哪些对象、撤销哪些变更，以及回归测试如何构造。用户得到一张图、一份变更摘要和一个撤销入口。

<figure>
<img alt="写回后的画布结果和撤销入口" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-a2-canvas-result.jpg"/>
<figcaption>一次操作只负责一张图。变更摘要区分新建、复用和未处理项，并提供撤销句柄。</figcaption>
</figure>

这个边界也控制故障影响范围。大型项目仍需要分支合并、并发写入和权限分区，本研究未公开相关机制。

## 5. 挂载位置不清楚时，作业怎样暂停

用户说“闸机控制包”时，工程中可能存在同名位置，也可能根本不存在。系统先查询工程索引。唯一命中才继续；候选较少时让用户选择；没有合理候选时要求补充包名或先创建范围。

系统不会默认写到项目根目录，也不会为了完成任务自动生成一棵父包树。

<figure>
<img alt="范围未命中时的澄清卡片和作业状态" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-04-clarify-scope.jpg"/>
<figcaption>澄清卡保留已经确定的图类型和操作，只补当前缺失的范围。</figcaption>
</figure>

等待用户时，一条 pending operation 保存 `action`、`diagram_type`、候选范围、当前阶段和处理选项。用户补充后，运行时从范围解析处继续，不重新完成整轮意图识别和规划。

这类 HITL 的关键是可恢复作业。界面弹窗负责收集信息，作业单负责冻结进度和恢复位置。

## 6. 写回前检查哪些事实

研究过程中把典型失败场景整理成一组程序可检查的条件。本文称它们为**写回校验**，也就是写入正式模型库前必须通过的确定性检查。

<table>
<thead>
<tr>
<th style="text-align: left;">检查项</th>
<th style="text-align: left;">程序核对什么</th>
<th style="text-align: left;">失败处理</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">范围唯一</td>
<td style="text-align: left;"><code>scope_ref</code> 指向已有且允许写入的对象</td>
<td style="text-align: left;">澄清或阻断</td>
</tr>
<tr>
<td style="text-align: left;">类型合法</td>
<td style="text-align: left;">元素、关系和图类型属于当前 Profile</td>
<td style="text-align: left;">唯一可修复时修复，其余阻断</td>
</tr>
<tr>
<td style="text-align: left;">引用闭合</td>
<td style="text-align: left;">每条关系两端都能解析到已验收对象</td>
<td style="text-align: left;">阻断</td>
</tr>
<tr>
<td style="text-align: left;">明示完整</td>
<td style="text-align: left;">用户点名的可计数对象都进入计划</td>
<td style="text-align: left;">写前澄清或由用户确认跳过</td>
</tr>
<tr>
<td style="text-align: left;">视图是子集</td>
<td style="text-align: left;">进入画布的对象都来自已验收模型结果</td>
<td style="text-align: left;">剔除或阻断</td>
</tr>
<tr>
<td style="text-align: left;">变更真实</td>
<td style="text-align: left;">写入产生可观察增量，或明确判定为幂等 <code>noop</code></td>
<td style="text-align: left;">空增量不能返回成功</td>
</tr>
<tr>
<td style="text-align: left;">单一写回</td>
<td style="text-align: left;">模型库和视图通过同一通道更新，并生成回执</td>
<td style="text-align: left;">部分成功不得冒充完整成功</td>
</tr>
</tbody>
</table>

<figure>
<img alt="写回前对照用户列举数量与元素计划" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-a3-prewrite-clarify.jpg"/>
<figcaption>用户点名三个用例，计划只有两个。系统在产生副作用前列出差异。</figcaption>
</figure>

写回后的结果只有四类。

<table>
<thead>
<tr>
<th style="text-align: left;">状态</th>
<th style="text-align: left;">是否写入</th>
<th style="text-align: left;">含义</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>APPLIED</code></td>
<td style="text-align: left;">是</td>
<td style="text-align: left;">计划、校验和回执一致</td>
</tr>
<tr>
<td style="text-align: left;"><code>APPLIED_WITH_WARNINGS</code></td>
<td style="text-align: left;">是</td>
<td style="text-align: left;">主结构可用，非破坏性缺项已经指名</td>
</tr>
<tr>
<td style="text-align: left;"><code>BLOCKED</code></td>
<td style="text-align: left;">否</td>
<td style="text-align: left;">结构条件不成立，工程保持原样</td>
</tr>
<tr>
<td style="text-align: left;"><code>NOOP</code></td>
<td style="text-align: left;">否</td>
<td style="text-align: left;">目标已存在，或本轮没有可写增量；原因必须区分</td>
</tr>
</tbody>
</table>

<figure>
<img alt="成功写回摘要，包含新建、复用和撤销信息" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-03-writeback-summary.jpg"/>
<figcaption>成功回执记录实际增量，并把撤销能力交给用户。</figcaption>
</figure>

<figure>
<img alt="画布保持未变，阻断卡说明悬空关系" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-07-blocked-failure.jpg"/>
<figcaption>关系端点无法解析时，系统不写入，并给出可以继续修正的原因。</figcaption>
</figure>

## 7. 哪些问题交给程序，哪些仍需要评审

研究过程中早期测试过“生成、模型评审、修改、再评审”的循环模式。实际验证出现三个问题：评审提示与工具 schema 的口径不一致，等待时间和费用增加，长评论没有直接提高写回可用性。

在早期本地验证中，写回后的模型自评循环没有带来相称收益。当前方案取消这段循环，在组装前只保留最多一次有界修复，写回准入交给程序检查。

<table>
<thead>
<tr>
<th style="text-align: left;">问题</th>
<th style="text-align: left;">合适的机制</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">类型、范围、引用、数量和实际增量能被程序判定</td>
<td style="text-align: left;">同步写回校验</td>
</tr>
<tr>
<td style="text-align: left;">写操作有副作用，错误必须在本轮阻断</td>
<td style="text-align: left;">校验加事务回执</td>
</tr>
<tr>
<td style="text-align: left;">命名质量、建模粒度等语义标准难以写成规则</td>
<td style="text-align: left;">写入前生成评审或人员评审</td>
</tr>
<tr>
<td style="text-align: left;">多个项目反复出现同类漏项</td>
<td style="text-align: left;">失败记录和离线分析</td>
</tr>
</tbody>
</table>

这项取舍没有否定反思。它把结构正确性交给可复验程序，把语义品质和跨项目改进留给模型或人员。判断依据是错误能否计算、副作用何时发生，以及用户能等待多久。

## 8. 类型名称不一致时，不要怪模型

规划阶段、宿主工具和写回回执可能使用不同类型名。模型计划使用业务细名，MagicDraw 或 Cameo API 使用元模型名，导入层还可能返回归一化后的粗类型。直接比较字符串会误杀合法结果，也可能把粗类型放进不合适的图。

系统需要一张显式类型翻译表。

<pre><code class="language-text">规划类型
  -&gt; 领域标准类型
  -&gt; 宿主工具元模型类型
  -&gt; 写回后返回类型
</code></pre>

翻译表按图类型和宿主适配器选择，并在日志中同时保存原始值和归一化值。这样，转换错误可以定位到 adapter 或 Profile，不会一概记成“LLM 幻觉”。

ADPS 概念库将这类机制暂记为[词表等价层](https://adpsagent.com/zh/concepts/vocabulary-equivalence-layer/)。现场实现仍应使用领域团队熟悉的名称。

## 9. 工程很大时，只给当前步骤所需上下文

完整工程树、九类图规则和全部历史对话不适合每次一起进入模型。面向大型工程模型，本研究采用五项约束控制上下文边界。

1. 只注入当前图类型的 Profile。
2. 业务理解生成一次稳定摘要，关系和视图阶段读取摘要与上游计划。
3. 近端上下文提供邻近包、元素和可复用对象，远端只保留项目约束与进度摘要。
4. 意图和澄清可使用轻量模型，元素与关系规划使用主模型。
5. 能由规则决定的视图筛选交给程序。

这套安排减少了每次调用的输入面。当前材料尚未提供 token、时延和成功率对照，因此本版只记录设计判断，不给出总体性能结论。

## 10. 研究环境演示截图

下面的截图来自袁良锭的个人本地实验环境，用于说明宿主集成、单次意图解析和关系写回机制。它们只证明截图所示运行，不代表商用交付能力或长期工程稳定性。

<figure>
<img alt="Magic Systems of Systems Architect 中的飞行汽车工程与 AI4MBSE 助手" src="../../assets/zh/cases/ark-mbse-agent/assets/shot-magicdraw-flycar.jpg"/>
<figcaption>AI4MBSE 以面板形式嵌入建模工具的实验演示。左侧是工程树，中间是模型视图，右侧是助手。</figcaption>
</figure>

<figure>
<img alt="意图识别日志，action 为 chat，diagramType 和 scope 为 null" src="../../assets/zh/cases/ark-mbse-agent/assets/log-intent-recognition.jpg"/>
<figcaption>一次咨询请求得到 <code>action=chat</code>，没有进入建模写回链。该截图只支持这一次运行的结论。</figcaption>
</figure>

<figure>
<img alt="卫星平台系统块定义图和元素规划面板" src="../../assets/zh/cases/ark-mbse-agent/assets/shot-satellite-bdd.jpg"/>
<figcaption>卫星平台工程示例中的块定义图。右侧面板列出本轮元素规划和归属。</figcaption>
</figure>

<figure>
<img alt="关系写回日志，关系与端点使用稳定标识" src="../../assets/zh/cases/ark-mbse-agent/assets/log-relation-writeback.jpg"/>
<figcaption>写回记录使用稳定元素和关系标识。单张日志不能说明所有图类型的总体成功率。</figcaption>
</figure>

<!-- CASE-V06-REPLAY-ark-mbse-agent-True:START -->

<section aria-labelledby="replay-mbse" class="case-replay">
<h2 id="replay-mbse">同一条闸机用例图任务重新跑一遍</h2>
<p>自然语言在进入宿主模型库之前，逐段收敛为可检查结构。</p>
<ol class="case-replay-list">
<li><span class="case-step-no">01</span><strong>建立 ModelingJob</strong><p>保存 create、use_case、明示对象和宿主 revision。</p></li>
<li><span class="case-step-no">02</span><strong>解析范围</strong><p>同名包出现时冻结作业；用户选择后按稳定 ID 与最新 revision 复核。</p></li>
<li><span class="case-step-no">03</span><strong>形成三段计划</strong><p>ElementPlan、RelationPlan、ViewPlan 分别约束对象、关系和当前视图。</p></li>
<li><span class="case-step-no">04</span><strong>执行七项门禁</strong><p>检查范围、类型、稳定引用、明示项、关系闭包、写集和宿主版本。</p></li>
<li><span class="case-step-no">05</span><strong>唯一写回</strong><p>同一个适配器提交模型库与画布，避免两条写入路径产生不同结果。</p></li>
<li><span class="case-step-no">06</span><strong>结果回执</strong><p>实际增量决定 APPLIED、WARNING、BLOCKED 或 NOOP，并保存撤销句柄。</p></li>
</ol>
<p class="case-outcome"><strong>提交条件</strong>计划通过门禁、宿主返回真实增量、模型库与画布一致，三项同时成立。</p>
</section>

<!-- CASE-V06-REPLAY-ark-mbse-agent-True:END -->

<!-- CASE-V06-EVIDENCE-ark-mbse-agent-True:START -->

<section aria-labelledby="evidence-mbse" class="case-evidence-section">
<p class="case-evidence-label">项目过程图与宿主截图</p>
<h2 id="evidence-mbse">从进度、澄清、写回到降级结果，证据要连成一段</h2>
<div class="case-evidence-grid">
<figure class="case-evidence"><img alt="AI4MBSE 建模作业进度线" loading="lazy" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-01-progress-line.jpg"/><figcaption><strong>阶段进度线</strong>元素、关系、视图和写回各自保留状态。<span class="case-evidence-proof">教学复原图；解释阶段边界，不证明宿主已经实现同名组件。</span></figcaption></figure>
<figure class="case-evidence"><img alt="AI4MBSE 模型库与画布写回" loading="lazy" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-02-canvas-writeback.jpg"/><figcaption><strong>模型库与画布写回</strong>同一变更集同时落到结构和呈现。<span class="case-evidence-proof">教学复原图；实际结果需结合宿主回读与日志。</span></figcaption></figure>
<figure class="case-evidence"><img alt="AI4MBSE 澄清后续跑时间线" loading="lazy" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-05-resume-timeline.jpg"/><figcaption><strong>澄清后续跑</strong>补充范围后继续原 ModelingJob，并复核宿主 revision。<span class="case-evidence-proof">图支持交互与状态设计；未覆盖多人并发修改。</span></figcaption></figure>
<figure class="case-evidence"><img alt="AI4MBSE 带警告写回结果" loading="lazy" src="../../assets/zh/cases/ark-mbse-agent/assets/fig-06-degraded-success.jpg"/><figcaption><strong>带警告结果</strong>结构写回成立，非破坏性问题进入 warnings。<span class="case-evidence-proof">状态枚举不等于质量保证；语义品质仍需评审。</span></figcaption></figure>
</div>
<div class="case-source-links">
<a href="https://www.mbse.ltd/zh/ai4mbse.html" rel="noopener" target="_blank"><strong>AI4MBSE 项目页</strong><span>项目说明、方法论包与本地交互示意</span></a>
<a href="https://www.mbse.ltd/zh/faq.html" rel="noopener" target="_blank"><strong>项目 FAQ</strong><span>当前状态、实验边界与材料说明</span></a>
<a href="https://adpsagent.com/zh/concepts/typed-ir-chain/"><strong>类型化 IR 链</strong><span>从项目机制提炼出的工程概念</span></a>
</div>
</section>

<!-- CASE-V06-EVIDENCE-ark-mbse-agent-True:END -->

## 11. 下一版最值得补的数据

<table>
<thead>
<tr>
<th style="text-align: left;">指标</th>
<th style="text-align: left;">回答的问题</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">范围解析准确率</td>
<td style="text-align: left;">自动命中的 <code>scope_ref</code> 有多少经人员复核正确</td>
</tr>
<tr>
<td style="text-align: left;">明示元素召回率</td>
<td style="text-align: left;">用户点名的对象有多少进入已验收计划</td>
</tr>
<tr>
<td style="text-align: left;">悬空引用逃逸数</td>
<td style="text-align: left;">有多少无效端点越过写回校验，目标值为 0</td>
</tr>
<tr>
<td style="text-align: left;">静默扩域事故数</td>
<td style="text-align: left;">是否未经确认写入错误范围或新建父结构</td>
</tr>
<tr>
<td style="text-align: left;">假成功率</td>
<td style="text-align: left;">返回成功但回执为空或结构验收失败的比例</td>
</tr>
<tr>
<td style="text-align: left;">澄清续跑正确率</td>
<td style="text-align: left;">用户补充信息后是否从正确阶段恢复</td>
</tr>
<tr>
<td style="text-align: left;">撤销完整率</td>
<td style="text-align: left;">撤销后模型库和画布是否都恢复</td>
</tr>
<tr>
<td style="text-align: left;">阶段成本</td>
<td style="text-align: left;">各阶段的时延、重试、token 和模型费用</td>
</tr>
</tbody>
</table>

指标应按图类型、创建或修改、宿主工具和用户经验分层，避免一个总成功率掩盖差异。

## 12. 迁移时可以照着做的八步

1. 选定一种图和一个真实工程范围，定义最小写入边界。
2. 把用户请求收敛为操作、图类型和稳定范围引用。
3. 将元素、关系和视图拆成有类型的阶段计划。
4. 为每个阶段写出输入白名单、输出 schema 和不允许越界的动作。
5. 列出范围、类型、引用、数量和实际增量等程序可判定条件。
6. 所有写入经过一个通道，并生成变更摘要、回执和撤销句柄。
7. 范围不明时保存 pending operation，测试补充、恢复、取消和超时。
8. 用固定测试集记录假成功、悬空引用和撤销完整率，再扩大图类型。

EDA、BIM、ERP 主数据、CMDB 和工艺路线也可能出现类似条件：结构进入正式库，引用必须有效，错误写入会影响后续工作。迁移的是阶段契约、稳定引用、确定性校验和带回执写入，不是 SysML 的具体类型表。

## 13. 三份技术方案对照观察

<table>
<thead>
<tr>
<th style="text-align: left;">方案</th>
<th style="text-align: left;">程序保管的严格事实</th>
<th style="text-align: left;">验收位置</th>
<th style="text-align: left;">主要恢复方式</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾</a></td>
<td style="text-align: left;">业务 ID、来源回执和任务节点</td>
<td style="text-align: left;">每步调用前后</td>
<td style="text-align: left;">会话内暂停、审批和恢复</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/cases/xuanxu-gis-agent/">玄宿科技</a></td>
<td style="text-align: left;">文件签名、SRS、bbox 和管线状态</td>
<td style="text-align: left;">发布后的真实请求</td>
<td style="text-align: left;">规则回退与跨运行失败沉淀</td>
</tr>
<tr>
<td style="text-align: left;">AI4MBSE 建模 Agent 项目</td>
<td style="text-align: left;">挂载位置、稳定标识、关系端点和类型翻译</td>
<td style="text-align: left;">写入模型库之前</td>
<td style="text-align: left;">有界修复、澄清、阻断或撤销</td>
</tr>
</tbody>
</table>

三个方案共同支持一条技术观察：精确结构坐标应由可追溯的程序状态传递，模型负责产生候选意图和计划。验证位置则由副作用、外部可观测性和修复窗口决定。这仍是跨方案观察，需要更多项目继续检验。

## 14. 适用边界与 ADPS 对照

本项目适合正式模型库中的有界写入场景验证。报告、课件和开放检索结果通常允许重写，不需要复制整套结构校验。当前材料也没有覆盖大团队并发写入、模型分支合并、权限分区、长事务补偿和安全关键项目认证。

SysML v2 提供更精确的语义和标准化模型访问接口，可以减少专有适配工作。范围解析、引用完整性和事务回执仍然需要由应用运行时负责。

<table>
<thead>
<tr>
<th style="text-align: left;">模式</th>
<th style="text-align: left;">本项目中的实现</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/a3-prompt-chaining/">A3 提示链</a></td>
<td style="text-align: left;">元素、关系和视图三段计划</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/a4-guardrail-sandwich/">A4 护栏三明治</a></td>
<td style="text-align: left;">范围检查、阶段校验和写回校验</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/g2-blast-radius-control/">G2 爆炸半径控制</a></td>
<td style="text-align: left;">一次一图、单一写回和可撤销变更集</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/g1-approval-gate/">G1 审批门</a></td>
<td style="text-align: left;">范围不明时澄清，高风险部署可在写回前确认</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/m3-progress-tracking/">M3 进度追踪</a></td>
<td style="text-align: left;">pending operation 保存图类型、范围和阶段</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/r2-complexity-based-routing/">R2 复杂度路由</a></td>
<td style="text-align: left;">轻重模型分流，执行深度随图类型变化</td>
</tr>
<tr>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/x1-observability/">X1 可观测性</a></td>
<td style="text-align: left;">阶段输入输出、校验裁决和写回日志</td>
</tr>
</tbody>
</table>

---

### 作者与引用说明

**项目发起人**：袁良锭（Liangding Yuan），成都的架构师，拥有十六年研发与架构经历，做过流程、搜索、协作、授权和知识系统等平台工作。AI4MBSE 是他发起并持续验证的建模 Agent 项目。

**项目站点**：[mbse.ltd](https://www.mbse.ltd/zh/)（用于技术学习与学术交流）

**建议引用格式**：ADPS、袁良锭，《AI4MBSE 建模 Agent：让自然语言取得工程模型写入资格》，ADPS Agent 系统蓝皮书项目报告 03，v0.6，2026。

> 版权说明：本文原创内容版权归属袁良锭，采用 CC BY 4.0 协议开放共享。

<div class="document-citation">
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>证据边界：</strong>本文记录袁良锭发起的 AI4MBSE 建模 Agent 项目在本地环境中的技术推演与闭环验证。截图和示例数据来自本地实验，尚未经过第三方独立工程审计。</p>
<p class="publication-disclaimer"><strong>使用边界：</strong>本文用于技术学习与学术交流，不构成软件产品、商业解决方案或项目交付能力说明。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/ark-mbse-agent/">AI4MBSE 建模 Agent 项目</a>；作者：袁良锭</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-02">2026-08-02</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#cases-ark-mbse-agent">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
