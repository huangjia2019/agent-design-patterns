# d · Guardrail Sandwich · 护栏三明治

> 专栏第 **05-05** 讲 · pattern · 行动 × 层级
>
> [English README](README.md)

## 故事

一家中型银行的对公转账 Agent，给客户经理辅助处理 B2B 转账。第三周
出事：客户邮件写"转 320 万到账户 ...XX23"，agent 把它解析成 ...XX32
（数字看错），`transfer_funds` 直接执行。12 小时后对账系统才抓到，
对方已经提现一部分。

根因：`transfer_funds` 是一个裸调用，**没有 pre-check**（账号合理
吗？金额合规吗？OFAC 制裁吗？AML 规则匹配吗？）**没有 post-check**
（钱真到指定账户了吗？返回值 schema 对吗？有 PII 泄漏吗？）。
Agent 的 reasoning trace 看着干净——它**自信地错了**，没有任何东西
站在错的 reasoning 和电汇之间。

重写后给所有 destructive tool 套 sandwich：

```
[pre-hooks]
  - 账号格式校验            → 形状错就 block
  - 客户白名单匹配          → 不在白名单 block
  - 金额阈值 (>¥1M 需人审)  → block 转人审
  - OFAC 制裁名单           → 直接 block
  - schema v2 校验          → 形状漂移 block
[transfer_funds]
  - 真 SWIFT 调用 (沙箱内)
[post-hooks]
  - 返回值 schema 校验      → 缺字段 mark rollback
  - 资金到账验证            → 没确认 mark rollback
  - PII 泄漏扫描            → 泄漏 mark rollback
  - AML 事后扫描            → 触发合规复核
  - 7 年审计 log            → 入归档
```

误转账率：0.3% → **0.001%**，延迟 +2-3s。在银行场景，**这不是
trade-off，这是 no-brainer**。

讲义的判断，用法律"程序正义"（due process）类比：**Guardrail
Sandwich 是 agent 行为的程序正义**。Pre-check 对应事前听证。Tool
调用是判决。Post-check 是事后救济 / 审计。**任一片面包缺了**，
你又回到"agent 想干啥就干啥，希望它干对"。

## 模式骨架

两个类 + 4 个 hook 工厂：

| 构件 | 角色 |
|---|---|
| `HookSpec` | 一个 hook。`name` / `phase`（PRE 或 POST）/ `fn` / `priority` / `blocks` / `applies_to`。Pre-hook BLOCK 阻断 tool。Post-hook BLOCK 标记 rollback |
| `GuardrailSandwich` | 把每个 tool 调用包成 `pre_hooks → tool → post_hooks`。记录完整 `SandwichTrace`。**注册进来的 tool 是唯一可调用入口**——裸 handler 不暴露（闭合 **composition bypass**） |
| `amount_threshold_hook` / `blocklist_hook` / `output_schema_hook` / `pii_redaction_hook` | 常用工厂。真实部署有 20-40 个 hook，这些是绕不开的几个 |

讲义命名的 3 种失败模式，pattern 分别闭合：

| 失败模式 | 是什么 | 怎么闭合 |
|---|---|---|
| **Composition bypass（构造绕过）** | Agent 找到一条 *不走 sandwich* 调用 tool 的路（一个子 tool wrap 它、或者裸 HTTP 调用） | `register_tool` 让 sandwich 是唯一入口。Tool handler 不暴露公共引用，没有第二条路 |
| **Sandwich overhead tax（三明治税）** | 给*每个* tool 都套 sandwich，包括读，延迟翻 3 倍 | `applies_to` 把 hook 绑特定 tool。读跳过 destructive sandwich；只有写付全税 |
| **Schema drift（schema 漂移）** | Pre-hook 按 v1 schema 验，LLM 改 emit v2，hook 放过坏 payload | `output_schema_hook` 对未知形状 fail-closed——`missing keys` 和 `not a dict` 都 block。Schema 版本在 hook 里，不散落在 prompt 里 |

3 条行为保证：

1. **Pre-hook BLOCK = tool 永远不跑**。不 retry 不警告，直接拒绝。
   Audit trail 写明哪个 hook 拒绝的。
2. **Hook 自己崩 fail-closed**。Hook 函数本身抛异常时 sandwich 当成
   BLOCK 处理。**有 bug 的 guardrail 不能变成开放后门**。
3. **Post-hook 即使有 block 也全部跑完**。Audit 完整性：每个问题都
   进 trace，不只是第一个。运维 dashboard 看全集。

加一个生产旋钮：**Shadow mode（影子模式）**。Hook 设 `blocks=False`
时 BLOCK 降级成 `[shadow] WARN`，执行继续。这直接对应讲义推荐的三
阶段 rollout：**周 1-2 monitor mode**（收集假阳性分布）/ **周 3-4
soft enforcement**（明显违规直接 block，边界 case 只 warn）/ **月 2+
full enforcement**。直接上 full enforcement 通常第一天就 block 掉
30%+ 合规流量——运维直接关 sandwich，前功尽弃。

## 跑起来

