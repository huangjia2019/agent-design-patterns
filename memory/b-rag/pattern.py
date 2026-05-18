"""RAG (Retrieval-Augmented Generation) pattern — agentic version.

Reference implementation of the agent-led multi-step retrieval pattern
from column lecture 03-03. The key shift since 2023's "naive RAG":

* **Naive RAG** is one shot — embed query, return top-K, generate answer.
  Cheap, fast, fragile. Works well only when the query and the corpus
  share vocabulary.
* **Agentic RAG** is a loop — decompose the query, retrieve, evaluate,
  refine, find counter-evidence, triangulate across corpora, synthesise
  with explicit evidence weighting. The agent does the retrieval rather
  than being a passive consumer of it.

The pattern's invariant: **the LLM judges retrieval quality on every
iteration and can refine the query**. That's why it's `memory × chain`
in the matrix (each step feeds the next), not `memory × single-step`.

Five canonical agentic modes are implemented:

* DECOMPOSITION  — split a complex query into 2-4 sub-queries
* ITERATIVE      — re-query if first results are insufficient
* HYPOTHESIS     — form a falsifiable claim, look for counter-evidence
* TRIANGULATION  — cross-check across multiple corpora
* EVIDENCE_WEIGHT — synthesise with per-chunk confidence weighting
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class RetrievalMode(Enum):
    DECOMPOSITION = "decomposition"
    ITERATIVE = "iterative"
    HYPOTHESIS = "hypothesis"
    TRIANGULATION = "triangulation"
    EVIDENCE_WEIGHT = "evidence_weight"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RetrievedChunk:
    """One retrieved unit (paper, doc page, code snippet) with provenance."""

    chunk_id: str
    content: str
    source: str = ""                  # corpus name: arxiv / wiki / internal-kb
    context_summary: str = ""         # Anthropic-style contextual retrieval header
    score_semantic: float = 0.0
    score_keyword: float = 0.0
    score_rerank: float = 0.0
    score_fused: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalEvent:
    """One retrieval call's trace — used for hit-rate + drift analysis."""

    query: str
    mode: RetrievalMode
    chunks_returned: list[str]
    chunks_actually_cited: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=_now_iso)


# ──────────────────────────── Hybrid retriever ────────────────────────────

EmbedFn = Callable[[str, int], list[RetrievedChunk]]
BM25Fn = Callable[[str, int], list[RetrievedChunk]]
RerankFn = Callable[[str, list[RetrievedChunk]], list[RetrievedChunk]]


