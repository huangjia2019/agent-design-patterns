# a · 生成-批评 Generator-Critic

> 专栏第 **06-02** 讲 · 模式 · 反思 × Chain
>
> [English README](README.md)

## 问题

一个 Agent 起草客户可见的故障更新，或者生成一份月末薪酬报告。文字可以很自信，但关键判断
必须来自外部信号：状态页事件、schema、SQL 对账、测试结果或策略条款。如果同一个生成步骤
还能顺手说一句「看起来没问题」，这套 harness 并没有真正反思，只是让模型给自己背书。

生成-批评把这几件事拆开：

- **生成者** 产出 artifact。
- **批评者** 只产出关于 artifact 的证据：分数、问题、阻断项、警告。
- **策略闸门** 用确定性代码决定能不能通过。

核心判断是：**批评者的成色取决于接进来的外部信号**。无证据的批评意见会被记录到
`dropped_issues`，但不能触发修订；只有带 `source` 和 `evidence` 的 finding 才能作为事实信号
进入闸门。

## 模式边界

拓扑是一条短链：

```text
generate -> critique -> gate -> optional revision draft
```

关键边界在最后一步。如果 reviser 起草了一个更好的版本，结果仍然是 `NEEDS_REVISION`；这个
模式不会在没有再次批评的情况下自动接受修改稿。要演示第二轮，应由 runner 显式再调用一次
Generator-Critic pass，并留下两次独立 trace。

这也把生成-批评和自愈循环区分开：生成-批评是固定边界、可审计的评审链；Self-Heal Loop 才由
停止条件驱动持续修复。

## 实现

| 构件 | 作用 |
|---|---|
| `Artifact` | 被评审的生成物。 |
| `Issue` | 一个批评 finding：`severity`、`message`、`location`、命名来源 `source`、外部证据 `evidence`。 |
| `Critique` | 分数、summary、证据支持的 `issues`，以及被证据闸丢弃的 `dropped_issues`。 |
| `AcceptancePolicy` | 确定性闸门。blocker、warning 和分数阈值都由代码判断。 |
| `GeneratorCriticChain` | 单次 `generate -> critique -> gate`。可选 reviser 只产出修改稿，不自动放行。 |

## 文件

| 文件 | 内容 |
|---|---|
| [`pattern.py`](pattern.py) | 框架无关参照实现：数据结构、证据闸门和单次 Chain primitive。 |
| [`shared.py`](shared.py) | 两套 reference notebook 共享的解析器、策略、mock 数据、reviser 和 trace 辅助函数。 |
| [`example.py`](example.py) | 用 mock critic 和可选 reviser 跑一条故障更新草稿。无需 API key。 |
| [`test_pattern.py`](test_pattern.py) | 覆盖分数阈值、证据闸、blocker/warning、严格解析失败、trace 顺序、修改稿不能自动放行等不变量。 |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | StateGraph 实现：显式 `generate -> critique -> gate -> revise` 节点和条件路由。 |
| [`langchain/tutorial.ipynb`](langchain/tutorial.ipynb) | LangChain LCEL 实现：更短的 runnable pipe，复用同一套解析器和策略闸门。 |
| [`../payroll-lab/generator_critic_lab.py`](../payroll-lab/generator_critic_lab.py) | 第 27 讲 Payroll Lab：接外部信号的批评链、橡皮图章、轮次耗尽交人工。重复 pass 由 runner 显式完成。 |

## 运行

```bash
python reflection/a-generator-critic/example.py
pytest reflection/a-generator-critic/test_pattern.py -v

# Payroll Lab：三场景，无需 API key
python reflection/payroll-lab/generator_critic_lab.py
python reflection/payroll-lab/generator_critic_lab.py --stubborn

# reference notebooks —— mock cell 无需 API key；配置好 .env 后 real backend cell 会直接运行
pytest --nbmake --nbmake-timeout=120 \
  reflection/a-generator-critic/langgraph/tutorial.ipynb \
  reflection/a-generator-critic/langchain/tutorial.ipynb
```

## 它在双轴里的位置

反思（认知功能）× Chain（执行拓扑）。最近的邻居是自愈循环，它会重复批评/修改路径；另一个
近邻是协作模块的对抗评审，它把「自己反思」推进到「独立评审者攻击」。见
[双轴矩阵](../../README.zh-CN.md#28-个模式的矩阵)。
