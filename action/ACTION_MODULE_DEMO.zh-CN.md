# 行动模块 Demo 全景：把判断安全地做出来

这份文档把《Agent 设计模式之美》第 21 至 25 讲使用的代码、案例和运行顺序串成一条线。

先说清当前设计：Repo 里只有**一套行动压力工作台**。Web 界面、CLI 和测试共用同一组 Stress Runner，不存在一套讲稿 Demo、另一套 Web Demo 的双系统。

## 快速启动

从 Repo 根目录执行：

```bash
uv sync --extra ui
uv run --extra ui python action/payroll-lab/web_app.py
```

浏览器访问 `http://127.0.0.1:8765`。控制台有三个视图：

- **实验**：按讲次运行 L0 到 L2、V3 到 V5、S1 到 S4 和完整矩阵。
- **数据库**：查看员工、工资单、审批单、策略表以及相对基线的变化。
- **系统结构**：查看统一入口、受控 Runner、证据层和当前集成边界。

FastAPI 只接受白名单中的 level、vector 和固定实验，不开放任意 shell 或 SQL。

## Repo 结构

Repo 采用两层设计：模式本体可以独立学习，Payroll Lab 把四个模式放进同一个薪酬语境。

```plain
action/
├── a-tool-dispatch/          # 工具调度：模式、独立示例、测试
├── b-plan-and-execute/       # 规划执行：模式、独立示例、测试
├── c-prompt-chaining/        # 提示链：模式、独立示例、测试
├── d-guardrail-sandwich/     # 守卫三明治：模式、独立示例、测试
└── payroll-lab/
    ├── db.py                 # SQLite 建库、基线快照与逐行 Diff
    ├── stress_ablation.py    # L0-L2 同刺激消融
    ├── stress_web_run.py     # 把 L0-L2 的动作写入真实 SQLite
    ├── stress_vectors.py     # V3-V5 独立边界向量
    ├── stress_gaps.py        # S1-S4 教学到生产压力
    ├── stress_full.py        # 五向量乘六配置逐格实跑
    ├── ui_service.py         # 白名单 Runner 与结构化证据服务
    ├── web_app.py            # FastAPI 入口
    ├── ui/                   # 无构建步骤的浏览器界面
    ├── test_stress_lab.py    # 压力实验测试
    └── test_ui_service.py    # 服务边界测试
```

四个模式目前还没有串成一笔共享事务。L0 到 L2 会写同一个 `payroll.db`，V3 到 V5 是调用真实模式 API 的独立切片，S1 到 S4 使用单独证据施加生产压力。它们共享评测协议，不共享 Plan、Quota、Saga、Artifact 或 Hook 状态。

## 为什么选择薪酬执行

行动模块需要一个能看见副作用、又不会伤害真实系统的场景。Payroll Lab 使用单文件 SQLite，内含 800 名模拟员工和四张表。

| 表 | 保存什么 | 为什么和行动有关 |
|:--|:--|:--|
| `employees` | 员工、部门、银行账号、基础工资 | 账号属于关键主数据 |
| `payroll` | 工资单、奖金、调整、状态、异议备注 | `DRAFT → PAID` 是可见副作用 |
| `approvals` | 调薪、奖金和审批状态 | 已批准不等于内容一定合理 |
| `policies` | 政策版本 | 执行动作必须说明依据哪个规则版本 |

数据是构造的，SQLite 写入和付款流水是真实可查的。Demo 不连接银行，不会产生真实付款。

## 一套实验怎样贯穿五讲

行动模块的主问题是：**怎样把模型的判断转成真实副作用，同时只做被授权、可验证、可追责的动作。**

| 讲次 | 实验 | 本讲解决的问题 | 主要证据 |
|:--|:--|:--|:--|
| 21 行动导论 | L0 裸奔与完整矩阵 | 没有执行边界时，坏提案如何变成真实副作用 | 状态账、动作账、SQLite Diff |
| 22 工具调度 | L0 到 L2 同刺激消融 | 怎样从工具候选收缩到单次调用准入 | 候选工具、拒绝原因、新鲜度、配额 |
| 23 规划执行 | V3 中途超时后整批重跑 | 怎样保住已完成步骤，只恢复失败子图 | 步骤状态、依赖、每名员工付款次数 |
| 24 提示链 | V4 污染工件向后传递 | 怎样在段间用链外事实拦住坏工件 | Artifact、闸门结果、链终态 |
| 25 守卫三明治 | V5 高风险输入输出 | 怎样在执行前阻断风险、执行后控制发布 | PRE、原始输出、可发布输出、POST |

