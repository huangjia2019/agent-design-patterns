<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/cases/" style="color: var(--color-text-muted);">案例库</a><span style="margin:0 0.45rem;">/</span>完整蓝皮书</p>

<header class="publication-head">
<p class="publication-series">ADPS 企业 Agent 系统蓝皮书 · 案例报告 01</p>
<h1>东方屹腾执行型 Agent：让业务状态沿流程准确传递</h1>
<p class="publication-deck">模型理解意图，程序保存业务参数来源，任务图与状态机维护严格执行顺序。</p>
</header>

<!-- CASE-V06-ROUTE-liangbo-execution-agent-True:START -->

<section aria-labelledby="case-route-liangbo" class="case-route">
<p class="case-route-kicker">贯穿任务</p>
<h2 id="case-route-liangbo">一条薪资组配置链，怎样从原型走到可恢复执行</h2>
<ol class="case-route-list">
<li><span class="case-step-no">01</span><strong>任务</strong><p>新客户选择薪资模板、保存现状、导入配置，并在敏感步骤等待确认。</p></li>
<li><span class="case-step-no">02</span><strong>第一处分叉</strong><p>模型从对话历史重写 <code>template_id</code>，字段合法，来源却不再可信。</p></li>
<li><span class="case-step-no">03</span><strong>架构修改</strong><p>严格值进入 SessionState，步骤依赖进入 Workspace，模型只处理意图与叙事。</p></li>
<li><span class="case-step-no">04</span><strong>重新验收</strong><p>批准后从原节点恢复；业务回读通过，任务才从 running 进入 completed。</p></li>
</ol>
</section>

<!-- CASE-V06-ROUTE-liangbo-execution-agent-True:END -->

## 案例速览

<table>
<thead>
<tr>
<th style="text-align: left;">项目</th>
<th style="text-align: left;">现场信息</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">业务任务</td>
<td style="text-align: left;">帮助中小企业完成薪资组配置，并逐步覆盖算薪、代发、报税等连续业务流程</td>
</tr>
<tr>
<td style="text-align: left;">最早暴露的问题</td>
<td style="text-align: left;">模型能选对工具，却会偶发误写上一步返回的业务 ID，或跳过有严格依赖的步骤</td>
</tr>
<tr>
<td style="text-align: left;">核心做法</td>
<td style="text-align: left;">模型处理意图和语义，程序保存业务参数来源，任务图与状态机维护执行顺序</td>
</tr>
<tr>
<td style="text-align: left;">关键运行结构</td>
<td style="text-align: left;">Orchestrator、Activity/Frame 时间线、Workspace、SessionState、SessionNarrative</td>
</tr>
<tr>
<td style="text-align: left;">当前证据</td>
<td style="text-align: left;">案例方项目复盘、系统结构和运行机制说明</td>
</tr>
<tr>
<td style="text-align: left;">适用范围</td>
<td style="text-align: left;">API 由组织管理，步骤依赖严格，参数错绑会造成真实业务后果的企业流程</td>
</tr>
</tbody>
</table>

## 1. 客户卡在首次配置

东方屹腾的 SaaS 产品覆盖人事、组织、考勤、审批和薪酬，并连接银行与税务系统。这个案例聚焦其中一条容易在首次配置阶段卡住的业务链。团队最初评估过用工分析、薪酬结构优化和报表分析，这些场景容易演示，却没有击中客户启用系统时最费力的环节。

客户访谈指向了首次配置。新企业需要建立薪资组和薪资项，导入员工与组织，完成定薪，再配置考勤和审批规则。由运营团队代为配置的客户通常能顺利启用，自行配置的客户更容易中途放弃。

团队把“薪资组快速搭建”定为首个场景。它的范围不大，却包含模板匹配、数据快照、连续 API 调用、失败回滚和人工确认。一个 Agent 若能稳定完成这条链，才有资格继续进入算薪、代发和报税。

## 2. 第一个原型：工具选对了，状态仍会传错

最初的设想是把现有 API 封装为 MCP Server，让模型按用户意图选择工具并组织参数。工具发现很快跑通，连续调用暴露了另一个问题。

以报销为例，流程依次创建申请、上传发票、提交审批和查询结果。上传接口使用的 `application_id` 必须来自刚才那次创建调用。薪资组配置也一样，模板匹配返回的 `template_id` 要原样进入后续导入接口。

