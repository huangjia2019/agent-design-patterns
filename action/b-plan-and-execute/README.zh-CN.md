# b · Plan-and-Execute · 规划-执行

> 专栏第 **05-03** 讲 · pattern · 行动 × 交接
>
> [English README](README.md)

## 故事

一家中型互联网公司的 HR 招聘 Agent，端到端做这件事：解析 JD、找候选、
打分、约面试、面试、生成 offer、背调、发 offer。v1 把 17 个 tool 全
给 LLM 自由决策。

第一个月财务把账单丢过来：**¥18 万**。然后 HR 那边的反馈不断：

* "Agent 把候选人**还没面试**的薪酬数据发给招聘经理了——这是隐私
  数据。"
* "Agent **跳过背景调查**直接发 offer——出大事差点。两次。"
* "它一天 query 了 50 次薪酬数据，因为每次 reasoning 完都忘了上一次
  查了啥。"

根因：agent 跑的是 ReAct 风格——每一步都是 reactive。**没有 plan**，
只有一个 200K context 装着中间 tool 结果，LLM 每次决定"下一步干啥"。
Context 装不下 12 步招聘流程的全貌，只能做局部决策，漏全局结构。

v2 拆成三段，每段绑不同档 model，把 plan 做成用户能签的文件：

```
1. Planner   → 12 步 DAG plan（高档 model）
2. HR review → 编辑 + approve plan，拿到 token
3. Executor  → 按 plan 走，[HUMAN] 处阻塞，失败 local 不 global
```

效果：错误率 8.3% → 0.4%，模型调用 47 → 13 次每候选人，账单 ¥18 万 →
¥6 万。整体招聘周期 23 天 → 16 天。

讲义的判断：**Plan-and-Execute 是任何 long-horizon agent 的工程地基**。
5 步以下随便跑。超过 5 步，plan 必须是 typed、可持久化、可签字的
artifact，executor 必须做到"一次只死一步"，不是整段重来。

## 模式骨架

3 个类 + 4 个函数：

| 构件 | 角色 |
|---|---|
| `PlanStep` | DAG 一个节点。带 `deps` / `handler` 名 / `args` / `requires_human`，runtime 状态 `status` / `output` / `error` |
| `Plan` | DAG 本体。会 validate（无环、所有 dep 都存在）/ 报 `ready_steps()` / 判 `is_complete()` |
| `Executor` | 走 DAG。按名字查 handler registry，自动把 `prior_outputs` 织进去，失败 cascade skip |
| `approve` | 用户标记 plan 可执行。token 是 audit handle |
| `release_blocked` | 单次 human gate 翻转。同时清 `requires_human`，下次 run 通过 |
| `replan_local` | 重跑 Planner，校验 merge 后 plan，cap 新 step 数量。Anthropic 建议 replan budget < 10% 总 budget |

3 条行为保证：

1. **Approve 前不能跑**。未 approve 的 plan 调 `Executor.run` 直接抛
   `PlanError`。**没有 "就这次破例" 的口子**。
2. **Step status 是唯一真相**。`TODO` / `DOING` / `DONE` / `BLOCKED`
   / `FAILED` / `SKIPPED`。状态机不倒退，除了 `release_blocked`
   (BLOCKED → TODO) 和 `replan_local` (FAILED/SKIPPED → TODO)。
3. **失败 local**。失败 step cascade `SKIPPED` 给所有传递性下游，
   **不 abort 整个 plan**。兄弟子图保留结果。replan 只 replan 受影响
   子树。

## 跑起来

```bash
python action/b-plan-and-execute/example.py
pytest action/b-plan-and-execute/
```

