<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/workshops/">研讨会</a><span style="margin: 0 0.45rem;">/</span>横切工程面 · 评测与验证</p>

<header class="publication-head">
<p class="publication-series">ADPS 设计模式系列研讨会</p>
<h1>Agent 评测与验证研讨会</h1>
<p class="publication-deck">车机测试、商品分类、AI 辅助研发与工程审图中的任务设计、评分方法和回归验证。</p>
</header>

<p class="publication-date">2026-09-29</p>

<table class="workshop-roster"><thead><tr><th>角色</th><th>姓名</th><th>公开身份</th></tr></thead><tbody>
<tr><td>主持人</td><td>黄佳</td><td>ADPS 发起人，Manning《Designing AI Agents》作者</td></tr>
<tr><td>主持人</td><td>高飞</td><td>软件测试 Agent AUUO.ai 技术负责人，前快手、爱奇艺资深架构师</td></tr>
<tr><td>研讨嘉宾</td><td>赵丽坤</td><td>蚂蚁支付宝技术部质量专家</td></tr>
<tr><td>研讨嘉宾</td><td>张栋</td><td>腾讯专家工程师，悟空研发安全负责人</td></tr>
<tr><td>研讨嘉宾</td><td>黄湘龙</td><td>北京微念智能创始人，OpenLogos 与 RunLogos 作者</td></tr>
<tr><td>研讨嘉宾</td><td>张海立</td><td>《LangGraph 实战》《LangChain 实战》作者，LangChain 官方大使</td></tr>
<tr><td>研讨嘉宾</td><td>李博</td><td>高级工程师，规划设计院总工</td></tr>
<tr><td>组织</td><td>白萍萍</td><td>ADPS 秘书，AI 产研峰会主理人</td></tr>
</tbody></table>

## 1. 软件开发、Agent 产品与药物研发的评测

黄佳以三个例子讨论评测对象的差别：用 AI 改写软件，检查交付的软件是否符合原要求；开发地图发布 Agent，检查它发布的地图；用 Agent 安排药物研发计算，检查计算结果能否帮助研究人员选择下一步实验。

软件迁移的教学例子是保留请求顺序。原程序要求结果按请求顺序返回，新实现打乱了顺序，测试失败。编程 Agent 可以修代码，也可以把测试改成“只检查元素相同，不检查顺序”。后一种改法虽然能通过测试，却改变了用户会得到的结果。原要求没变，就应修代码；确实不再要求保序，则先由需求负责人确认，再检查受影响的调用方并修改测试。

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-opening-software-zh.png"><img alt="软件迁移示例：修复返回顺序与放宽顺序断言的区别" loading="lazy" src="../../assets/images/workshops/evaluation-opening-software-zh.png"/></a><figcaption>保序要求仍然有效时，修改实现并按原断言重测；改变保序要求，需先确认调用方是否接受。</figcaption></figure>

地图发布使用了既有 GIS 案例中的故障：服务返回 HTTP 200，响应内容却是 XML 格式的 <code>LayerNotDefined</code> 错误。检查程序需要读取响应内容，确认收到的是可解码的地图图像。沿这个案例还可以继续设计位置验收：用已知港口或岸线的控制点核对坐标，检查图层顺序是否遮挡了要显示的要素。位置偏移和遮挡是开场的教学扩展，原案例记录的故障是图层请求失败。

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-opening-gis-zh.png"><img alt="地图发布的响应内容、图像解码和位置核对" loading="lazy" src="../../assets/images/workshops/evaluation-opening-gis-zh.png"/></a><figcaption>地图发布检查：读取响应内容，解码图像，再按控制点核对地图位置。</figcaption></figure>

药物研发也是教学示例。准备给一个候选分子做实验，需要把溶液配到规定浓度。两个溶解度预测模型中，A 预测能达到，B 预测达不到。Agent 首先核对两个工具使用的分子表示、单位、温度、pH 和适用范围。如果条件一致仍有分歧，可以请领域人员选择另一种计算方法，或安排针对性的溶解度实验，而不是直接再找一个模型投票。

怎样判断追加检查是否有用？选一批已有可靠实验结果、未用于调整流程的分子，在相同预算下比较两个流程：哪些可用分子被错排除了，哪些不适合实验的分子被错误推荐，以及有多少分歧需要研究人员处理。这样才能判断追加计算有没有改善候选选择。

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-opening-science-zh.png"><img alt="两个溶解度预测冲突后的输入核对、补充计算与实验选择" loading="lazy" src="../../assets/images/workshops/evaluation-opening-science-zh.png"/></a><figcaption>两个溶解度预测相反时，先核对输入条件，再决定补算或安排实验。</figcaption></figure>

## 2. 车机 GUI 测试的任务与环境

