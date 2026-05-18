# b · RAG (Retrieval-Augmented Generation) — agentic

> Column lecture **03-03** · pattern · memory × chain
>
> [中文 README](README.zh-CN.md)

## The problem

A single-cell RNA-seq researcher needs a paper-recommender. She gets 50
new preprints per day from arXiv + bioRxiv + RSS, can only read ~30 a
month, and recently realised she missed a 2023 method paper that was
deeply relevant to her thesis. She tried four off-the-shelf tools:

* **Keyword search.** Returned 5,000 hits, all papers she had already read.
* **Vector-DB semantic search.** Returned 20 papers, the top 10 being
  2018-2020 "classics," not the new ones she needed.
* **Semantic + metadata filters.** Worked, but required 10 minutes per
  query to tune the filters.
* **HyDE (hypothetical-document embedding).** Returned relevant papers
  but couldn't surface anything that contradicted her standing hypothesis.

Her diagnosis: "All four tools could *find things*. None of them
searched like a working researcher — iteratively, with counter-examples,
across multiple sources."

Naive RAG (one-shot embed + top-K + answer) is the right tool for
narrow factual lookups in a corpus that shares vocabulary with the
query. It's the wrong tool for research-grade questions where the user
doesn't fully know what they're looking for.

## The pattern

Agentic RAG turns retrieval into a loop the agent drives, with five
canonical modes.

| Mode | What it does |
|---|---|
| **DECOMPOSITION** | Split the query into 2-4 sub-queries before any retrieval |
| **ITERATIVE** | Evaluate retrieved chunks; if insufficient, refine query and retry |
| **HYPOTHESIS** | Form a falsifiable claim and search for counter-evidence |
| **TRIANGULATION** | Cross-check across multiple sub-queries / corpora — favour chunks appearing in more than one |
| **EVIDENCE_WEIGHT** | Synthesise with explicit per-chunk confidence weighting |

Under the hood it uses **hybrid retrieval** — embedding similarity +
BM25 keyword, fused via Reciprocal Rank Fusion (RRF), optionally with a
cross-encoder reranker on top. The invariant: **the LLM judges
retrieval quality on every iteration and can refine the query**. That
loop is why this pattern sits at `memory × chain` in the matrix.

## Quickstart

```bash
python memory/b-rag/example.py
pytest memory/b-rag/
```

The demo runs the biology-researcher scenario over a 30-paper corpus.
Naive RAG ranks the target 2023 method paper somewhere in the top 10
(coincidentally — typically much lower in real corpora). Agentic RAG
locates it explicitly through hypothesis-refined iterative retrieval
and surfaces it in the synthesised answer.

## Files in this folder

| File | What it is |
|---|---|
| `pattern.py` | `HybridRetriever` + `AgenticRAG` + `RetrievedChunk` + `RetrievalEvent` + 5 `RetrievalMode` (~220 lines) |
| `example.py` | 30-paper synthetic corpus + deterministic stub judge (no API keys) |
| `test_pattern.py` | 9 invariants: RRF dedup + scoring, decompose cap, iterative refinement, triangulation ranking, full research shape, reranker hook |

## Engineering references (verified)

* **Anthropic Contextual Retrieval** ([2024 blog](https://www.anthropic.com/news/contextual-retrieval))
  — 49% reduction in retrieval failure by prepending a context summary
  to each chunk before embedding
* **Boris Cherny** on Claude Code dropping RAG for agentic search
  ([X post](https://x.com/bcherny/status/2017824286489383315)) — the
  case for when not to use RAG at all (code search) is from the same
  engineering team
* **Agentic RAG survey** — [arXiv:2501.09136](https://arxiv.org/abs/2501.09136)
  is a good entry point to the 2024-2026 academic literature
* **DeerFlow** ([bytedance/deer-flow](https://github.com/bytedance/deer-flow))
  — multi-agent research framework with Researcher / Coder / Writer
  agents, an industrial example of agentic RAG in production
* **Reciprocal Rank Fusion** (Cormack, Clarke & Buettcher, SIGIR 2009)
  — the dead-simple fusion algorithm used here

## When this pattern doesn't apply

* **Code search.** Claude Code, Cursor, and Aider explicitly dropped
  RAG for grep-based agentic search. Code is too structurally regular
  for semantic similarity to add value. See `perception/c-progressive-discovery/`.
* **Narrow factual lookups in a curated corpus.** Naive RAG (one-shot,
  embedding-only) is cheaper and just as good when the query language
  and the corpus language match.
* **Sub-second latency budgets.** Iterative retrieval costs latency.
  Single-shot RAG with a good reranker is faster and may be sufficient.
