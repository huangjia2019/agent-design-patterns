<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>F4
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>F4 · Self-Heal Loop · 自愈循环</h1>
<p class="publication-deck">deterministic 失败信号触发后，自动执行诊断、修复和验证，直到通过或熔断。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">反思 Reflection × 循环 Loop（转）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中高（诊断、隔离修复、完整验证、回滚与人工接管）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">反思模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">deterministic 失败信号触发后，自动执行诊断、修复和验证，直到通过或熔断。</td>
</tr>
</tbody>
</table>

---

## 问题

测试失败、lint 报错、build 挂掉、CI 红了，这些 deterministic 失败信号判据清楚，适合触发自动修复。依赖缺失、配置错位和局部逻辑错误也常有稳定的排查路径。工程师仍要负责修复范围、发布权限和人工接管，重复的诊断与验证步骤可以交给 Agent 执行。

Self-Heal Loop 让 Agent 消化这些信号并闭环修复：失败信号触发 → 诊断根因 → 生成修复 → 应用 → 重新验证。修复未通过时，系统必须在受控范围内继续尝试或转人工。Coding Agent 和内部修复系统提供了实现参考，其生产效果仍应从一手材料和本地评测中验证。

## 坐标说明：反思 × 循环

- **纵轴 · 反思**：Agent 读取失败信号，诊断自身产出并尝试修复，适用于具有明确正确性判据的软件任务。
- **横轴 · 循环**：检测失败 → 诊断 → 修复 → 再测试构成 mandatory loop。终止条件为测试通过、达到 max\_iterations 或检测到 regression 后 rollback。

## 解决方案与机制

一个 production-grade Self-Heal Loop 由六段流水线加三重停止机制构成。流水线：Test Fail → Diagnose → Generate Fix → Critic → Atomic Apply → Verify，验证失败时回滚本轮变更，再决定重试或转人工。

修复前先做两次判断：**这是什么失败，Agent 有权改什么。** 研讨会把生产故障归为四类：

<table>
<thead>
<tr>
<th style="text-align: left;">失败类别</th>
<th style="text-align: left;">常见信号</th>
<th style="text-align: left;">默认处理</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">运行时失败</td>
<td style="text-align: left;">超时、依赖异常、资源不足</td>
<td style="text-align: left;">可在受控范围重试、切换或降级</td>
</tr>
<tr>
<td style="text-align: left;">过程失败</td>
<td style="text-align: left;">工具顺序错误、参数错误、步骤遗漏</td>
<td style="text-align: left;">可修订当前计划或调用参数</td>
</tr>
<tr>
<td style="text-align: left;">业务失败</td>
<td style="text-align: left;">规则冲突、关键知识缺失、审批条件不满足</td>
<td style="text-align: left;">补证据或转业务负责人，不能靠模型猜规则</td>
</tr>
<tr>
<td style="text-align: left;">体验失败</td>
<td style="text-align: left;">结果正确但等待过长、解释不足、交互中断</td>
<td style="text-align: left;">进入产品与流程改进，不宜自动改生产策略</td>
</tr>
</tbody>
</table>

每类失败都要绑定 `change_scope` 和 `release_authority`。修改临时文件、重跑沙箱任务与修改生产规则不是同一级权限。诊断完成后若所需改动超出授权范围，循环应立即转人工，不能用多试几轮来绕过权限边界。

三重停止机制是把 Generator-Critic 升级成 Self-Heal 的关键，缺一就有"把 main branch 改坏"的风险：

1. **max\_iterations 硬熔断**：按任务风险和本地评测限制修复次数，防止连续修复产生新的失败。
2. **独立 critic verifier**：使用独立配置的 reviewer 检查修复。跨 model family 可以减少部分共同盲区，但独立性还取决于 prompt、证据和 trace 是否分开。
3. **stability check via signature**：用 failure signature 区分修复进展和问题漂移，并按业务定义 severity、影响范围、性能、安全和覆盖率回归。

