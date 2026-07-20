# b · 扇出聚合 Fan-out / Gather

> 模式 · 协作 × 并行
>
> [English README](README.md)

## 问题

并行调用很容易，可信聚合还要回答五个问题：

1. 多路结果是竞争答案，还是可组合贡献
2. 每个值来自哪个来源、快照、周期和单位
3. 同一身份下的多份贡献怎样合并
4. 冲突和跨来源接缝由谁处理
5. 必要来源缺席时，整份报告是否失效

## 模式

一个根 `TaskContract` 按可归因边界扇成多份 `SourceSpec`。每个工人返回
`ArtifactEnvelope[SourceResult]`。`SourceAdmissionPolicy` 检查契约摘要、来源身份、
快照、周期、单位、预期字段、证据、置信度和失败状态。

聚合阶段执行 `AggregatorPolicy`：

| 问题 | 接口 |
|---|---|
| 竞争还是相加 | `Strategy` |
| 冲突怎样解决 | `conflict_resolver` |
| 身份与贡献怎样合并 | `identity_key` + `ContributionRule` |
| 谁检查组合后的接缝 | `seam_reviewer` |

竞争式结果生成冻结的 `LineItemVerdict`，明确区分一致、可归因分歧和不可解释分歧。
相加式结果生成 `MergedItem`，保留每一路贡献和原始键。最终
`ReconciliationReport` 绑定根契约，并取得自己的 `AcceptanceReceipt`。

跨模式共用的传输接口位于
[`../boundary_contract.py`](../boundary_contract.py)：

```text
TaskContract -> HandoffEnvelope -> ArtifactEnvelope -> AcceptanceReceipt
```

## 公共接口

| 对象 | 职责 |
|---|---|
| `SourceSpec` | 来源身份、快照、范围和预期字段 |
| `SourceResult` | 单个来源产生的不可变读数 |
| `SourceAdmissionPolicy` | 来源工件验收与回执 |
| `AggregatorPolicy` | 可执行的聚合语义 |
| `LineItemVerdict` | 竞争证据及其可选裁决 |
| `MergedItem` | 保留来源贡献的组合值 |
| `ReconciliationReport` | 类型化的聚合结果 |
| `FanOutGather` | 并行派发、来源底线、聚合和根级回执 |

## 运行

```bash
python collaboration/b-fan-out-gather/example.py
pytest collaboration/b-fan-out-gather/test_pattern.py -v
python collaboration/payroll-lab/fan_out_gather_lab.py
python collaboration/payroll-lab/fan_out_gather_lab.py --additive
```

两套框架教程分别展示 LangGraph 与 Claude Agent SDK 的派发接缝。模式契约与确定性聚合保持框架无关。

## 它在双轴里的位置

协作 × 并行。层级委派把不同责任单元交给不同工人，扇出聚合让多个独立来源回答同一个
契约问题，再把一致和分歧都当成证据。
