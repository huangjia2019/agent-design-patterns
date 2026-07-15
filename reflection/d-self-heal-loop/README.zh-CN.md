# 自愈循环

> 专栏第 **06-05** 讲 · 模式 · 反思行 × Loop列
> [English README](README.md)

## 状态

pattern.py 已落地（跟随极客时间《Agent 设计模式之美》第 30 讲 / 06-05，反思模块收官）。核心判断：**自愈循环的安全性全在停止机制上**。循环本身很简单（红灯、诊断、打补丁、再跑），把生产自愈和 main 分支事故分开的是三重停止：硬轮数上限（学 Aider 的 3）、每个补丁 apply 前过独立 critic（专拦"改弱测试不改代码"的作弊补丁）、失败签名 + 爆炸半径的回归检测（越修越糟就整栈回滚，逐个 revert）。触发信号是确定性的 test/lint/build/CI，不是模型对自己产出的意见。轮次耗尽带完整 trace 交人工。反复自愈同一类失败的，用 `propose_guard` 毕业成回归测试护栏（接 25 讲），今天靠修救，下个月靠拦防。

## 快速开始

```bash
cd ../payroll-lab
python3 self_heal_lab.py             # 场景一：两处真缺陷两轮收敛+毕业提案；场景二：作弊补丁被 critic 拦下
python3 self_heal_lab.py --meltdown  # 场景三：裸循环复刻 main 分支事故 vs 三重停止一轮止损全量回滚
```

## 矩阵位置

这个模式坐落在 **反思（认知功能）× Loop（执行拓扑）** 的交点。
跟邻居模式的关系见
[双轴矩阵](../../README.zh-CN.md#28-个模式的矩阵)。

## 这个模式讲什么

工作标题：**自愈循环**（英文：Self-Heal Loop）。完整内容见 Manning *Designing
AI Agents* 第 06 章和极客时间专栏。
