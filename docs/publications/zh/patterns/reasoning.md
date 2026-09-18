<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>Reasoning
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书 · 模块总纲</p>
<h1>推理模块 · 把证据编译成可检查的判断</h1>
<p class="publication-deck">推理产物、深度路由、并行探索、假设验证、实时交互与工程验收。</p>
</header>

推理位于感知、记忆与行动之间。感知提供当前信号，记忆取回过去的事实与经验；推理据此形成判断，行动再决定怎样改变外部环境。

生产系统还要保存判断记录：证据引用、候选方案、不确定性、预算消耗、验证办法和下一步。后续模块据此复核、拒绝或执行这项判断。

<figure class="workshop-diagram"><img alt="推理请求经过复杂度路由后进入链式、并行、循环或分层路径，最后形成结构化判断" src="../../assets/images/workshops/reasoning-selection-zh.svg"/><figcaption>R2 选择推理资源与路径；R1、R3、R4、R5处理不同的判断结构。它们可以组合，不构成固定流水线。</figcaption></figure>

## 推理的输出边界

“建议批准”只是一句结论。可交给下游系统的推理产物需要说明这项结论依据什么、在哪些条件下成立、还缺什么，以及谁有资格执行后续动作。

<pre><code class="language-yaml">decision_id: dec_01K...
goal_ref: goal://incident/482
evidence_refs:
  - log://gateway/482#timeout
  - change://config/917
choice: rollback_recent_configuration
alternatives:
  - keep_observing
  - isolate_single_instance
uncertainty:
  level: medium
  unresolved: database latency has not been excluded
validation:
  before_action: reproduce on canary
  after_action: error rate returns to baseline
authority:
  required: on_call_approval
next_action: prepare_rollback_intent
</code></pre>

这份记录仍是判断，不是执行指令。行动模块需要重新检查权限、工具、参数、现实状态和验收条件。

## 模式职责

<table><thead><tr><th>模式</th><th>描述范围</th><th>关键产物</th></tr></thead><tbody>
<tr><td><a href="https://adpsagent.com/zh/patterns/r1-chain-of-thought/">R1 思维链</a></td><td>按顺序形成判断，并管理接口允许保留的摘要、依据和模型元数据</td><td>推理摘要、证据绑定、决策记录</td></tr>
<tr><td><a href="https://adpsagent.com/zh/patterns/r2-complexity-based-routing/">R2 复杂度路由</a></td><td>根据任务难度、风险、证据缺口和服务目标选择模型、推理深度与回退路径</td><td>RouteDecision、预算与降级规则</td></tr>
<tr><td><a href="https://adpsagent.com/zh/patterns/r3-parallel-exploration/">R3 并行探索</a></td><td>为同一问题启动相互隔离的候选路径，再按错误代价聚合</td><td>分支结果、分歧记录、聚合结论</td></tr>
<tr><td><a href="https://adpsagent.com/zh/patterns/r4-iterative-hypothesis-testing/">R4 迭代假设验证</a></td><td>用新证据更新假设，直到收敛、预算耗尽或转交人工</td><td>假设树、反证、退出原因</td></tr>
<tr><td><a href="https://adpsagent.com/zh/patterns/r5-talker-reasoner/">R5 双模架构</a></td><td>把低延迟交互与高成本分析放在不同职责中，通过结构化状态交接</td><td>任务包、共享状态、推理结果包</td></tr>
</tbody></table>

## 复杂度与风险分别判断

问题很难，不一定允许花更多权限解决；问题很短，也可能触发高风险动作。路由器应分别计算推理难度和业务风险，再确定模型档位、并行数量、时间预算和人工边界。

<table><thead><tr><th></th><th>低风险</th><th>高风险</th></tr></thead><tbody>
<tr><th>低难度</th><td>规则或轻量模型；结果可快速复验</td><td>计算可以简单，证据与审批仍需收紧</td></tr>
<tr><th>高难度</th><td>深度推理或并行探索；限制成本与时延</td><td>深度推理、独立验证、明确人审和停止条件</td></tr>
</tbody></table>

## 模式可以嵌套

