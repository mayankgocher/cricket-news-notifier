"""
RAG Pipeline Latency Benchmarker
Measures retrieval, LLM, and total latency across multiple questions.
Run BEFORE and AFTER advanced RAG implementation to compare.

Usage:
    python benchmark_latency.py --tag baseline
    python benchmark_latency.py --tag advanced_rag
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config.settings import GROQ_API_KEY
from src.rag.vectordb import get_retriever

# ── Test questions (representative mix of types) ──────────────────────────────
TEST_QUESTIONS = [
    "Who is Vaibhav Suryavanshi?",
    "How many wickets did Jasprit Bumrah take in IPL 2026?",
    "What happened in the India vs England T20 World Cup match?",
    "Which team won the IPL 2026 title?",
    "What is Rohit Sharma's ODI record?",
    "Who scored the fastest century in IPL history?",
    "What was Virat Kohli's performance against KKR?",
    "How did Mumbai Indians perform in IPL 2026?",
]

RUNS_PER_QUESTION = 3  # Average over multiple runs to reduce variance

# ── LLM + Prompt (same as query_engine.py) ────────────────────────────────────
_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.1-8b-instant", temperature=0.3)

_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a cricket news assistant. Answer the user's question using "
        "only the context below. Be concise (2-4 sentences). "
        "If the context doesn't contain the answer, say so.\n\n"
        "CONTEXT:\n{context}"
    )),
    ("human", "{question}"),
])

def _format_docs(docs) -> str:
    return "\n\n".join(
        f"[{doc.metadata.get('source', 'unknown').upper()}] {doc.page_content}"
        for doc in docs
    )


def measure_single(question: str, retriever) -> dict:
    """Measure latency for one question. Returns breakdown in ms."""

    # ── Stage 1: Retrieval ────────────────────────────────────────────────────
    t0 = time.perf_counter()
    docs = retriever.invoke(question)
    retrieval_ms = (time.perf_counter() - t0) * 1000

    context = _format_docs(docs)

    # ── Stage 2: LLM ─────────────────────────────────────────────────────────
    t1 = time.perf_counter()
    answer = (_prompt | _llm | StrOutputParser()).invoke(
        {"context": context, "question": question}
    )
    llm_ms = (time.perf_counter() - t1) * 1000

    total_ms = retrieval_ms + llm_ms

    return {
        "retrieval_ms": round(retrieval_ms, 1),
        "llm_ms":       round(llm_ms, 1),
        "total_ms":     round(total_ms, 1),
        "docs_retrieved": len(docs),
    }


def run_benchmark(tag: str):
    print(f"\n{'='*60}")
    print(f"  RAG LATENCY BENCHMARK  |  tag: {tag}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  {len(TEST_QUESTIONS)} questions × {RUNS_PER_QUESTION} runs each")
    print(f"{'='*60}\n")

    retriever = get_retriever()
    results = []

    for i, question in enumerate(TEST_QUESTIONS):
        print(f"[{i+1}/{len(TEST_QUESTIONS)}] {question}")
        run_times = []

        for run in range(RUNS_PER_QUESTION):
            m = measure_single(question, retriever)
            run_times.append(m)
            print(f"  run {run+1}: retrieval={m['retrieval_ms']}ms  llm={m['llm_ms']}ms  total={m['total_ms']}ms")
            time.sleep(0.5)  # avoid rate limiting

        avg = {
            "question":       question,
            "avg_retrieval_ms": round(sum(r["retrieval_ms"] for r in run_times) / RUNS_PER_QUESTION, 1),
            "avg_llm_ms":       round(sum(r["llm_ms"]       for r in run_times) / RUNS_PER_QUESTION, 1),
            "avg_total_ms":     round(sum(r["total_ms"]     for r in run_times) / RUNS_PER_QUESTION, 1),
            "docs_retrieved":   run_times[0]["docs_retrieved"],
        }
        results.append(avg)
        print(f"  → avg total: {avg['avg_total_ms']}ms\n")

    # ── Summary ───────────────────────────────────────────────────────────────
    avg_retrieval = round(sum(r["avg_retrieval_ms"] for r in results) / len(results), 1)
    avg_llm       = round(sum(r["avg_llm_ms"]       for r in results) / len(results), 1)
    avg_total     = round(sum(r["avg_total_ms"]     for r in results) / len(results), 1)
    min_total     = min(r["avg_total_ms"] for r in results)
    max_total     = max(r["avg_total_ms"] for r in results)

    print("=" * 60)
    print(f"  SUMMARY ({tag})")
    print("=" * 60)
    print(f"  Avg retrieval latency : {avg_retrieval} ms")
    print(f"  Avg LLM latency       : {avg_llm} ms")
    print(f"  Avg total latency     : {avg_total} ms")
    print(f"  Min / Max total       : {min_total} ms / {max_total} ms")
    print("=" * 60)

    # ── Save to JSON ──────────────────────────────────────────────────────────
    os.makedirs("latency_results", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = f"latency_results/{tag}_{ts}.json"

    output = {
        "tag":              tag,
        "timestamp":        ts,
        "runs_per_question": RUNS_PER_QUESTION,
        "summary": {
            "avg_retrieval_ms": avg_retrieval,
            "avg_llm_ms":       avg_llm,
            "avg_total_ms":     avg_total,
            "min_total_ms":     min_total,
            "max_total_ms":     max_total,
        },
        "per_question": results,
    }

    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Results saved → {out_path}")
    return output


def compare(path1: str, path2: str):
    """Compare two benchmark runs side by side."""
    with open(path1) as f: r1 = json.load(f)
    with open(path2) as f: r2 = json.load(f)

    print(f"\n{'='*60}")
    print(f"  LATENCY COMPARISON")
    print(f"  {r1['tag']}  vs  {r2['tag']}")
    print(f"{'='*60}")
    print(f"  {'Metric':<25} {r1['tag']:>12} {r2['tag']:>12} {'Delta':>10}")
    print(f"  {'-'*55}")

    for key, label in [
        ("avg_retrieval_ms", "Avg retrieval (ms)"),
        ("avg_llm_ms",       "Avg LLM (ms)"),
        ("avg_total_ms",     "Avg total (ms)"),
        ("min_total_ms",     "Min total (ms)"),
        ("max_total_ms",     "Max total (ms)"),
    ]:
        v1 = r1["summary"][key]
        v2 = r2["summary"][key]
        delta = round(v2 - v1, 1)
        arrow = "▲" if delta > 0 else "▼"
        print(f"  {label:<25} {v1:>12} {v2:>12} {arrow} {abs(delta):>7} ms")

    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag",     default="baseline", help="Label for this run e.g. baseline / advanced_rag")
    parser.add_argument("--compare", nargs=2, metavar="JSON", help="Compare two result JSON files")
    args = parser.parse_args()

    if args.compare:
        compare(args.compare[0], args.compare[1])
    else:
        run_benchmark(args.tag)