"""
Benchmark Script - Measures execution time of each pipeline node
Run with: python benchmark_pipeline.py

After implementing semantic deduplication, run again and compare results.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pipeline.nodes.ingestion_node import ingestion_node
from src.pipeline.nodes.deduplication_node import deduplication_node
from src.pipeline.nodes.sentiment_node import sentiment_node
from src.pipeline.nodes.newsletter_node import newsletter_node
from src.pipeline.nodes.enrichment_node import enrichment_node


# ── helpers ──────────────────────────────────────────────────────────────────

def fmt(seconds: float) -> str:
    if seconds >= 60:
        return f"{seconds / 60:.1f} min"
    return f"{seconds:.2f}s"


def run_node(label: str, fn, state: dict) -> tuple[dict, float]:
    print(f"\n{'─' * 50}")
    print(f"⏱  Running: {label}")
    print(f"{'─' * 50}")
    start = time.perf_counter()
    result = fn(state)
    elapsed = time.perf_counter() - start
    print(f"✅  {label} done in {fmt(elapsed)}")
    return result, elapsed


# ── main benchmark ────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("🏏  PIPELINE BENCHMARK")
    print("=" * 60)

    timings: dict[str, float] = {}
    state: dict = {
        "news_items": [],
        "newsletter_content": None,
        "executive_summary": None,
        "email_sent": None,
        "telegram_sent": None,
        "enrichment_complete": None,
    }

    total_start = time.perf_counter()

    # 1. Ingestion
    state, t = run_node("Ingestion", ingestion_node, state)
    timings["ingestion"] = t
    items_after_ingestion = len(state.get("news_items", []))

    # 2. Deduplication  ← this is the node we're experimenting with
    state, t = run_node("Deduplication (LLM)", deduplication_node, state)
    timings["deduplication"] = t
    items_after_dedup = len(state.get("news_items", []))

    # 3. Sentiment
    state, t = run_node("Sentiment", sentiment_node, state)
    timings["sentiment"] = t

    # 4. Newsletter
    state, t = run_node("Newsletter", newsletter_node, state)
    timings["newsletter"] = t

    # 5. Enrichment
    state, t = run_node("Enrichment", enrichment_node, state)
    timings["enrichment"] = t

    total_elapsed = time.perf_counter() - total_start

    # ── Report ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📊  BENCHMARK RESULTS")
    print("=" * 60)
    print(f"  {'Node':<30} {'Time':>10}   {'% of total':>10}")
    print(f"  {'─'*30} {'─'*10}   {'─'*10}")

    for node, t in timings.items():
        pct = (t / total_elapsed) * 100
        bar = "█" * int(pct / 5)
        print(f"  {node:<30} {fmt(t):>10}   {pct:>8.1f}%  {bar}")

    print(f"  {'─'*30} {'─'*10}   {'─'*10}")
    print(f"  {'TOTAL':<30} {fmt(total_elapsed):>10}   {'100.0%':>10}")

    print(f"\n  📰 Items after ingestion  : {items_after_ingestion}")
    print(f"  📰 Items after dedup      : {items_after_dedup}")
    print(f"  🗑  Duplicates removed     : {items_after_ingestion - items_after_dedup}")

    print("\n" + "=" * 60)
    print("  💡 Run again after switching to semantic deduplication")
    print("     and compare the 'Deduplication' row.")
    print("=" * 60 + "\n")

    return timings


if __name__ == "__main__":
    main()