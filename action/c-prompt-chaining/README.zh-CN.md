# c · Prompt Chaining · 提示链

> 专栏第 **05-04** 讲 · pattern · 行动 × 串行
>
> [English README](README.md)

## 故事

一家中型财经媒体的内容编辑 Agent。第一版把 7 件事写在一段 prompt 里
一次干完——校对错别字、改写句式、统一风格、核查数字、生成标题、写
摘要、给配图建议。一个 prompt，一次模型调用。

一周后出事了。一篇放出去的稿原稿写"GMV 增长 35%"，agent 改成了
"GMV 增长 53%"。3 和 5 两个数字它都看到了——但到第 4 步（数字核查）
时它已经不在看原稿了，它在看自己第 2 步改写后的版本，而改写已经把
数字写颠倒了。

修法不是写一个更聪明的 prompt，是**把 7 件事拆成 7 个独立 step**，
每步一个适合它的模型（Haiku 校对 / Sonnet 改写 / Opus + thinking 核查），
每两步之间挂一个**程序化 gate**（数字保留 / 长度范围 / 必填字段）。
**关键改动**：核查步骤明确读**原稿**，不读改写版本。数字准确率从
87% 飙到 99.4%，编辑信任度 42% → 91%。成本 +30%，延迟 12s → 38s，
在内容场景这账算得过来。

讲义的判断：**Prompt Chaining 是 Unix 管道在 LLM 上的复刻**。每步只
干一件事，两步之间挂便宜的 gate，按需选模型，让一步的错在污染下一步
之前就被挡住。

## 模式骨架

两个类 + 一组 gate 工厂函数：

| 构件 | 角色 |
|---|---|
| `ChainStep` | 一个 prompt step。带 `system_prompt` / `prompt_template` / `model` / 一个 `gate` callable / `max_retries`。模板用 user input + 所有 prior step 输出（按 `step_id` 索引）插值 |
| `PromptChain` | 顺序跑 step。把输出传给下一个，gate 失败时 bounded retry，每次 attempt 都进 `ChainTrace` |
| `length_gate` / `keys_gate` / `regex_gate` / `any_gate` / `all_gate` | gate 工厂函数。**Gate 是程序化检查，不是 LLM 调用**。如果你的 gate 要调 LLM，那它其实是另一个 step |

讲义命名的两个失败模式，pattern 分别解决：

| 失败模式 | 是什么 | 怎么解决 |
|---|---|---|
| **信息饥饿（information starvation）** | Step 3 要 Step 1 的数据，但 Step 2 没传过去 | 每个 step 都能按 id 拿到**所有** prior outputs，不只是上一步 |
| **闸门暴政（gate tyranny）** | Gate 卡太死（"刚好 500 词"），499 跟 501 都被拒，无限重试 | `max_retries` 是硬上限，失败 retry 记录 gate description 让运维知道松哪条 |

3 条值得记住的行为：

1. **Gate 失败 retry，LLM 错误 fail-fast**。Gate 没过会重提示直到
   `max_retries`，LLM 异常立即终止 step。不同异常不同处理。
2. **模板缺 key 不崩**。`{nonexistent}` 替换成 `[chain: missing
   template key: …]` 标记。Chain 继续跑到底，标记进 trace 让 debug
   pass 找到接错的线。**契约：暴露问题，不掩盖**。
3. **Step id 稳定**。它是 prior_outputs 的 key、模板的引用名、trace
   的 audit handle。**改名 = 破坏 chain**。

## 跑起来

```bash
python action/c-prompt-chaining/example.py
pytest action/c-prompt-chaining/
```