早期原型把每步回执追加到对话上下文，再让模型生成下一步参数。测试中出现过 ID 误写和参数错绑。JSON Schema 可以检查字段类型和格式，无法证明一个值来自哪次调用。对于 64 位或 128 位业务标识，只错一个字符也可能访问错误实体。

这次失败划出了一条系统边界。

- 报告、摘要和 PPT 在步骤间传递文本，局部偏差通常还能重写。
- 薪酬、审批和报销在步骤间传递业务状态，漏步、跨步和参数错绑会改变真实数据。

东方屹腾继续使用模型理解用户和选择业务路径，同时把严格参数从语言上下文中拿出来，交给程序保存和注入。

## 3. 运行过程的可观测性

后端使用 Go，初期没有引入 Agent 框架。第一阶段只接通连续对话、附件上传和流式回复，先固定入口和输出协议。Web 界面同步建设，业务人员可以在同一页面检查用户输入、执行进度和最终结果。

运行时从第一天就记录结构化事件。一次对话拆成按时间排序的 `Activity`，每个 Activity 下包含一个或多个 `Frame`。Frame 保存当时的输入、模型输出、工具调用、耗时和费用。意图识别、路由、ReAct 循环和状态变化也写入同一时间线。

这套记录先解决开发问题：哪一步选错了工具，哪个 ID 来自哪次调用，任务为何停在审批节点。生产环境再按权限隐藏调试详情。可观测性在这里不是上线后的监控补丁，它是业务评审和问题复现的共同底座。

## 4. 一次请求怎样流过系统

用户输入先经过意图识别，得到有限的控制信号。早期信号包括 `chat`、`analyze` 和 `resolve`，解析失败则进入 `unknown`。后续类型可随业务扩展，但每个类型都必须对应明确的程序分支。

<pre><code class="language-text">用户消息
  -&gt; MessageHandler 接收并建立事件流
  -&gt; 意图识别生成控制信号
  -&gt; Orchestrator 选择执行链
  -&gt; 推理或规划确定下一步
  -&gt; 行动模块调用工具
  -&gt; 状态、任务进度和叙事摘要分别落盘
  -&gt; 统一事件流向界面返回进度与结果
</code></pre>

`MessageHandler` 处理消息入口、SSE 和结束协议。`Orchestrator` 读取控制信号，调用推理、记忆、检索和行动模块。业务能力注册在明确的输入输出契约上，新增能力主要接入中段流程，不需要改动消息入口。

系统也把两类信息分开保存。控制信号、任务状态和准入结果驱动程序分支；用户目标、分析结论和执行摘要进入模型上下文。前者要求枚举和校验，后者允许语言表达。案例方把它们分别称为控制平面和叙事平面。

<figure>
<img alt="Orchestrator 连接控制平面、叙事平面、MessageHandler 与 Harness 边界" src="../../assets/images/concepts/orchestrator.png"/>
<figcaption>读图重点：<code>MessageHandler</code> 只负责入口与展示；<code>Orchestrator</code> 把控制信号、语义上下文和工具执行组成可跟踪的运行链。</figcaption>
</figure>

## 5. 什么时候探索，什么时候按计划执行

`resolve` 说明用户要完成一件事，还没有给出稳定步骤。任务边界模糊时，系统使用链式推理或 ReAct 边执行边判断。每轮把 `Thought`、`Action` 和 `Observation` 追加到 scratchpad，下一轮读取最新观察。

严格依赖出现后，控制权交给规划执行。规划器把任务拆成 DAG，执行器只调度所有上游节点已经完成的 `ready` 节点，验收器决定节点能否进入 `completed`。

<table>
<thead>
<tr>
<th style="text-align: left;">现场状态</th>
<th style="text-align: left;">使用方式</th>
<th style="text-align: left;">原因</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">目标仍需澄清，下一步取决于刚取得的信息</td>
<td style="text-align: left;">ReAct</td>
<td style="text-align: left;">保留探索空间</td>
</tr>
<tr>
<td style="text-align: left;">步骤和依赖已经明确</td>
<td style="text-align: left;">任务 DAG 与状态机</td>
<td style="text-align: left;">防止跨步、漏步和重复执行</td>
</tr>
<tr>
<td style="text-align: left;">某一步会产生高风险副作用</td>
<td style="text-align: left;">状态机加人工审批</td>
<td style="text-align: left;">在原节点暂停并保留恢复位置</td>
</tr>
<tr>
<td style="text-align: left;">只需查询或生成内容</td>
<td style="text-align: left;">短链或直接回答</td>
<td style="text-align: left;">不为低风险任务引入完整调度成本</td>
</tr>
</tbody>
</table>