```bash
python action/d-guardrail-sandwich/example.py
pytest action/d-guardrail-sandwich/
```

demo 跑 4 个对公转账场景：¥4,200 常规转账（通过）、误写账号被白名单
PRE 抓住（钱没动）、¥5M 被金额阈值 PRE 抓住（转人审）、shadow-mode
demo（BLOCK 降级成 `[shadow] WARN`，tool 继续跑，让你边调边升级）。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `HookPhase` + `HookResult` + `HookSpec` + `HookOutcome` + `SandwichTrace` + `GuardrailSandwich` + 4 hook 工厂 + `GuardrailViolation`（~260 行） |
| `example.py` | 对公转账场景，复刻 ¥320 万误转账事故的修法 |
| `test_pattern.py` | 23 条不变式：每个 hook 工厂 / 重复注册守卫 / 未知 tool / 无 hook 直通 / pre-block 阻断 tool / 优先级顺序 / shadow mode / hook crash fail-closed / post-block 标 rollback / post-chain 完整性 / tool 错误跳过 post / `applies_to` scoping / trace 时间戳 |

## 工程引用（都核过源码）

* **Claude Code** Hooks Pipeline —— 12 个 lifecycle event；
  `PreToolUse` 是**唯一能 block 的 hook**（退出码 2）。`PostToolUse`
  没法 un-run tool，但可以 validate / scan / flag。Pattern 的两阶段
  chain 是直接 port。
* **OWASP** [*Top 10 for Agentic Applications
  (2026)*](https://genai.owasp.org/) —— A1 *Agent Goal Hijack* /
  A2 *Tool Misuse* / A3 *Prompt Injection* 都映射到 pre-hook
  （whitelist / blocklist / schema）。讲义引的 88% 事故率来自 OWASP
  行业调研。
* **NVIDIA NeMo Guardrails** —— 基于 Colang DSL 的可编程 guardrail。
  4 类 rail（input / dialog / retrieval / output）映射到 pre-hook
  （input rail）和 post-hook（output rail）。GPU 加速 ML rail。
* **GuardrailsAI** —— RAIL spec 声明式 guardrail。Self-correction
  loop（失败输出 → 反馈 → 模型 retry）是 `blocks=False` 能组合的
  形态——guardrail 不是 veto 而是 feedback。
* **Microsoft Guidance** —— grammar 级 schema 约束。编译期 deterministic
  guardrail。**跟这个 pattern 互补**：用 Guidance 做结构约束，用 hook
  做语义约束。
* **Anthropic** [*Defense-in-depth* rollout
  guidance](https://www.anthropic.com/news/agent-security) —— 三阶段
  rollout（monitor → soft → full enforcement）。Shadow-mode feature
  就是为这条 rollout 设计的。
* **arxiv:2509.23994** [*AI Agent Code of Conduct: Policy-as-Prompt
  Synthesis*](https://arxiv.org/abs/2509.23994) —— 某金融 agent 在
  monitor mode 跑 14 天：47 条规则裁到 21 条（剪假阳性），新增 13 条
  （monitoring 发现的新攻击模式）。这就是 shadow mode 启用的生产校准
  闭环。

## 什么时候不要用

* **全只读 tool 集**。没有 destructive 表面，两面包都没必要。包读
  操作是纯 latency 税。
* **单 tool agent**。如果只有一个能干的事，且它本身有原生 check
  基建，sandwich 是重复劳动。
* **< 100ms 硬实时 loop**。Hook 通常便宜但叠加：5 个 hook × 5ms =
  25ms，还没算 tool 本身。静态选档接受 noise。

Sandwich 的价值集中在 **destructive 表面 + 高错代价** 的交集。银行
/ 医疗 / 基础设施变更 / 任何动客户数据的场景。**纯信息查询，三明治
是 theatre**。

## 诚实承认的局限

Sandwich 不做 rollback。它**标记**一个 trace 需要 rollback（post-hook
BLOCK 设 `rollback_marked=True`），实际的反向 saga 在 [Tool Dispatch
pattern](../a-tool-dispatch/) 里——后者注册时就声明 rollback action。
**生产里两个 pattern 配合用**：Tool Dispatch 的 saga log 管 un-doing，
Sandwich 的 post-hook chain 决定**什么时候**调 rollback。

参考实现不处理 hook **顺序独立性**。今天 priority 是手工整数。生产
部署经常想要某些 hook 声明"必须在 X 之前/之后"作为 DAG；参考实现
的扁平 priority list 是最小诚实形态。简单形态太粗时 override
`_applicable_hooks` 按依赖图排序。

Hook 这里是同步的。真银行部署常有 hook 自己再调外部服务（CSAI /
DLP / SIEM / 反欺诈评分）。把每个 hook 包 `asyncio` 直接做，contract
（`HookFn` 返回 `(HookResult, reason)`）不变。

最后一条：**Block 太多的 sandwich 比没 sandwich 更糟**。运维一个季
度内就会关掉它。Shadow-mode hook 存在就是为了让你**不要从 0 直接
跳到"第一天 block 30% 合规流量"**。用它。