五个累计层级分别是：

```plain
L0 裸循环
L1 + 最简工具集
L2 + 工具调度
L3 + 规划执行
L4 + 提示链
L5 + 守卫三明治
```

这里的 L 编号只表示消融层级。四个模式不用 A1、A2 一类代号，讲稿、代码和工作台都直接写模式名。

## 第 21 讲：先看一次裸奔

L0 接收一份固定的外部薪酬备注。确定性攻击夹具会解析备注内容，提出三类坏动作：越界改银行账号、跳过可信读取、对同一笔薪酬重复付款。

```bash
uv run python action/payroll-lab/stress_ablation.py --walk L0
```

实验不会测“真实模型有多大概率中招”。它只保证每次课堂都把同一份坏提案送进运行时，从而验证运行时能否控制已经出现的错误动作。

L0 的执行器没有准入边界，结果是三行状态变化和两笔无纪律付款。第 21 讲到这里收住：它只把问题暴露清楚，不提前讲后面四个模式的解法。

## 第 22 讲：工具调度控制一次调用

第 22 讲沿用同一份备注，只改变控制层。

```bash
uv run python action/payroll-lab/stress_ablation.py --walk L0
uv run python action/payroll-lab/stress_ablation.py --walk L1
uv run python action/payroll-lab/stress_ablation.py --walk L2
```

三层结果如下：

| 层级 | 状态差异 | 付款 | 结论 |
|:--|:--|:--|:--|
| L0 裸奔 | 3 行 | 2 笔，无纪律 | 坏提案全部落地 |
| L1 最简工具集 | 1 行 | 2 笔，无纪律 | 越界字段保住了，调用纪律还没建立 |
| L2 工具调度 | 1 行 | 1 笔，先读后写 | 新鲜度与会话配额共同完成准入 |

工具调度不负责规划整件事。它只回答当前这一笔调用是否存在、是否获准、参数是否满足运行时条件，以及成功动作怎样进入补偿记录。

## 第 23 讲：规划执行控制失败恢复

V3 先让 E0007 付款成功，再让 E0012 在中途超时。无模式路径读取外部恢复说明后整批重跑，E0007 因而支付两次。规划执行路径把任务保存为 DAG，只替换失败步骤 `s12`，已完成的 `s7` 保持 `DONE`。

```bash
uv run python action/payroll-lab/stress_vectors.py --vector V3
```

关键结果：

```plain
整批重置：E0007=2、E0012=1、E0300=1
局部重排：E0007=1、E0012=1、E0300=1
```

`replan_local()` 当前会计算失败节点及其传递后继，只允许补丁替换受影响子图。补丁不能覆盖已完成或无关步骤，不能丢掉子图外部依赖，新节点还必须与失败子图结构相连。

这仍是内存参考实现。审批 token 没有绑定计划版本，Plan 和步骤输出也没有持久化 checkpoint。

## 第 24 讲：提示链控制段间交接

V4 让第一段生成结构合法、总额为 `9999999` 的污染对账工件。仅检查“非空”的线性串接会继续生成付款申请。提示链把 JSON 工件与链外 SQLite 可信账核对，闸门拒绝该工件，下游申请不会生成。

```bash
uv run python action/payroll-lab/stress_vectors.py --vector V4
```

这里的控制点是 Artifact 交接。闸门必须解析结构并核验业务不变量，字符串包含和“模型说已经对账”都不足以构成证据。

## 第 25 讲：守卫三明治控制高风险输入输出

V5 分别施加输入和输出压力：异常金额进入转账参数，完整银行账号进入外发结果。

```bash
uv run python action/payroll-lab/stress_vectors.py --vector V5
```

前置守卫在工具运行前拦住 `999999`，所以异常转账执行次数为 0。后置守卫看到工具已经生成的原始账号，记录 `blocked_post` 并把可发布输出留空。原始结果仍保留在 Trace 中，便于审计与补偿分析。

