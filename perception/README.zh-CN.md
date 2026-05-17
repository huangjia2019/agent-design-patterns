# 感知模块（Perception）

> 专栏第 **02 章 · 感知世界之美** · 双轴矩阵里的认知功能行
>
> [English README](README.md)

## 这个模块讲什么

感知是 agent 栈里第一个认知功能，也是生产 agent 最容易翻车的一层。本模块
四个模式合起来回答一个问题：agent 看到什么、按什么顺序、付多少代价？

| 文件夹 | 模式 | 执行拓扑 | 对应讲次 |
|---|---|---|---|
| `a-context-triage` | 上下文分诊：按优先级排，砍掉其余 | Router | 02-02 |
| `b-semantic-compaction` | 语义压缩：锚定式迭代摘要 | Sequential | 02-03 |
| `c-progressive-discovery` | 渐进发现：agentic search | Loop | 02-04（占位）|
| `d-multimodal-fusion` | 多模态融合：图 / 表 / 文 | Parallel | 02-05（占位）|

四个模式坐落在同一行（感知）的四个不同执行拓扑格子上。这是专栏双轴框架的
设计点：同一个认知功能在不同 runtime 拓扑下会催生不同模式。

## 怎么读这个模块

先读 `a-context-triage`。它是最简单的模式，每个生产 agent 早晚都会撞上，
也是后面三个模式的地基。再读 `b-semantic-compaction`：它接的是 Triage
预算耗尽之后的故事。`c` 和 `d` 把故事延伸到 "压根不知道该读什么"（渐进发现）
和 "输入不是文字"（多模态融合）。

## 整模块跑一遍

```bash
# 从仓库根目录
python perception/a-context-triage/example.py
python perception/b-semantic-compaction/example.py
pytest perception/
```

## 签名级洞见

感知不是"给模型喂更多上下文"。感知是**不确定性下的预算分配**问题，跟操作系统
调度器从 1970 年代就在解的是同一件事：优先级队列、虚拟内存、惰性加载。本模块
四个模式都是这个观察在 LLM 基底上的重述。
