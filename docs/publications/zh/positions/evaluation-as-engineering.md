<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/positions/" style="color: var(--color-text-muted);">立场</a>
</p>

# Eval 的工程化：从设计约束到生产证据

> ADPS 立场专文  
> 发布：2026-05-30  
> 署名：ADPS 共同体（Agent Design Patterns Society）

## 定义范围

Agent 系统同时包含确定性软件和概率性行为。数据结构、权限、工具契约、幂等性和业务账本继续使用传统测试；模型输出、执行路径和多次运行之间的差异由 Eval 测量。

四类验证活动各自提供不同证据：

<table>
<thead>
<tr>
<th style="text-align: left;">活动</th>
<th style="text-align: left;">关注对象</th>
<th style="text-align: left;">典型结果</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">Test</td>
<td style="text-align: left;">确定性组件、合同和状态变化</td>
<td style="text-align: left;">pass / fail 与错误位置</td>
</tr>
<tr>
<td style="text-align: left;">Eval</td>
<td style="text-align: left;">样本集上的能力、行为和失败分布</td>
<td style="text-align: left;">分数、分类、样本级证据</td>
</tr>
<tr>
<td style="text-align: left;">Monitoring</td>
<td style="text-align: left;">生产流量、成本、延迟和漂移</td>
<td style="text-align: left;">时间序列、告警和异常轨迹</td>
</tr>
<tr>
<td style="text-align: left;">Acceptance</td>
<td style="text-align: left;">业务结果与发布责任</td>
<td style="text-align: left;">通过、拒绝、限量发布或回滚</td>
</tr>
</tbody>
</table>

一个确定性 grader 可以同时出现在 Test 和 Eval 中。工程上需要记录证据来源、维护者和它支持的决策。

## Eval 进入设计

设计阶段先定义任务、环境、权限、成功条件和不可接受结果。延迟、成本和质量目标会影响模型、工具、拓扑、缓存和人工介入方式。

缺少这组约束时，团队只能在系统完成后评价“效果好不好”，很难解释某项架构选择服务于什么目标。

## Eval Contract

<pre><code class="language-yaml">eval_id: payroll-action-v5
system_under_test:
  agent_version: payroll-agent-2.3
  components:
    - planner
    - tool_dispatcher
    - action_guard
task_set:
  dataset: payroll-action-boundaries-v4
environment:
  database: disposable_snapshot
  tools: sandbox_registry_v3
permissions:
  max_risk_class: medium
outcomes:
  required:
    - correct_business_ids
    - no_skipped_dependencies
    - ledger_matches_receipts
  forbidden:
    - production_write
    - duplicate_submission
graders:
  - deterministic_ledger_check
  - dependency_order_check
  - rubric_review
trials: 3
release_gate:
  p0_failures: 0
  regression: no_material_drop
owner: payroll-platform
evidence: artifacts/evals/payroll-action-v5/
</code></pre>

合同把被测系统、任务分布、环境、权限、评分器和发布门放在一起。随机性较强的任务保留多次运行和每次轨迹，避免平均分掩盖稀有的严重失败。

## 三个阶段

### 设计阶段

用小型代表性任务集检查架构约束。此时关注：

- 任务能否被观测和验收；
- 工具与权限边界是否可实现；
- 选定拓扑能否满足延迟和成本目标；
- 哪些结果必须由人工或业务系统确认。

### 开发与上线前

确定性测试随每次提交运行。能力 Eval、回归 Eval、权限测试和沙箱验收按风险分层。新能力与现行版本在同一任务集上比较，发布门读取样本级失败和完整轨迹。

能力集用于判断新增功能是否成立；回归集用于保护已有行为。两套样本可以共享基础设施，维护目的和发布规则应分别记录。

### 生产阶段

生产请求产生真实分布和延迟结果。系统对流量分层抽样，关联输入、组件版本、轨迹、业务回执和人工处置。发现新失败后，完成脱敏、归因和复现，再进入回归集。

监控发现变化，Eval 判断变化是否影响能力，Acceptance 决定是否发布、限流或回滚。

## 证据优先级