class HybridRetriever:
    """Embedding + BM25 keyword + optional reranker, fused via RRF."""

    def __init__(
        self,
        embedding_fn: EmbedFn,
        bm25_fn: BM25Fn,
        rerank_fn: RerankFn | None = None,
        rrf_k: int = 60,
    ) -> None:
        self.embedding_fn = embedding_fn
        self.bm25_fn = bm25_fn
        self.rerank_fn = rerank_fn
        self.rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
        top_k_initial: int = 50,
        top_k_final: int = 10,
    ) -> list[RetrievedChunk]:
        semantic = self.embedding_fn(query, top_k_initial)
        keyword = self.bm25_fn(query, top_k_initial)
        merged = self._rrf_merge(semantic, keyword)
        if self.rerank_fn is not None:
            merged = self.rerank_fn(query, merged)
        return merged[:top_k_final]

    def _rrf_merge(
        self,
        a: list[RetrievedChunk],
        b: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Reciprocal Rank Fusion. Robust to score scales differing across signals."""
        scores: dict[str, float] = {}
        by_id: dict[str, RetrievedChunk] = {}
        for rank, c in enumerate(a):
            scores[c.chunk_id] = scores.get(c.chunk_id, 0.0) + 1.0 / (self.rrf_k + rank + 1)
            by_id[c.chunk_id] = c
        for rank, c in enumerate(b):
            scores[c.chunk_id] = scores.get(c.chunk_id, 0.0) + 1.0 / (self.rrf_k + rank + 1)
            by_id.setdefault(c.chunk_id, c)
        for cid, chunk in by_id.items():
            chunk.score_fused = scores[cid]
        return sorted(by_id.values(), key=lambda c: c.score_fused, reverse=True)


# ──────────────────────────── Agentic RAG ────────────────────────────

# llm_judge is a callable that takes a prompt-like dict and returns a dict
# describing the LLM's verdict. In production it wraps an Anthropic/OpenAI
# call; in tests and examples it's a deterministic stub.
LlmJudge = Callable[[dict[str, Any]], dict[str, Any]]


class AgenticRAG:
    """Agent-led multi-step RAG with five canonical modes."""

    def __init__(
        self,
        retriever: HybridRetriever,
        llm_judge: LlmJudge,
        max_iterations: int = 3,
    ) -> None:
        self.retriever = retriever
        self.llm_judge = llm_judge
        self.max_iterations = max_iterations
        self.events: list[RetrievalEvent] = []

    # ──────────────── public ────────────────

    def research(self, query: str) -> dict[str, Any]:
        sub_queries = self._decompose(query)
        per_subq: list[list[RetrievedChunk]] = [
            self._iterative_retrieve(q, RetrievalMode.ITERATIVE) for q in sub_queries
        ]
        hypothesis = self._form_hypothesis(query, per_subq)
        counter = self._iterative_retrieve(
            f"counter evidence to: {hypothesis}",
            RetrievalMode.HYPOTHESIS,
        )
        triangulated = self._triangulate(per_subq)
        return self._synthesize(query, hypothesis, triangulated, counter)

    # ──────────────── mode 1: decomposition ────────────────

    def _decompose(self, query: str) -> list[str]:
        verdict = self.llm_judge({"task": "decompose", "query": query})
        subs = verdict.get("sub_queries") or [query]
        return subs[:4]   # cap at 4 sub-queries

    # ──────────────── mode 2: iterative retrieve ────────────────

    def _iterative_retrieve(
        self, query: str, mode: RetrievalMode
    ) -> list[RetrievedChunk]:
        all_chunks: list[RetrievedChunk] = []
        seen_ids: set[str] = set()
        current = query
        for _ in range(self.max_iterations):
            chunks = self.retriever.retrieve(current)
            self.events.append(RetrievalEvent(
                query=current,
                mode=mode,
                chunks_returned=[c.chunk_id for c in chunks],
            ))
            for c in chunks:
                if c.chunk_id not in seen_ids:
                    seen_ids.add(c.chunk_id)
                    all_chunks.append(c)
            verdict = self.llm_judge({
                "task": "is_sufficient",
                "query": query,
                "current_query": current,
                "chunks": [c.chunk_id for c in chunks],
            })
            if verdict.get("sufficient"):
                break
            current = verdict.get("refined_query", current)
        return all_chunks

    # ──────────────── mode 3: hypothesis ────────────────

    def _form_hypothesis(
        self, query: str, candidates_per_subq: list[list[RetrievedChunk]]
    ) -> str:
        verdict = self.llm_judge({
            "task": "form_hypothesis",
            "query": query,
            "candidates": [[c.chunk_id for c in lst] for lst in candidates_per_subq],
        })
        return verdict.get("hypothesis", "")

    # ──────────────── mode 4: triangulation ────────────────

    def _triangulate(
        self, candidates_per_subq: list[list[RetrievedChunk]]
    ) -> list[RetrievedChunk]:
        """Prefer chunks confirmed by multiple sources or multiple sub-queries."""
        appearance: dict[str, int] = {}
        by_id: dict[str, RetrievedChunk] = {}
        for lst in candidates_per_subq:
            seen_in_this_subq: set[str] = set()
            for c in lst:
                if c.chunk_id not in seen_in_this_subq:
                    appearance[c.chunk_id] = appearance.get(c.chunk_id, 0) + 1
                    seen_in_this_subq.add(c.chunk_id)
                by_id[c.chunk_id] = c
        ranked = sorted(by_id.values(),
                        key=lambda c: (appearance[c.chunk_id], c.score_fused),
                        reverse=True)
        return ranked

    # ──────────────── mode 5: evidence-weighted synthesis ────────────────

    def _synthesize(
        self,
        query: str,
        hypothesis: str,
        evidence: list[RetrievedChunk],
        counter: list[RetrievedChunk],
    ) -> dict[str, Any]:
        verdict = self.llm_judge({
            "task": "synthesize",
            "query": query,
            "hypothesis": hypothesis,
            "evidence_chunks": [c.chunk_id for c in evidence[:10]],
            "counter_chunks": [c.chunk_id for c in counter[:5]],
        })
        return {
            "query": query,
            "hypothesis": hypothesis,
            "answer": verdict.get("answer", ""),
            "supporting_evidence": [c.chunk_id for c in evidence[:10]],
            "counter_evidence": [c.chunk_id for c in counter[:5]],
            "confidence": verdict.get("confidence", 0.5),
            "retrieval_events": list(self.events),
        }
