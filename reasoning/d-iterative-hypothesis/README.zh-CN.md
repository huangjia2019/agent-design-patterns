# d · Iterative Hypothesis Testing · 迭代假设验证

> 专栏第 **04-05** 讲 · pattern · 推理 × 循环
>
> [English README](README.md)

## 故事

凌晨 3:47。某中型化工厂一条聚乙烯生产线报警——反应釜温度从 80°C
（正常）上升到 92°C。值班工程师老陈接到 Agent 推送的假设清单，按
先验概率排序：

```
H1  78%   冷却水循环泵故障
H2  12%   温度传感器漂移
H3   5%   工艺配方异常
H4   3%   催化剂活性突变
H5   2%   PID 参数被异常修改
```

老陈先验证 H1，看冷却水流量——正常，**淘汰**。再验证 H2，对比另一只
冗余传感器读数——一致，**淘汰**。H3 查 1 小时前的进料口流量 log——
正常，**淘汰**。H4 催化剂活性要从实验室分析，等结果至少 30 分钟。
生产线已经停了 1 小时。CFO 在群里发了一句——"这条线每停 1 小时损失
¥45 万"。

老陈给 Agent 喂了一个新事实：**"刚才发现 PID 控制日志里 02:33 有一
次远程登录修改"**。Agent **没有**把这个事实塞进既有 ranking。它
**重置**：

```
new hypothesis tree (基于新证据):
  H5' (95%): PID 参数被异常修改
    └─ 下钻: 查 02:33 远程登录的具体改动
       └─ 发现: P 参数从 0.8 改到 2.5
          └─ 反推: 这个改动会导致控温过激, 温度震荡上行
            ✅ 与现状吻合
```

P 参数 04:51 回滚。温度 05:14 回归正常。整次故障停产 87 分钟。复盘
后老陈团队写下两条：

1. **H5 的 2% 先验是错的**。Planner 要枚举因果上不同的可能性，不是
   只列统计上最高的。
2. **新证据是 reset 不是 refine**。当一条新证据重新排列假设空间时，
   重新 propose，不是在原 tree 上微调。这跟 Anthropic 2026 三 Agent
   Harness 论文里那个 "context reset, not compaction" 的判断完全
   重合。

## 模式骨架

三个类对应三个角色：

| 类 | 角色 | 生产档位 |
|---|---|---|
| `Hypothesis` | 一条候选：先验、后验、状态、累积证据 | 数据 |
| `HypothesisTree` | 跨迭代的工作集；survivor count 是 Popper 量 | 数据 |
| `IterativeHypothesisLoop` | 跑 Planner → Generator → Evaluator 直到收敛或上限 | Anthropic 三 Agent harness |

退出条件是 **Popperian**——不是"找到一个看起来对的假设"，而是"所有
strong alternative 都被证伪"。这个 reframe 是整个 pattern 里**最
load-bearing 的设计选择**。Evaluator 的 system prompt 应该明确写：
*"your job is to falsify, not confirm."*

收敛 4 种情况：

1. **单 confirmed survivor**：教科书 win，loop 退出。
2. **全部 falsified mid-loop**：下个迭代邀请 Planner 提新假设（context
   reset 场景）。
3. **达到上限，剩 1 个 survivor**：不触发 HITL，survivor 作为"证据
   累积出来的工作答案"。
4. **达到上限，剩多个 survivor**：HITL。把完整 tree 交给人，**不要
   majority-vote 凑一个**。

5 种 evidence effect：

* `supports` 加 delta —— 把 posterior 推高；≥ 0.9 自动 confirm。
* `refutes` 加 delta —— posterior 砍到 0；状态立即翻 `FALSIFIED`，
  不管 delta 大小（Popperian 不对称：一条强反驳杀掉假设，一条 support
  不能 confirm）。
* `neutral` —— 不变，Evaluator 入 audit log。

硬上限：

* `max_iterations` 默认 5。Anthropic harness 用 5-10。> 10 不是在跑
  推理 loop，是在烧 budget。
