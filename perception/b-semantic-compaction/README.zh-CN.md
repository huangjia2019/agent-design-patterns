# b · 语义压缩（Semantic Compaction）

> 专栏第 **02-03** 讲 · 模式 · 感知行 × 串行列
>
> [English README](README.md)

## 解决的问题

Agent 跑得足够久之后，分诊也救不了，候选集装不下，必须压。简单粗暴的摘要会
丢掉一个绝对不能丢的信号：agent **已经排除过哪些方案**。典型翻车场景：一段
487-token 的连接池耗尽堆栈被压成 "a database error occurred"，agent 接下来
三小时反复重试已经被排除过的方案。

## 模式本体

三层级联，按顺序触发，第一层达成预算就停：

| 级别 | 做什么 | 什么时候 |
|---|---|---|
| **L1 清理工具输出** | 把长 tool 输出替换为占位符 | 先试 |
| **L2 折叠到 anchor** | 把老 turns 摘要并合并到 5 字段 anchor（intent / changes / decisions / **excluded approaches** / next steps）| L1 不够时 |
| **L3 错误归档** | 只完整保留最近 3 个错误堆栈，其余压成 "do not retry" 清单 | 最后手段 |

两条不能动的不变量：

* **错误堆栈永远不丢**。它是 agent 的反馈回路，丢了 agent 就瞎了
* **excluded approaches 跨所有层级保留**。这是终结 "agent 反复试已排除方案"
  这个失败模式的关键字段

触发阈值用 60% 窗口容量，不是 95%。质量退化早在窗口装满之前就开始了，95%
社区默认值等于"在 agent 已经变笨之后再压"。

## 快速跑通

```bash
python perception/b-semantic-compaction/example.py
pytest perception/b-semantic-compaction/
```

Demo 模拟一个 30 轮的调试会话，跑压缩，打印结果 anchor。你能看到三个已排除
方案（cache warming / retry-with-backoff / query rewriting）虽然 27 轮普通
对话全被折叠，但仍保留在 `EXCLUDED (do not retry):` 段里。

## 文件清单

| 文件 | 说明 |
|---|---|
| `pattern.py` | `SemanticCompactor` + `CompactionAnchor` + `Turn` + `CompactionEvent`，约 220 行 |
| `example.py` | 调试会话 demo，用确定性 stub LLM，无需 API key 也能跑 |
| `test_pattern.py` | 8 条不变量测试，含 L1 → L2 → L3 级联行为 |

## 工程引用（已核对）

* OpenHands 的可配置 condenser：[`openhands/core/config/condenser_config.py`](https://github.com/All-Hands-AI/OpenHands/blob/main/openhands/core/config/condenser_config.py)
  —— 5 种内置 condenser（NoOp / RecentEvents / LLMSummarizing /
  ObservationMasking / AmortizedForgetting）。V0 文件标了 legacy，V1 在
  [software-agent-sdk](https://github.com/OpenHands/software-agent-sdk)
* Aider 的 49 行递归对半切：[`aider/history.py`](https://github.com/Aider-AI/aider/blob/main/aider/history.py)
  —— depth cap 5 + multi-model fallback
* Anthropic Claude Code compaction 参考：[Best Practices · Context management](https://docs.claude.com/en/docs/claude-code/best-practices)
  —— 默认 95% 自动触发；社区共识更常落在 55-70%
* Manus 那段 487-token 连接池耗尽堆栈被压成 "a database error occurred"
  的真实事故，原文在 [Manus 的 Context Engineering 博客](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

## 什么时候不该用这个模式

如果你的 session 很短（单轮 Q&A、固定 pipeline 的 ETL）或者 tool 输出很短
（百字节级 API 响应），调用 anchor LLM 的成本会超过省下的 token。等总 token
撞到预算 60% 再压。
