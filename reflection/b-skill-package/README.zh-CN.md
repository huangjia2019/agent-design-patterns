# 技能包

> 专栏第 **06-03** 讲 · 模式 · 反思行 × Route列
> [English README](README.md)

## 状态

pattern.py 已落地（跟随极客时间《Agent 设计模式之美》第 28 讲 / 06-03）。核心判断：**技能 verified 才入库，路由只看 VERIFIED**。所有技能入库一律先进 TRIAL（人写的也一样），过 golden questions（确定性的输入→期望输出对照）全通过才转正。复用后的成功率跌破阈值自动降回 TRIAL 重新验证，这是防过期的护栏。Hermes 提供“成功且足够复杂的任务值得沉淀”的现实锚点，本接口再用工具种类过滤琐碎轨迹。蒸馏只挣得存储资格，挣不到信任。

## 快速开始

```bash
cd ../payroll-lab
python3 skill_package_lab.py             # 场景一：验证闸拦下旧年度口径；场景二：路由只见 VERIFIED
python3 skill_package_lab.py --no-gate   # 场景三：不过闸直接入库，800 人里 209 个基数算错
```

## 矩阵位置

这个模式坐落在 **反思（认知功能）× Route（执行拓扑）** 的交点。
跟邻居模式的关系见
[双轴矩阵](../../README.zh-CN.md#28-个模式的矩阵)。

## 这个模式讲什么

工作标题：**技能包**（英文：Skill Package）。完整内容见 Manning *Designing
AI Agents* 第 06 章和极客时间专栏。
