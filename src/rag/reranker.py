"""
Reranker — Cross-encoder based precise relevance scoring.

Uses cross-encoder/ms-marco-MiniLM-L-6-v2 (small, fast, CPU-friendly).
Takes (query, chunk) pairs jointly — far more accurate than cosine similarity.

Pipeline position: after MMR (receives ~10 diverse chunks), outputs top-5.
Latency: ~40-60ms for 10 pairs on CPU.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.documents import Document

# Lazy-loaded — avoid slow model init at import time
_reranker = None


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        print("   ✅ Cross-encoder reranker loaded")
    return _reranker


def rerank(query: str, docs: list[Document], top_n: int = 5) -> list[Document]:
    """
    Rerank documents using cross-encoder joint scoring.

    Each (query, chunk) pair is scored together — the model reads both
    simultaneously, giving far more accurate relevance than bi-encoder
    cosine similarity.

    Args:
        query:  User query string
        docs:   Candidate documents (typically MMR output, ~10 docs)
        top_n:  Number of top documents to return after reranking

    Returns:
        Top-n documents sorted by cross-encoder relevance score (best first)
    """
    if not docs:
        return []

    if len(docs) <= top_n:
        # Not enough candidates to rerank — return as-is
        return docs

    reranker = _get_reranker()

    # Build (query, passage) pairs for the cross-encoder
    pairs = [(query, doc.page_content) for doc in docs]
    scores = reranker.predict(pairs)

    # Sort by score descending, keep top_n
    scored_docs = sorted(
        zip(docs, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return [doc for doc, _ in scored_docs[:top_n]]
