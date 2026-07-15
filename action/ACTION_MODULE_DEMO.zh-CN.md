# 行动模块 Demo 全景：从裸循环到高风险行动防线

这份文档把《Agent 设计模式之美》行动模块第 21—25 讲的代码、案例和运行顺序串成一条完整脉络。

课堂演示优先使用 Web 控制台：

```bash
uv sync --extra ui
uv run --extra ui python action/payroll-lab/web_app.py
```

浏览器访问 `http://127.0.0.1:8765`。CLI 脚本全部保留，既是 Web
控制台的执行来源，也是读者逐行核对模式行为的最小入口。

先给结论：Repo 采用的是**模式实现分目录、统一案例在 Payroll Lab 汇合**的两层设计。

```plain
action/
├── a-tool-dispatch/          # 工具调度模式本体、独立案例、测试
├── b-plan-and-execute/       # 规划执行模式本体、独立案例、测试
├── c-prompt-chaining/        # 提示链模式本体、独立案例、测试
├── d-guardrail-sandwich/     # 守卫三明治模式本体、独立案例、测试
└── payroll-lab/              # 同一个薪酬案例的第 21—25 讲实操
    ├── web_app.py            # FastAPI 教学入口
    ├── ui_service.py         # 受控 Runner 与 SQLite 结构化读模型
    └── ui/                   # 无构建步骤的浏览器界面
```

四个模式目录是可以单独学习和复用的参考实现。`payroll-lab` 负责把它们放进同一业务语境，形成连续课程故事。

目前四个模式**尚未装配成一个共享运行时**。每个 Lab 都是独立 Python 进程，数据库在每讲前重置，内存中的 Plan、Trace、Quota、Saga 和 Hook 状态不会跨 Lab 传递。这是教学切片，不是假装已经完成的生产 Agent。

## 为什么选择薪酬执行

行动模块需要一个能够看见副作用、又不会伤害真实系统的场景。Payroll Lab 使用单文件 SQLite，包含 800 名模拟员工和四张表：

| 表 | 作用 | 行动风险 |
|:--|:--|:--|
| `employees` | 员工、部门、银行账号、基础工资 | 账号属于关键主数据 |
| `payroll` | 月度工资单、奖金、调整、状态、异议备注 | `DRAFT → PAID/REVERSED` 是可见副作用 |
| `approvals` | 调薪、奖金和审批状态 | “已批准”不自动等于内容合理 |
| `policies` | 政策版本 | 提醒执行依赖具体规则版本 |

数据是模拟的，SQLite 写入是真实发生的。Demo 不连接银行，不会产生真实付款。

共享角色来自前面的推理模块：

- E0007：咖哥，18% 调薪对应 5400 元调整。
- E0012：小雪，9600 元奖金，异议备注必须保留。
- E0300：仍在等待第二签的奖金审批，同时用于冻结账户场景。
- E0099：人为注入的 999999 元错误调整，用于验证“流程批准但内容异常”。

## 一条主线看懂五讲

行动模块围绕同一个问题逐层收紧：**怎样把判断转成真实副作用，同时只做被授权、可验证、可补偿的动作。**

| 讲 | 模式与坐标 | 控制对象 | Payroll 故障 | 关键证据 |
|:--|:--|:--|:--|:--|
| 21 | 行动导论 | 裸循环的副作用范围 | 顺手改账号、清空异议、999999 穿透 | DB diff、scope creep ratio |
| 22 | 工具调度 × 路由 | 当前调用哪个工具、是否准入 | 幻觉工具、旧状态、重复调用、缺审批 | DispatchTrace、Quota、Saga log |
| 23 | 规划执行 × 编排 | 整件事有哪些步骤、走到哪里 | b3 超时、局部重排、对账待人审 | PlanStep 状态、尝试次数、Ledger |
| 24 | 提示链 × 链式 | 段与段之间交接什么 | 总额抄错两位，27 万差额继续传播 | ChainTrace、Gate result、最终申请书 |
| 25 | 守卫三明治 × 层级 | 高风险动作执行前后如何控制 | 999999、冻结账户、缺回执、PII 输出 | SandwichTrace、DB 终态、补偿信号 |