薪资组快速搭建的模拟链包含模板匹配、现有数据快照、模板导入和失败回滚。它曾仅以文字步骤交给 ReAct，测试中出现跨步和漏步。任务图正是由这次失败推动出来的。

## 6. 业务 ID 由程序保管来源

工具回执中的严格参数进入 `SessionState`。后续工具按坐标读取，模型只看到“模板已经匹配”这类叙事摘要。每个状态值同时保存来源信息，调用前可以核对生产工具和调用实例。

下面是 ADPS 根据案例机制整理的示意结构。

<pre><code class="language-json">{
  "scope": "session/payroll_setup",
  "key": "template_id",
  "value": "9287461350021",
  "producer": "match_salary_template",
  "call_id": "call_0187",
  "receipt_ref": "events/0187/tool-result"
}
</code></pre>

工具注册时声明自己生产和消费哪些状态。`RunPipeline` 在调用前完成四件事：根据坐标取值，核对来源，注入参数，记录本次消费关系。模型不会再次拼写 `template_id`。

这套机制成立于封闭工具体系。组织需要事先管理工具注册、状态键、作用域和权限。开放网络中的任意工具无法自动获得同样的来源保证。

<figure>
<img alt="机械状态平面以 Producer、Consumer、Scope 和 Key 记录参数来源" src="../../assets/images/concepts/mechanical-state-plane.png"/>
<figcaption>一个值能否进入下一步，取决于生产者、消费者、作用域和状态键是否同时对得上；缺值或来源不明时直接失败。</figcaption>
</figure>

## 7. 审批要能停住，也要能从原处继续

敏感节点开始前，执行器将节点置为等待审批。人工批准后，系统重新读取持久化状态，校验任务与工具条件，再从原节点继续。拒绝或超时则进入明确的终止或改计划路径。

案例包含两种人机衔接。

- **下一轮继续**：当前会话结束，用户之后输入“继续”或补充信息，系统从已保存目标和进度恢复。
- **执行中等待**：会话运行仍存在，某个任务节点阻塞，审批事件到达后恢复。

第二种方式需要持久化 DAG、节点状态、审批结果和参数来源。确认弹窗只能暂时阻断一次动作，恢复所需的断点由任务状态机提供。

## 8. 长程状态分放三处

系统逐步形成三个状态平面，各自回答一个问题。

<table>
<thead>
<tr>
<th style="text-align: left;">状态平面</th>
<th style="text-align: left;">回答的问题</th>
<th style="text-align: left;">真源</th>
<th style="text-align: left;">主要读取方</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;"><code>SessionNarrative</code></td>
<td style="text-align: left;">用户要什么，已经发生了什么</td>
<td style="text-align: left;">Anchor、Ledger 与上下文投影</td>
<td style="text-align: left;">模型推理和回复合成</td>
</tr>
<tr>
<td style="text-align: left;"><code>SessionState</code></td>
<td style="text-align: left;">业务参数是什么，从哪里来</td>
<td style="text-align: left;">带 Provenance 的状态 Cell</td>
<td style="text-align: left;">工具调用和前置校验</td>
</tr>
<tr>
<td style="text-align: left;"><code>Workspace</code></td>
<td style="text-align: left;">哪个任务现在可以执行</td>
<td style="text-align: left;">DAG 与节点状态迁移</td>
<td style="text-align: left;">规划器、调度器和执行器</td>
</tr>
</tbody>
</table>

`Anchor` 保存原始目标，避免长任务反复摘要后偏离。`Ledger` 追加关键进展，`Collection` 在当前步骤选择必要记录。它们服务语义理解，不承担业务 ID 传递。

记忆再按使用距离分层：L1 服务当前步骤，L2 保存可追溯事实，L3 保存从多次任务中提炼的经验。L3 召回结果仍保留指向 L2 的来源 ID，需要核对时再加载原始记录。召回集中在首次推理、ReAct 首轮和任务规划等边界，不在每一步重复检索。

<figure>
<img alt="会话统一状态平面分为 Workspace、SessionNarrative 和 SessionState" src="../../assets/images/concepts/unified-session-state.png"/>
<figcaption>三个状态平面分别服务调度、模型理解和 API 交付。它们统一归档，不共用同一种真源。</figcaption>
</figure>