demo 跑 5 步编辑流水线：proofread → rewrite → style → factcheck →
title。factcheck 步显式同时引用**原稿 `user_input`** 和最近的
`style` 输出——所以开篇那个 bug（改写污染原稿后被 factcheck 当成
事实）**这里不可能发生**：factcheck 永远拿得到原稿。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `StepResult` + `ChainStep` + `StepRun` + `ChainTrace` + `PromptChain` + 5 个 gate 工厂（~200 行） |
| `example.py` | 5 步内容编辑流水线，复刻讲义开篇的修法 |
| `test_pattern.py` | 15 条不变式：每个 gate 工厂 / chain 构造守卫（空 / 重 id）/ 顺利路径 / 按 id 拿 prior outputs / gate 失败有 cap retry / retry 成功完成 / LLM 错误 fail-fast / 缺模板 key 不崩 / trace 记账 |

## 工程引用（都核过源码）

* **Aider** [`aider/history.py`](https://github.com/Aider-AI/aider/blob/main/aider/history.py)
  —— 49 行递归 summary chain。`depth=0` 是递归硬上限（防无限链），
  内部 `summarize_all` 自带 fallback-model chain，**partial summary
  是错误，不是返回值**。这个 pattern 的最小诚实形态。
* **Claude Code** PRA loop —— Read / Grep / Edit / Bash 每次返回都
  是下一步 reasoning 的输入。这个 loop 是**隐式** prompt chain，
  把它显式化（加 gate）就是这个 pattern。Slash command `/commit` /
  `/review` 是 pre-built chain。
* **Claude Code Skills** —— 声明式 chain 段。`.claude/skills/` 下
  `SKILL.md` 是 model 按需组合的 chain 段。同 pattern 不同 surface。
* **Anthropic** [*Building Effective
  Agents*](https://www.anthropic.com/research/building-effective-agents)
  —— prompt chaining 列为最简单也最被低估的 agent pattern。参考形态
  "数量不多但定义清楚的 step + 步骤间 gate"。
* **Anthropic** [*Prompt engineering best
  practices*](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
  —— 每个 step 的 prompt 用 5 段 XML 结构（role / task / context /
  format / constraints）。chain 上实测比 unwrapped paragraph 提升
  8-15% 可靠性。
* **Anthropic** self-check block 推荐 —— 每个 step prompt 末尾加
  "answer 之前先 check X / Y / Z"。每 step 多 200-500 token，能抓
  大部分"小错沿 chain 下传"问题。这个 pattern 的 gate 是这条建议
  的**out-of-band 版本**（Python `if`，不靠 LLM 自查），两个都有用。
* **Doug McIlroy** —— "Do one thing and do it well."。这个 pattern
  port 到 LLM 的 Unix pipe 哲学源头。

## 什么时候不要用

* **One-shot 任务**。"翻译这句话。"一个 step，不需要 gate。
* **DAG 形状的工作**。依赖是图不是线时用 [Plan-and-Execute](../b-plan-and-execute/)。
* **硬实时 loop**。每个 step 是 1 个 model RTT，5 个 step 是 5 个
  RTT，不可能塞进 300ms budget。单 step 或 model 内部 batch。

生产里大部分 chain 落在 3-5 步。**> 5 步通常是 DAG 伪装的**——升
[Plan-and-Execute](../b-plan-and-execute/)。**< 3 步是 chain 是
overhead**——折成一步。

## 诚实承认的局限

参考实现是同步的。生产部署对独立的 prior outputs 会并行 fan-out
（比如 step 3 依赖 step 1，但 step 2 独立）。这里的 chain 类没有
DAG 语义，需要的话那就是 [Plan-and-Execute](../b-plan-and-execute/)。
升级，不要硬塞。

默认缺模板 key 的行为——在 prompt 里留 marker——是有意但不常见的选择。
Code review 有时候会要求改成 raise。两种都站得住，参考实现选"保活
trace 暴露问题"是因为内容编辑流水线常有一次性模板手误，不该 kill
整批。**支付 / 医疗 chain 应该 override renderer 改 raise**。

Gate 失败的 retry 是简单的——同模板重提示。真实 chain 经常想**把
gate 的描述塞进 retry prompt** 让模型知道它失败在哪。钩子已经有了
（gate 工厂会 set `__name__`），但 `_run_step` 的模板渲染默认没
wire 进去。需要的话 `_run_step` 改两行就行。