demo 跑 9 步招聘 DAG。3 个 sourcing 步骤并行（互相无依赖）。Interview
步是 `requires_human=True` 阻塞到 `release_blocked` 被调。`send_offer`
依赖 `assemble_offer` 依赖 `background_check` 加 `query_salary_band`
—— **DAG 强制 没背调过 不可能发 offer**。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `StepStatus` + `PlanStep` + `Plan` + `Executor` + `PlanError` + `approve` + `release_blocked` + `replan_local`（~240 行） |
| `example.py` | 招聘 agent 场景，并行 sourcing + human 面试 gate + DAG 强制 background_check |
| `test_pattern.py` | 20 条不变式：环检测 / unknown-dep 拒绝 / ready-step 集合 / approval gate / 并行执行 / handler 看到 prior outputs / human 阻塞 + release 一次性 / 失败 cascade / unknown handler = failed / replan 在 cap 内/超 cap / 完成检查 |

## 工程引用（都核过源码）

* **Aider** [`aider/coders/architect_coder.py`](https://github.com/Aider-AI/aider/blob/main/aider/coders/architect_coder.py)
  —— 最小可行形态。49 行代码，核心 9 行是 architect / editor 分家：
  按角色绑不同 model、角色间清 context、execute 前 user approval。
  绝大多数生产部署就是这个骨架加更多旋钮。
* **Claude Code** ExitPlanMode tool —— **plan 写文件** 这条工程纪律。
  Plan 由 agent 写文件；tool 只 signal "ready for review"，不传输
  plan 内容（已经在磁盘上）。跟 `approve(plan, token)` 同一原则：
  Plan 是持久化 artifact，不是临时字符串。
* **LangGraph 1.0** —— 生产 runtime。BSP / Pregel + SQLite checkpoint；
  90M 月下载量。参考实现是它的同步内存版本，contract 一致（steps
  有 status、deps gate 执行、replan local）。
* **Manus** —— Yichao "Peak" Ji 的 *Context Engineering for AI Agents*。
  `todo.md` 持续重写 pattern：把 plan 推到 context 末尾，让模型的
  recent-attention 窗口覆盖它。Cache hit rate 是生产 agent 单一最重要
  指标。
* **Anthropic (2026)** [*How we built our multi-agent research
  system*](https://www.anthropic.com/research/multi-agent-research)
  —— Adaptive Replanning：每 N 步检查 plan 是否成立；replan budget
  上限 < 10% 总 budget；长任务用 JSON checkpoint 比 Markdown 更抗
  损坏。
* **AWS** [Saga pattern prescriptive guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)
  —— plan-and-execute 配合 [Tool Dispatch](../a-tool-dispatch/) 的
  saga inverse：destructive step 注册 rollback；中途失败 reverse saga
  跑回去，不是 silent state corruption。

## 什么时候不要用

* **短任务（< 5 步）**。直接跑就行。DAG plumbing 是 overhead。
* **探索型工作**。不知道要多少步时 plan 是幻觉。用
  [Iterative Hypothesis Testing](../../reasoning/d-iterative-hypothesis/)。
* **用户每轮 steer 的对话场景**。Plan 是用户的 mental model，显式
  DAG 跟它打架。

Pattern 的价值集中在 **目标明确 + 步骤可枚举 + 副作用敏感** 三件叠加。
任何一件不占都是过度工程。

## 诚实承认的局限

DAG runtime 这里是单线程。真 LangGraph 部署用 asyncio 协程 fan-out
独立分支。生产并行对招聘场景重要（3 个 sourcing 应该并发）。数据
模型已支持——`Executor` 只是顺序迭代，换成对 `ready_steps()` 跑
`asyncio.gather` 就行，contract 不变。

`replan_local` 当前不保留**用户对 plan 的编辑**。如果 HR review 时
改了 step 5，后续 step 5 失败时 `replan_local` 重跑 Planner，可能
生成 HR 没 approve 过的 step 5。生产需要"用户编辑的 step replan 时
保留"或"编辑过的 step 锁定" 概念。Contract 一致，policy 不同。

`requires_human` 是一次性的，翻转后就关掉。这对面试调度对的（用户
approve 这位候选人）。对**每次执行都需要审批的 governance gate**
是错的（"每次 send_offer 都要审"）。后者用独立的 Approval Gate
pattern（Ch9）。