<!-- CASE-V06-REPLAY-liangbo-execution-agent-True:START -->

<section aria-labelledby="replay-liangbo" class="case-replay">
<h2 id="replay-liangbo">同一条薪资组配置任务重新跑一遍</h2>
<p>下面只追踪一条任务。每一步都写明状态归属和提交条件。</p>
<ol class="case-replay-list">
<li><span class="case-step-no">01</span><strong>建立作业</strong><p>Workspace 保存目标、租户、DAG 版本和当前节点。</p></li>
<li><span class="case-step-no">02</span><strong>匹配模板</strong><p>工具返回 <code>template_id</code>；SessionState 连同 producer、call_id 和 receipt_ref 一起保存。</p></li>
<li><span class="case-step-no">03</span><strong>保存快照</strong><p>现有薪资组配置形成可回查 snapshot，导入节点才进入 ready。</p></li>
<li><span class="case-step-no">04</span><strong>等待批准</strong><p>节点保持 blocked，审批事件与原作业关联，不新建第二条任务。</p></li>
<li><span class="case-step-no">05</span><strong>恢复导入</strong><p>执行器重新校验版本与参数来源，再把严格值注入工具。</p></li>
<li><span class="case-step-no">06</span><strong>业务回读</strong><p>读取实际薪资组配置并核对后置条件；不一致时进入恢复或人工接管。</p></li>
</ol>
<p class="case-outcome"><strong>提交条件</strong>接口回执、状态来源和业务回读同时成立，任务才写成 completed。</p>
</section>

<!-- CASE-V06-REPLAY-liangbo-execution-agent-True:END -->

<!-- CASE-V06-EVIDENCE-liangbo-execution-agent-True:START -->

<section aria-labelledby="evidence-liangbo" class="case-evidence-section">
<p class="case-evidence-label">机制图</p>
<h2 id="evidence-liangbo">执行型 Agent 的四个运行结构</h2>
<div class="case-evidence-grid">
<figure class="case-evidence"><img alt="任务 DAG 与节点状态机" loading="lazy" src="../../assets/images/concepts/task-dag-state-machine.png"/><figcaption><strong>任务 DAG 与状态机</strong>步骤依赖确定以后，执行器只调度 ready 节点。<span class="case-evidence-proof">ADPS 依据案例讲解重绘；说明调度机制，不代表生产类名。</span></figcaption></figure>
<figure class="case-evidence"><img alt="审批阻塞与原节点恢复" loading="lazy" src="../../assets/images/concepts/hitl-block-resume.png"/><figcaption><strong>审批阻塞与恢复</strong>审批事件回到原作业和原节点，避免“批准后重新开始”。<span class="case-evidence-proof">图支持状态语义；审批有效期和权限仍由部署方定义。</span></figcaption></figure>
<figure class="case-evidence"><img alt="Anchor Ledger Collection 长程叙事结构" loading="lazy" src="../../assets/images/concepts/anchor-ledger-collection.png"/><figcaption><strong>Anchor、Ledger、Collection</strong>目标、进展和当前投影分开保存，降低长程摘要漂移。<span class="case-evidence-proof">它服务模型上下文，不承担业务 ID 传递。</span></figcaption></figure>
<figure class="case-evidence"><img alt="统一活动事件与运行时间线" loading="lazy" src="../../assets/images/concepts/observability-glass-dome.png"/><figcaption><strong>Activity 与运行时间线</strong>模型、工具、状态变化和审批都进入同一条可追查时间线。<span class="case-evidence-proof">图说明事件组织方式；公开材料未给出总体运行指标。</span></figcaption></figure>
</div>
</section>

<!-- CASE-V06-EVIDENCE-liangbo-execution-agent-True:END -->

## 9. 当前证据能说明什么

<table>
<thead>
<tr>
<th style="text-align: left;">主张</th>
<th style="text-align: left;">当前依据</th>
<th style="text-align: left;">状态</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">首次配置是中小客户启用产品的重要阻力</td>
<td style="text-align: left;">客户访谈与交付反馈</td>
<td style="text-align: left;">案例方业务证据</td>
</tr>
<tr>
<td style="text-align: left;">把工具回执放回上下文仍会出现 ID 误写</td>
<td style="text-align: left;">早期原型测试</td>
<td style="text-align: left;">案例方复盘，未公开错误率</td>
</tr>
<tr>
<td style="text-align: left;">DAG 与状态机可以阻止未满足依赖的节点调度</td>
<td style="text-align: left;">调度规则与状态结构</td>
<td style="text-align: left;">架构机制说明</td>
</tr>
<tr>
<td style="text-align: left;">SessionState 保留参数来源并由程序注入</td>
<td style="text-align: left;">状态坐标和调用链设计</td>
<td style="text-align: left;">架构机制说明</td>
</tr>
</tbody>
</table>

