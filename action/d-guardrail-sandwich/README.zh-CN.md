# d · Guardrail Sandwich · 护栏三明治

> 专栏第 **05-05** 讲 · pattern · 行动 × 层级
>
> [English README](README.md)

## 故事

Payroll Lab 注入一条 E0099 审批：调整金额 999999，状态 APPROVED。
审批流程本身没有报错，内容却明显越过单笔上限。Guardrail Sandwich
在调用前读取这条审批证据，金额 hook 将它 BLOCK，账本仍保持 DRAFT。

同一实验还覆盖冻结账户、缺少银行回执、输出携带账号和 shadow mode。
这些都是确定性的课程场景，展示前置、执行、后置三种时态，不声称来自
某家银行，也不引用没有来源的事故率。

高风险工具的目标结构如下：

```
[pre-hooks]
  - 账号格式校验            → 形状错就 block
  - 客户白名单匹配          → 不在白名单 block
  - 金额阈值 (>¥1M 需人审)  → block 转人审
  - OFAC 制裁名单           → 直接 block
  - schema v2 校验          → 形状漂移 block
[transfer_funds]
  - 受控支付调用（课程中用 SQLite 状态变更代替）
[post-hooks]
  - 返回值 schema 校验      → 缺字段 mark rollback
  - 资金到账验证            → 没确认 mark rollback
  - PII 泄漏扫描            → 泄漏 mark rollback
  - AML 事后扫描            → 触发合规复核
  - 7 年审计 log            → 入归档
```

这套结构提供 defense in depth。它能证明哪些检查执行过、工具是否已经
运行、后置失败后是否需要补偿，不能承诺模型永远理解正确。

## 模式骨架

两个类 + 4 个 hook 工厂：

| 构件 | 角色 |
|---|---|
| `HookSpec` | 一个 hook。`name` / `phase` / `fn` / `priority` / `blocks` / `applies_to`，并携带 `policy_owner` 与 `policy_version`。Pre-hook BLOCK 阻断 tool。Post-hook BLOCK 标记 rollback |
| `GuardrailSandwich` | 把每个 tool 调用包成 `pre_hooks → tool → post_hooks`，记录完整 `SandwichTrace`。参考实现的 handler registry 仍是公开属性，生产环境还要在服务边界封死裸调用 |
| `amount_threshold_hook` / `blocklist_hook` / `output_schema_hook` / `pii_redaction_hook` | 常用工厂。真实部署有 20-40 个 hook，这些是绕不开的几个 |

讲义命名的 3 种失败模式，pattern 分别闭合：

| 失败模式 | 是什么 | 怎么闭合 |
|---|---|---|
| **Composition bypass（组合绕过）** | Agent 找到一条 *不走 sandwich* 调用 tool 的路（一个子 tool wrap 它、或者裸 HTTP 调用） | 参考实现只展示风险，尚未从语言层封死。生产部署应把裸 handler 放进私有执行服务，只暴露受控代理 |
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
时 BLOCK 降级成 `[shadow] WARN`，执行继续。团队可先收集命中率、误拦
率和业务影响，再决定何时转成强制策略。观察期多久、可接受误拦率多少，
需要由具体业务风险决定。

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
| `test_pattern.py` | 24 条不变式：每个 hook 工厂 / 重复注册守卫 / 未知 tool / 无 hook 直通 / pre-block 阻断 tool / 优先级顺序 / shadow mode / hook crash fail-closed / post-block 标 rollback / post-chain 完整性 / tool 错误跳过 post / `applies_to` scoping / Trace 时间戳与策略版本 |

## 工程引用（都核过源码）

* **Claude Code** Hooks Pipeline —— `PreToolUse` 可以在工具执行前
  deny，`PostToolUse` 与 `PostToolUseFailure` 在动作发生后提供观察点。
  后置 hook 无法撤销已经发生的文件写入或网络请求。
* **OWASP** [*Top 10 for Agentic Applications
  (2026)*](https://genai.owasp.org/) —— Agent Goal Hijack、Tool Misuse
  与 Prompt Injection 都要求执行层具备独立于模型的控制点。本文只引用
  风险分类，不引用无法核验的固定事故率。
* **NVIDIA NeMo Guardrails** —— 基于 Colang DSL 的可编程 guardrail。
  4 类 rail（input / dialog / retrieval / output）映射到 pre-hook
  （input rail）和 post-hook（output rail）。GPU 加速 ML rail。
* **GuardrailsAI** —— RAIL spec 声明式 guardrail。Self-correction
  loop（失败输出 → 反馈 → 模型 retry）是 `blocks=False` 能组合的
  形态——guardrail 不是 veto 而是 feedback。
* **Microsoft Guidance** —— grammar 级 schema 约束。编译期 deterministic
  guardrail。**跟这个 pattern 互补**：用 Guidance 做结构约束，用 hook
  做语义约束。
* **Anthropic** [*Trustworthy agents in practice*](https://www.anthropic.com/research/trustworthy-agents)
  —— 高自治系统需要 defense in depth、可观测性和可控边界。Shadow
  mode 是把新规则先变成可观测信号，再决定是否执法的一种工程实现。

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

最后一条：误拦过多会诱发人工绕过。Shadow-mode hook 的价值，是让团队
在强制执行前拿到真实分布，并为每条规则留下 owner、版本和转正标准。
