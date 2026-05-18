"""Invariants the Agentic RAG pattern must preserve."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    AgenticRAG,
    HybridRetriever,
    RetrievalMode,
    RetrievedChunk,
)


# ───────────────────── shared fixtures ─────────────────────

def _make_chunks(ids: list[str]) -> list[RetrievedChunk]:
    return [RetrievedChunk(chunk_id=i, content=f"content of {i}") for i in ids]


def _build_retriever(*, semantic_ids: list[str], keyword_ids: list[str]) -> HybridRetriever:
    return HybridRetriever(
        embedding_fn=lambda q, k: _make_chunks(semantic_ids)[:k],
        bm25_fn=lambda q, k: _make_chunks(keyword_ids)[:k],
    )


def _build_rag(
    *,
    retriever: HybridRetriever | None = None,
    judge_responses: list[dict] | None = None,
    max_iterations: int = 3,
) -> AgenticRAG:
    responses = list(judge_responses or [])

    def judge(prompt):
        if responses:
            return responses.pop(0)
        return {}

    return AgenticRAG(
        retriever=retriever or _build_retriever(
            semantic_ids=["a", "b", "c"], keyword_ids=["b", "c", "d"]
        ),
        llm_judge=judge,
        max_iterations=max_iterations,
    )


# ───────────────────── invariants ─────────────────────

def test_rrf_merge_deduplicates_chunks_across_signals() -> None:
    r = _build_retriever(
        semantic_ids=["a", "b", "c"],
        keyword_ids=["b", "c", "d"],
    )
    out = r.retrieve("anything", top_k_initial=10, top_k_final=10)
    ids = [c.chunk_id for c in out]
    assert set(ids) == {"a", "b", "c", "d"}
    # b and c appear in both signals so they should rank higher than a or d
    assert ids.index("b") < ids.index("a")
    assert ids.index("c") < ids.index("d")


def test_rrf_assigns_score_fused_to_each_chunk() -> None:
    r = _build_retriever(semantic_ids=["a"], keyword_ids=["a"])
    out = r.retrieve("anything")
    assert out[0].score_fused > 0


def test_decompose_caps_at_four_sub_queries() -> None:
    rag = _build_rag(
        judge_responses=[
            {"sub_queries": ["q1", "q2", "q3", "q4", "q5", "q6"]},
            {"sufficient": True}, {"sufficient": True}, {"sufficient": True}, {"sufficient": True},
            {"hypothesis": "h"},
            {"sufficient": True},
            {"answer": "a", "confidence": 0.5},
        ],
    )
    rag.research("anything")
    subqs_event_count = sum(
        1 for e in rag.events if e.mode == RetrievalMode.ITERATIVE
    )
    # We expect at most 4 sub-queries each with at least 1 retrieve call
    assert subqs_event_count <= 4


def test_iterative_retrieve_stops_when_judge_returns_sufficient() -> None:
    rag = _build_rag(
        judge_responses=[
            {"sufficient": True},
        ],
        max_iterations=5,
    )
    chunks = rag._iterative_retrieve("q", RetrievalMode.ITERATIVE)
    assert len(chunks) > 0
    # one iteration only
    assert len(rag.events) == 1


def test_iterative_retrieve_refines_query_until_max_iterations() -> None:
    judge_calls = []

    def judge(p):
        judge_calls.append(p)
        return {"sufficient": False, "refined_query": f"refined_{len(judge_calls)}"}

    rag = AgenticRAG(
        retriever=_build_retriever(semantic_ids=["a"], keyword_ids=["a"]),
        llm_judge=judge,
        max_iterations=3,
    )
    rag._iterative_retrieve("initial", RetrievalMode.ITERATIVE)
    assert len(rag.events) == 3
    assert rag.events[0].query == "initial"
    assert rag.events[1].query == "refined_1"
    assert rag.events[2].query == "refined_2"


def test_triangulate_ranks_chunks_appearing_in_multiple_subqueries_higher() -> None:
    rag = _build_rag()
    a = _make_chunks(["x", "y", "z"])
    b = _make_chunks(["y", "z", "w"])
    c = _make_chunks(["z"])
    ranked = rag._triangulate([a, b, c])
    # z appears in all three -> first; y in two; w and x in one each
    assert ranked[0].chunk_id == "z"
    assert ranked[1].chunk_id == "y"


def test_research_returns_full_synthesis_shape() -> None:
    rag = _build_rag(
        judge_responses=[
            {"sub_queries": ["sub1"]},
            {"sufficient": True},
            {"hypothesis": "H1"},
            {"sufficient": True},
            {"answer": "the answer", "confidence": 0.7},
        ],
    )
    result = rag.research("main question")
    assert result["query"] == "main question"
    assert result["hypothesis"] == "H1"
    assert result["answer"] == "the answer"
    assert result["confidence"] == 0.7
    assert "supporting_evidence" in result
    assert "counter_evidence" in result
    assert "retrieval_events" in result


def test_research_records_event_per_retrieve_call() -> None:
    rag = _build_rag(
        judge_responses=[
            {"sub_queries": ["sub1", "sub2"]},
            {"sufficient": True},     # sub1 sufficient in 1 iter
            {"sufficient": True},     # sub2 sufficient in 1 iter
            {"hypothesis": "h"},
            {"sufficient": True},     # counter sufficient in 1 iter
            {"answer": "ok", "confidence": 0.6},
        ],
    )
    rag.research("q")
    # Expect 3 retrieval events: sub1, sub2, counter
    assert len(rag.events) == 3
    modes = [e.mode for e in rag.events]
    assert modes.count(RetrievalMode.ITERATIVE) == 2
    assert modes.count(RetrievalMode.HYPOTHESIS) == 1


def test_reranker_runs_after_rrf_merge_when_provided() -> None:
    reranker_calls = []

    def rerank(query, chunks):
        reranker_calls.append((query, [c.chunk_id for c in chunks]))
        # Return in reverse to verify the reranker actually changed order
        return list(reversed(chunks))

    r = HybridRetriever(
        embedding_fn=lambda q, k: _make_chunks(["a", "b", "c"])[:k],
        bm25_fn=lambda q, k: _make_chunks(["a"])[:k],
        rerank_fn=rerank,
    )
    out = r.retrieve("anything", top_k_final=3)
    assert len(reranker_calls) == 1
    # After reranker reversal, last-merged chunk should now be first
    assert out[0].chunk_id != "a"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
