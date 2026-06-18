# 案例：从规则抽取到高召回审阅队列

一个落地问题：当你面对一份几十页的业务规范，想让 Agent 抽成可执行 checklist 时，组合模式到底有没有用？

结论先说。同一份金融产品披露规范，单次生成只命中 12 条标准规则里的 6 条。加入生成-批评和自我修正后到 7 条。引入候选队列后到 9 条。把多条路径的结果保留下来形成高召回审阅队列，可以到 10 条。

重点不在模型越来越聪明，而在架构师怎么把不稳定输出变成可审阅流程。

## 任务：把一份规范变成 checklist

业务任务可以这样抽象：

```text
long-form source standard
  -> candidate clauses
  -> reviewed golden checklist
  -> model-generated checklist
  -> score + review queue
  -> human-approved checklist
```

deliverable 是 checklist。Schema 规定每条规则要有 `source`、`category`、`predicate`、`requirement`、`severity` 等字段。给下游检测模块使用的是 12 条经过审阅的 Golden Rules。

这 12 条里，11 条来自披露质量相关章节，1 条来自目标客群适配相关章节。多放这一条是为了避免测试集惯性——如果全是同类规则，模型容易靠惯性猜中。加一条 target-segment suitability 检验它有没有真的看见任务边界。

## 第一轮：普通模型能到哪里

不用复杂架构，只做一次普通抽取：

```text
source bundle + checklist schema
  -> model call
  -> predicted checklist
  -> score against 12 golden rules
```

结果是 `6 / 12`。

这个分数并不奇怪。普通模型读长文档时往往抓住显眼条款、漏掉边角条款；也容易把多个义务合并成一句漂亮的话。人读起来顺，机器评分时就丢了，因为 checklist 要的是"可检查的原子规则"。

第一轮的产出叫 baseline：如果只靠一次生成，这个任务大概就是一半覆盖。

## 第二轮：反思模式能修多少

加入 Reflection。

第一条路径 `critique_repair`：先生成一版，再让模型对照 source 和 schema 做批评修复。第二条路径 `iterative_self_refine`：让模型多轮自我修正。

结果接近：

| 路径 | 双轴位置 | 命中 |
|---|---|---:|
| `critique_repair` | Reflection × Chain | 7 / 12 |
| `iterative_self_refine` | Reflection × Loop | 7 / 12 |

反思有用，但在这个任务里不能神化。它能修掉一些明显遗漏和字段问题，却不一定能发现所有没被初稿覆盖的条款。原因很简单：如果初稿没有把某个条款放进候选空间，后面的自我批评也可能围着已有答案打转。

这是很多 Agent 项目会踩的坑——以为"多想几轮"就一定更好。实际工程里，循环只能提高局部质量，不能自动保证全局覆盖。

## 第三轮：候选队列把问题变成审阅

真正的变化出现在 Governance × Route。

先用确定性程序从文档里切出候选条款，再让模型做"晋级"：

```text
source standard
  -> deterministic candidate extractor
  -> candidate queue
  -> model promotes / edits / merges / rejects
  -> reviewed checklist draft
```

结果是 `9 / 12`。

提升明显是因为任务形态变了。前两轮让模型"凭理解写 checklist"，这一轮让模型"从候选队列里做审阅"。审阅比凭空生成更适合合规场景。候选条款把搜索空间摊开，模型不容易完全漏掉某个角落。

Governance 在这里不是把正确答案给模型看，而是指：候选队列、schema gate、score evidence、人工审核路径。它给系统加的是审计结构，不是答案泄露。

## 第四轮：组合策略为什么赢

最后一步，把多个路径的结果保留下来，不急着压缩成最终 checklist：

```text
single pass draft
critique repair draft
self-refine draft
candidate-guided draft
  -> union by source/category
  -> preserve complementary coverage
  -> human review queue
```

这条 `coverage_preserving_union_queue` 路径拿到 `10 / 12`。

它的 predicted item 数量更多，precision 不是最高，但 recall 最高。对生产系统来说这反而是合理的——这个阶段不是最终发布 checklist，而是给人审的候选队列。宁可多给审阅者几个可删的候选，也不要在自动压缩阶段把重要规则藏掉。

还有一条 `orchestrated_consensus_refine` 路径——先合并多路结果，再压缩成更像最终清单的一版。结果是 `8 / 12`。它比 baseline 好，但比高召回队列差。

这个对比关键。它说明"最终答案更整齐"不等于"工程效果更好"。在有人工审核的流程里，最有价值的中间产物常常不是 final answer，而是 review queue。

## 用 Pattern Selection Card 复盘

这个案例的 Pattern Selection Card 可以这样填：

| 步骤 | 选择 |
|---|---|
| ASSESS | 长文档、schema 输出、覆盖风险、人工审核、证据追踪 |
| ROUTE | Reasoning × Chain 做 baseline，Reflection 做修复，Governance × Route 做候选队列，Parallel -> Route 做高召回组合 |
| SELECT | 跑 6 条路径，比较覆盖率、可审阅性和压缩损失 |

如果只看单个模式，结论可能是"用生成-批评就够了"。但一旦进入组合视角，答案变了：先用 baseline 确定难度，再用 candidate-guided review 拉高覆盖，再用 union queue 保留互补候选，最后交给人工审核。

这就是 Composition 的价值：把不同模式放在不同阶段，让它们各自暴露一种信息。

## 三个 takeaway

读完这个案例可以带走三件事。

**第一，Golden Rules 要先有**。没有标准答案，无法判断模式有没有变好。很多 Agent 项目的问题，常常出在根本没有可评分的目标。

**第二，单次生成只是 baseline**。它很适合快速试水，但不要把 baseline 当架构。baseline 的价值是让你知道任务难在哪里。

**第三，高召回队列是合规类任务的好中间态**。在需要人工审核的场景里，保留候选比过早收敛更重要。最终 checklist 可以晚一点定，但审阅证据不能丢。

## 结果汇总

```text
single pass                  -> 6 / 12
critique repair              -> 7 / 12
iterative self-refine        -> 7 / 12
candidate-guided review      -> 9 / 12
coverage-preserving queue    -> 10 / 12
consensus refine             -> 8 / 12
```

数字背后的架构判断：当任务需要覆盖率、证据和人工审核时，最好的系统形态往往不是"给我最终答案"，而是"给我一条可审计、可修改、可继续推进的路径"。

## 思考题

如果把这个案例换成合同条款审查、医疗指南抽取、企业安全策略检查，`coverage_preserving_union_queue` 还会是最优吗？什么时候应该放弃高召回队列，直接追求 compact final checklist？

## 参考

* Anthropic, *Building Effective Agents*，2024-12-19
* OpenAI Agents SDK Tracing / Trace Grading 文档
* LangGraph Durable Execution / Human-in-the-loop 文档
