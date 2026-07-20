# 生成批评

> 专栏第 **06-02** 讲 · 模式 · 反思行 × 链式列
>
> [English README](README.md)

## 模式契约

生成批评只审一份产出，只走一遍有界链：

```text
生成 -> 批评 -> 策略裁决 -> 可选的修订草稿
```

批评者负责报告问题和证据，没有放行权。确定性的 `AcceptancePolicy`
根据有依据的问题和分数，对本遍真正审过的产出作出 `ACCEPTED` 或
`NEEDS_REVISION` 裁决。

一个可执行的问题必须同时带命名检查 `check`（notebook JSON 中叫
`source`）和 `evidence`。缺少任一项的意见会进入 `dropped_issues`，
保留在审计轨迹中，但不能触发自动修订。低分也遵守同一规则：启用证据
要求时，只有同时给出 `Critique.score_evidence`，低分才能进入策略闸门。

如果 reviser 生成了新稿，这份稿件明确处于未复审状态。
`ChainResult.reviewed_artifact` 指明本遍真正审过的版本，
`ChainResult.revision_draft` 必须由外层流程再次调用 `review()`，才能获得
新的裁决。

这条边界决定了它位于反思行、链式列。由 test、lint、build 或 CI 红灯
强制驱动、一直修到转绿或熔断的结构，属于相邻的
[自愈循环](../d-self-heal-loop/README.zh-CN.md)。

## 快速开始

```bash
python3 reflection/a-generator-critic/example.py
python3 reflection/payroll-lab/generator_critic_lab.py
python3 reflection/payroll-lab/generator_critic_lab.py --rubber-stamp

uv run pytest reflection/a-generator-critic/test_pattern.py -q
```

薪酬 Lab 中，月报声称 800 张工资单已支付，而 SQLite 里的事实是 798 张
`PAID`、2 张 `REVERSED`。标准批评者挂接账本与 schema 证据，第一遍只
生成待复审的修订稿，第二遍显式提交后才可能放行。`--rubber-stamp`
移除这些外部事实，展示一位文风漂亮的批评者如何批准错误月报。

## 参考接口

| 构件 | 责任 |
|---|---|
| `Artifact` | 生成物及其修订元数据。 |
| `Issue` | 带严重级别、位置、命名检查和证据的问题。 |
| `Critique` | 有依据的问题、被丢弃的意见、摘要、分数和分数依据。 |
| `AcceptancePolicy` | 确定性的证据与严重级别闸门。 |
| `ChainResult` | 把本遍已审产出和未复审的修订草稿明确分开。 |
| `GeneratorCriticChain` | 从 prompt 运行一遍，或显式复审已有 artifact。 |

## 文件

| 文件 | 内容 |
|---|---|
| [`pattern.py`](pattern.py) | 框架无关参照接口和单遍边界。 |
| [`shared.py`](shared.py) | 两套 notebook 共享的 JSON 解析器、策略、确定性 fixture、reviser 和 trace。 |
| [`example.py`](example.py) | 对客户故障更新做两遍显式评审；无需 API key。 |
| [`test_pattern.py`](test_pattern.py) | 证据、分数、解析、版本边界和可选依赖不变量。 |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | 用 StateGraph 节点和条件路由表达同一契约。 |
| [`langchain/tutorial.ipynb`](langchain/tutorial.ipynb) | 用 LCEL 表达同一套解析器、策略、fixture 和术语。 |
| [`../payroll-lab/generator_critic_lab.py`](../payroll-lab/generator_critic_lab.py) | 接账本证据的批评者与橡皮图章批评者对照。 |

## Notebook 验证

两套 notebook 都先运行确定性的 fake-model 场景，最后的可选真实后端区段
直接调用 `get_model()`，不需要额外的 fake/real 环境变量。

```bash
env OPENAI_API_KEY= ANTHROPIC_API_KEY= ERNIE_API_KEY= \
  uv run pytest --nbmake --nbmake-timeout=120 \
  reflection/a-generator-critic/langgraph/tutorial.ipynb \
  reflection/a-generator-critic/langchain/tutorial.ipynb
```

## 矩阵位置

这个模式坐落在 **反思 × 链式** 的交点。相邻模式见
[双轴矩阵](../../README.zh-CN.md#28-个模式的矩阵)。
