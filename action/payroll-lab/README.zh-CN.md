# 薪酬实验台（payroll-lab）· 行动模块动手环节

[English](README.md)

这是极客时间专栏《Agent设计模式之美》行动模块（21-25 讲）的动手实验台：一个 mock 的薪酬系统，SQLite 单文件，800 名员工、一个月的工资单草稿、两笔已批准待生效的变更（第 17 讲咖哥的 18% 调薪、第 19 讲小雪的 9600 奖金）。数据是造的，结构是真的，副作用看得见。

不需要 API key，不需要云服务，一台装了 Python 3 的笔记本就够。

## 一次跑完整个行动模块

```bash
python3 run_action_module.py
```

Runner 按第 21→25 讲顺序运行。每个实验开始前都会重置数据库，避免前一讲的副作用污染后一讲。它展示的是同一 Payroll 案例的五个独立教学切片，不代表四个模式已经装配进同一个生产运行时。

完整设计、逐讲终态和集成边界见 [`../ACTION_MODULE_DEMO.zh-CN.md`](../ACTION_MODULE_DEMO.zh-CN.md)。

## 教学 Web 控制台

从 Repo 根目录执行：

```bash
uv sync --extra ui
uv run --extra ui python action/payroll-lab/web_app.py
```

浏览器打开 `http://127.0.0.1:8765`。控制台保留第 21—25 讲原有 CLI
脚本作为事实来源，并提供三种视图：

- **实验**：逐讲运行，按阶段、控制点和业务证据展示结果。完整 CLI 输出
  收在折叠区。
- **数据库**：查看四张表的 schema、数据、分页与搜索结果。
- **系统结构**：查看 Browser、FastAPI、Controlled Runner、模式目录与
  SQLite 之间的关系。

页面右上角可以恢复基线或注入 E0099 的 999999 错误审批。服务端只接受
预先登记的实验和表名，不提供任意 shell 或 SQL 执行入口。

只跑一讲或保留最后数据库状态：

```bash
python3 run_action_module.py --lecture 23
python3 run_action_module.py --lecture 25 --keep-state
```

## 快速开始（第 21 讲动手环节）

```bash
git clone https://github.com/huangjia2019/agent-design-patterns.git
cd agent-design-patterns/action/payroll-lab

python3 db.py           # 建库：800 人 + 两笔已批准变更，并存一份基线快照
python3 naked_loop.py   # 跑 50 行、没有任何护栏的 PRA 循环
python3 db.py --diff    # 对照基线快照，看它到底动了哪些行
```

你会看到它把两笔变更写进了工资单、把 800 张工资单一口气标成 PAID。你还会看到它做了几件没人叫它做的事：把两个员工的银行账号"顺手"规范化了，把小雪那条第 19 讲反复强调必须留痕的异议备注"顺手"清空了。

然后改一处，再跑：

```bash
python3 db.py                 # 重置数据库
python3 db.py --inject-typo   # 塞进一笔手滑多打了几个零的"已批准"调整：999999
python3 naked_loop.py         # 看它眼都不眨地写进去
```

这就是接下来四讲要一层层解决的问题。

## 每讲对应的代码

| 讲 | 模式（坐标） | 代码位置 |
|:--|:--|:--|
| 21 导论 | 裸奔的 PRA 循环 + ActionTrace 观测层 | 本目录 `naked_loop.py` / `action_trace.py` |
| 22 工具调度 | Action × Router | 本目录 `tool_dispatch_lab.py`（薪酬版五场景）+ 模式本体 [`../a-tool-dispatch/`](../a-tool-dispatch/) |
| 23 规划执行 | Action × Orchestration | 本目录 `plan_execute_lab.py`（800 人打款 DAG 四幕）+ 模式本体 [`../b-plan-and-execute/`](../b-plan-and-execute/) |
| 24 提示链 | Action × Chain | 本目录 `prompt_chain_lab.py`（打款链两轮对照：有闸/裸闸）+ 模式本体 [`../c-prompt-chaining/`](../c-prompt-chaining/) |
| 25 守卫三明治 | Action × Hierarchy | 本目录 `guardrail_lab.py`（读取 E0099 APPROVED 审批证据后，把转账夹进三明治）+ 模式本体 [`../d-guardrail-sandwich/`](../d-guardrail-sandwich/) |

每讲动手环节固定五步：克隆、跑起来、看输出、改一处、再跑。

## 文件说明

- `db.py` — 建库、基线快照、`--diff` 逐行对账、`--inject-typo` 注入手滑数据
- `naked_loop.py` — 50 行上下、无护栏的感知-推理-行动循环（反面教材，故意的）
- `action_trace.py` — 统一观测层的数据结构草图：四个生产指标 + 健康检查。当前用固定重放演示 scope-creep 报警，尚未自动采集四个模式的原生 Trace
- `tool_dispatch_lab.py` — 第 22 讲动手环节：把转账、冲正、查工资条、改银行账号四个工具挂上元数据，跑五个场景（工具臆造 / 过期状态 / 重复打款 / 审批门 / saga 冲正），第 21 讲那个"顺手改账号"在场景四被当场拦下
- `plan_execute_lab.py` — 第 23 讲动手环节：800 人打款排成一张 DAG 计划，四幕剧本（财务审批 → 批次 b3 银行超时失败、已成批次不动 → 局部重排只补 b3 → 对账人审放行）
- `prompt_chain_lab.py` — 第 24 讲动手环节：结算→对账→生成指令→打款申请书四段链，mock 模型在生成指令时手抄总额抄串两位数字，第一轮校验闸当场拦下重试通过，第二轮把闸门放松成"非空"，27 万元的差额一路流进打款申请书且每段都报成功
- `guardrail_lab.py` — 第 25 讲动手环节：先运行 `python3 db.py --inject-typo`，实验读取 E0099 的 APPROVED 审批 ID 与金额，再把同一笔转账夹进守卫三明治，运行六个场景（正常放行 / 999999 在前置层被摁住、工具压根没跑 / 风控冻结账户前置拦 / 银行没回执后置拦并标记冲正 / 单步全合规的组合式数据外泄被 PII 后置闸拦下 / 更严阈值以 shadow 模式陪跑只记不拦）
- `web_app.py` / `ui_service.py` — FastAPI 教学入口与结构化服务层
- `ui/` — 无构建步骤的浏览器界面，包含实验、数据库和系统结构视图
- `test_ui_service.py` — UI 服务层的 5 条测试：讲次注册、输出分类、数据库状态、搜索分页与表名白名单

表结构四张：`employees`（员工与银行账号）、`payroll`（月度工资单）、`approvals`（审批单）、`policies`（政策版本）。