一次生产故障诊断可以先由 R2 判断复杂度和风险。常见低风险问题进入 R1；证据冲突时启动 R3，让不同分支独立分析；根因仍不清楚时，R4 按“假设—取证—证伪”循环推进。用户等待期间，R5 的交互者说明进度，推理者在后台继续分析。

组合设计需要一个明确的收口位置。它负责等待必要分支、处理超时和冲突、检查退出条件，并把结果压成同一种决策结构。缺少收口规则时，增加分支只会增加答案数量。

## 预算、退出与升级

<table><thead><tr><th>控制项</th><th>需要回答的问题</th></tr></thead><tbody>
<tr><td>预算</td><td>允许多少 token、模型调用、并发、时延和外部检索？</td></tr>
<tr><td>证据</td><td>哪些结论必须绑定外部事实？证据是否仍在有效期内？</td></tr>
<tr><td>分歧</td><td>多数票、任一路告警和独立裁判分别适用于什么错误代价？</td></tr>
<tr><td>退出</td><td>证据充分、候选无法区分、预算耗尽和用户改题时怎样停止？</td></tr>
<tr><td>升级</td><td>移交人工时要携带哪些假设、证据、已排除路径和待决问题？</td></tr>
</tbody></table>

## 与相邻模块的接口

<table><thead><tr><th>模块</th><th>交给推理的内容</th><th>从推理接收的内容</th></tr></thead><tbody>
<tr><td>感知</td><td>当前信号、来源、时间与解析结果</td><td>补充观测或澄清请求</td></tr>
<tr><td>记忆</td><td>带版本和作用域的事实、经验与进度</td><td>可发布的决策摘要与适用边界</td></tr>
<tr><td>行动</td><td>工具结果、业务回执与最新状态</td><td>结构化判断，不直接继承执行权限</td></tr>
<tr><td>反思</td><td>评测结果、失败归因与延迟反馈</td><td>本轮决策记录和可复验条件</td></tr>
<tr><td>治理</td><td>权限、预算、禁区与人审要求</td><td>风险声明、待批准意图与证据</td></tr>
</tbody></table>

## 验证指标

- **判断质量：**在业务评测集上统计正确率、漏报、误报和校准误差。
- **路由质量：**比较实际路径与可接受的最低成本路径，记录误降级和不必要升档。
- **收敛质量：**统计假设被证伪的效率、超限退出、人工升级和重复取证。
- **运行代价：**同时报告质量、时延、token、并发和外部工具成本。
- **可复核性：**检查关键结论是否能够回到证据、版本、规则和责任主体。

## 公开模式

- [R1 · 思维链](https://adpsagent.com/zh/patterns/r1-chain-of-thought/)
- [R2 · 复杂度路由](https://adpsagent.com/zh/patterns/r2-complexity-based-routing/)
- [R3 · 并行探索](https://adpsagent.com/zh/patterns/r3-parallel-exploration/)
- [R4 · 迭代假设验证](https://adpsagent.com/zh/patterns/r4-iterative-hypothesis-testing/)
- [R5 · 双模架构（扩展）](https://adpsagent.com/zh/patterns/r5-talker-reasoner/)

<section aria-labelledby="reasoning-workshop-link" class="related-case-band">
<p class="related-case-label">研讨来源</p>
<h2 id="reasoning-workshop-link"><a href="https://adpsagent.com/zh/workshops/reasoning-2026-08-26/">推理模块第一次研讨会</a></h2>
<p>参会名单、公开讨论范围与模式阅读路径。</p>
</section>

<div class="document-citation"><p><strong>建议引用：</strong>ADPS，《推理模块：把证据编译成可检查的判断》，Agent 设计模式白皮书，2026。</p><p><a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p><p class="publication-disclaimer"><strong>范围：</strong>本页定义模块边界与工程检查项，不认证具体模型、产品或企业实现。场景用于说明模式组合；具名案例以蓝皮书页面的证据说明为准。</p></div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd><a href="https://adpsagent.com/zh/workshops/reasoning-2026-08-26/">推理模块第一次研讨会</a>（2026-08-26）；ADPS 推理模式公开规范</dd></div>
<div><dt>来源日期</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-26">2026-08-26</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-reasoning">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