* Generator 每假设每迭代拿一次证据。三角色绑 Opus/Sonnet/Haiku 时，
  成本 `n_hypotheses × iterations × (~tier_cost)`，可控。

## 跑起来

```bash
python reasoning/d-iterative-hypothesis/example.py
pytest reasoning/d-iterative-hypothesis/
```

demo 跑化工厂事故全流程。迭代 1 提 4 个 sensor-team 起手假设，全部
falsified。迭代 2 Planner 提 recovery 假设（操作员的新事实），证据
确认，loop 退出。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `Hypothesis` + `HypothesisStatus` + `Evidence` + `HypothesisTree` + `IterativeHypothesisLoop`（~210 行） |
| `example.py` | 反应釜温度事故 · 6 假设扇出 · 中途 context-reset |
| `test_pattern.py` | 13 条不变式：证据驱动的状态转换 / posterior 区间钳位 / tree 去重 / survivor 计数 / 4 种 loop outcome（收敛、context-reset、HITL、上限单 survivor）/ max_iterations 守卫 / 迭代号记录 |

## 工程引用（都核过源码）

* **Anthropic (2026)** [*How we built our multi-agent research
  system*](https://www.anthropic.com/research/multi-agent-research)
  —— 三 Agent Harness（Planner / Generator / Evaluator）和
  "context reset, not compaction" 规则。这个 pattern 是它的单进程
  port。
* **Aider** `aider/coders/base_coder.py` —— `max_reflections=3` 是这个
  pattern 家族最小诚实形态（Self-Refine 变体）。对 deterministic 失败
  （lint / test）有效，对模糊诊断束手无策——这个更丰富的 pattern 存在
  的理由。
* **Yao et al. (2022)** [*ReAct*](https://arxiv.org/abs/2210.03629)
  —— Reason → Act → Observe loop。最灵活，token 也最贵。这个 pattern
  的 Generator + Evaluator 部分是 ReAct 拆责任后的样子。
* **Xu et al. (2023)** [*ReWOO*](https://arxiv.org/abs/2305.18323)
  —— 先 plan，再并行跑 tool，最后一次性 synthesize。比 ReAct 节省
  ~5× token，但 plan 一旦错没法 mid-flight 改。
* **Madaan et al. (2023)** [*Self-Refine*](https://arxiv.org/abs/2303.17651)
  —— 生成 → 自评 → 改 → 循环。不适合事故诊断（没有外部证据 loop），
  适合写作 / 代码 / 总结。
* **Karl Popper** *The Logic of Scientific Discovery* (1959) —— 哲学
  锚：**理论不能被 confirm，只能被 falsify**。loop 的退出条件是这套
  哲学的直接 port。

## 什么时候不要用

* **单步任务**。"今天周几"不需要 hypothesis tree。plumbing 是 overhead。
* **闭式答案任务（数学 / 分类）**。lucky-seed 问题用 [Parallel
  Exploration](../c-parallel-exploration/)。Iterative 是给**开放集
  诊断**用的。
* **没有 tool floor**。Generator 需要真证据——telemetry / log / sensor
  / ground-truth test。没这些 loop 只是多步幻觉。

## 诚实承认的局限

Planner 最大的失败模式是 **prior bias**。开篇故事就是：H5 的 2% 先验
是因为"最近没人改 PID 日志"，但这事就是发生了。生产部署需要**因果上
不同**的假设注入机制（不只是统计概率最高的）——通常是每类事故的固定
prior 清单，或者一个 long-tail seed prompt 强制 Planner 至少给一条
低概率 alternative。

`record_evidence` 里的 0.9 confirm 阈值是可调默认。high-stakes（医疗 /
安全 / 风控）要调高，low-stakes 可以调低。**这个阈值是产品经济学，
不是算术**。

HITL 切换只在有人可切换时才有意义。无人化自动化要 graceful 降级：
取最高 posterior survivor 作为临时答案，log 多 survivor 状态，异步
escalate。**不要假装收敛了**。
