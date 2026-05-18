# a · Chain of Thought · 思维链

> 专栏第 **04-02** 讲 · pattern · 推理 × 串行
>
> [English README](README.md)

## 故事

一家中型财险公司给小额车险理赔做自动审核 Agent。从非 reasoning model
升级到 reasoning model 时，团队顺手在 prompt 里加了一段：

```
请逐步分析这份理赔单：
1. 先核对条款适用性
2. 再核对金额是否在限额内
3. 然后查验出险记录
4. 最后给出最终决定
```

上线后两件事同时发生。每件 claim 处理时间从 4 秒涨到 11 秒，月度 LLM
账单翻三倍。团队以为是 reasoning model 本身贵。两周后合规审计来了，
监管挑了一份 5 月 3 号的拒赔信问 reasoning，**那一单 thinking 字段
是空的**。

复盘发现根因——那一单 Opus 限流切到 fallback Sonnet。Sonnet 不收 Opus
的 signed thinking block，整段 thinking 在 fallback 时被自动 strip 了，
留下来的只有最终拒赔决定。**模型确实在 think，但没有任何机制把这件
事写成结构化记录**。

两条真正的教训，没一条是"加 step-by-step prompt"：

1. **"Let's think step by step" 在 reasoning model 上已经死了**。模型
   自己在 think，再喂 step instruction 是叠加干预。Wharton 2025 实测
   提升仅 2.9-3.1%，在噪声范围内。
2. **不喂 instruction 不代表不需要管 thinking**。存储、跨模型 fallback
   签名、监管视图、effort 控制——这些是 harness 的硬责任，模型不替你做。

## 模式骨架

四阶段生命周期：

```
emit  →  store  →  audit  →  migrate  →  control
```

2026 reframe 一句话：**CoT 不是 prompt 技巧，是 agent reasoning
trajectory 的 audit log，按 harness 层的 lifecycle 不变量来管**。

模式由三个类组成：

| 类 | 角色 |
|---|---|
| `ThinkingBlock` | 模型 emit 的一段 reasoning。带 provider signature，跨模型 fallback 时判断可不可迁移用 |
| `CoTTrace` | 一个任务的完整 trajectory。知道自己的 thinking token 总数、reasoning-token ratio，能 `strip_for_fallback(target_model)` 不污染自己 |
| `CoTManager` | runtime 入口。建 trace / 估 effort 档 / 跨 provider 标签 normalize / 出双视图 audit |

5 档 effort（`OFF` / `LOW` / `MEDIUM` / `HIGH` / `MAX`）—— Anthropic
标准 4 档 + `OFF`。Hermes 用 6 档（多一个 `MINIMAL`），4 档是更常见的
生产选择，参考实现走 4 档。

## 跑起来

```bash
python reasoning/a-chain-of-thought/example.py
pytest reasoning/a-chain-of-thought/
```

example.py 复刻开篇那个理赔故事。两件 claim 进来：第 1 件常规，第 2
件 ambiguous，跑到一半 Opus 限流，trace 被 strip 后 fallback 到 Sonnet，
Sonnet emit 一个 portable（unsigned）block，客户视图保持脱敏，监管
视图能看到完整 fallback chain。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `ThinkingEffort` + `ThinkingBlock` + `CoTTrace` + `CoTManager`（~230 行） |
| `example.py` | 车险理赔场景，含中途 provider fallback |
| `test_pattern.py` | 19 条不变式：block 可移植性 / strip 不污染原 trace / token ratio / 3 个 provider 的标签 normalization / effort 估计分支 / 监管 vs 客户视图 |

## 工程引用（都核过源码）

* **Claude Code** `query.ts:151-163` —— 三大铁律：thinking 签名是
  model-bound（`strip_for_fallback`）/ thinking 是付费 token 但不是
  免费 quality（effort 控制曲面）/ thinking 必须能在 trajectory 里
  反序列化。
* **Hermes Agent** `agent/cli.py` `_strip_reasoning_tags` —— 跨 provider
  标签 normalizer。OpenAI `<reasoning>` / DeepSeek `<think>` / Google
  `<thought>` / Anthropic 结构化 block。`CoTManager.normalize_tags`
  是这个思路的最小版本。
* **Anthropic Think-as-Tool** —— 把 thinking step 包成显式 tool。
  Tau-bench airline 报了约 20pp 准确率提升。参考实现没有专门做 tool
  封装，但 audit-log 形态完全一样。
* **OpenAI (2026)** [*Reasoning models struggle to control their chains
  of thought*](https://openai.com/index/reasoning-models-chain-of-thought-controllability/)
  —— controllability score 在所有 frontier reasoning model 上 0.1-15.4%。
  含义：模型不能自我 redact，harness 必须做。
* **OpenAI (2026)** [*Evaluating CoT
  monitorability*](https://openai.com/index/evaluating-chain-of-thought-monitorability/)
  —— "monitoring chains-of-thought is substantially more effective than
  monitoring actions and final outputs alone." 这句话是把 CoT 当 audit
  data（而不是看完即弃临时数据）的工程依据。
* **Goodfire (2026)** [*Reasoning Theater: Performative
  CoT*](https://www.goodfire.ai/research/reasoning-theater) —— CoT
  文字有时跟 internal activations 不一致。下面"诚实承认的局限"段会
  说怎么应对。
* **Wharton (2025)** —— prompt-style CoT 在 reasoning model 上提升
  2.9-3.1%，噪声范围内。这是淘汰 `Let's think step by step` 的实证依据。

## 什么时候不要用

* **超低延迟交互场景**。用户需要 200ms 内回应，extended thinking 不是
  免费的。用 `ThinkingEffort.OFF`，把 trace 壳保留做 audit 钩子。
* **分类 / 情感 / 简单 Q&A**。让 reasoning model 花 800 个 thinking
  token 判断一句话是正面还是负面是错的形态。estimate 直接给 LOW 或 OFF。
* **demo / 原型且没有 audit 消费方**。整套 lifecycle 是 overhead。
  保留 `CoTTrace` 的形状，跳过监管视图。

## 诚实承认的局限

CoT 是 2026 年 agent 时代我们能拿到的最有用的可观测性信号——但它**不
能被完全信任**。Goodfire 的 *Reasoning Theater* 研究表明，模型 emit
的文字 chain 有时是事后写出来 justify 的"剧本"，而不是真实计算过程
的忠实记录。**Trace 要做，dashboard 要做，alert 要做；但金融、医疗、
法律这种 high-stakes 决策，要加额外的验证层（tool check / test case /
ground truth），不能只靠 CoT 审**。

OpenAI 的 monitorability 论文把这件事叫 "a fragile opportunity"——
未来的 model generation 可能完全不 emit visible CoT。**现在窗口还
开着的时候赶紧把 audit infrastructure 建起来**。
