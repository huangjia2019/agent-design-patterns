<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;"><a href="https://adpsagent.com/zh/patterns/">模式目录</a><span style="margin: 0 0.45rem;">/</span>横切工程面<span style="margin: 0 0.45rem;">/</span>X2</p>

<header class="publication-head">
<p class="publication-series">ADPS 横切工程面规范</p>
<h1>X2 · Evaluation &amp; Validation · 评测与验证</h1>
<p class="publication-deck">以可重复样本、评分器、回归和外部验收管理 Agent 能力证据。</p>
</header>

**样本、评分器、回归和验收**共同构成 X2 的能力证据。样本界定任务与边界，评分器把标准变成可重复判断，回归保护已经建立的能力，外部验收核对真实系统中的结果。

X2 管理 Agent 能力的验证证据。它把确定性测试、行为评测、外部验收和生产反馈接到同一发布与复验流程。

## 范围

被测对象可以是模型、提示词、工具、Skill、路由、工作流、治理策略或完整 Agent 系统。对象不同，样本、环境、评分器和发布门也随之变化。

<table><thead><tr><th>证据</th><th>适用判断</th></tr></thead><tbody>
<tr><td>外部事实与业务回执</td><td>现实状态是否达到目标</td></tr>
<tr><td>schema、规则、状态机与幂等断言</td><td>确定性合同是否成立</td></tr>
<tr><td>轨迹、沙箱与故障注入</td><td>执行路径、恢复和权限边界是否可靠</td></tr>
<tr><td>校准后的模型评分器</td><td>难以写成硬规则的语义质量</td></tr>
<tr><td>专家或用户复核</td><td>含糊标准与高风险发布裁决</td></tr>
</tbody></table>

## Eval Contract

<pre><code class="language-yaml">eval_id: payroll-change-regression-v3
system_under_test: payroll-agent@v8
task: change_one_allowance
environment: payroll-sandbox@2026.08
allowed_authority: no_production_write
required_outcomes: [receipt_matches_after_read]
forbidden_outcomes: [modify_unrelated_employee]
graders: [schema_contract, ledger_probe]
trials: 5
release_gate: all_required_cases_pass
evidence: artifacts/evals/payroll-v3/</code></pre>

## 生命周期

设计阶段定义能力样本与负例；发布前同时运行能力集和回归集；灰度阶段比较影子流量与现行版本；运行故障进入可重放样本；模型、工具、策略或数据变化后重新认证。G3 的授权升降级使用 X2 的结果，不能只看一次演示。

## 与 X1、X3 的边界

X1 记录发生了什么，X2 按合同判断结果是否合格，X3 限制评测器和候选系统各自能够访问或改写什么。Agent 与 grader 同时修改，或由候选系统自由改写发布门，会破坏结论的独立性。

## 常见失效

- 只测最终文本，不检查外部状态；
- 只运行一次，将随机成功当成稳定能力；
- 只有正例，没有拒绝、越权、恢复和未知输入；
- 用一条 golden trajectory 排除其他正确路径；
- 只公布综合分数，不保留样本级失败和轨迹；
- grader 未经人工校准，分数变化无法解释。

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《X2 · Evaluation &amp; Validation · 评测与验证》，ADPS 横切工程面规范 v0.5，2026-08-20。</p>
<p><a href="https://adpsagent.com/zh/topics/agent-evals-and-testing/">Agent 评测与验证专题</a> · <a href="https://adpsagent.com/zh/workshops/reflection-2026-08-12/">反思研讨会</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>使用边界：</strong>本页定义工程范围与接口，不构成产品认证。具名实践以案例页与公开代码为准。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-08-20">2026-08-20</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-x2-evals-and-testing">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
