# c · Parallel Exploration · 并行探索

> 专栏第 **04-04** 讲 · pattern · 推理 × 并行
>
> [English README](README.md)

## 故事

一家三甲医院的医疗影像辅助 Agent，读 CT 影像帮医生标记可疑结节。
团队线下验证单链 CoT 准确率 89%，"够用了"上了试点科室。三周后某患者
CT 上有一个 12mm 肺结节，Agent 给出 BI-RADS 3 类。**3 个月后患者复
查，结节长到 18mm，病理是肺腺癌早期**。

回查 Agent 的 thinking trajectory——每一步看着都对：检测到 12mm 结节、
形态边缘较光滑、未见明显毛刺，综合评估 BI-RADS 3 类。医生复盘时点出
问题：**这个 case 单链推理刚好走偏了，毛刺很轻但存在，单链就是抓不
到，多跑几次至少有一次能抓住**。

团队重写成 N=5 并行 reading。3 路给 BI-RADS 3（置信度 ~0.85），
**2 路抓到毛刺 / 胸膜凹陷，flag 4a**（置信度 ~0.74）。majority vote
仍然 3。团队的实际决策：**任何一路 flag 4a 立即触发人工二审**。下
一个同类 case 提前 3 个月发现。

| 工程现实 | 含义 |
|---|---|
| 单 CoT 链有"侥幸偏差" | 同 prompt 同 model 不同 sample 给不同答案 |
| Majority vote 不是处处对 | 医疗场景"漏诊代价 >> 误诊代价"，应该 ANY_ALARM |
| 5× 成本换 7pp 准确度 | 不对称错代价场景里值得 |
| Branch 之间要隔离 | event loop 串扰会把"独立采样"变成"伪独立" |

## 模式骨架

一个类 `ParallelExploration`。N 路并行，5 种聚合策略选一种，所有
branch 进 trace（不只是赢家）让 audit 能 replay disagreement。

5 种聚合策略，按 **业务错代价形状** 选，不是按工程口味选：

| 策略 | 适用 | 一句话规则 |
|---|---|---|
| `MAJORITY` | 答案离散、错代价对称 | 投票 |
| `WEIGHTED` | branch 自报置信度 | 按答案累加置信度 |
| `VERIFIER` | 开放式答案（写作 / 代码） | judge 函数选最好的 |
| `FIRST_CORRECT` | 有便宜的 correctness check | 第一个通过 check 的赢 |
| `ANY_ALARM` | 不对称错代价（医疗 / 风控 / 安全） | 任一路 flag 都升级 |

开篇医疗 case 是 `ANY_ALARM` 的教科书用法。大部分生产流量走 `MAJORITY`
或 `WEIGHTED`。`VERIFIER` 最贵，在开放式生成场景里值。

两个生产健康指标 pattern 暴露：

* **`branch_agreement_rate`** —— 投给众数答案的 branch 占比。健康线
  0.60-0.80。太低（< 0.50）说明任务真的难，parallel 在干活；太高
  （> 0.90）说明 branch 在说同一件事，N 过剩。
* **`effective_n`** —— **不同**答案的数量。接近 N 说明 prompt 扰动
  到位；接近 1 说明 branch 在浪费。

N 通常 3-5。Wang 2024 CoT-PoT 给的数据：N=2 已经能拿到 N=10 90% 的
lift。N > 5 边际收益递减明显，成本却线性。

## 跑起来

```bash
python reasoning/c-parallel-exploration/example.py
pytest reasoning/c-parallel-exploration/
```

demo 把 CT 影像场景的同一份 5 branch 用 5 种聚合各跑一次。并排输出
表明：同一份数据，5 种策略 5 种结论。**聚合策略不是 nice-to-have，是
load-bearing 决策**。

## 这个文件夹有什么

| 文件 | 说明 |
|---|---|
| `pattern.py` | `AggregationStrategy` 枚举 + `BranchResult` + `ParallelTrace` + `ParallelExploration`（~180 行） |
| `example.py` | CT 影像场景——5 路并读，5 种聚合策略并排对照 |
| `test_pattern.py` | 16 条不变式：每种聚合 / alarm 升级 / 置信度加权 / 函数缺失 guard / first_correct 全失败回退 majority / 空 trace 健康指标 |

## 工程引用（都核过源码）

* **Wang et al. (2022)** [*Self-Consistency Improves Chain of Thought
  Reasoning in Language
  Models*](https://arxiv.org/abs/2203.11171) —— N-sample + majority
  vote；GSM8K 上 GPT-3 从 17.9% 提到约 58%。
* **Wang et al. (2023)** [*Universal
  Self-Consistency*](https://arxiv.org/abs/2311.17311) —— 扩展到开放
  式输出，用 judge LLM 评分。对应 `AggregationStrategy.VERIFIER`。
* **Yao et al. (2023)** [*Tree of
  Thoughts*](https://arxiv.org/abs/2305.10601) —— 把 N 扁平 branch 升
  级到 search tree。Game-of-24 IO 7.3% → ToT-5 74%，约 25× token
  成本。这个最小 pattern 不包含树搜索，组合搜索任务特化场景才用。
* **Wang et al. (2024)** [*CoT-PoT
  Ensembling*](https://arxiv.org/abs/2406.14833) —— N=2 已经拿到 N=10
  90% 的 lift。"N 不要大"的实证依据。
* **DeerFlow** isolated event-loop 模式 —— 每个 branch 独立 asyncio
  协程 + 独立 LLM client + 独立 trace buffer，branch 挂掉不串扰。
  生产 wrapper 应该走这个形态。
* **Anthropic** sub-agent fan-out —— 同 pattern 不同单元（sub-agent
  代替 reasoning branch）。2026 年大部分生产 parallel reasoning 都在
  multi-agent orchestrator 里，不在单独的 "parallel CoT" middleware。

## 什么时候不要用

* **cheap 档已经够用**。单链准确率已经达标时 N 路只在乘账单。改用
  [Complexity-Based Routing](../b-complexity-routing/)，把 parallel
  留给真正需要的 case。
* **硬 latency budget**。同步 fan-out 是单 branch latency 的 N 倍。
  异步 fan-out 受最慢 branch 限制。两种都不适合 < 500ms budget，静态
  选档接受 noise。
* **超长上下文**。每个 branch 都带完整 context。N=5 + 200k 窗口 = 1M
  context token 才输出一个 token。要么先做 [Semantic
  Compaction](../../perception/b-semantic-compaction/)，要么 N=2。

## 诚实承认的局限

`branch_agreement_rate` 和 `effective_n` 是健康信号不是安全保证。
**5 branch 全部高置信度地一致答错** 看 metrics 是健康的——这是
"correlated lucky seeds" 失败模式。聚合是统计学不是 ground truth。
**任务有真后果时在聚合之上加外部验证步骤，不要在聚合之下**。

参考实现走同步 sampling 是为了 clarity。生产部署要把每个 branch 包
进独立 asyncio 协程 + 独立 LLM client（DeerFlow 模式），让 slow
branch 在其他 branch 已经收敛后可取消。没有 isolation 的话"独立采样"
会通过 shared buffer 和 shared retry state 悄悄变成"共享错误"。