四个模式的通用标题是：

1. 工具调度：从候选选择到执行准入。
2. 规划执行：用全局计划约束局部行动。
3. 提示链：用段间契约阻断错误传播。
4. 守卫三明治：高风险行动的前中后防线。

## 第 21 讲：先让没有护栏的循环跑起来

`naked_loop.py` 只有感知、推理、行动三个阶段：

```plain
PERCEIVE：读取 APPROVED 审批和 DRAFT 工资单数量
REASON：为每条审批生成 apply_approval，再追加 pay_everyone
ACT：执行数据库更新
```

它能完成任务，也会顺手做四类计划外动作：格式化银行账号、清空备注、把全部工资单直接改成 PAID，以及无条件接受 999999 元调整。

第一轮运行后的终态：

```plain
payroll={'PAID': 800}
approvals={'APPLIED': 2, 'PENDING': 1}
scope creep ratio=2.33
```

第二轮先执行 `db.py --inject-typo`，再运行裸循环。E0099 的 999999 会被应用，三条 APPROVED 审批全部变成 APPLIED。

`action_trace.py` 当前是固定重放的观测骨架。它没有自动采集 `naked_loop.py` 的真实调用，也没有接入后面四种模式的 Trace。

## 第 22 讲：工具调度控制一次调用

模式本体位于 `a-tool-dispatch/pattern.py`。Payroll 适配层注册四个工具：

```plain
query_payroll
transfer_salary
reverse_transfer
update_bank_account
```

实验依次验证：

1. 未注册的 `transfer_money_fast` 被拒绝为 `tool_hallucination`。
2. 没有 fresh read 的转账被拒绝，查询以后重试成功。
3. 同一员工第二次转账被 session quota 拦截。
4. 修改银行账号停在 `awaiting_approval`。
5. 操作员中止 session，成功转账按逆序补偿。

最终终态：

```plain
payroll={'DRAFT': 798, 'REVERSED': 2}
rejected=4 of 8 dispatches
```

教学边界：

- 调度器从模型已经给出 `tool_name` 以后开始工作，没有实现语义候选检索。
- quota 在内存中按 session 计数，不能替代跨进程支付幂等。
- freshness 只按 session 记录，没有绑定员工、月份和资源版本。
- `awaiting_approval` 没有审批票据与恢复流程。
- Saga 以 session 为补偿范围，`rollback_action` 也没有自动保存 before-image。

## 第 23 讲：规划执行控制全局步骤

模式本体位于 `b-plan-and-execute/pattern.py`。Payroll Planner 生成九个节点：

```plain
prep_payroll ─┐
              ├→ verify → gen_instructions → transfer_b1 ─┐
prep_accounts ┘                            → transfer_b2  │
                                             transfer_b3  ├→ reconcile [HUMAN]
                                             transfer_b4 ─┘
```

b1、b2 完成后，b3 第一次触发模拟网关超时。Executor fail-fast，b4 保持 TODO，对账被标成 SKIPPED。此时数据库已有 400 条 PAID。

局部 replanner 重新提出 b3。第二次执行完成 b3 和 b4，对账进入 BLOCKED，人工释放后结束。

最终终态：

```plain
payroll={'PAID': 800}
attempts={'b1': 1, 'b2': 1, 'b3': 2, 'b4': 1}
reconciled=800, exceptions=0
```

教学边界：

- DAG 表达了并行可能，当前 Executor 实际顺序执行 ready steps。
- Plan、output 和状态都在内存中，没有 checkpoint。
- approval token 只是字符串，没有绑定 plan hash 和版本。
- `replan_local()` 会重置整张计划里所有 FAILED/SKIPPED 节点，没有严格计算某个失败节点的 affected subgraph。
- PlanStep 直接调用 handler，尚未接入第 22 讲的 ToolDispatcher。

