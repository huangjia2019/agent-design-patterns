# d · 交接链 Handoff Chain

> 专栏第 **07-05** 讲 · 模式 · 协作 × 链式
>
> [English README](README.md)

## 问题

一个 AI 出行助手，把「我明天下午要到上海」变成一趟订好的行程，靠的是一根接力棒沿着一队
专才往下传：意图 → 路线（高德）→ 机票 → 去机场的车（滴滴）→ 酒店（携程）。每一棒读一下
接力棒，干自己那一件事，再往上添。

这不是树（那是层级委派），也不是并排的副本（那是扇出聚合），是一条线。它全部的风险都在
每一棒之间的**接缝**上。如果路线那一棒忘了把出发时限交下去，订车那一棒就会叫一辆赶不上
飞机的车，而你要到机场才发现，离出错的地方已经隔了三棒，根因也追不回来了。

## 模式

两个命名工具（来自讲稿）。

**接力棒规约** —— 每一棒都声明它从接力棒上 `requires`（需要什么）、`provides`（交付
什么）。链在每个接缝上都校验这两样。一棒收到的接力棒缺了它要的东西，或者一棒没交出它
答应的东西，都会当场失败，**就在丢东西的那个接缝上**，还带着那一棒的名字，而不是拖到三棒
之后根因已丢的地方。

**棒上不回改** —— 意图设一次、全程不变，已锁的事实一旦设定就锁死。后面的棒只能添，不能
悄悄覆盖。交接传的是值，不是一块共享的可变草稿纸，所以一棒改不动另一棒已经提交的东西。

两条都编在 `pattern.py` 里，链一断就抛一个点名到那一棒的 `SeamError`，改一处就行，不用
满链去找。

## 两套可运行实现

同一个模式、同一份 `pattern.py` 契约，两种把这条线跑起来的方式。

| | [`langgraph/`](langgraph/tutorial.ipynb) | [`claude-agent-sdk/`](claude-agent-sdk/tutorial.ipynb) |
|---|---|---|
| **链** | 一张线性 `StateGraph`：`意图 → 路线 → 机票 → 车 → 酒店` | 一个 Python 序列，每一棒跑一个子代理 |
| **接力棒** | 图里累积的 state | 一个 JSON 接力棒，一棒棒手手相传 |
| **接缝校验** | 一个 `guarded` 节点包装，复用 `StageSpec` / `SeamError` | 同一套 `HandoffChain` 校验，在 Python 里 |
| **模型** | provider 无关（`model_config`）| Claude 原生（每棒一个 `haiku` 专才）|

这里没有并行，所以不需要 reducer，链就是一条直线。两边的契约完全一致。

## 文件

| 文件 | 内容 |
|---|---|
| [`pattern.py`](pattern.py) | 框架无关参照（约 140 行）：`Baton`、`StageSpec`、`SeamError`、`HandoffChain`、`trip_chain`。可插拔的 `StageFn` 是两套 tutorial 各自填的接缝。 |
| [`example.py`](example.py) | 用 mock 各棒跑出行程链，无需 API key。演示一次干净的传递，以及一个丢了的交接如何在出错那一棒当场失败。 |
| [`test_pattern.py`](test_pattern.py) | 8 个测试：累积+顺序、缺 require 的接缝错、棒上不回改、没交付的检查、意图全程不变。 |
| [`langgraph/tutorial.ipynb`](langgraph/tutorial.ipynb) | 一步步：累积 State → `guarded` 接缝包装 → 线性图 → 断链在接缝上当场失败。 |
| [`claude-agent-sdk/tutorial.ipynb`](claude-agent-sdk/tutorial.ipynb) | 一步步：每棒一个 `AgentDefinition` → Python 里的 `HandoffChain` 契约 → 真跑的 `query()` 链。 |

## 运行

```bash
# 框架无关的核心 —— 无需 API key
python collaboration/d-handoff-chain/example.py
pytest collaboration/d-handoff-chain/test_pattern.py -v

# 两套实现需要模型 —— 见 .env.example
```

## 它在双轴里的位置

协作（认知功能）× 链式（执行拓扑）。同模块的邻居：层级委派（一棵树）、扇出聚合（并排的
副本）、对抗评审（一个循环）。交接链是那条线，最简单的拓扑，也是风险全在关节处的那个。见
[双轴矩阵](../../README.zh-CN.md)。
