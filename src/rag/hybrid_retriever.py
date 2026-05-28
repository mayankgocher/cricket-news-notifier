"""
Hybrid Retriever — Full advanced retrieval pipeline.

Pipeline:
  1. BM25 search          → top-15 (keyword, exact match)
  2. ChromaDB dense search → top-15 (semantic similarity)
  3. RRF fusion            → all unique chunks (~20-25)
  4. MMR                   → top-10 diverse chunks
  5. Cross-encoder reranker→ top-5 precise chunks

BM25 and Dense run on the same corpus. RRF merges by rank position only
(not raw scores), so different score scales don't matter.

MMR penalizes redundancy before the expensive reranker step.
Reranker makes the final precise selection from the diverse pool.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_core.documents import Document

from src.rag.vectordb import get_vectorstore, _get_embeddings
from src.rag import bm25_index
from src.rag.reranker import rerank

# RRF constant — standard value, smooths rank differences
RRF_K = 60

# Pipeline parameters
BM25_TOP_N   = 15   # BM25 candidates
DENSE_TOP_N  = 15   # Dense candidates
MMR_TOP_N    = 10   # After MMR diversity filtering
RERANK_TOP_N = 5    # Final chunks passed to LLM


def _ensure_bm25_built() -> None:
    """Build BM25 index from ChromaDB if not already built."""
    if bm25_index.is_built():
        return

    print("   🔨 Building BM25 index from ChromaDB...")
    store = get_vectorstore()

    # Fetch all documents from ChromaDB
    collection = store._collection
    result = collection.get(include=["documents", "metadatas"])

    docs = [
        Document(
            page_content=text,
            metadata=meta or {},
        )
        for text, meta in zip(result["documents"], result["metadatas"])
    ]

    bm25_index.build_index(docs)


def _rrf_merge(
    bm25_results: list[tuple[Document, float]],
    dense_results: list[tuple[Document, float]],
) -> list[Document]:
    """
    Reciprocal Rank Fusion — merges two ranked lists by rank position only.

    RRF score = 1/(k + rank_bm25) + 1/(k + rank_dense)
    Chunks appearing in both lists are rewarded heavily.
    Chunks appearing in only one list still get partial credit.

    Returns deduplicated list sorted by RRF score descending.
    """
    scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    # Score BM25 ranked list
    for rank, (doc, _) in enumerate(bm25_results, start=1):
        key = doc.page_content  # use content as dedup key
        scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank)
        doc_map[key] = doc

    # Score dense ranked list
    for rank, (doc, _) in enumerate(dense_results, start=1):
        key = doc.page_content
        scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank)
        doc_map[key] = doc

    # Sort by RRF score descending — return all unique chunks
    sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
    return [doc_map[k] for k in sorted_keys]


def _mmr_select(
    query: str,
    docs: list[Document],
    top_n: int = MMR_TOP_N,
    lambda_mult: float = 0.5,
) -> list[Document]:
    """
    Maximal Marginal Relevance — select diverse top-n from candidates.

    Each step picks the document that maximises:
        MMR = λ × relevance_to_query - (1-λ) × max_similarity_to_selected

    lambda_mult=0.5 balances relevance and diversity equally.

    Uses the same embedding model as ChromaDB for consistency.
    """
    if len(docs) <= top_n:
        return docs

    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    embeddings_model = _get_embeddings()

    # Embed query and all candidate docs
    query_emb = embeddings_model.embed_query(query)
    doc_embs  = embeddings_model.embed_documents([d.page_content for d in docs])

    query_emb = np.array(query_emb).reshape(1, -1)
    doc_embs  = np.array(doc_embs)

    # Relevance of each doc to the query
    relevance = cosine_similarity(query_emb, doc_embs)[0]

    selected_indices: list[int] = []
    remaining = list(range(len(docs)))

    for _ in range(top_n):
        if not remaining:
            break

        if not selected_indices:
            # First pick: most relevant to query
            best = max(remaining, key=lambda i: relevance[i])
        else:
            # Subsequent picks: balance relevance vs redundancy
            selected_embs = doc_embs[selected_indices]
            best = max(
                remaining,
                key=lambda i: (
                    lambda_mult * relevance[i]
                    - (1 - lambda_mult)
                    * cosine_similarity(doc_embs[i].reshape(1, -1), selected_embs).max()
                ),
            )

        selected_indices.append(best)
        remaining.remove(best)

    return [docs[i] for i in selected_indices]


def retrieve(query: str) -> list[Document]:
    """
    Full hybrid retrieval pipeline for a single query.

    Steps:
      1. Ensure BM25 index is built (no-op if already cached)
      2. BM25 top-15 + ChromaDB dense top-15 in parallel
      3. RRF merge → all unique chunks
      4. MMR → top-10 diverse
      5. Cross-encoder reranker → top-5

    Args:
        query: Standalone query string (already rewritten if needed)

    Returns:
        Top-5 reranked Documents ready for LLM context
    """
    # Step 1 — ensure BM25 is ready
    _ensure_bm25_built()

    # Step 2a — BM25 search
    bm25_results = bm25_index.search(query, n_results=BM25_TOP_N)

    # Step 2b — ChromaDB dense search
    store = get_vectorstore()
    dense_raw = store.similarity_search_with_relevance_scores(query, k=DENSE_TOP_N)

    # Step 3 — RRF merge → all unique chunks
    merged = _rrf_merge(bm25_results, dense_raw)

    # Step 4 — MMR diversity filtering
    diverse = _mmr_select(query, merged, top_n=MMR_TOP_N)

    # Step 5 — Cross-encoder reranking → final top-5
    final = rerank(query, diverse, top_n=RERANK_TOP_N)

    return final
