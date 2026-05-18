# d · Failure Journals · 失败日记

> 专栏第 **03-05** 讲 · pattern · 记忆 × 循环
>
> [English README](README.md)

## 故事

两周前，Claude Code 帮我修 `auth-service` 一个 302 跳转死循环。它把
bug 修对了。在改 OAuth 配置时，它顺手把*测试环境*的 `client_id`
写进了 `config/prod/oauth.yaml`。Pre-deploy 阶段的 diff review 抓回来。

两周后，另一个 Claude Code 实例去修 `billing-service` 一个完全无关的
OAuth refresh bug。它也把 bug 修对了。改 OAuth 配置时，它又把一个测试
`client_id` 写进了 `config/prod/oauth.yaml`。这次 staging 部署后才被
抓到。

**模型并没有第二次变笨**，模型完全一样。缺的是第一次事故的"日记"——
一条结构化记录写着："两周前你在这类任务上做过这件事；改任何 prod
config 之前先回看一下。"没有任何机制写过这条记录。

这就是**可观测性**（事后到 Sentry 搜得到）和**召回**（agent 在动手
*之前*把教训读一遍）之间的缝。Failure Journals 这一讲专门来补这条缝。

## 模式骨架

四个阶段，借 [arxiv:2509.25370 (Where LLM Agents Fail)](https://arxiv.org/abs/2509.25370) 的提法：

```
检测 → 分类 → 记录 → 召回
```

绝大多数团队停在第三步。第四步才是让日志变经验的那一步。

一条记录的 schema：

| 字段 | 例子 | 为什么要 schema 化 |
|---|---|---|
| `failure_id` | `eec56c352a1e` | 稳定 hash · 重试时不会重复入库 |
| `task_signature` | "fix oauth callback bug in auth-service; touch config/oauth.yaml" | 召回时用来匹配的 key |
| `category` | `BOUNDARY_LEAK` | 10 个枚举类 · 便于聚类/过滤/分级保留 |
| `summary` | "Test client_id 'test-acme-3489' written to config/prod/oauth.yaml" | 一行 · 上限 200 字符 |
| `root_cause` | `RuntimeError` | 异常类或一句话根因 |
| `lessons` | ["always re-read env header", "diff unrelated config changes"] | 下次任务来时要回灌到 prompt 的可执行教训 |
| `access_count` | `3` | 被召回过几次 · 这是"配得到保留"的依据 |

10 个失败大类是 [Hermes Agent 的 13 种 `FailoverReason`](https://github.com/openhermes/agent)
（auth/billing/rate_limit/overloaded/server_error/timeout/...）的浓缩，加上
agent 时代独有的 3 个：

* `SEMANTIC_DRIFT` —— agent 偏离用户原任务
* `BOUNDARY_LEAK` —— config/env/tenant 越界（开篇故事就是这一类）
* `INDEX_LAG` —— Boris Cherny 视角的新失败类型：数据在磁盘上但索引
  还没追上

其中两类 `BOUNDARY_LEAK` 和 `PERMISSION_DENY` 是**高风险**。日记不
驱逐它们，而且每次召回都**强制带出来**，不管相似度。它们是"永远不
能忘"的那种失败。

## 跑起来

```bash
python memory/d-failure-journals/example.py
pytest memory/d-failure-journals/
```

example.py 复刻开篇那个 OAuth 故事：两周间隔的两次 session，第二次
session 在动 config 之前调一次 `recall_for_task`，第一次的日记自动注
入到 prompt 里，agent 在动手前先把教训读一遍。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `FailureCategory` + `FailureEntry` + `FailureJournal`（~240 行） |
| `example.py` | 两次 session 的 OAuth 故事 · 复刻讲义开篇 |
| `test_pattern.py` | 15 条不变式：稳定 id / 分类 / 召回排序 / top_k / 高风险强制召回 / 驱逐保护 / render 格式 / 健康报告 |

## Manus 那条铁律

引自 [Yichao Peak Ji 的 *Context Engineering for AI Agents* 一文](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)：

> "When the model sees a failed action and the resulting observation
> or stack trace, it implicitly updates its internal beliefs, shifting
> its prior away from similar actions and reducing the chance of
> repeating the same mistake. Erasing failure removes evidence, and
> without evidence, the model can't adapt."

一句话：**抹掉失败就是抹掉证据，没有证据模型没法学**。这就是这个模式
存在的工程依据。日记不是 audit log，是模型召回时需要的那份"证据"。

## 工程引用（都核过源码）

* **Hermes Agent** [`agent/error_classifier.py`](https://github.com/openhermes/agent) ——
  13 种 `FailoverReason` 枚举 + `trajectory_compressor.py` 把完整 agent
  trajectory（含失败）压缩存档喂回训练。当前工业界最接近这个模式完整
  实现的代码。
* **Aider** [`aider/coders/base_coder.py`](https://github.com/Aider-AI/aider/blob/main/aider/coders/base_coder.py)
  —— `max_reflections=3` + `reflected_message` 字段 · 任务内自愈循环。
  Failure Journals 等于 Aider 把 `reflected_message` 持久化到下次会话。
* **Manus** [*Context Engineering for AI Agents*](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)
  —— "don't hide errors from the model" 这条铁律的出处。
* **arxiv:2603.21357 (AgentHER)** —— *Hindsight Experience Replay for
  LLM Agents.* 训练侧对应：失败的 trajectory 重新标注为新任务下的成功
  样本，85% 的失败 trajectory 可被复用。
* **arxiv:2506.06698 (CER)** —— *Contextual Experience Replay.*
  推理侧对应：把召回的过往经验注入到 prompt。这个模式是 CER 的最小实现。
* **arxiv:2509.25370 (Where LLM Agents Fail)** —— 四阶段框架的论文出处。
* **NeuralWired (2026)** [*Why AI Agents Fail in Production*](https://neuralwired.com/2026/04/28/why-ai-agents-fail-production/)
  —— 48h/30d/90d 分层保留的工程建议，`_evict_if_needed` 是它的单层简化。
* **Mem0 (2026)** [*State of AI Agent Memory*](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
  —— procedural-memory 召回率指标，`health_report()` 暴露的就是这个。

## 什么时候不要用这个模式

* **一次性脚本/原型。** 没有"下次 session"可以召回，没法回本。
* **严格无 PII 存储策略的 agent。** task_signature 里如果有租户信息，
  入库前要脱敏或 hash，或者只存 category + count 的 aggregate。
* **纯聊天 agent。** 没有动作没有外部后果，日记会塞满"模型说话不
  得体"这种没人去处理的噪声。

这个模式的价值集中在**长期运行的、会动配置/工具/租户数据的生产 agent**。
开篇那个故事就发生在这种场景里。

## 老实承认的简化

参考实现是"最小诚实版本"。上生产前要补：

* **embedding 相似度。** 默认 `_jaccard_similarity` 是词集合重合度，
  生产里换 `text-embedding-3-small` 或 `bge-base` 的 cosine。
* **持久化。** 现在是内存 dict，换 sqlite/postgres，API 不变。
* **写入审查。** 让 agent 提交 entry，但校验 `category` 枚举、`summary`
  长度上限、`lessons` 必须可执行才入库。
* **分层保留。** 48h 热 / 30d 温 / 90d+ 冷各上一套 backend。

这些是部署层的工程问题，不是模式层的事情。模式层的合同是"四阶段 +
schema"，其它都是水电管路。
