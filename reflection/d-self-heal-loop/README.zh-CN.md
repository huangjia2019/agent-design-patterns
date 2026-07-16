# 自愈循环

> 专栏第 **06-05** 讲 · 模式 · 反思行 × 循环列
> [English README](README.md)

## 模式契约

自愈循环是一笔由确定性红灯驱动、失败可回滚的修复事务：

```text
诊断 -> 生成补丁 -> 补丁审查 -> 原子应用 -> 重新验证 -> 继续或停止
```

循环在这里是结构本体。验证转绿才算修好，否则由三条停止线接管：

1. 硬轮数预算耗尽。
2. 补丁 critic 在应用前拦下危险修改。
3. 稳定性检查发现回归，或发现同一失败与同一补丁再次出现、没有进展。

每个已应用补丁都有独立提交号。凡是未修复成功的终态，系统都会逆序撤销
整个提交栈，先恢复基线，再把完整 trace 交给人。靠改弱测试换来的绿灯会
在应用前被拦下。

## 快速开始

```bash
python3 reflection/payroll-lab/self_heal_lab.py
python3 reflection/payroll-lab/self_heal_lab.py --meltdown
```

默认实验先修复两处薪酬缺陷，再演示作弊补丁被拦。`--meltdown` 是受控的
事故重演：前半段展示裸重试如何留下九轮重叠修改，后半段展示有界修复
事务如何发现爆炸半径扩大，并完整恢复基线。

## 参考接口

[`pattern.py`](pattern.py) 把安全性做成可以查询和测试的事实：

- `FailureSignal.signature` 标识稳定的失败类别。
- `Patch.fingerprint` 发现无进展的重复尝试。
- `HealStatus` 为每一种成功和停机路径命名。
- `HealTrace.baseline_restored` 证明基线是否完整。
- `propose_guard` 把反复出现的失败提议为待人审的回归护栏。

运行不变量测试：

```bash
uv run pytest reflection/d-self-heal-loop/test_pattern.py -q
```

## 矩阵位置

这个模式坐落在 **反思 × 循环** 的交点。相邻模式见
[双轴矩阵](../../README.zh-CN.md#28-个模式的矩阵)。