Spotify Honk 按 format、lint、build、test 顺序执行四级 cascade，先运行低成本检查，再进入语义和测试级检查。

## 在线修复与离线发布

在线循环适合低风险、可回滚、能立即验证的改动，例如在沙箱中修正参数、重新生成临时产物或提交待审 PR。会改变共享规则、Skill、prompt、模型路由和生产配置的修复进入离线流程：汇总同类失败，完成回放、影响分析和审批，再按版本发布。这样可以避免一次偶发故障把局部补丁直接写成全局规则。

## 适用场景

- **代码 / 测试 / CI 这类对错明确的领域**：CI 失败自动修、lint 自动修、测试失败自动诊断修复，这是 Self-Heal 的主战场，因为有 deterministic ground truth。
- **Coding agent 标配能力**：Aider、Spotify Honk、GitHub Copilot 都把它当默认 feature，是 coding agent 的基础设施。
- **有清晰分层 ground truth 信号的工程流水线**：format/lint/build/test 分层清楚的 CI 才适合上 self-heal，信号越分明、修复越可靠。

## 已知失效方式

- **没有 deterministic 失败信号还硬用**：写作、设计这种主观判断没有客观对错信号，走 Generator-Critic（F1）而非 Self-Heal。修复代价大于失败代价的任务（生产数据库改 schema）走治理模块的 Approval Gate 加人审。
- **失败签名持续变化**：没有 stability check 时，Agent 可能修复一个错误并引入另一个错误。应同时使用 failure signature 比对、regression detection 和 max\_iterations。
- **回归级联**：每轮 fix 不是 atomic commit，一连串 cascade 后 rollback 还原不到正确状态。防法是 per-iteration atomic commit 加 "modify only files in diagnosis" 严格约束。
- **虚假恢复**：agent 改的是 test 而不是 code，把测试改弱让它过——指标全绿、问题全在。防法是 critic 显式审"改的是 production code 还是 test"加 test coverage 不许下降。
- **缺知识却继续自修**：业务规则、领域知识或目标定义缺失时，模型无法从失败信号中恢复事实。继续循环只会扩大猜测，应请求证据或转交领域负责人。
- **诊断错误**：failure signature 相似不代表根因相同。修复前要保留原始证据、诊断置信度和替代假设，高风险场景由独立评审确认。
- **越权写入长期资产**：一次线上修复直接改写共享 Skill、prompt 或生产配置。长期变更需要离线评测、审批、版本发布和回滚路径。
- **触底不转人工**："修不好就崩溃"是不可接受的工程做法。HITL handoff 必须是一等公民，触底转人审，并按任务风险和业务 SLA 明确队列责任人与处理时限。

## 验证指标

- **自愈成功率**：自动修复通过全部验收的比例。应按 failure signature 和风险等级拆分，不能用总体均值掩盖高风险失败。
- **平均修复轮数**：观察收敛分布和触顶比例。长尾增长时检查 ground truth、诊断质量和停止条件。
- **regression 率**：修复引入新失败的比例。上升时检查 stability check、测试覆盖和 atomic commit。
- **HITL 队列处理时延**：触底转人工后多久被接手。SLA 由业务风险和人员安排确定，并与自动化熔断策略联动。
- **误诊率**：抽样核对诊断根因与最终处置，区分“修复未通过”和“起点就判断错了”。
- **越权阻断与交接完整度**：统计超出 `change_scope` 后是否及时停止，以及交接包是否包含失败证据、尝试记录、diff 和回滚状态。

## 最小实现

```
for i in range(MAX_ITERATIONS):           # 按任务风险和评测配置
    diagnosis = diagnose(current_failure)
    if diagnosis.required_scope > change_authority:
        return handoff("insufficient_authority", evidence, diagnosis)
    fix = generate_fix(diagnosis)         # 只改 diagnosis 里的文件
    critique = cross_family_critic(fix)   # 不同 vendor, 打破 self-bias
    if critique.block:
        return "blocked_by_critic"        # 转 HITL
    commit = atomic_apply(fix)            # per-iteration atomic commit
    new_failure = verify()                # format/lint/build/test 四级 cascade
    if new_failure is None:
        return "fixed"
    if is_regression(current_failure, new_failure):   # 业务定义的回归规则
        rollback(all applied commits)
        return "rolled_back_regression"
    current_failure = new_failure
return "max_iterations_human_handoff"     # 触底转人审
```