高飞区分了公开榜单和企业自己的测试。他介绍了 <a href="https://github.com/open-compass/AgentCompass">AgentCompass</a> 对基准、Harness、模型和环境的解耦，以及 <a href="https://github.com/harbor-framework/harbor">Harbor</a> 对任务、运行环境、Agent 交互和验证结果的组织。框架可以帮助重复运行，但任务集仍要回答“这个产品应该完成什么”。他用 <a href="https://github.com/swe-bench/SWE-bench">SWE-bench</a> 的仓库问题、补丁和测试说明，软件修复可以有相对明确的通过条件；调研报告、GUI 操作等任务则还要检查引用、界面状态和中间步骤。

他的车机测试现场更具体。部分设备无法依赖调试接口输入和读取状态，于是测试 Agent 从摄像头画面识别屏幕，再通过机械臂操作。换一套车机界面，就要采集新的图标与页面图片，人工标注一部分数据，重新检验识别与操作能力。早期方案每输入一个字母都重新观察屏幕，功能虽能跑通，速度却无法满足测试需要；后来把键盘输入拆成连续操作，减少逐字观察。评测在这里不仅查“能否点击”，还暴露出方案的时延问题。

黄佳问：报告、网站这类没有单一标准答案的成果，怎么比较新旧版本？高飞建议先确定产品任务，再分别检查可运行性、内容覆盖、引用真实性和风格；失败样本记录未完成的步骤。例如，报告引用了不存在的资料，与缺少一个要求分析的主题，应该分别记录，后续修改和重测的对象也不同。

## 3. 业务评测集与模型评分校准

赵丽坤介绍了消费端、商家端和内部运营等不同类型的智能体。功能、性能与首 Token 时间沿用软件测试的办法；回答是否符合业务，则需要按业务建评测集和评分标准。样本来自人工构造的典型问题、真实用户问题、线上失败案例和 AI 合成的问题。样本量不能脱离场景定：有的业务一百条能覆盖首批关键任务，有的要扩到更大规模。

商品标签是其中一个例子。模型把商品判断成食品还是服饰，可以先由人标出一批正确答案，再用另一个模型批量评分；当模型评分与人工标注不一致时，回看样本、分类标准与评分提示，校准负责评分的模型（Judge Model）。业务线越来越多时，共用平台能承接通用安全、多轮对话等横向测试，各业务团队维护自己的场景和指标。

黄佳问，很多团队各自做 Agent，怎样管理？赵丽坤介绍了共享底座、按团队管理的方式。关于业务效果，她认为面向消费者的应用还需要继续观察，部分面向企业的客服、策略和创意工作已能节省处理时间。

## 4. 端到端评测与重复运行稳定度

张栋建议按业务场景组织评测。以安全检测为例，先列最常见的几类问题，覆盖高频且高风险的任务，达到约定的上线标准后，再从线上失败案例补样本。安全场景重点检查漏了多少真实问题、报出的漏洞有多少是真的；质量检测或客户服务则需要按各自任务确定指标。

他提出的“黑盒”也不是不保存轨迹。第一次先检查端到端结果；若结果符合业务要求，暂时无需把每个内部步骤都变成独立评测项目。一旦结果不对，再把检测、执行和验证等环节拆开，定位是哪一步丢了证据或做错了判断。高飞随后追问指标如何贴近真实任务，张栋补了模型时代的一项指标：**稳定度**。同一任务、同一模型与配置多跑几次，漏洞有时查出、有时漏掉；只报一次准确率会把这种波动藏掉。版本更新后也要重跑旧场景，不能默认新模型全面优于旧模型。

对于线上拦截规则等会影响客户业务的改动，张栋主张保留人工检查和批准。Agent 可以在开发环境生成用例、分析失败和提出规则修改，也可以用不同模型交叉复核；上线前由负责人检查测试结果及改动范围。

## 5. AI 研发中的测试账本与代码评审

黄湘龙介绍 OpenLogos 与 RunLogos 中的研发流程：需求拆成场景，场景关联测试用例，代码和测试围绕用例 ID 展开；每轮测试把结果写入结构化账本，验收时按 ID 逐项核对。大任务分成小片，每片先测试，再进入下一片，最后做全量回归。测试不通过或账本损坏时，流程停下等待人处理。

他用一个模型开发、另一个模型评审。评审意见须标出代码位置、严重程度和修复依据；开发方逐条答复已修复、驳回或暂缓。没有轮次上限，评审会不断找到更细的小问题，于是流程设置发现问题与收敛处理的阶段，无法裁决的高风险问题交给人。

黄湘龙还遇到过重复实现的问题：Agent 没读透旧代码，为一个新需求又建缓存、事件源或流控机制。代码评审因此先查现有实现，指出可以复用的代码；修复缺陷时，也检查相关机制是否仍有必要。他还提出，测试代码、结果账本和评审规则本身需要测试。用例逐渐增多以后，每个小改动都跑全量测试会拖慢研发，需要分层或并行安排回归。

