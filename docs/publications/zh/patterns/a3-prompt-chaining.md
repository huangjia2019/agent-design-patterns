<p style="font-size: 0.9rem; color: var(--color-text-faint); margin-bottom: 1.75rem;">
<a href="https://adpsagent.com/zh/patterns/" style="color: var(--color-text-muted);">模式矩阵</a>
<span style="margin: 0 0.45rem;">/</span>模式白皮书<span style="margin: 0 0.45rem;">/</span>A3
            </p>

<header class="publication-head">
<p class="publication-series">ADPS Agent 设计模式白皮书</p>
<h1>A3 · Prompt Chaining · 提示链</h1>
<p class="publication-deck">将复杂任务拆成线性步骤，每步使用独立 prompt 和验收闸门，前一步输出作为下一步输入。</p>
</header>

<table>
<tbody>
<tr>
<td style="text-align: left;"><strong>坐标</strong></td>
<td style="text-align: left;">行动 Action × 链式 Chain（传）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>成本</strong></td>
<td style="text-align: left;">中（拆成 N 段、N 次调用，但每段可用更便宜的模型摊薄）</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式组</strong></td>
<td style="text-align: left;">行动模式</td>
</tr>
<tr>
<td style="text-align: left;"><strong>模式简介</strong></td>
<td style="text-align: left;">将复杂任务拆成线性步骤，每步使用独立 prompt 和验收闸门，前一步输出作为下一步输入。</td>
</tr>
</tbody>
</table>

---

## 问题

单个 prompt 同时承担多个目标时，不同约束会竞争模型注意力。设想一个内容编辑 Agent 把校对、改写、风格统一、数字核查、标题、摘要和配图建议放在同一段提示中。改写步骤可能改变原稿数字，后续步骤又沿用这个错误。

Prompt Chaining 把大任务拆成几段独立的 prompt 串行处理，每段只干一件事、有自己的角色和最合适的模型、有自己的成功标准。它和单个超大 prompt 的区别，就是复杂度只能靠拆分降下来，塞进一个更大的盒子是降不下来的。

## 坐标说明：行动 × 链式

- **纵轴 · 行动**：一个 prompt 完不成的任务被拆成几段串行的 prompt，每一段都要触发一次模型调用或工具输出，落点是"做事"而不是单点"想事"，所以属于行动模块。
- **横轴 · 链式**：prompt1 → prompt2 → prompt3 是典型的线性 pipeline，前段输出即后段输入，既不是路由分流也不是图状依赖。它和规划-执行（A2）同属链式，区别在 A3 是纯直线、无 replan，A2 是 DAG、有 replan。

## 解决方案与机制

它的工程原型是 Unix 管道。`cat data.csv | grep ERROR | sort | uniq -c` 把几个单一职责的小程序靠 stdin/stdout 串起来，每个程序只读输入、写输出，不需要知道前后是谁。Prompt chain 是同一件事在 LLM 这一层的复刻，每一段 prompt 就是一个"小程序"。

提示链在步骤之间增加程序化闸门。闸门可以使用 Python 条件判断，不通过时重试或升级。例如，研究阶段可按主题覆盖、来源类型和可追溯性校验参考资料，未满足项目约定时不进入下一步。

几个落地要点：

- **每段 prompt 使用显式契约**：写清 role、task、context、format 和 constraints，并使用稳定边界分隔。是否降低解析失败，应在整链回放中测量。
- **每段独立选模型**：校对、创意改写和数字核查可以使用不同模型与工具。选型依据是该步骤的评测结果和可验证性，整链成本由真实流量回放计算。
- **闸门要带容差**：不要要求“字数必须恰好等于某值”，应使用业务可接受的范围，并把必要内容单独写成条件。
- **重试携带失败原因**：将上一次未通过的字段和规则反馈给模型，避免无条件重复调用。

Claude Code 把 chain 做出了三种工业形态：感知-推理-行动主循环里每个工具结果就是一节链节（隐式链）；slash command 是预制链（`/commit` 是 status → diff → 推理 → 起草 → 提交的五步模板）；SKILL.md 是可组合的链段（声明式定义多步流程，被嵌进更大的链里）。

## 适用场景