1. **外部事实和业务回执**：数据库状态、交易回执、编译结果、执行产物。
2. **确定性规则**：schema、引用完整性、状态机和业务不变量。
3. **独立测试环境**：沙箱、副本和可重复任务。
4. **专家与人工标注**：处理领域判断、主观质量和高风险边界。
5. **模型评分器**：扩展覆盖面，输出需校准并接受抽样复核。

模型评分器适合处理开放输出，不能覆盖工具副作用、权限越界和业务事实。生成模型与评分模型的差异只能增加视角，无法单独保证独立性。

## 评测集生命周期

<pre><code class="language-text">规格与业务验收条件
        ↓
初始能力集
        ↓
开发运行与样本级分析
        ↓
生产失败、人工复核和新边界
        ↓
脱敏、去重、归因和复现
        ↓
回归集与版本发布记录
        ↓
定期淘汰失效样本并保留历史基线
</code></pre>

每条样本需要来源、适用版本、期望结果、评分器和修改记录。Agent 与 grader 同时变化时，旧基线必须保留，否则新旧分数无法比较。

## 发布门

发布门组合多层证据，不使用一个综合分数代替全部判断。常见规则包括：

- P0 失败为零；
- 关键回归项全部通过；
- 权限、隔离和副作用测试通过；
- 质量、延迟与成本没有超出约定边界；
- 高风险样本完成人工验收；
- 证据和回滚版本已归档。

规则应与任务风险对应。低风险内容生成允许概率性阈值；资金、生产数据和外部发布需要更强的确定性证据。

## 常见失效

<table>
<thead>
<tr>
<th style="text-align: left;">失效</th>
<th style="text-align: left;">影响</th>
<th style="text-align: left;">修正</th>
</tr>
</thead>
<tbody>
<tr>
<td style="text-align: left;">只跑公共 benchmark</td>
<td style="text-align: left;">无法代表业务流量</td>
<td style="text-align: left;">建立领域任务集和生产抽样</td>
</tr>
<tr>
<td style="text-align: left;">系统完成后才建 Eval</td>
<td style="text-align: left;">架构缺少设计约束</td>
<td style="text-align: left;">在任务和权限定义阶段建立合同</td>
</tr>
<tr>
<td style="text-align: left;">只看综合分数</td>
<td style="text-align: left;">严重少数失败被平均</td>
<td style="text-align: left;">保留样本、轨迹和失败分类</td>
</tr>
<tr>
<td style="text-align: left;">Agent 与 grader 同时修改</td>
<td style="text-align: left;">新旧结果不可比较</td>
<td style="text-align: left;">独立版本、冻结基线和回放</td>
</tr>
<tr>
<td style="text-align: left;">生产监控没有组件版本</td>
<td style="text-align: left;">漂移无法归因</td>
<td style="text-align: left;">事件关联模型、Prompt、Skill 和工具版本</td>
</tr>
<tr>
<td style="text-align: left;">Eval 通过即可扩大权限</td>
<td style="text-align: left;">能力证据与治理脱节</td>
<td style="text-align: left;">另设审批、隔离和恢复门槛</td>
</tr>
</tbody>
</table>

## 与 ADPS 的关系

Eval 为模式选型和演进提供证据。Perception 检查输入覆盖和漏报，Memory 检查写入、召回与过期，Reasoning 检查路径和结论，Action 检查工具副作用，Reflection 检查修改是否改善结果，Collaboration 检查交接和隔离，Governance 检查权限与影响范围。

模式目录说明系统可以怎样设计；Eval 记录某个实现是否在指定环境中达到目标。

---

ADPS · Agent Design Patterns Society · adpsagent.com

---

<p style="font-size: 0.92rem; color: var(--color-text-muted);">
<a href="https://adpsagent.com/zh/positions/">← 返回全部立场</a>
</p>

<!-- PAGE-CHRONICLE:START -->

<section aria-labelledby="page-chronicle-title" class="page-chronicle">
<h2 id="page-chronicle-title">溯源记录</h2>
<dl>
<div><dt>来源记录</dt><dd>ADPS 技术立场；论据与参考资料见正文</dd></div>
<div><dt>本页首次公开</dt><dd><time datetime="2026-06-07">2026-06-07</time></dd></div>
</dl>
<p><a href="https://adpsagent.com/zh/chronicle/#positions-evaluation-as-engineering">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
