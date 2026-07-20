# 模式选型卡

> 专栏第 **41** 讲 · 组合方法 · [English README](README.md)

## 工程化定义

**模式选型卡是一份版本化的架构决策工件。** 它把问题边界、最小基线、
候选模式组合、成立前提、被拒绝的替代方案、模式接缝和验证计划绑定在同一份
可审计记录中。选型卡不替架构师自动挑模式，也不凭模式名称宣布设计正确。
它先生成一份可证伪的架构假设，再用同负载对照实验决定这份假设能否获得采用资格。

组合方法位于 28 个核心模式的矩阵之外。双轴矩阵描述单个模式的
“认知功能 × 执行拓扑”坐标，选型卡处理的是跨坐标的架构决策。

## 为什么不能只靠手工挑选

模式目录能压缩工程经验，也能提醒团队检查容易漏掉的设计力。
它仍然无法预先证明一套组合满足具体系统的准确率、延迟、成本和风险要求。

这个实现因此守住三条纪律：

1. **复杂度要有病因。** 没有观测到最小基线的失败，就没有增加模式的依据。
2. **模式前提要有证据。** 扇出聚合要求来源独立，卡片必须绑定来源谱系，
   不能只写“看起来独立”。
3. **实验拥有裁决权。** 候选必须在同一批代表性任务上通过验收门。
   如果最小基线已经通过，新增模式会被拒绝。

## 核心对象

| 对象 | 作用 |
|---|---|
| `ProblemContract` | 在命名模式之前写清问题、负载、依赖关系和约束 |
| `PatternSpec` | 记录一个模式解决什么、采用何种拓扑、依赖哪些前提 |
| `ArchitectureCandidate` | 把一个或多个模式组成可证伪候选 |
| `SeamContract` | 约束模式交界处的所有者、版本和可变性 |
| `ExperimentPlan` | 绑定代表性负载、验收指标、反证信号和回退计划 |
| `TrialResult` | 保存基线与候选的实测指标和证据引用 |
| `PatternSelectionCard` | 预检假设，并依据对照实验给出采用或拒绝结论 |

## 最小示例

```python
outcome = card.evaluate(
    (
        baseline_trial,
        proposal_trial,
    )
)

assert outcome.baseline_passed is False
assert outcome.proposal_passed is True
assert outcome.state.value == "accepted"
```

这里的 `accepted` 只表示候选在卡片绑定的负载和验收门下获得采用资格。
输入规模、风险边界或依赖关系变化时，卡片必须升版重测。

## 运行

```bash
python3 composition/a-pattern-selection-card/example.py
uv run pytest -q composition/a-pattern-selection-card/test_pattern.py
```

完整的薪酬场景与 Web 工作台见
[`composition/payroll-lab`](../payroll-lab/)。
