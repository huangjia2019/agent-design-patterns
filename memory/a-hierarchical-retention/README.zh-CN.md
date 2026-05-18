# a · 分层保留（Hierarchical Retention）

> 专栏第 **03-02** 讲 · 模式 · 记忆行 × 路由列
>
> [English README](README.md)

## 解决的问题

一家在线 Python 学校做了个编程教练 agent。第一周 agent 无状态，学生第三次回来
agent 还在问"你学过 list 吗？"—— 前两次明明已经学了。

工程团队加了 chat-history 字段，把过往会话全部塞进 prompt。第五次会话时 prompt
已经是 30K token 的无关历史，agent 反而忘了当下在做什么。学生反馈："以前它什么
都不记得，现在它什么都记得，但分不清重点。"

Agent 的记忆不是一件事。用户的 Python 水平（几个月才变一次）跟项目的技术栈
（每项目不同）跟当前会话的主题（每次会话变）跟刚定义的辅助函数（每轮工具调用
变）—— 四件事**作用域完全不同**。一股脑塞进一个 prompt 要么 token 爆掉，要么
信号被噪声埋掉。

## 模式本体

四层，从粗到细，每层独立的 backend / TTL / token 预算。键冲突时内层覆盖外层；
从最细层向外读，这条路由方式就是这个模式坐落在矩阵 "路由列" 的原因。

| 层 | 作用域 | 典型 backend | TTL | Token 预算 |
|---|---|---|---|---:|
| **USER** | 跨所有 session、所有 project | postgres | 永久 | 2,000 |
| **PROJECT** | 单 project、跨 session | file | 永久 | 4,000 |
| **SESSION** | 单次会话 | redis | 24h | 8,000 |
| **TURN** | 单轮工具调用 | in-process | 5 分钟 | 2,000 |

两条不变量：

* **从内层读。** SESSION 层的 `preference` 覆盖 USER 层的 `preference`——但
  不**改写** USER 层。覆盖是上下文意义上的，不是销毁意义上的。
* **从外层组装。** 拼 prompt 时按 USER → PROJECT → SESSION → TURN 渲染，让
  模型从粗到细读，匹配人类吸收层级化信息的顺序。

## 快速跑通

```bash
python memory/a-hierarchical-retention/example.py
pytest memory/a-hierarchical-retention/
```

Demo 模拟 Alice 在 Python 学校的第 4 次会话：USER 画像从 postgres 载入，PROJECT
从 file backend 载入，SESSION 从 redis 还原，TURN 启动时为空。看到覆盖语义生效
+ TURN 到 TTL 后自动过期。

## 文件清单

| 文件 | 说明 |
|---|---|
| `pattern.py` | `HierarchicalRetention` + `Layer` + `MemoryLayer`，约 150 行 |
| `example.py` | 编程教练场景，Alice 的第 4 次会话 |
| `test_pattern.py` | 10 条不变量：分层读写、内层覆盖外层、TTL 过期、evict_expired、组装顺序、health report、自定义配置 |

## 工程引用（已核对）

* **Claude Code** 的 memory hierarchy：4 级（Enterprise / User / Project /
  Local）+ `@import` 按需挂载，见 [Best Practices · Memory](https://docs.claude.com/en/docs/claude-code/memory)
* **MemGPT**（Packer et al. 2023，[arXiv:2310.08560](https://arxiv.org/abs/2310.08560)）
  —— 把 OS 虚拟内存 hot/warm/cold 分层搬到 LLM 上，是这条 OS-内存层级类比最早
  有影响力的表述
* **CoALA**（Sumers et al. 2024）—— 三层认知架构（working / episodic / semantic）。
  分层保留的 4 层在 CoALA 基础上更靠近生产 agent 的基础设施
* **Hermes Honcho** —— 两层切：persistent user model + ephemeral session context，
  是最小化的真实实现
* **Cline Memory Bank** —— 项目级文件持久化，对应这里的 PROJECT 层

## 什么时候不该用这个模式

* **单轮 agent。** 不需要 SESSION 或 TURN，USER + PROJECT 就够
* **单用户 agent。** 跳过 USER，PROJECT + SESSION 够用
* **冷启动 agent。** 按需跑、永不 resume 的 pipeline，一层就够
* **大规模 + 严格隐私场景。** 跨会话保留可能跟数据驻留规则冲突，启用 USER
  层前先跟隐私团队对齐