## 第 24 讲：提示链控制段间交接

模式本体位于 `c-prompt-chaining/pattern.py`。Payroll 链包含四段：

```plain
settle → reconcile → instructions → payment_request
```

mock model 在第一次生成 instructions 时，把总账 `13744541` 抄成 `13474541`。

严格 checksum gate 拒绝第一次输出，第二次恢复正确。把 gate 放松成“非空即通过”后，27 万差额一路进入最终申请书，后续每段仍显示 SUCCESS。

这个实验不修改数据库：

```plain
payroll={'DRAFT': 800}
approvals={'APPROVED': 2, 'PENDING': 1}
```

教学边界：

- `keys_gate()` 和 checksum 使用字符串包含，无法替代结构化解析和业务不变量。
- Gate failure 重试时没有把拒绝原因反馈给模型。Demo 靠 mock 内部计数在第二次改对。
- 模板缺 key 或 `static_args` 覆盖受保护产物名时，当前实现会在模型调用前 fail-closed。
- Trace 没有保存 prompt hash、token、latency、artifact version 和结构化失败字段。

## 第 25 讲：守卫三明治控制高风险动作

模式本体位于 `d-guardrail-sandwich/pattern.py`。调用被拆成三种时态：

```plain
PRE hooks → tool execution → POST hooks
```

Runner 在第 25 讲隔离重置后重新执行 `db.py --inject-typo`。实验先读出
E0099 的审批 ID、金额和 APPROVED 状态，再把同一金额交给 Sandwich。
六个场景验证：正常转账、999999 前置拦截、冻结账户前置拦截、缺回执后置拦截、账号内容 DLP 检测，以及 5 万阈值的 shadow mode。

最终数据库有三条 PAID：

```plain
E0012：正常通过
E0021：工具已经执行，POST 因缺 receipt BLOCK，但只标记 rollback
E0025：5 万阈值处于 shadow mode，WARN 后继续执行
```

因此，`BLOCKED_PRE` 表示工具没有运行，`BLOCKED_POST` 表示副作用已经发生。Runner 的 Ledger 提示已经明确区分这两种状态。

教学边界：

- `rollback_marked=True` 只是信号，没有调用 Saga 或确认补偿完成。
- handler 抛异常后跳过全部 POST hooks，无法处理远端成功、本地超时的模糊结果。
- amount 字段缺失时阈值 hook 返回 PASS，需要工具级 schema 先行。
- 原始 handler 仍可从公开 `tools` 字典取到，语言层没有真正封死旁路。
- PII hook 只对 `str(output)` 做正则扫描，不能覆盖编码、分片和语义泄漏。
- Hook Trace 已记录规则 owner 与版本；规则依据、审批记录和生效范围仍需进入统一 Policy Store。

## 一条命令跑完整模块

从 Repo 根目录执行：

```bash
python3 action/payroll-lab/run_action_module.py
```

Runner 会按以下顺序执行：

```plain
21 裸循环与范围漂移
21 注入 999999 后再次裸跑
22 工具调度
23 规划执行
24 提示链
25 守卫三明治
```

每个场景开始前都会运行 `db.py`，所以各讲互不污染。全部完成后再次恢复基线。

只运行一讲：

```bash
python3 action/payroll-lab/run_action_module.py --lecture 22
python3 action/payroll-lab/run_action_module.py --lecture 25
```

保留最后一个实验的数据库状态：

```bash
python3 action/payroll-lab/run_action_module.py --lecture 25 --keep-state
python3 action/payroll-lab/db.py --diff
```

恢复基线：

```bash
python3 action/payroll-lab/db.py
```

## 运行测试

四个模式与 UI 服务层共有 83 条定向测试：

