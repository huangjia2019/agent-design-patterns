# a · Tool Dispatch · 工具调度

> 专栏第 **05-02** 讲 · pattern · 行动 × 路由
>
> [English README](README.md)

## 故事

一家中型物流公司的城配 Agent，接入 17 个 tool：`query_orders` /
`query_drivers` / `query_traffic` / `get_eta` / `assign_driver` /
`unassign_driver` / `notify_customer` / `reroute` /
`consolidate_orders` / `split_order` ... 团队把所有 tool 全开放给 LLM
自由选。

周一上午 10 点。80 个周末积压订单进队列。Agent 开始跑 5 分钟后——
**80 单全部分给同一个司机 `driver_007`**，那位司机当时正堵在长安街。

复盘 Agent 的 trace。它调 `query_drivers`，拿到 12 个 available 司机，
挑了评分最高的 driver_007（4.9 星），派第一单成功，告诉自己"看来
driver_007 状态好，继续派"，然后 79 次 `assign_driver(order_N,
driver_007)` 跑下去，**全程没有再 query 状态**。Dispatcher 对这一切
没有任何意见。

团队复盘出三个根因：

1. **Tool 选择错**。Agent 直接进派单逻辑，没用 `consolidate_orders`
   合单也没用 `query_traffic` 看路况。
2. **参数过期**。司机的 `available` flag 第一单后翻成 false，但 agent
   再也没刷新。
3. **副作用累积**。80 次写操作没有 quota / 没有 inverse / 没有 audit；
   回滚是 90 分钟手工清理。

讲义的判断：**LLM 擅长 *用* 工具（填参数、解结果），不擅长 *选* 工具**。
选工具是 harness 责任。这个 pattern 的 dispatcher 就是这条责任的代码
化身。

## 模式骨架

三个类，一个 contract：

| 类 | 角色 |
|---|---|
| `ToolMetadata` | 一个 tool 的 typed contract。Claude Code 14 字段 schema 精简到 dispatcher 关心的 10 字段：身份、用途、互斥、5 个执行标志（read-only / concurrency-safe / destructive / requires-fresh-state / requires-approval）、quota、rollback action |
| `DispatchTrace` | 单次调用的 audit 记录。Status `success` / `failed` / `rejected`。`rejected` 必带 *原因*——`tool_hallucination` / `quota_exceeded` / `stale_state_must_refresh` / `awaiting_approval` |
| `ToolDispatcher` | runtime。注册 tool，每次调用强制 contract，维护 saga log，反向 rollback |

5 个不可妥协的执行点。**第一条是铁律**：

| 点 | 做什么 |
|---|---|
| 默认不安全 | `is_read_only` 和 `is_concurrency_safe` 默认 `False`。沉默 = 破坏性。Tool 实现者忘记声明，dispatcher 保守处理。这一行代码价值千金 |
| `quota_per_session` | 每 session × tool × 主参数 N 次上限。开篇 80 单到一个司机的守卫 |
| `requires_fresh_state` | session 在 `STATE_FRESHNESS_SECONDS` 内没读过就阻断写。读成功自动刷新 timestamp |
| `requires_approval` | 短路执行返回 `awaiting_approval`。交接给 Approval Gate pattern |
| `rollback_action` | 注册 saga 反向动作。**没声明 rollback 的 destructive tool 注册不进来**（直接抛 `ToolDispatchError`） |

两条注册期的守卫：

* destructive 但没 rollback_action 的 tool **拒绝注册**
* 同时 `is_read_only=True` 和 `is_destructive=True` 的 tool **拒绝注册**

## 跑起来

```bash
python action/a-tool-dispatch/example.py
pytest action/a-tool-dispatch/
```

demo 复刻城配故事。Agent 试着把 8 单全派给 driver_007。前 5 单成功，
后 3 单 `quota_exceeded` 拒绝。一个 Agent 编造的 tool name 被
`tool_hallucination` 拒绝。新司机的写操作因为 session 没刷状态被
`stale_state_must_refresh` 拒绝。Saga rollback 反向 unwind 已 commit
的 5 单。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `RiskLevel` + `ToolMetadata` + `DispatchTrace` + `ToolDispatcher` + `ToolDispatchError`（~230 行） |
| `example.py` | 城配场景，完整复刻讲义开篇 |
| `test_pattern.py` | 18 条不变式：注册守卫 / quota scoping（按 session × tool × 主参数）/ state-freshness 窗口 / 审批短路 / 幻觉拒绝 / saga rollback 反向顺序 / 跨 session 隔离 / trace 记录 |

## 工程引用（都核过源码）

* **Claude Code** [`Tool.ts:386-456`](https://docs.claude.com/en/docs/claude-code/)
  —— 14 字段 tool metadata schema。Pattern 用了其中 10 个；剩下 4
  个（`aliases` / `prompt` / `interruptBehavior` / `shouldDefer`）
  是 UI / progressive-disclosure 议题，不改 dispatcher contract。
* **Anthropic** [*Programmatic Tool Calling*](https://platform.claude.com/docs/en/agents-and-tools/tool-use/programmatic-tool-calling)
  —— 讲义里讲的 "工程层主导 dispatch"。参考实现两条路都支持：
  `triggered_by="llm"` 自由选 / `triggered_by="programmatic"`
  工程师定义序列。Contract 一样，只是 caller 不同。
* **Codex CLI** `execpolicy` Rust crate —— 进程外的 policy engine。
  参考实现把 policy 嵌在 dispatcher 里；生产部署通常分离到独立
  binary 做 tamper resistance。
* **arxiv:2602.14878** [*MCP Tool Descriptions Are Smelly*](https://arxiv.org/html/2602.14878v1)
  —— 实测给 tool description 加 selection guidance 提升 15-25pp
  准确率。`when_to_use` / `when_not_to_use` 字段就是为这个存在的。
* **OWASP Top 10 for Agentic Applications (2026)** A2 *Tool Misuse*
  —— 给这个 pattern 的失败模式命名，并给出工业数据：88% 组织过去
  一年至少出过一次 agent 相关安全事故。
* **Manus** —— Yichao Peak Ji 的 *Context Engineering for AI Agents*：
  **32 个工具是上限**，超过 LLM 选择准确率断崖下跌。讲义引 GitHub
  Copilot 从 40 砍到 13、Block 把 Linear MCP server 从 30+ 砍到 2 作
  为佐证。

## 什么时候不要用

* **只有 1-2 个 tool 的 agent**。Dispatcher 整套是 overhead，直接函数
  调用就行。
* **纯对话 agent**。没有外部 tool 也就没有 dispatch。
* **全只读 tool 集**。Risk 表面小，quota / rollback 是 theatre。一个
  简单 registry 够用。

Dispatcher 的价值集中在 **tool 多 + 副作用多 + 错调代价大** 三件叠加
的场景。任何一件不占都是过度工程。

## 诚实承认的局限

默认 quota key 是 `(session, tool, 第一个参数)`。这个形态贴合"不要
80 单全给 driver_007"，但对主资源不在第一个参数位置的 tool 会失准。
要么 override `_quota_key`，要么传入 canonicalized 的主参数。

State freshness 这里是 timestamp-based 且 per-session 全局。真实部署
经常需要 per-resource freshness（"driver_007 的状态必须重读，driver_012
的旧读还行"）。简单形态太粗的话，包一层 per-key 版本号。

Saga log 在内存里。生产需要持久化存储，崩溃后能 replay inverse chain。
Contract（destructive 成功后记 inverse，rollback 反向跑）不变，只换
存储介质。
