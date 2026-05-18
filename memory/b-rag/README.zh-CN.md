# b · RAG · 检索增强生成（Agentic 版）

> 专栏第 **03-03** 讲 · 模式 · 记忆行 × 串行列
>
> [English README](README.md)

## 解决的问题

一位做单细胞 RNA-seq 的研究员需要一个论文推荐器。她每天从 arXiv + bioRxiv +
RSS 收到 50 篇新预印本，一个月只能精读 30 篇，最近发现错过了 2023 年的一篇方法
论文，是跟她课题深度相关的。她试过四个工具：

* **关键词检索。** 返回 5000 篇，全是她已经读过的
* **Vector DB 语义检索。** 返回 20 篇，前 10 篇是 2018-2020 年的"经典"，不是她
  需要的新论文
* **语义检索 + metadata 过滤。** 工作，但每次要花 10 分钟调过滤条件
* **HyDE（让 LLM 生成假设答案再 embed）。** 找到的论文相关，但没法证伪她
  已有的判断

她的诊断："四个工具都'能找到东西'。没有一个像活的研究员那样查——会迭代、会
找反例、能跨语料对比。"

Naive RAG（一次 embed + top-K + 生成）是窄场景事实查询的对的工具，前提是
查询词跟语料用词对得上。对于研究级问题（用户自己也不完全清楚要找什么），它
就不对了。

## 模式本体

Agentic RAG 把检索变成 agent 主导的循环，5 种 canonical 模式：

| 模式 | 做什么 |
|---|---|
| **DECOMPOSITION** | 把复杂 query 拆成 2-4 个子 query 再检索 |
| **ITERATIVE** | 评估返回结果，不够就 refine query 再查 |
| **HYPOTHESIS** | 形成可证伪假设，主动找反例 |
| **TRIANGULATION** | 跨多个子 query / 多语料对比，多源出现的 chunk 优先 |
| **EVIDENCE_WEIGHT** | 按每 chunk 置信度加权合成 |

底层用 **hybrid retrieval**：embedding 相似度 + BM25 关键词，用 Reciprocal Rank
Fusion (RRF) 合并，可选再叠一个 cross-encoder reranker。不变量：**LLM 每轮判
检索质量并可以 refine query**。正是这个循环让它坐落在矩阵 "串行列"。

## 快速跑通

```bash
python memory/b-rag/example.py
pytest memory/b-rag/
```

Demo 跑生物学研究员场景，30 篇合成语料。Naive RAG 在这个小 demo 里偶然把目标
2023 方法论文排到 top 10（真实大语料里通常排得低得多）。Agentic RAG 通过
hypothesis-refined 迭代检索显式定位它，并在合成答案里点出来。

## 文件清单

| 文件 | 说明 |
|---|---|
| `pattern.py` | `HybridRetriever` + `AgenticRAG` + `RetrievedChunk` + `RetrievalEvent` + 5 `RetrievalMode`，约 220 行 |
| `example.py` | 30 篇合成论文语料 + 确定性 stub judge（无需 API key）|
| `test_pattern.py` | 9 条不变量：RRF 去重 + 打分、decompose 上限、迭代 refine、triangulation 排序、研究全形态、reranker 钩子 |

## 工程引用（已核对）

* **Anthropic Contextual Retrieval**（[2024 博客](https://www.anthropic.com/news/contextual-retrieval)）
  —— chunk embedding 前加一句 context summary，召回失败率降低 49%
* **Boris Cherny** 关于 Claude Code 弃 RAG 转 agentic search
  （[X post](https://x.com/bcherny/status/2017824286489383315)）—— 同一支
  工程团队给出"什么时候不该用 RAG"的判断（代码搜索就是）
* **Agentic RAG 综述** —— [arXiv:2501.09136](https://arxiv.org/abs/2501.09136)
  是 2024-2026 学术文献的入口
* **DeerFlow**（[bytedance/deer-flow](https://github.com/bytedance/deer-flow)）
  —— 多 agent 研究框架，Researcher / Coder / Writer 三 agent 协作，生产级
  agentic RAG 实例
* **Reciprocal Rank Fusion**（Cormack, Clarke & Buettcher，SIGIR 2009）—— 这
  里用的简单融合算法的出处

## 什么时候不该用这个模式

* **代码搜索。** Claude Code / Cursor / Aider 都明确弃了 RAG 改走 grep 式
  agentic search。代码结构太规则，语义相似度不增加价值。见
  `perception/c-progressive-discovery/`
* **窄场景的事实查询 + 精心维护的语料。** Naive RAG（一次 embedding + top-K）
  更便宜效果一样好——前提是 query 用词跟语料用词对得上
* **亚秒级延迟预算。** 迭代检索增加延迟。带好 reranker 的单轮 RAG 更快可能就够