- **工作流有清晰阶段、阶段间能用短小代码描述“什么算合格”**：内容编辑、合同审阅和客服工单分诊都适用。步骤数量由职责边界和回放结果决定。
- **要把工作流产品化成可复用入口**：slash command 就是把领域专属工作流封装成预制链，用户一条命令触发整链，不用每次手写步骤。
- **需要可追溯的产出**：整链 trace 让业务方从终稿回看每一步输入、输出、闸门结果和人工修改。

## 已知失效方式

- **信息饥饿**：后续步骤所需信息可能在中间传递时丢失。chain 不会自动让早期信息流到末端，应另带一个所有步骤都能读取的累积上下文对象（类似 saga context）。
- **闸门条件过严**：精确字数等脆弱条件会拒绝本来可用的结果。应使用业务范围和必要条件。
- **乘积效应被低估**：只要每一步都存在失败概率，链条变长后整链成功率就会下降。设计时要用本地单步通过率计算整链风险，并尽量减少不必要步骤。
- **system prompt 缺少分区装配**：生产 system prompt 通常由基础指令、用户身份、历史、当前任务、工具清单、风格和格式约束组成。应保留独立数据源和更新边界。

## 验证指标

- **整链成功率**：任一步无法通过闸门都算整链失败。应同时查看失败集中在哪一段，以及是模型输出、数据传递还是闸门规则造成。
- **每步耗时分布**：查看各步骤的中位数和长尾，定位拖慢整链的模型、工具或外部依赖。
- **闸门重试分布**：某一步重试突然增多时，检查输入漂移、模型变化和闸门标准是否失配。

## 最小实现

```
chain = [step1, step2, step3]        # 每步自带 system_prompt + model + gate
current = initial_input
for step in chain:
    for attempt in range(max_retry + 1):
        result = step.run(current)   # 调对应模型
        若 result 过闸门:
            current = result.output
            break
        elif 还能重试:
            current += "[未达标: 原因。重试]"   # 回喂失败原因
        else:
            return 失败(step, trace)
return 成功(current, total_tokens, trace)
```

生产实现为闸门设置合理容差；将 token 和耗时写入结构化 trace；数字核查等步骤重新读取原始输入，避免前序改写污染事实。

## 场景化示例

设想一个财经媒体内容编辑 Agent 把流程拆为校对、改写、统一风格、数字核查、标题、摘要和配图建议。校对与改写各自使用适合的模型；数字核查必须回到原稿或权威数据源，不接受上一环节改写后的文本作为唯一依据；每一步都有独立 schema 和闸门。整链保留 trace，使编辑能看到数字在哪一步被读取、核对或修改。该结构也可用于合同审阅、医疗辅助和客服分诊，但每个领域的闸门必须重新定义。

## 相邻模式

- **规划-执行（A2）**：线性任务可使用 A3；存在并行或跨步依赖的 DAG 使用 A2。生产系统常由 A2 编排外层任务，在子任务内部运行 A3。
- **工具调度（A1）**：嵌套关系而非替代。chain 的某一步内部可能调工具，那一步是 A1（在多个工具中选一个），但它发生在 chain 的某一节里。
- **护栏三明治（A4）**：chain 的闸门是同步的程序化检查，A4 的 hook 是套在工具调用前后的夹层。两者都是"让流程在卡点处可拦截"。

## 工程判断

多轮 LLM 调用已经形成事实上的 prompt chain。将链路显式化后，团队可以分别配置模型、校验门、trace 和失败重放，避免控制关系只存在于对话历史中。

## 企业证据

<p class="evidence-empty">当前没有与本模式绑定的公开评审案例。模式定义不因此视为已经获得企业验证。</p>

<p style="font-size: 0.88rem; color: var(--color-text-muted);">案例收录要求说明业务约束、实现结构、已知失败和迁移边界。参见 <a href="https://adpsagent.com/zh/join/">贡献与评审规则</a>。</p>

<div class="document-citation">
<p><strong>引用建议：</strong>ADPS，《A3 提示链》，Agent 设计模式白皮书 v0.3，2026-07-30。</p>
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
<p><a href="https://adpsagent.com/zh/chronicle/#patterns-a3-prompt-chaining">在 ADPS Chronicle 中查看</a></p>
</section>

<!-- PAGE-CHRONICLE:END -->
