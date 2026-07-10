# 薪酬实验台（payroll-lab）· 行动模块动手环节

[English](README.md)

这是极客时间专栏《Agent设计模式之美》行动模块（21-25 讲）的动手实验台：一个 mock 的薪酬系统，SQLite 单文件，800 名员工、一个月的工资单草稿、两笔已批准待生效的变更（第 17 讲咖哥的 18% 调薪、第 19 讲小雪的 9600 奖金）。数据是造的，结构是真的，副作用看得见。

不需要 API key，不需要云服务，一台装了 Python 3 的笔记本就够。

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
| 22 工具调度 | Action × Router | [`../a-tool-dispatch/`](../a-tool-dispatch/) |
| 23 规划执行 | Action × Orchestration | [`../b-plan-and-execute/`](../b-plan-and-execute/) |
| 24 提示链 | Action × Chain | [`../c-prompt-chaining/`](../c-prompt-chaining/) |
| 25 守卫三明治 | Action × Hierarchy | [`../d-guardrail-sandwich/`](../d-guardrail-sandwich/) |

每讲动手环节固定五步：克隆、跑起来、看输出、改一处、再跑。

## 文件说明

- `db.py` — 建库、基线快照、`--diff` 逐行对账、`--inject-typo` 注入手滑数据
- `naked_loop.py` — 50 行上下、无护栏的感知-推理-行动循环（反面教材，故意的）
- `action_trace.py` — 行动模块共用的观测层：四个生产指标 + 健康检查（`python3 action_trace.py` 可看 scope-creep 报警的演示）

表结构四张：`employees`（员工与银行账号）、`payroll`（月度工资单）、`approvals`（审批单）、`policies`（政策版本）。