`rollback_marked=True` 只是一条补偿请求，不等于补偿已经开始、成功或得到外部确认。输入守卫和输出守卫也是两个独立调用边界，Demo 没有把它们伪装成同一笔事务。

## 教学实现走向生产时会漏什么

`stress_gaps.py` 不植入假 bug，只向现有工具调度实现施加并发、状态变化、重启和补偿失败。

```bash
uv run python action/payroll-lab/stress_gaps.py
```

当前稳定暴露四个缺口：

1. **并发配额竞态**：会话配额是内存中的先读后写，并发请求可能双付。
2. **读取后状态变化**：新鲜度没有绑定员工、月份和资源版本，挡不住 TOCTOU。
3. **进程重启失忆**：配额、读取时间和 Saga 都在内存里，重启后不再认识旧动作。
4. **补偿债务丢失**：冲正失败后，当前实现会把对应 entry 移出 `saga_log`。

这些结果说明教学代码守住了模式边界，也说明生产系统还需要共享持久层、实体版本、跨进程幂等和补偿债务队列。

## 完整消融矩阵

```bash
uv run python action/payroll-lab/stress_full.py
```

`stress_full.py` 会逐格运行五类故障向量和六种累计配置。V1、V2 共用一份薪酬备注，V3、V4、V5 使用与各自模式边界匹配的独立压力。矩阵是一套统一评测协议，不表示五种故障来自同一条万能提示词。

预期结果是一条清晰的阶梯：

```plain
L0 暴露 5 类
L1 暴露 4 类
L2 暴露 3 类
L3 暴露 2 类
L4 暴露 1 类
L5 全部守住
```

## 运行测试

从 Repo 根目录执行：

```bash
uv run ruff check action
uv run pytest -q action
```

如果只核对工作台：

```bash
uv run pytest -q \
  action/payroll-lab/test_stress_lab.py \
  action/payroll-lab/test_ui_service.py
```

## 当前架构与未来集成

目前的运行关系是：

```plain
Web / CLI
    ↓
ui_service 白名单入口
    ↓
Stress Runners
    ├── L0-L2：状态账 + 动作账 + SQLite Diff
    ├── V3：Plan + Executor + replan_local
    ├── V4：PromptChain + 链外事实闸门
    ├── V5：PRE / TOOL / POST Trace
    └── S1-S4：生产压力证据
```

生产级行动运行时不会把四个模式简单首尾相接。更合理的嵌套关系是：

```plain
推理决策（ReasoningDecision）
    ↓
目标契约（Goal Contract）与计划（Plan）
    ↓ 执行器选择当前计划步骤（PlanStep）
提示链（Prompt Chain）生成或校验结构化工件（Artifact）
    ↓
工具调度器（Tool Dispatcher）缩小候选并决定执行准入
    ↓
守卫三明治（Guardrail Sandwich）执行前置检查、工具调用与后置检查
    ↓
业务账本（Business Ledger）+ 统一行动事件（ActionEvent）+ 检查点（Checkpoint）
```

继续生产化时，需要补上五类共享构件：

1. **行动契约**：统一保存目标、范围、工具意图、审批、幂等键和完成证据。
2. **来源与版本**：关键参数使用可信状态引用，每个 Artifact 带来源、版本和有效期。
3. **统一行动事件**：把 DispatchTrace、PlanStep、ChainTrace 和 SandwichTrace 映射到一条事件流。
4. **持久化检查点**：保存计划、步骤输出、幂等记录、外部回执和补偿状态。
5. **受控执行入口**：业务工具只能经过准入与守卫代理，不能绕过 Harness 直连。

## 阅读顺序

1. 先在 Web 工作台运行第 21 讲 L0，观察坏提案如何进入状态账和动作账。
2. 运行 L0 到 L2，对照最简工具集与工具调度各自解决了什么。
3. 依次运行 V3、V4、V5，再读三个模式目录里的 `pattern.py` 与测试。
4. 运行 S1 到 S4，分清教学实现已经证明的能力和仍待生产化的边界。
5. 最后运行完整矩阵，复盘五讲怎样逐层收紧行动自由度。

行动模块最终要训练的判断很简单：模型可以提出动作，Harness 必须决定动作是否属于目标、参数是否可信、执行是否获准、结果是否可以发布，以及失败以后由谁接管。
