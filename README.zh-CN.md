# Agent 设计模式之美 · 配套代码

> 黄佳老师极客时间专栏《Agent 设计模式之美》和 Manning 书 *Designing AI Agents*
> 的配套代码。每个文件夹对应一讲，每个模式都附带一份最小可跑的 Python
> 参考实现和一份 README，你不用离开 GitHub 就能读懂这个模式。

[English README](README.md)

---

## 这个仓库是干什么的

生产环境的 agent 在"接缝"处翻车。所谓接缝，就是一项能力交给另一项能力的地方。
这些接缝里大部分都是软件工程几十年来研究透了的老问题：操作系统的优先级调度、
惰性加载、虚拟内存、事件驱动控制循环。Agent 设计模式之美这个项目，是给这些
接缝命名，给每个接缝一份小而诚实的参考实现。

模式按双轴组织：

* **认知功能**：agent 在做什么（感知 / 记忆 / 推理 / 行动 / 反思 / 协作 / 治理）
* **执行拓扑**：runtime 是怎么编排的（单步 / 串行 / 并行 / 循环 / 路由 / 分层）

矩阵共 7 × 6 = 42 格。大部分格子单独看没意思，27 个有意思的就是你在这里看到的
模式。

## 目录结构

```
perception/       # 感知模块（第 02 章）
  a-context-triage/
  b-semantic-compaction/
  c-progressive-discovery/
  d-multimodal-fusion/

memory/           # 记忆模块（第 03 章）        — 待补
collaboration/    # 协作模块（第 04 章）        — 待补
composition/      # 模式组合（第 05 章）        — 待补
```

字母前缀 `a-`、`b-`... 反映模式在专栏里出现的顺序，不代表依赖关系。每个模式
文件夹都是自包含的。

## 快速开始

```bash
git clone https://github.com/<你的用户名>/agent-design-patterns.git
cd agent-design-patterns
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# 跑第一个模式的示例
python perception/a-context-triage/example.py

# 或者跑完整测试套件
pytest
```

每个模式文件夹自己也有 `README.md`，一屏可读完的 quickstart。

## 目前已收录的模式

| 文件夹 | 模式 | 对应专栏讲次 | 状态 |
|---|---|---|---|
| `perception/a-context-triage` | 上下文分诊（P0/P1/P2/P3 优先级调度）| 02-02 | 可跑 |
| `perception/b-semantic-compaction` | 语义压缩（锚定式迭代摘要）| 02-03 | 可跑 |
| `perception/c-progressive-discovery` | 渐进发现（agentic search）| 02-04 | 占位 |
| `perception/d-multimodal-fusion` | 多模态融合 | 02-05 | 占位 |

## 怎么读一个模式文件夹

每个模式文件夹结构都一样：

```
README.md / README.zh-CN.md   # 故事：这个模式为什么存在
pattern.py                    # 最小诚实参考实现
example.py                    # 在拟真数据上跑通的演示
test_pattern.py               # pytest：模式承诺的不变量
```

先读 README 理解问题。再读 `pattern.py` 看用最少的代码怎么解。跑 `example.py`
看它在拟真数据上是什么样。测试钉死了你在自己项目里改造时不该破坏的不变量。

## 工程引用与可验证性

专栏或 README 里引用其他开源框架的文件（如 Aider 的 `repomap.py`、OpenHands 的
`condenser_config.py`），引用的都是上游真实存在的文件和路径。如果你发现引用跟
上游代码对不上，请提 issue，这是 bug 不是文档选择。

## 状态说明

这是一个教学仓库。API 故意做得小而不稳定，目标是清晰而不是被采用为框架。需要
生产 runtime 请用专栏剖析的那些 harness（Claude Code、Aider、OpenHands、
DeepAgents 等）。想搞懂这些 harness 在做什么，把这个仓库跟专栏一起读。

## 许可证

MIT。见 [LICENSE](LICENSE)。
