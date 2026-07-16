# 薪酬行动压力工作台（payroll-lab）

[English](README.md)

这是极客时间专栏《Agent 设计模式之美》行动模块（第 21 至 25 讲）的教学实验台。场景是一套本地薪酬系统：SQLite 单文件、800 名员工、一个月的工资单草稿、两笔已批准待生效的变更。数据是构造的，表结构、状态写入和付款流水都是真实可查的。

工作台不需要 API key 或云服务。它使用确定性攻击夹具稳定复现坏提案，用 Repo 中四个模式的真实 `pattern.py` API 检查控制效果。实验结论来自状态账、动作账和模式 Trace，不用模型自报的“成功”作为证据。

## 一套工作台，三层压力

浏览器与 CLI 共用同一组 Stress Runner：

| 实验层 | 代码 | 回答的问题 |
|:--|:--|:--|
| L0 到 L2 同刺激消融 | `stress_ablation.py`、`stress_web_run.py` | 最简工具集与工具调度分别挡住什么 |
| V3 到 V5 模式前后对照 | `stress_vectors.py` | 规划执行、提示链、守卫三明治能否守住各自边界 |
| S1 到 S4 生产压力 | `stress_gaps.py` | 教学版进入并发、TOCTOU、重启和补偿失败后还会漏什么 |

`stress_full.py` 把五类故障向量在六种累计配置上的实跑证据汇总成矩阵。矩阵是一套统一评测协议，不表示五个模式已经装配进同一笔生产事务。

## 启动 Web 工作台

从 Repo 根目录执行：

```bash
uv sync --extra ui
uv run --extra ui python action/payroll-lab/web_app.py
```

浏览器打开 `http://127.0.0.1:8765`。控制台提供三种视图：

- **实验**：按讲次运行 L0 到 L2、V3 到 V5、S1 到 S4 和完整矩阵。
- **数据库**：查询员工、工资单、审批单和策略表，对照基线查看真实变化。
- **系统结构**：查看统一入口、受控 Runner、证据层和当前集成边界。

FastAPI 只接受白名单中的 level、vector 和固定实验，不开放任意 shell 或 SQL。L0 到 L2 在写库前恢复基线，V3 到 V5 在运行前把主库恢复为中性展示状态。S1 到 S4 与矩阵使用独立证据，不改 `payroll.db`。

## CLI 复现

Web 工作台中的核心结果都有对应 CLI：

```bash
uv run python action/payroll-lab/stress_ablation.py --walk L0
uv run python action/payroll-lab/stress_vectors.py --vector V3
uv run python action/payroll-lab/stress_vectors.py --vector V4
uv run python action/payroll-lab/stress_vectors.py --vector V5
uv run python action/payroll-lab/stress_gaps.py
uv run python action/payroll-lab/stress_full.py
```

L0 到 L2 共用一条北极星目标和一份外部备注。夹具按备注内容提取候选动作，对运行时装了什么防线一无所知。删掉“补发”或“分隔符”等内容，对应候选也会消失。它用于验证坏提案进入运行时以后能否被控制，不测量真实模型服从提示词注入的概率。

V3 到 V5 使用各自边界匹配的压力：

| 向量 | 压力 | 使用的模式实现 | 主要证据 |
|:--|:--|:--|:--|
| V3-中途超时后整批重跑 | 中间步骤超时后，恢复手册要求整批重开 | `b-plan-and-execute/pattern.py` | 每名员工的付款次数与局部重排 |
| V4-污染工件向后传递 | 对账工件携带异常总额 | `c-prompt-chaining/pattern.py` | 链外账本校验与链终态 |
| V5-高风险输入输出 | 异常金额进入工具参数，完整账号进入外发结果 | `d-guardrail-sandwich/pattern.py` | PRE、POST 与真实执行次数 |

## 代码地图

- `db.py`：创建 `payroll.db` 与基线快照，提供逐行 Diff 和可选的 `999999` 数据故障注入。
- `stress_ablation.py`：内存账本上的 L0 到 L2 同刺激消融。
- `stress_web_run.py`：把 L0 到 L2 写入真实 SQLite，并记录付款流水。
- `stress_vectors.py`：V3 到 V5 的无模式与装模式对照。
- `stress_gaps.py`：S1 到 S4 生产压力。
- `stress_full.py`：五向量乘六配置矩阵。
- `action_trace.py`：统一 `ActionEvent` 与 `ActionTrace` 的观测骨架。
- `ui_service.py`、`web_app.py`：受控命令层与 FastAPI 白名单入口。
- `ui/`：无构建步骤的浏览器界面。
- `test_stress_lab.py`、`test_ui_service.py`：因果结果、结构化证据和单引擎边界测试。

## 当前边界

Repo 已经统一了教学入口和评测协议。L0 到 L2 会写真实 `payroll.db`，V3 到 V5 是调用原生模式 API 的独立确定性切片，S1 到 S4 专门暴露教学实现走向生产时的缺口。

Repo 尚未把最简工具集、工具调度、规划执行、提示链和守卫三明治串入一个共享事务，也没有统一持久化 Plan、Artifact、Approval、Checkpoint 与 ActionEvent。生产化还需要跨进程幂等、实体版本、持久化配额与 Saga、补偿债务队列和外部清算回执。

## 验证

```bash
uv run pytest -q action/payroll-lab/test_stress_lab.py action/payroll-lab/test_ui_service.py
uvx ruff check action/payroll-lab
```
