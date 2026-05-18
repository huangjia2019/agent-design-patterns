"""Runnable demo for the Agentic RAG pattern.

Scenario: a single-cell RNA-seq researcher needs a survey-paper helper.
Her corpus is 30 synthetic papers. She missed a 2023 method paper that
turned out to be highly relevant for her work. Naive RAG (one shot,
embedding-only) returns the usual 2018-2020 classics. Agentic RAG, with
iterative refinement + hypothesis + counter-evidence + triangulation,
locates the 2023 method paper in two iterations.

Run:
    python memory/b-rag/example.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
sys.modules.pop("pattern", None)

from pattern import (   # noqa: E402
    AgenticRAG,
    HybridRetriever,
    RetrievedChunk,
)


# ───────────────────── synthetic corpus ─────────────────────

CORPUS: list[dict] = [
    # The hidden gem: a 2023 method paper she missed
    {
        "id": "p-2023-method-x",
        "title": "Scalable batch correction for million-cell atlases via residual normalisation (2023)",
        "abstract": "We introduce a residual-normalisation method that scales linearly with cell count "
                    "while preserving rare-population signal. Tested on three million-cell datasets.",
        "year": 2023,
    },
    # Classic 2018-2020 papers
    {"id": "p-2018-seurat", "title": "Seurat v3 integration of single-cell data (2018)",
     "abstract": "Canonical correlation analysis for single-cell integration.", "year": 2018},
    {"id": "p-2019-scvi", "title": "scVI: deep generative modeling for single-cell transcriptomics (2019)",
     "abstract": "Variational autoencoder approach to scRNA-seq batch correction.", "year": 2019},
    {"id": "p-2020-harmony", "title": "Harmony: integrating single-cell data quickly and accurately (2020)",
     "abstract": "Fast integration via soft clustering in PCA space.", "year": 2020},
    {"id": "p-2020-bbknn", "title": "BBKNN: fast batch alignment of single-cell data (2020)",
     "abstract": "Batch-balanced k-nearest-neighbour graph correction.", "year": 2020},
    # Newer 2023-2024 follow-ups (also relevant but not the target)
    {"id": "p-2023-scgen", "title": "scGen perturbation prediction (2023)",
     "abstract": "Conditional VAE to predict cellular response to perturbations.", "year": 2023},
    {"id": "p-2024-tahoe", "title": "Tahoe-100M: a foundation atlas for single-cell biology (2024)",
     "abstract": "100M cell foundation model for downstream tasks.", "year": 2024},
    # Off-topic papers
    {"id": "p-2022-llm-surv", "title": "Pre-training language models: a survey (2022)",
     "abstract": "Survey of pre-training methods in NLP.", "year": 2022},
    {"id": "p-2023-vit", "title": "Vision Transformers revisited (2023)",
     "abstract": "Scaling laws of ViT.", "year": 2023},
    {"id": "p-2021-flow", "title": "Flow matching for generative modeling (2021)",
     "abstract": "Continuous normalising flow alternative.", "year": 2021},
]
# Pad to 30 papers with low-relevance noise
for i in range(20):
    CORPUS.append({
        "id": f"p-noise-{i:02d}",
        "title": f"Unrelated topic paper {i} (2021)",
        "abstract": "lorem ipsum filler paper unrelated to single-cell or batch correction",
        "year": 2021,
    })


def _full_text(p: dict) -> str:
    return f"{p['title']} {p['abstract']}"


# ───────────────────── tool stubs ─────────────────────

def stub_embedding(query: str, k: int) -> list[RetrievedChunk]:
    """Imitate a semantic retriever that favours older 'classic' papers.

    This mirrors the researcher's complaint that the off-the-shelf
    vector DB returned 2018-2020 classics. We give classics a small
    semantic bonus.
    """
    q_words = set(query.lower().split())
    scored = []
    for p in CORPUS:
        text = _full_text(p).lower()
        overlap = sum(1 for w in q_words if w in text)
        classic_bonus = 0.3 if p["year"] <= 2020 else 0.0
        score = overlap * 0.5 + classic_bonus
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        RetrievedChunk(
            chunk_id=p["id"], content=_full_text(p), source="arxiv",
            score_semantic=s, metadata={"year": p["year"]},
        )
        for s, p in scored[:k]
    ]


def stub_bm25(query: str, k: int) -> list[RetrievedChunk]:
    """Keyword retriever — boosts exact phrase matches."""
    q_lower = query.lower()
    q_words = set(q_lower.split())
    scored = []
    for p in CORPUS:
        text = _full_text(p).lower()
        # exact-phrase boost
        phrase_hits = text.count(q_lower) * 2.0
        word_hits = sum(text.count(w) for w in q_words)
        score = phrase_hits + word_hits * 0.3
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda t: t[0], reverse=True)
    return [
        RetrievedChunk(
            chunk_id=p["id"], content=_full_text(p), source="arxiv",
            score_keyword=s, metadata={"year": p["year"]},
        )
        for s, p in scored[:k]
    ]


# ───────────────────── deterministic LLM judge stub ─────────────────────

class StubJudge:
    """Deterministic LLM judge for the demo — no API key needed."""

    def __init__(self):
        self.iteration_count = 0

    def __call__(self, prompt: dict) -> dict:
        task = prompt.get("task")
        if task == "decompose":
            return {"sub_queries": [
                "batch correction methods for million-cell scRNA-seq",
                "residual normalisation single-cell rare population",
            ]}
        if task == "is_sufficient":
            self.iteration_count += 1
            chunks = prompt.get("chunks", [])
            # If we already have the target paper, declare sufficient
            if "p-2023-method-x" in chunks:
                return {"sufficient": True}
            # Otherwise refine to bias toward newer / residual / rare-population
            return {
                "sufficient": False,
                "refined_query": "residual normalisation rare population atlas million cells 2023",
            }
        if task == "form_hypothesis":
            return {"hypothesis": "2023+ methods explicitly preserve rare populations during batch correction"}
        if task == "synthesize":
            return {
                "answer": (
                    "Recent (2023+) batch-correction methods focus on rare-population preservation. "
                    "The residual-normalisation paper directly addresses million-cell scale + rare cells "
                    "and is the closest match to the user's open research need."
                ),
                "confidence": 0.78,
            }
        return {}


# ───────────────────── main ─────────────────────

def main() -> None:
    retriever = HybridRetriever(
        embedding_fn=stub_embedding,
        bm25_fn=stub_bm25,
        rerank_fn=None,
    )
    judge = StubJudge()
    rag = AgenticRAG(retriever=retriever, llm_judge=judge, max_iterations=3)

    query = "what should I read for batch correction in million-cell single-cell datasets, especially preserving rare populations"

    print(f"=== Naive RAG (one-shot, embedding only) ===")
    naive = stub_embedding(query, k=10)
    for c in naive:
        marker = " ← TARGET (missed)" if c.chunk_id == "p-2023-method-x" else ""
        print(f"  {c.chunk_id:25s}  year={c.metadata['year']}  sem={c.score_semantic:.2f}{marker}")
    target_naive_rank = next(
        (i for i, c in enumerate(naive) if c.chunk_id == "p-2023-method-x"), -1
    )
    print(f"  → target paper rank in naive RAG: "
          f"{target_naive_rank if target_naive_rank >= 0 else 'NOT FOUND'}")
    print()

    print(f"=== Agentic RAG (decompose + iterative + hypothesis + triangulate) ===")
    result = rag.research(query=query)
    print(f"hypothesis        : {result['hypothesis']}")
    print(f"answer            : {result['answer']}")
    print(f"confidence        : {result['confidence']}")
    print(f"supporting evidence ({len(result['supporting_evidence'])}):")
    for cid in result["supporting_evidence"]:
        target_marker = " ← TARGET FOUND" if cid == "p-2023-method-x" else ""
        print(f"  · {cid}{target_marker}")
    print()
    print(f"retrieval events ({len(result['retrieval_events'])}):")
    for e in result["retrieval_events"]:
        print(f"  [{e.mode.value:13s}]  query='{e.query[:60]}'  returned={len(e.chunks_returned)} chunks")


if __name__ == "__main__":
    main()
