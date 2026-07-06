# a · 生成-批评 Generator-Critic

> 专栏第 **06-02** 讲 · 模式 · 反思 × Chain
>
> [English README](README.md)

## 问题

一个 Agent 起草客户可见的故障更新。文字很自信，但影响范围那句话没有证据来源。如果同一个
生成步骤还能顺手说一句「看起来没问题」，那这套 harness 并没有真正反思，只是让模型给自己
刚写出的东西背书。

生成-批评把这两件事拆开。生成者产出一个 artifact。批评者只产出关于这个 artifact 的证据：
分数、问题、阻断项、警告。最后由确定性的策略决定能不能通过。批评者可以影响闸门，但不能
靠一句「挺好」直接放行。

## 模式

拓扑是一条短链：

```text
generate -> critique -> gate -> optional revision draft
```

关键边界在最后一步。如果 reviser 起草了一个更好的版本，结果仍然是 `NEEDS_REVISION`；这个
模式不会在没有再次批评的情况下自动接受修改稿。这也把生成-批评和自愈循环区分开：自愈循环
会重复「批评/修改」直到满足停止条件。

实现里有三个核心件：

- **Artifact** —— 被评审的生成物。
- **Critique** —— 分数和具体问题。它能报告 blocker 和 warning，但没有「批准」方法。
- **AcceptancePolicy** —— 确定性闸门。阻断项、警告、分数阈值都由代码判断。

## 文件

| 文件 | 内容 |
|---|---|
| [`pattern.py`](pattern.py) | 框架无关参照：`Artifact`、`Issue`、`Critique`、`AcceptancePolicy`、`GeneratorCriticChain`。 |
| [`shared.py`](shared.py) | 两套 reference notebook 共享的解析器、策略、mock 数据、reviser 和 trace 辅助函数。 |
| [`example.py`](example.py) | 用 mock critic 和可选 reviser 跑一条故障更新草稿。无需 API key。 |
| [`test_pattern.py`](test_pattern.py) | 8 个测试：分数阈值、blocker/warning 闸门、trace 顺序、修改稿不能自动放行的不变量。 |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | StateGraph 实现：显式 `generate -> critique -> gate -> revise` 节点和条件路由。 |
| [`langchain/tutorial.ipynb`](langchain/tutorial.ipynb) | LangChain LCEL 实现：更短的 runnable pipe，复用同一套解析器和策略闸门。 |

## 运行

```bash
python reflection/a-generator-critic/example.py
pytest reflection/a-generator-critic/test_pattern.py -v

# reference notebooks —— mock cell 无需 API key；配置好 .env 后 real backend cell 会直接运行
pytest --nbmake --nbmake-timeout=120 \
  reflection/a-generator-critic/langgraph/tutorial.ipynb \
  reflection/a-generator-critic/langchain/tutorial.ipynb
```

## 它在双轴里的位置

反思（认知功能）× Chain（执行拓扑）。最近的邻居是自愈循环，它会重复批评/修改路径；另一个
近邻是协作模块的对抗评审，它把「自己反思」推进到「独立评审者攻击」。见
[双轴矩阵](../../README.zh-CN.md)。
