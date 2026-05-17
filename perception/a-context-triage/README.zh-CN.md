# a · 上下文分诊（Context Triage）

> 专栏第 **02-02** 讲 · 模式 · 感知行 × 路由列
>
> [English README](README.md)

## 解决的问题

候选 context 信息加起来超出模型窗口时，必须取舍。挑错了，agent 会默默看错东西。
典型翻车场景：一个银行贷款评审 agent 按文件名排序留前砍后，结果丢掉了 2024 年
的抵押物估值评估，留下了 2019 年早就过期的工商登记，给出"建议批准"。Bug 不在
推理，agent 根本没**看到**那份关键文件。

## 模式本体

把候选信息分成四级，按优先级从高往低塞，错误堆栈永不丢。

| 级别 | 装什么 | 加载策略 |
|---|---|---|
| **P0 CRITICAL** | system prompt、安全规则、租户身份、当前任务 | 永远加载 |
| **P1 IMPORTANT** | 当前文件、最近 tool 结果、错误堆栈 | 预算允许就装 |
| **P2 SUPPORTING** | 历史对话、背景文档 | 预算允许就装，可压缩 |
| **P3 DEFERRABLE** | 知识库、档案、runbook | 不预加载，通过 tool handle 按需取 |

一条贯穿所有层级的不变量：**错误堆栈永远不能被丢弃**。

这个模式就是操作系统的优先级调度器换了身衣服。P0 是实时进程队列，P3 是被换出
等待页错的虚拟内存页。

## 快速跑通

```bash
python perception/a-context-triage/example.py
pytest perception/a-context-triage/
```

`example.py` 的预期输出会展示被选中的项、被延迟到 P3 handle 的项，并验证两条
不变量 —— 错误堆栈保留、P3 不预加载。

## 文件清单

| 文件 | 说明 |
|---|---|
| `pattern.py` | `ContextTriage` 类，约 90 行，零依赖 |
| `example.py` | 多租户 SaaS 场景，12 个候选项，8K 预算 |
| `test_pattern.py` | 7 条不变量测试 |

## 工程引用（已核对）

* Aider 的 `RepoMap`：[`aider/aider/repomap.py`](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)
  —— 自动符号抽取 + PageRank 一类排序，跟 Claude Code 的 CLAUDE.md 一道处于
  "人工 vs 算法"两端
* Anthropic Claude Code memory hierarchy：[Best Practices · Memory](https://docs.claude.com/en/docs/claude-code/memory)
  —— 四级层级（Enterprise / User / Project / Local）+ `@import` 按需挂载，
  常被引用的"CLAUDE.md 200 行甜点区"出处也在这里
* DeerFlow 的 schema 化分诊：[bytedance/deer-flow](https://github.com/bytedance/deer-flow)
  —— 把 `tenant_id`、`user_id`、`project_id` 做成强制 schema 字段而非可选
  元数据
* Manus 那个 487-token 连接池耗尽堆栈被压成 "a database error occurred"
  的真实事故，原文在
  [Manus 的 Context Engineering 博客](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)

## 什么时候不该用这个模式

如果你的任务全部材料确定不超过 50K token —— 窄场景 chatbot、单文档摘要 ——
直接全塞 prompt。分诊会带来工程成本，要等你撞上窗口才有回本可能。