```bash
uv run --frozen pytest \
  action/a-tool-dispatch/test_pattern.py \
  action/b-plan-and-execute/test_pattern.py \
  action/c-prompt-chaining/test_pattern.py \
  action/d-guardrail-sandwich/test_pattern.py \
  action/payroll-lab/test_ui_service.py -q
```

Runner 自身使用 Python 标准库，不需要 API Key。

## 当前架构是什么

可以把现状画成两层：

```plain
教学案例层
Payroll Lab
  ├── tool_dispatch_lab.py
  ├── plan_execute_lab.py
  ├── prompt_chain_lab.py
  └── guardrail_lab.py
          │ imports
          ▼
模式参考实现层
  ├── ToolDispatcher
  ├── Plan + Executor
  ├── PromptChain
  └── GuardrailSandwich
```

这种布局有三个优点：

1. 每个模式可以独立阅读、测试和迁移到其他业务。
2. Payroll 业务代码不会污染模式骨架。
3. 每讲只引入一个新变量，实验现象清楚。

它也有一个明确限制：四个模式还没有共享一个 Action Runtime。

## 如果增强成一个真正的行动模块

生产级集成不应把四个 Lab 简单首尾相接。更合理的调用关系是嵌套：

```plain
ReasoningDecision
    ↓
Goal Contract + Plan
    ↓ Executor 选择当前 PlanStep
Prompt Chain 生成或校验该步骤的结构化 Artifact
    ↓
Tool Dispatcher 缩小候选并完成执行准入
    ↓
Guardrail Sandwich 执行 PRE / TOOL / POST
    ↓
Business Ledger + unified ActionEvent + Checkpoint
```

下一阶段可以增加五个共享构件。

### 1. Action Contract

统一保存 `goal_id`、`plan_id`、scope、tool intent、参数引用、审批、幂等键和完成证据。四个模式都围绕同一份合同工作。

### 2. SessionState 与 Provenance

金额、账号、员工 ID 和月份从机械状态解析，模型只生成引用。每个 Artifact 带来源、版本和有效期。

### 3. Unified ActionEvent

把 `DispatchTrace`、PlanStep 状态、ChainTrace 和 SandwichTrace 映射为统一事件：

```plain
ACTION_PROPOSED
ACTION_ADMITTED
ACTION_BLOCKED_PRE
ACTION_STARTED
ACTION_SUCCEEDED
ACTION_FAILED_AMBIGUOUS
ACTION_BLOCKED_POST
COMPENSATION_REQUESTED
COMPENSATED
```

当前 `action_trace.py` 可以演进为这个事件层，而不再固定重放七个动作。

### 4. Durable Checkpoint

Plan、step output、幂等记录、审批凭证、外部回执和补偿状态进入持久化存储。进程重启后从最后一个确定事件恢复。

### 5. Integrated Payroll Agent

新增一个 `integrated_payroll_agent.py`，只暴露一个受控入口。真正的集成不会顺序运行四个 Demo。它会在一个 PlanStep 内同时调用 ToolDispatcher 与 GuardrailSandwich，并让 PromptChain 产出的 Artifact 接受 schema 与业务校验。

这个增强的优先级高于继续增加更多 mock 场景。它能把课程中的四种模式从“同一个案例的四张切片”推进到“同一个执行事务的四层控制”。

## 阅读顺序

建议按下面的顺序阅读和运行：

1. 先跑 `naked_loop.py`，建立对副作用和范围漂移的感觉。
2. 读四个模式目录里的 `pattern.py` 与 `test_pattern.py`。
3. 回到 Payroll Lab 跑对应业务场景。
4. 用本文件的“教学边界”检查代码到底保证了什么。
5. 最后运行 `run_action_module.py`，从头复盘整条行动主线。

行动模块最终要训练的判断很简单：模型可以提出动作，Harness 必须决定动作是否属于目标、参数是否可信、执行是否获准、结果是否真实，以及失败后由谁接管。
