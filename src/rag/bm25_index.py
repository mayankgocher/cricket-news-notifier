"""
BM25 Index — In-memory keyword search alongside ChromaDB dense retrieval.

Built once at startup from all chunks in ChromaDB.
Rebuilt automatically whenever called after a process restart.

IDF naturally down-weights stopwords like "who", "is", "the" —
high-value cricket terms like player names, team codes, scores
get full weight automatically.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rank_bm25 import BM25Okapi
from langchain_core.documents import Document

# Module-level cache — built once per process, stays in memory
_bm25: BM25Okapi | None = None
_bm25_docs: list[Document] = []


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer."""
    return text.lower().split()


def build_index(docs: list[Document]) -> None:
    """
    Build BM25 index from a list of LangChain Documents.
    Called once at startup from hybrid_retriever.
    """
    global _bm25, _bm25_docs
    _bm25_docs = docs
    tokenized = [_tokenize(doc.page_content) for doc in docs]
    _bm25 = BM25Okapi(tokenized)
    print(f"   ✅ BM25 index built — {len(docs)} chunks")


def search(query: str, n_results: int = 15) -> list[tuple[Document, float]]:
    """
    Search BM25 index and return top-n (Document, score) pairs.
    Score is raw BM25 score (not normalized) — used only for RRF rank position.

    Args:
        query:     User query string
        n_results: Number of top results to return

    Returns:
        List of (Document, bm25_score) sorted by score descending
    """
    if _bm25 is None or not _bm25_docs:
        return []

    tokens = _tokenize(query)
    scores = _bm25.get_scores(tokens)

    # Pair each doc with its score, sort descending
    scored = sorted(
        zip(_bm25_docs, scores),
        key=lambda x: x[1],
        reverse=True,
    )
    return scored[:n_results]


def get_doc_count() -> int:
    """Return number of chunks indexed."""
    return len(_bm25_docs)


def is_built() -> bool:
    """Return True if index has been built."""
    return _bm25 is not None and len(_bm25_docs) > 0