## 6. 工程图纸审查的资料要求

李博从规划设计院的工作讲起。最早的工具是协助一个专业的总工审图；后来要让多个专业围绕同一工程事实提出意见、核对冲突。他并不要求所有任务有同一个自动化比例：高风险问题留给人，中低风险的资料检查和规则提示可以逐步交给系统。

李博举例说，大型工程审查需要先检查地勘等先决资料。如果缺少地勘报告，系统应暂停正式审查，列出缺少的资料，等补齐后再继续。评测这个任务时，要检查它是否发现缺项、是否停止了依赖这些资料的审查。

在 Skill、单专业 Agent、多专业 Agent 三个阶段，团队分别检查方法对审图工作的帮助、专业任务的完成情况、跨专业意见的一致性。李博建议在测试集中保留真实工程任务。他还介绍，某些图纸场景使用图片或 PDF，比直接处理 CAD/BIM 更便于现阶段的模型读取，输入格式也需要纳入测试。

## 7. 评测设计检查表

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-evidence-loop-zh.svg"><img alt="业务任务、运行条件、结果验证和失败样本回流示意" loading="lazy" src="../../assets/images/workshops/evaluation-evidence-loop-zh.svg"/></a><figcaption>评测流程示意：按业务要求检查运行结果，把失败记录补充到后续测试中。</figcaption></figure>

<table class="evaluation-checklist"><thead><tr><th>要写清的事</th><th>本次讨论给出的检查方式</th></tr></thead><tbody>
<tr><td>任务与结果</td><td>谁的任务？正确答案、允许的停止条件和风险等级分别是什么？</td></tr>
<tr><td>运行条件</td><td>任务数据、环境、模型、Harness、工具与预算能否记录并重放？</td></tr>
<tr><td>裁判</td><td>程序、业务规则、模型评委和人各判什么？评委如何用人工样本校准？</td></tr>
<tr><td>版本比较</td><td>只改一个主要变量时，新旧版本的质量、稳定度、成本和时延如何变化？</td></tr>
<tr><td>发布与回流</td><td>哪些失败进入回归集？哪些线上改动必须由人复核？</td></tr>
</tbody></table>

张海立介绍了两类开发方式：组织现成的 Coding Agent 完成研发任务，以及使用 LangGraph 等框架开发自己的 Agent 产品。两种方式接入运行轨迹的方法不同，具体框架的比较留待后续讨论。

## 8. 相关规范与案例

- [X2 评测与验证](https://adpsagent.com/zh/patterns/x2-evals-and-testing/)记录横切工程要求；本场讨论补进业务真值、评委校准、重复稳定度、评测设施自身的测试与生产放行边界。
- [评测与测试专题](https://adpsagent.com/zh/topics/agent-evals-and-testing/)可继续收纳分领域的评测任务、数据集和验证器做法；本页保留现场讨论的来龙去脉。
- [GIS 发布案例](https://adpsagent.com/zh/cases/xuanxu-gis-agent/)提供“接口成功但地图错误”的具体项目背景；[反思模块](https://adpsagent.com/zh/patterns/reflection/)讨论失败如何变成下一版能力。

还没有在本场得到统一答案的问题包括：长程任务中断后怎样复位，多模型互审时怎样量化评委质量，以及评测集更新由谁批准。它们值得在后续的领域实例里继续验证。

开场材料用地图发布演示了回归检查。假设旧版把 HTTP 200 返回的 XML 错误当成地图，新版增加响应内容检查后，先重跑这条故障样例，再测试一批类似错误和正常地图。如果错误响应被识别出来，但正常地图也被拒绝发布，修改仍需继续。测试记录同时保存代码版本、工具配置和适用的地图类型，供负责人决定是否批准新版使用。

<figure class="workshop-diagram"><a href="../../assets/images/workshops/evaluation-opening-regression-zh.png"><img alt="地图发布修复后的错误样例检查与正常地图回归" loading="lazy" src="../../assets/images/workshops/evaluation-opening-regression-zh.png"/></a><figcaption>地图发布回归：既检查 XML 错误是否被识别，也检查正常地图能否继续发布。</figcaption></figure>

<p class="publication-note publication-note-end">本页依据 2026 年 9 月 29 日会议逐字稿整理。内部项目细节已脱敏。</p>

<!-- PAGE-CHRONICLE:START -->
<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>Agent 评测与验证研讨会；会议日期 <time datetime="2026-09-29">2026-09-29</time></dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-09-29">2026-09-29</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-10-01">2026-10-01</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/">查看 ADPS 来源时间线</a></p>
</section>
<!-- PAGE-CHRONICLE:END -->
