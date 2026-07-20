# d · 可观测性 Observability Harness

> 模式 · 治理 × 编排
>
> [English README](README.md)

## 问题

“系统有日志”不能证明一次付款经过了审批、预算和权限检查。普通日志还可能混入不同提案版本，
遗漏关键控制，或把银行账号和模型隐藏推理写进审计系统。

## 模式

`ObservabilityHarness` 把治理决定写成带语义的因果事件。每个事件绑定：

- `trace_id`、`span_id` 和父跨度
- 提案摘要、策略摘要和控制名称
- 决定、回执摘要、可核验的证据引用
- 前一个事件哈希和当前事件哈希

`TracePolicy` 定义一条完整轨迹必须出现哪些事件、控制、直接因果边、决定、单例事件和回执。
审计会报告缺失控制、因果边缺口、决定不符、单例事件重复、提案漂移、同一控制的策略漂移、
父子断链和哈希破坏。同一轨迹中的跨度身份必须唯一，子事件时间不能早于因果父事件。已知
敏感字段在入库前脱敏。隐藏思维过程不属于接口，系统记录可公开的决策摘要和外部证据。

## 公共接口

| 对象 | 职责 |
|---|---|
| `EventDraft` | 一个待写入的语义治理事件 |
| `EventRecord` | 带序号和哈希链的不可变记录 |
| `RedactionPolicy` | 入库前脱敏和禁止字段 |
| `TracePolicy` | 完整轨迹的事件、控制、因果边、决定和回执要求 |
| `TraceAudit` | 完整性、漂移和哈希校验结果 |
| `ObservabilityHarness` | 发事件、记回执、重放和审计 |

## 运行

```bash
python3 governance/d-observability-harness/example.py
pytest governance/d-observability-harness/test_pattern.py -q
python3 governance/payroll-lab/observability_harness_lab.py
```

## 它在双轴里的位置

治理 × 编排。它横切审批、预算、权限和执行适配器，任何单个组件都看不到完整因果链。
