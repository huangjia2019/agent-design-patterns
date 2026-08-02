# 薪酬实验台 · 反思模块（26—30 讲）

[English](README.md)

本目录承接 [`../../action/payroll-lab/`](../../action/payroll-lab/) 的 SQLite
薪酬库，并重建一个明确的月末反思场景：798 张工资单为 `PAID`，E0007、
E0012 两张为 `REVERSED`。Agent 的月报却声称 800 张已支付、0 笔冲正。

这里不是行动模块多个隔离实验自然累积出来的生产终态。`bench.py` 会专门
重建这份教学数据，让五讲从同一个可复现事实面出发。

## Web 教学控制台

在仓库根目录运行：

```bash
uv sync --extra ui
uv run --extra ui python reflection/payroll-lab/web_app.py
```

浏览器打开 `http://127.0.0.1:8766`。控制台可以运行 26—30 五讲，展示
证据时间线、检查 SQLite、重建月末场景，并触发每个模式的对照变体。
所有实验串行执行，避免多个浏览器标签同时写同一份本地数据库。

## 统一 CLI 入口

```bash
python3 reflection/payroll-lab/run_reflection_module.py --lecture 27
python3 reflection/payroll-lab/run_reflection_module.py --lecture 27 --variant
python3 reflection/payroll-lab/run_reflection_module.py --lecture all
```

`--variant` 对应每讲的“改一处再跑”：

| 讲 | 标准实验 | 对照变体 |
|:--|:--|:--|
| 26 导论 | 纯内省 vs SQL 对账 | 自评分更严格，盲区不变 |
| 27 生成评审 | 第一遍出修订稿，第二遍显式复审 | 橡皮图章批准错误月报 |
| 28 技能包 | 验证、准入，再路由 | 跳过验证闸 |
| 29 经验回放 | 召回、反馈、出池与毕业 | 断开下游反馈 |
| 30 自愈循环 | 修到绿，并拦下作弊补丁 | 受控重演失控重试并完整回滚 |

也可以直接运行原始 Lab：

```bash
python3 reflection/payroll-lab/self_grade_lab.py
python3 reflection/payroll-lab/generator_critic_lab.py
python3 reflection/payroll-lab/skill_package_lab.py
python3 reflection/payroll-lab/experience_replay_lab.py
python3 reflection/payroll-lab/self_heal_lab.py
```

## 设计边界

统一 Runner 只调度白名单命令，FastAPI 负责串行触发与结构化证据，各模式
仍保留自己的状态机和测试。第 27 讲的生成评审内部没有隐藏重试，第一遍
产生的新稿必须再次送审；第 30 讲的自愈循环才负责强制重复、停机与回滚。

## 验证

```bash
uv run pytest reflection/a-generator-critic/test_pattern.py \
  reflection/d-self-heal-loop/test_pattern.py \
  reflection/payroll-lab/test_ui_service.py -q
```
