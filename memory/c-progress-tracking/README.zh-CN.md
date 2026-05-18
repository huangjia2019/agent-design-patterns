# c · 进度追踪（Progress Tracking）

> 专栏第 **03-04** 讲 · 模式 · 记忆行 × 交接列
>
> [English README](README.md)

## 解决的问题

Agent 接到任务：把一个 600 行的 Python 模块拆成 4 个文件 + 测试，保留兼容
API。它先写好了清晰的 plan，迁移完文件 1-3，然后在 `parsers.py` 撞到 bug，
花了 20 轮 debug。debug 完之后它去写测试、跑 CI，然后报告"完成"。

跑测试，失败。**第 4 个文件根本没建**。Agent 在 debug 那段把它忘了。指出之后，
agent 愣 3 秒说"你说得对，我忽略了"。

LLM 没有真正的工作记忆。它"记得"的全部活在 context window 里，而 context
window 是 U 形 attention——中间段会被淹没。一段 20 轮的 debug 打野把原 plan 埋了。

修复方案非常工程化、非常笨：强制 agent 维护一份结构化的 todo list，外部化到
对话流里，对话偏题时反复 nudge 它回去看自己的清单。

## 模式本体

照搬 Claude Code 的三字段 `TodoWrite`：

| 字段 | 例子 | 用途 |
|---|---|---|
| `content` | "Fix cache invalidation bug" | 任务祈使式 |
| `active_form` | "Fixing cache invalidation bug" | 进行中显示用 |
| `status` | `pending` / `in_progress` / `completed` / `needs_review` | 动态字段，防失忆的关键 |

三条不变量：

* **同一时刻最多一个 `in_progress`。** 启动新项会把现有的 in-progress 弹回
  pending。强制 agent 要么完成一件事要么显式 defer
* **按 owner 隔离。** Sub-agent 有自己的清单，不污染父 agent 的 todos
* **完成自动清空。** 全部 completed 时清空清单。Claude Code 反直觉但必要的
  "完成即清空"行为——防止过期 plan 干扰下次会话

清单之上 `ProgressTracker` 监听最近消息流。当复杂度高（大量动作动词 + 序列词）
且没有 todos 时，注入**递进 nudge**——先是一句平和提醒，再是"你似乎偏题了"，
最后是"STOP"。

## 快速跑通

```bash
python memory/c-progress-tracking/example.py
pytest memory/c-progress-tracking/
```

Demo 重演 600 行重构事故：plan 写好、1-3 文件完成、24 轮 debug 打野、tracker
触发 context-loss nudge、agent 重读清单、找回被遗忘的第 4 个文件、全部完成、
清单自动清空。

## 文件清单

| 文件 | 说明 |
|---|---|
| `pattern.py` | `TodoItem` + `TodoList` + `ProgressTracker` + `TodoStatus`，约 170 行 |
| `example.py` | 重构场景复现讲座开篇事故 |
| `test_pattern.py` | 14 条不变量：稳定 id、单 in-progress、render 规则、all_done、auto-evict、context-loss 检测、递进 nudge、owner 隔离 |

## 工程引用（已核对）

* **Claude Code** `TodoWrite` 工具——三字段 `content` / `activeForm` /
  `status`，"已经启动 todo 系统就要完成并清空"的提示写在 prompt 里
* **DeepAgents** `TodoListMiddleware`——`create_deep_agent` 默认 stack 的
  第一个 middleware，位于
  [`libs/deepagents/deepagents/middleware/`](https://github.com/langchain-ai/deepagents)
* **DeerFlow** `TodoMiddleware`——加了**context-loss detection**，用最近消息
  复杂度评分 + 递进 nudge；本仓库 `context_loss_detected()` 的灵感来源
* **Codex CLI** `update_plan` 工具——同一思路的单清单实现
* **Anthropic Effective Context Engineering**——U 形 attention 的观察，是这个
  模式的根本动机

## 什么时候不该用这个模式

* **短任务。** 3 步以内不需要 TodoWrite，overhead 比收益大
* **纯对话。** 没工具调用、没多步 plan，todo 就是噪声
* **单次 Q&A。** 一问一答，肯定不要用

Claude Code 自己的 prompt 列了 4 个 don't-use 场景。该用不用是欠工程，不该
用硬用是过度工程。