后续公开材料最值得增加三类数据：严格流程的成功率与人工接管率，参数来源校验拦截的错误数，以及审批暂停后的恢复成功率。

## 10. 迁移时可以照着做的七步

1. 选择一条会修改真实业务状态的连续流程，不从开放问答开始。
2. 列出每一步的输入、输出、副作用、回滚方式和人工责任人。
3. 标记所有不能由模型重新生成的值，例如业务 ID、版本号、金额和权限范围。
4. 为每个严格值登记生产工具、消费工具、作用域和回执位置。
5. 把已知依赖写成任务图，由程序决定节点是否可执行。
6. 将高风险节点设为可持久化的等待状态，测试批准、拒绝、超时和重复事件。
7. 用统一时间线串起模型、工具、状态和任务事件，再开始扩大场景。

第一条流程跑稳后，再判断哪些任务需要 ReAct，哪些可以直接进入固定计划。这样能把探索能力留给开放部分，把确定性留给业务状态。

## 11. 何时不该照搬

这套设计适合步骤明确、状态依赖严格、错误会改变业务数据的执行型任务。工具需要由组织注册和管理，状态键与来源能够事先定义。

资料检索、总结和报告生成通常不需要完整 DAG、机械状态平面和审批恢复。一次性脚本也未必值得建设长期会话状态。若工具来自开放生态，或同一业务值存在多个并发写入者，还需要补充信任策略、事务、锁和冲突处理，本案例没有覆盖这些问题。

## 12. ADPS 对照

<table>
<thead>
<tr>
<th style="text-align: left;">模式</th>
<th style="text-align: left;">本案例中的实现</th>
<th style="text-align: left;">进一步阅读</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">工具调度</td>
<td style="text-align: left;">工具注册、状态生产消费声明、调用前注入</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/a1-tool-dispatch/cases/liangbo/">A1 工具调度</a></td>
</tr>
<tr>
<td style="text-align: left;">规划执行</td>
<td style="text-align: left;">DAG、节点状态机和验收器</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/a2-plan-and-execute/cases/liangbo/">A2 规划执行</a></td>
</tr>
<tr>
<td style="text-align: left;">进度追踪</td>
<td style="text-align: left;">Workspace 与持久化节点状态</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/m3-progress-tracking/cases/liangbo/">M3 进度追踪</a></td>
</tr>
<tr>
<td style="text-align: left;">上下文分诊</td>
<td style="text-align: left;">Anchor、Ledger 与当前 Collection</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/p1-context-triage/cases/liangbo/">P1 上下文分诊</a></td>
</tr>
<tr>
<td style="text-align: left;">审批门</td>
<td style="text-align: left;">高风险节点等待审批并从原处恢复</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/g1-approval-gate/cases/liangbo/">G1 审批门</a></td>
</tr>
<tr>
<td style="text-align: left;">可观测性</td>
<td style="text-align: left;">Activity、Frame 与统一事件时间线</td>
<td style="text-align: left;"><a href="https://adpsagent.com/zh/patterns/x1-observability/cases/liangbo/">X1 可观测性</a></td>
</tr>
</tbody>
</table>

## 案例提供与引用

**案例提供：**梁博（Bo Liang），上海东方屹腾科技有限公司。

**建议引用：**ADPS、梁博，《东方屹腾执行型 Agent：让业务状态沿流程准确传递》，ADPS 企业 Agent 系统蓝皮书·案例报告 01，v0.4，2026。

<div class="document-citation">
<p><a href="https://adpsagent.com/zh/cases/">案例报告目录</a> · <a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>证据边界：</strong>本文记录东方屹腾执行型 Agent 的项目实践。业务背景、原型问题和架构取舍由案例方梁博提供，尚未经过独立审计。示例数据结构由 ADPS 根据案例机制整理，用于解释设计，不代表案例方实际类名或字段名。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/cases/liangbo-execution-agent/">东方屹腾执行型 Agent 案例</a>；案例提供：梁博</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-19">2026-06-19</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#cases-liangbo-execution-agent">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
