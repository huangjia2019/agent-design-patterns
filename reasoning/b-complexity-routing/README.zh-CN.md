# b · Complexity-Based Routing · 复杂度路由

> 专栏第 **04-03** 讲 · pattern · 推理 × 路由
>
> [English README](README.md)

## 故事

一个数据分析 Agent，给中型 SaaS 内部数据团队用。让产品、增长、财务的
人都能用自然语言查 BI。团队默认全用 Claude Opus——"反正 Opus 最强，
免得出错"。功能没问题。

8 月初财务来了张账单：**¥48 万**。团队开始拆每条 query 的真实复杂度：

| 查询类型 | 占比 | Opus 真实需要的能力 |
|---|---:|---|
| "上周注册用户数" | 41% | 0%，一句 SQL 模板填空 |
| "按地区分组的留存曲线" | 22% | 30%，加个 GROUP BY |
| "为什么本周 GMV 同比下降 8%" | 19% | 80%，多步归因 |
| "如果价格调 +10%，用户流失率会怎么变" | 4% | 100%，因果建模 |
| 工具调用 / schema 探查等中间步骤 | 14% | 取决具体 step |

41% 是 SQL 模板填空。Opus 每百万 token 入 15 元出 75 元，Haiku 每百万
token 入 1 元出 5 元——**15 倍冤枉钱**。团队 3 周后改成三层路由，账单
回到 ¥12 万一个月，0.5% 错误率以内。

总判断：GPT-4o vs GPT-4o-mini 价差 16 倍，Claude 各档之间类似。**把
40-70% 流量路由到 cheap 档通常能砍掉一半账单且质量无明显下降——前提
是路由信号靠谱且 fallback 路径老实记下"cheap 档错在哪"**。

## 模式骨架

两个类，各管一件事：

| 类 | 角色 |
|---|---|
| `ComplexityRouter` | 按 task 形状用可插拔信号选初始档。返回 `RoutingDecision` 含 `reason` 和 `score`。reason 是监管最先问的东西 |
| `FallbackChain` | 跑选定档、validate 输出、不达标抛 `FallbackTriggeredError` 升档。**每步失败原因都进 audit log**，不只是"用了 tier=2" |

三档（`SIMPLE` / `MEDIUM` / `COMPLEX`）覆盖大部分生产需求。Hermes 用
6 档。绝大多数团队发现 3 个模型档加一个 OFF 是 sweet spot——档多了
运维负担超过质量收益。

可插拔信号：`length_signal` / `causal_keyword_signal` /
`template_query_signal`。router 取**最强的 positive 信号**（不是平均）——
出现一个强信号（"prove" / "why"）就够升档，不需要被弱 length 信号
稀释回去。Negative 信号（template）取平均后减去，让 template pattern
能把边界 task 拉回 SIMPLE。

`FallbackTriggeredError` 是**语义** exception——"质量不达标"，跟普通
网络 / 鉴权错误不一样。Validator 可插拔。Cascade 有硬上限（默认 2 次
升档 = 最多跑 3 个档）。

## 跑起来

```bash
python reasoning/b-complexity-routing/example.py
pytest reasoning/b-complexity-routing/
```

example.py 跑 6 条 query 通过 router 和完整 cascade。模板 query 落
SIMPLE 通过 validator；因果 query 直接落 COMPLEX 跳过低档；一条升档
case 展示完整 audit trail（每步带 `fail_reason`）。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `ComplexityTier` + `RoutingDecision` + 3 个 signal 函数 + `ComplexityRouter` + `FallbackChain` + `FallbackTriggeredError`（~220 行） |
| `example.py` | 6 条数据分析 query 场景，含 toy LLM + validator |
| `test_pattern.py` | 15 条不变式：3 个 signal 函数 / router 档位选择 / 自定义 tier-model 映射 / cascade 升档 / fail_reason 记录 / 起点 COMPLEX 跳过低档 / 耗尽行为 |

## 工程引用（都核过源码）

* **Claude Code** `FallbackTriggeredError` —— 输出质量不达标时升档的
  语义 exception。参考实现的 `FallbackTriggeredError` 是直接 port 这
  个形态——它是 *quality* 信号，不是 transport 信号。
* **Hermes Agent** `ReasoningEffort` 6 档枚举（OFF / MINIMAL / LOW /
  MEDIUM / HIGH / MAX）—— 更细粒度的同源做法。6 档替换 3 档的工程
  理由：每两档间价差 3-5 倍，`OFF` vs `MINIMAL` 在有"零推理流量"类型
  的场景里有意义。
* **Aider** `--model` + `--weak-model` 两条 flag —— 按 *动作类型* 路由
  而不是按复杂度。Git commit 走 weak model，code 改动走 main model。
  另一个正交维度：按 agent 在做什么路由，不是按 task 多难。
* **Anthropic** [*Building Effective Agents*](https://www.anthropic.com/research/building-effective-agents)
  —— "用最便宜的能解决问题的模型，需要时再升级"。
* **Augment Code (2026)** [*AI model routing
  guide*](https://www.augmentcode.com/guides/ai-model-routing-guide)
  —— coding agent 角色分工：Opus 协调，Sonnet 实现，Haiku 文件导航，
  GPT-5.2 review。
* **Paxrel (2026)** [*AI agent cost
  optimization*](https://paxrel.com/blog-ai-agent-cost-optimization)
  —— 跨多个生产部署实测好的 routing 能拿到 47-80% 成本下降，质量回归
  < 1%。

## 三条工业路线（选其一并明示）

1. **模型层内化（OpenAI GPT-5 路线）**。Provider 替你 routing。零工程
   零可观测性，单厂商锁定。
2. **Harness 显式（本 pattern + Hermes 风格）**。policy 加 audit 都
   是你的。工程量大但能 log 每一条决策，可跨厂商。生产用这条。
3. **第三方 router（OpenRouter / LiteLLM）**。工程量最低，多一跳
   latency 加数据流问题。prototype 可用，监管 workload 慎用。

这个文件夹里的 pattern 走第 2 条。

## 什么时候不要用

* **单厂商单模型部署**。没档可路由。用 [Chain-of-Thought
  pattern](../a-chain-of-thought/) 的 effort 档代替。
* **窄领域 agent 且 cheap 档已经达标**。Haiku 就够翻译 / 情感分析，
  cascade 只是在 speculative quality lift 上烧钱。
* **硬实时 loop（<200ms budget）**。Cascade 本身加 latency。静态选档
  接受它。

## 诚实承认的局限

基于信号的 router 是个 heuristic，两边都会误分类。**真正的产品投入
应该在 validator 上**——router 给简单 query 选 SIMPLE 是 OK 的，只要
validator 抓得到 bad output 让 cascade 升档；router 给简单 query 选
COMPLEX 是浪费但不会错。**先把 validator 做对，再调 router**。

Cascade 还隐含一个"质量单调"假设：N+1 档至少不比 N 档差。Claude / GPT
各档间大部分时候成立，边缘情况会破——小模型有时拒答的 query 大模型
也会乱答。**能同时识别"拒答"和"幻觉"的 validator 比只查一种的强**。