生产实现的 Critic 要和修复者保持足够独立；regression detection 按业务加入性能、安全和覆盖率规则；每轮使用 atomic commit；达到上限后进入由人员实际处理的 HITL 队列。涉及共享资产和生产配置的变化不在在线循环中直接发布。

## 场景化示例

设想一家 DevTool 公司构建 CI/CD 自动修复 Agent。第一版对所有失败持续尝试修复，却没有 Critic、rollback 和 stability check。一次失败链中，Agent 反复改动并触及无关代码，提交又无法按轮精确回滚。后续版本加入 max\_iterations 熔断、独立 Critic 和 failure-signature stability check；验证按 format、lint、build、test 分层执行；每轮使用 atomic commit；达到上限后生成 PR 并进入 HITL。自愈是否有效，要看通过完整验收的修复、regression 和人工接管质量，不能只统计“Agent 做过修改”。

## 相邻模式

- **Generator-Critic（F1）**：Generator-Critic 从可用输出开始做可选质量改进；Self-Heal Loop 从确定性失败开始执行 mandatory loop。两者的 stop condition、rollback 和 blast radius 不同。
- **Adversarial Review（协作模块）**：cross-family critic 衔接。Rubber Duck 的 dual-model review 是这个思路的轻量版，Adversarial Review 把它推到极端（multi-agent debate）。
- **Iterative Hypothesis（推理模块）**：Loop 同源思路，都是"试—验—再试"的迭代结构。
- **Guardrail Sandwich（行动模块）**：sandbox 同源。Honk 把 agent 放隔离 container 加限权运行，把 blast radius 从"production 全开"压到"sandbox 内全开"。

## 工程判断

Self-Heal Loop 适用于存在确定性失败信号、可验证修复和可用回滚的任务。缺少这些条件，或错误影响不可逆时，循环必须转入人工处理。

## 延伸阅读

- [反思模块总纲：从运行反馈到受控修改](https://adpsagent.com/zh/patterns/reflection/)
- [反思模块第一次研讨会（2026-08-12）](https://adpsagent.com/zh/workshops/reflection-2026-08-12/)
- [Anthropic：Agent 评测中的 grader 与 trace](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

<!-- ADPS-BLUEBOOK-SLOT -->

<!-- RELATED-CASE-DEEPAGENTS:START -->

<section aria-labelledby="related-deepagents-case" class="related-case-band">
<p class="related-case-label">相关开源框架案例</p>
<h2 id="related-deepagents-case"><a href="https://adpsagent.com/zh/cases/deepagents-dynamic-orchestration/">Deep Agents：从固定图到代码生成的动态协作</a></h2>
<p>张海立在协作研讨会中的框架研究，经公开文档与源码复核，连接层级委派、扇出聚合、子代理隔离、独立复核以及评测与可观测性。</p>
</section>

<!-- RELATED-CASE-DEEPAGENTS:END -->

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《F4 自愈循环》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
<p><a href="https://adpsagent.com/zh/patterns/">模式目录</a> · <a href="https://github.com/huangjia2019/agent-design-patterns" rel="noopener" target="_blank">参考实现</a> · <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener" target="_blank">CC BY 4.0</a></p>
<p class="publication-disclaimer"><strong>文档状态：</strong>本页为公开评审稿。模式定义与分类可供讨论和引用；场景化示例用于说明机制，不代表已经核验的企业案例。具名实践另见<a href="https://adpsagent.com/zh/cases/">案例库</a>。ADPS 欢迎业界提交带来源、测量口径和发布授权的案例。</p>
</div>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 模式白皮书；先行工作与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-f4-self-heal-loop">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
