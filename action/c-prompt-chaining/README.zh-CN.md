# c · Prompt Chaining · 提示链

> 专栏第 **05-04** 讲 · pattern · 行动 × 串行
>
> [English README](README.md)

## 故事

Payroll Lab 把结算、对账、生成指令和打款申请书拆成四段。mock model
第一次生成指令时把总账的两位数字抄反。严格 checksum gate 当场拒绝，
把 gate 放松成“非空即通过”后，27 万元差额会进入最终申请书，而后续
步骤仍然显示 SUCCESS。

这组数据来自可重复的课程实验，不代表任何真实模型的固定准确率。它要
说明的是传播机制：拆段能降低单步复杂度，**段间契约**才能阻止错误产物
继续下传。

Prompt Chaining 可以借用 Unix 管道来理解，但实现并非没有中心。这里由
`PromptChain` 统一控制顺序、重试和 Trace。它与 Plan-and-Execute 的区别
在于没有全局 DAG，也不做动态路径选择。

## 模式骨架

两个类 + 一组 gate 工厂函数：

| 构件 | 角色 |
|---|---|
| `ChainStep` | 一个 prompt step。带 `system_prompt` / `prompt_template` / `model` / 一个 `gate` callable / `max_retries`。模板用 user input + 所有 prior step 输出（按 `step_id` 索引）插值 |
| `PromptChain` | 顺序跑 step。把输出传给下一个，gate 失败时 bounded retry，每次 attempt 都进 `ChainTrace` |
| `length_gate` / `keys_gate` / `regex_gate` / `any_gate` / `all_gate` | gate 工厂函数。参考实现使用便宜的程序化检查；语义判断可升级成独立 evaluator step，并保留确定性外层契约 |

讲义命名的两个失败模式，pattern 分别解决：

| 失败模式 | 是什么 | 怎么解决 |
|---|---|---|
| **信息饥饿（information starvation）** | Step 3 要 Step 1 的数据，但 Step 2 没传过去 | 每个 step 都能按 id 拿到**所有** prior outputs，不只是上一步 |
| **闸门暴政（gate tyranny）** | Gate 卡太死（"刚好 500 词"），499 跟 501 都被拒，无限重试 | `max_retries` 是硬上限，失败 retry 记录 gate description 让运维知道松哪条 |

3 条值得记住的行为：

1. **Gate 失败 retry，LLM 错误 fail-fast**。Gate 没过会重提示直到
   `max_retries`，LLM 异常立即终止 step。不同异常不同处理。
2. **模板接线错误 fail-closed**。缺少 `{step_id}` 或 `static_args`
   覆盖 `user_input`、前序产物时，Chain 在模型调用前终止。模型不负责
   猜测丢失的业务输入。
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
| `test_pattern.py` | 16 条不变式：每个 gate 工厂 / chain 构造守卫（空 / 重 id）/ 顺利路径 / 按 id 拿 prior outputs / gate 失败有 cap retry / retry 成功完成 / LLM 错误 fail-fast / 模板缺 key 与产物名覆盖 fail-closed / trace 记账 |

## 工程引用（都核过源码）

* **Aider** [`aider/history.py`](https://github.com/Aider-AI/aider/blob/main/aider/history.py)
  —— `ChatSummary.summarize_real()` 会在摘要与尾部仍超预算时递归压缩，
  并设置递归深度上限。这里借鉴的是“固定变换 + 预算 + 递归终止条件”，
  不把整个文件的行数当作模式结论。
* **Claude Code Skills** —— Skill 是可复用的提示与工作流能力包。它
  可以写成固定链，也可以调工具、启动子 Agent 或运行循环，因此不能把
  Skill 与 Prompt Chaining 直接画等号。
* **Anthropic** [*Building Effective
  Agents*](https://www.anthropic.com/research/building-effective-agents)
  —— prompt chaining 列为最简单也最被低估的 agent pattern。参考形态
  "数量不多但定义清楚的 step + 步骤间 gate"。
* **Anthropic** [*Prompt engineering best
  practices*](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
  —— 可用清晰结构分开指令、上下文和输出格式。具体收益需要在自己的
  数据集上评测，本文不引用无来源的固定提升比例。
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

缺模板 key 和产物名覆盖现在都会 fail-closed。调试工具仍可把错误写入
Trace，但不能把带缺口的 prompt 交给模型继续猜。

Gate 失败的 retry 是简单的——同模板重提示。真实 chain 经常想**把
gate 的描述塞进 retry prompt** 让模型知道它失败在哪。钩子已经有了
（gate 工厂会 set `__name__`），但 `_run_step` 的模板渲染默认没
wire 进去。需要的话 `_run_step` 改两行就行。
