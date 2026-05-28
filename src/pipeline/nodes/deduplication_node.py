"""
Deduplication Node - Removes duplicate news using semantic embeddings + cosine similarity.
No LLM calls. Uses the same HuggingFaceEmbeddings model as vectordb.py.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from src.rag.vectordb import _embeddings
from src.config.settings import DEDUP_THRESHOLD

# Source priority — lower index = higher priority
SOURCE_PRIORITY = ["espn", "hindustan_times", "india_today", "indian_express", "crictracker", "bbc_cricket", "guardian_cricket", "reddit", "twitter"]


def _source_rank(source: str) -> int:
    """Lower rank = higher priority source."""
    source = source.lower()
    for i, s in enumerate(SOURCE_PRIORITY):
        if s in source:
            return i
    return len(SOURCE_PRIORITY)


def deduplication_node(state: dict) -> dict:
    """
    Remove duplicate news items using semantic similarity.

    Steps:
        1. Embed all headlines in one batch
        2. Compute cosine similarity matrix
        3. For each duplicate pair above threshold, keep higher-priority source
        4. Return deduplicated state

    Args:
        state: Pipeline state with 'news_items'

    Returns:
        Updated state with deduplicated news
    """
    print("\n" + "=" * 50)
    print("🔄 DEDUPLICATION NODE - Removing duplicates...")
    print(f"   Threshold: {DEDUP_THRESHOLD}")
    print("=" * 50)

    news_items = state.get("news_items", [])

    if len(news_items) <= 5:
        print("✅ Too few items, skipping deduplication")
        return state

    try:
        # Step 1 — Embed all headlines in one batch
        headlines = [item["headline"] for item in news_items]
        vectors = np.array(_embeddings.embed_documents(headlines))

        # Step 2 — Cosine similarity matrix (N x N)
        sim_matrix = cosine_similarity(vectors)

        # Step 3 — Greedy deduplication
        n = len(news_items)
        is_duplicate = [False] * n

        for i in range(n):
            if is_duplicate[i]:
                continue
            for j in range(i + 1, n):
                if is_duplicate[j]:
                    continue
                if sim_matrix[i][j] >= DEDUP_THRESHOLD:
                    rank_i = _source_rank(news_items[i].get("source", ""))
                    rank_j = _source_rank(news_items[j].get("source", ""))

                    if rank_i <= rank_j:
                        is_duplicate[j] = True
                        print(f"  🗑  Duplicate (score={sim_matrix[i][j]:.2f}): "
                              f"[{news_items[j]['source']}] {news_items[j]['headline'][:60]}...")
                    else:
                        is_duplicate[i] = True
                        print(f"  🗑  Duplicate (score={sim_matrix[i][j]:.2f}): "
                              f"[{news_items[i]['source']}] {news_items[i]['headline'][:60]}...")
                        break

        # Step 4 — Filter
        deduplicated = [item for i, item in enumerate(news_items) if not is_duplicate[i]]

        print(f"\n✅ Reduced {len(news_items)} → {len(deduplicated)} items")
        state["news_items"] = deduplicated

    except Exception as e:
        print(f"⚠️ Deduplication error: {e} — keeping all items")

    return state


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    state = {
        "news_items": [
            {"headline": "Kohli scores century against Australia", "source": "espn"},
            {"headline": "KOHLI 100! What an innings vs AUS", "source": "twitter"},
            {"headline": "Bumrah takes 5 wickets in first innings", "source": "reddit"},
            {"headline": "India's Bumrah gets fifer against England", "source": "espn"},
            {"headline": "IPL 2025 auction date announced", "source": "reddit"},
        ]
    }

    result = deduplication_node(state)
    print("\nKept items:")
    for item in result["news_items"]:
        print(f"  [{item['source']}] {item['headline']}")