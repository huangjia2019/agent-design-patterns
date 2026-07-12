# 经验回放

> 专栏第 **06-04** 讲 · 模式 · 反思行 × Hierarchy列
> [English README](README.md)

## 状态

pattern.py 已落地（跟随极客时间《Agent 设计模式之美》第 29 讲 / 06-04）。核心判断：**一条教训能留在回放池里，靠的是复用后的真实成功率，不是 Agent 觉得它有用**。经验分层存（L0 原始轨迹留审计 / L1 单任务教训供注入 / L2 跨任务规律），检索命中后 render 成上层背景层包住当前决策。每次复用把下游成败回写（EMA），复用够多仍低于健康线的自动归档出池。确定性可判、战绩过硬的教训该毕业成动作前护栏（接第 25 讲），软教训随之退休。

## 快速开始

```bash
cd ../payroll-lab
python3 experience_replay_lab.py                # 场景一：召回改变决策；场景二：同一个信号，一头请伪经验出库、一头送真经验毕业
python3 experience_replay_lab.py --no-feedback  # 场景三：不回写成败，错误归因的伪经验第 7 个月还在 context 里
```

## 矩阵位置

这个模式坐落在 **反思（认知功能）× Hierarchy（执行拓扑）** 的交点。
跟邻居模式的关系见
[双轴矩阵](../../README.zh-CN.md#28-个模式的矩阵)。

## 这个模式讲什么

工作标题：**经验回放**（英文：Experience Replay）。完整内容见 Manning *Designing
AI Agents* 第 06 章和极客时间专栏。
