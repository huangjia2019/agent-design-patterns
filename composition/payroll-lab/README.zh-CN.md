# 组合选型工作台

这套 Lab 用三讲回答一个很具体的问题：架构师从模式目录里手工挑出几个
模式，真的能得到可用系统吗？

答案分两层。

1. 模式名能帮助团队提出更好的候选架构。
2. 候选架构只有在同一批代表性任务上赢过最小基线，才获得采用资格。

第 41 讲使用 Repo 中真实的
`Fan-out and Gather` 与 `Iterative Hypothesis` 实现。两项任务表面上都叫
“查出薪酬差异”，数据关系却不同：

| 场景 | 数据关系 | 基线问题 | 候选模式 |
|---|---|---|---|
| 四源独立 | 来源各自拥有快照 | 单源检查看不见差异 | 扇出聚合 |
| 共享结转 | 四源依赖同一上月状态 | 并行比较产生虚假一致 | 迭代假设验证 |

第 42 讲继续使用真实的 `Plan and Execute` 与 `Handoff Chain`。它先把
“两个模式都写 `net_amount`”的组合拦在实验前，再比较三个候选和两个消融：

| 方案 | 局部恢复 | 提交后覆盖 | 交接回执 |
|---|---:|---:|---:|
| 共享可变字典基线 | 0 | 1 | 0 |
| 仅交接链 | 0 | 0 | 0 |
| 规划执行 + 交接链，职责拆分 | 1 | 0 | 1 |
| 移除规划执行 | 0 | 0 | 0 |
| 移除交接链 | 1 | 1 | 0 |

第 43 讲把八个模块接到同一轮月结任务。它使用
`Context Triage`、`Handoff Chain`、`Iterative Hypothesis`、
`Plan and Execute`、`Generator-Critic`、`Approval Gate`、
`Progress Tracking` 和 `Full System Assembly` 的真实接口。

对照中的两种接法都有 `8/8` 张局部通过回执。仅看局部成功时，治理仍绑定
旧报告，而且模块回执没有父链，系统验收拒绝。端到端绑定后，SQLite 发布行、
报告摘要和治理回执指向同一版本，系统才被接受。

## 运行 CLI

```bash
python3 composition/payroll-lab/selection_card_lab.py
python3 composition/payroll-lab/six_step_lab.py
python3 composition/payroll-lab/capstone_lab.py --mode local-only
python3 composition/payroll-lab/capstone_lab.py --mode bound
```

## 运行 Web 工作台

```bash
uv sync --extra ui
uv run uvicorn web_app:app --app-dir composition/payroll-lab --port 8041
```

浏览器打开：

- 第 41 讲：`http://127.0.0.1:8041`
- 第 42 讲：`http://127.0.0.1:8041/42`
- 第 43 讲：`http://127.0.0.1:8041/43`

## 运行测试

```bash
uv run pytest -q \
  composition/a-pattern-selection-card/test_pattern.py \
  composition/b-six-step-methodology/test_pattern.py \
  composition/c-argus-full-case/test_pattern.py \
  composition/payroll-lab
```
