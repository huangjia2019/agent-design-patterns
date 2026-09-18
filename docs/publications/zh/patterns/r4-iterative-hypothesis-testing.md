<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>R4
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>R4 · Iterative Hypothesis Testing · 迭代假设验证</h1>
<p class="publication-deck">生成假设、收集反证、更新假设树，直到证据收敛或达到迭代上限。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">推理 Reasoning × 循环 Loop（转）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">高（多轮迭代累计成本，需用熔断和预算上限约束）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">推理模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">生成假设、收集反证、更新假设树，直到证据收敛或达到迭代上限。</td>
</tr>
</tbody>
</table>

---

## 问题

根因诊断等任务需要逐步收集证据，首轮假设的先验排序可能与实际原因不一致。单次推理会过早提交结论，简单 retry 又不会更新假设，因此都难以利用新增证据。

迭代假设验证重复执行“假设 → 验证 → 修正”。每轮都根据证据更新假设树，并优先寻找反证。retry 通常重复同一动作，迭代假设验证则修改下一轮的认知状态。并行探索（R3）同时运行多条候选路径，本模式在时间维度连续更新同一棵假设树。

## 坐标说明：推理 × 循环

- **纵轴 · 推理**：它走的是"假设 → 验证 → 修正 → 假设"的经验科学风格推理，不是单次 deduce。每一轮都在主动修正自己的 belief，而不是等结果稳定。
- **横轴 · 循环**：多轮迭代直到证据收敛或达到上限，是天然的循环结构。同列的双模架构（R5）也在循环列，但侧重不同——迭代是单 Agent 跟自己循环验证假设，双模是双 Agent 协同分处理"说"和"想"。

## 解决方案与机制

成熟的迭代假设验证常用三 Agent 分工，对应一个严格的循环：

1. **假设生成（Planner）**：根据症状和历史 case 列出候选假设，按先验概率排序。模型和 effort 档位应由假设覆盖率、漏因率与调用成本的本地评测决定。
2. **证据收集（Generator）**：给定一个假设，决定调用哪些工具验证它，例如查询 metric、检索 log 或读取 sensor。证据必须来自可追溯、可复现的数据源，不能用“模型认为如此”代替外部证据。
3. **判定（Evaluator）**：综合证据判断假设是被确认、被证伪，还是证据不足。Evaluator 应显式寻找反证，并在回放集上比较不同提示和模型配置，不能预设某种 framing 一定提高准确率。

循环规则为：证伪后返回生成阶段，确认后退出，证据不足时继续收集。出现改变问题边界的新证据时，应重建假设树；达到迭代上限仍未收敛时，触发 HITL 并提交完整证据。

## 适用场景

- **诊断类任务**：工业故障定位、医疗诊断、安全事故根因分析。根因不明、需要逐步收集证据、单链走偏后能 reset 重启。
- **复杂代码 debug**：每次修改后执行验证，使用失败信息更新假设，逐步定位缺陷。
- **需要严格证据链的判断**：每一步结论都要有可复现证据支撑、最终能向监管解释推理路径的场景。

## 已知失效方式

- **时间预算太紧还硬上**：延迟预算无法容纳证据收集和验证，或错误成本很低时，迭代可能是过度工程。
- **达到上限后继续迭代**：达到配置上限仍未收敛，可能是症状描述不准确、证据不可得或问题边界错误，应 reset 或转人工处理。
- **Evaluator 只找支持证据**：这种提示会放大确认偏误。Evaluator 应同时记录支持证据、反证和缺失证据，并优先设计能够区分候选假设的测试。
- **新证据来了还在旧树上微调**：出现完全新的证据时应该 reset 假设树重新生成，在旧树上打补丁会被错误的先验带偏。
- **没有熔断**：任何迭代都要有 max\_iterations 硬上限加成本上限，否则成本爆炸、Agent 卡死。

## 验证指标

- **收敛率 Convergence Rate**：在预算和迭代上限内形成可验证结论的比例。未收敛样本应区分任务过大、证据不可得和假设生成质量问题。
- **平均收敛迭代数**：按任务类型观察成功 case 的迭代分布。持续增长说明单轮信息增益不足或假设质量下降。
- **证伪率 Falsification Rate**：记录候选假设被反证淘汰的情况。长期没有假设被证伪，可能意味着 Evaluator 只在寻找支持材料。
- **人工介入率 HITL Trigger Rate**：结合任务风险、证据缺口和最终结果分析。比例本身没有通用健康区，关键是该升级的 case 是否升级。

## 最小实现

```
任务进来 → Planner 生成假设清单（按先验概率排序）
循环（上限 max_iterations）：
    选先验最高的待验假设
    Generator 收证据（deterministic 数据源）
    Evaluator 判定（强调证伪而非确认）：
        confirmed   → 收敛，退出
        falsified   → 剪掉，继续下一个假设
        若假设全被证伪 → 拿新证据回 Planner 重新生成
    遇到全新证据 → reset 整个假设树
循环结束仍未收敛 → 触发 HITL，附完整假设树 + 证据 + 已跑迭代
全程 trace 留档（合规场景需长期保留）
```

生产实现可按角色路由模型：高能力模型生成假设，低成本模型收集证据，中档模型判定；证据使用严格 schema；HITL 升级携带完整假设树和证据；trace 长期留档。

## 场景化示例

设想一个工厂设备告警。Agent 首轮围绕常见机械故障建立假设，但现场工程师随后补充“远程配置刚发生变化”这一新事实。系统不把它硬塞进旧树，而是触发 reset，重建候选假设并追查被修改的参数。生成假设、收集证据和判定使用独立 schema；Evaluator 优先寻找反证；证据不足时升级人工；重启关键设备始终需要人工确认。实际收敛情况应由事故回放和现场复盘验证。

## 相邻模式

- **并行探索（R3）**：对偶关系。并行是空间维度同时开 N 条线一次选优，迭代是时间维度一条线跑多次逐步收敛。
- **思维链（R1）**：迭代的每一轮内部就是一条思维链，迭代把多条思维链在时间维度串起来反复修正。
- **复杂度路由（R2）**：迭代里三个角色用不同档位模型，正是路由思路在循环内部的应用。
- **双模架构（R5）**：同在循环列。迭代是单 Agent 自我循环验证，双模是双 Agent 协同分工。

## 工程判断

迭代假设验证要求每轮用新观测更新候选假设，并记录排除依据。退出条件应同时覆盖证据充分、剩余假设无法区分、预算耗尽和需要人工升级等情况。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《R4 迭代假设验证》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-r4-iterative-hypothesis-testing">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
