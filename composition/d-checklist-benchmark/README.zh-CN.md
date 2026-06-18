# 清单抽取基准案例

> 专栏第 **09-组合-集成之美** 配套案例 · 组合行 × 多拓扑组合
> [English README](README.md)

## 是什么

一个匿名的金融产品披露规范 checklist 抽取基准。先由强智能工具和人工审阅得到 12 条 Golden Rules，然后让普通模型按照同一个 schema 去抽取 checklist。不同模式组合的得分不同，用数据说明为什么组合策略值得用。

## 这个案例讲什么

这个案例不是为了证明某个模型“聪明”。它要证明一个更工程化的判断：

**当任务目标是把长文档抽成可审阅 checklist 时，模式组合可以把一次性抽取变成可测量、可回放、可人工修正的流程。**

公开版保留了 6 条策略的基准结果：

| 策略 | 双轴位置 | 命中 |
|---|---|---:|
| `single_pass` | Reasoning × Chain | 6 / 12 |
| `critique_repair` | Reflection × Chain | 7 / 12 |
| `iterative_self_refine` | Reflection × Loop | 7 / 12 |
| `candidate_guided_review` | Governance × Route | 9 / 12 |
| `coverage_preserving_union_queue` | Composite: Parallel -> Route | 10 / 12 |
| `orchestrated_consensus_refine` | Composite: Parallel -> Route -> Loop | 8 / 12 |

读法很简单：一次性抽取只能拿到 `6 / 12`。加入候选队列后到 `9 / 12`。把多个模式的互补结果保留下来，形成 review queue，可以到 `10 / 12`。但如果太早压缩成最终清单，又会掉回 `8 / 12`。

这就是第 09 模块要讲的组合思想：组合不是堆模式，而是让不同模式暴露不同类型的信息，再把这些信息交给正确的收口机制。

## 文件说明

| 文件 | 作用 |
|---|---|
| `case-study.zh-CN.md` | 案例叙述：4 轮 benchmark + Pattern Selection Card 复盘 + 3 个 takeaway |
| `anonymized_case.json` | 静态匿名案例数据 |
| `checklist_benchmark.ipynb` | 已执行 notebook，展示同一套结果 |

## 使用

这不是程序包。建议先读 `case-study.zh-CN.md`，再打开 `checklist_benchmark.ipynb` 看表格化结果。`anonymized_case.json` 是结果数据的稳定引用。

## 跟第 09 模块的关系

这个案例可以接在 `09-01 Pattern Selection Card` 和 `09-02 Six-Step Methodology` 后面讲。

第一步，先把业务任务写成 Pattern Selection Card：

* **ASSESS**：长文档、规则抽取、schema 合规、人工审阅、可追溯证据。
* **ROUTE**：先跑 Reasoning × Chain 做 baseline，再引入 Reflection 做修复，再用 Governance × Route 建候选队列。
* **SELECT**：不是选一个模式，而是比较 6 条路径，看哪条路径让下游审核最省力。

第二步，用 6 步法解释为什么 `coverage_preserving_union_queue` 胜出。它的胜出不是因为输出最漂亮，而是因为它把互补覆盖保留下来，给人工审核留下了修改空间。

这页案例的金句可以这样讲：

> 单次生成追求“看起来像答案”。组合基准追求“哪里漏了、谁补上了、下一步谁来审”。

## 工程切片

这个案例和 2024 年以来主流 agent 工程经验是同一条线：

* Anthropic 在 *Building Effective Agents* 里强调：先从简单、可组合 workflow 开始，只有复杂度值得时再增加 agentic 结构。
* OpenAI Agents SDK 的 tracing / trace grading 把“每一步怎么走的”变成可评估对象，和这里的 per-pattern notebook / score table 是同一种工程边界。
* LangGraph 的 durable execution / human-in-the-loop 说明：一旦流程需要人工审核，就要把状态和中间产物留下来，而不是只留下最终回答。

这些外部经验都指向同一件事：**生产级 Agent 不是一次回答，而是一条可审计的路径。**
