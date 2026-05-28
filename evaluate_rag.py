"""
RAG Pipeline Evaluator — Cricket Daily Digest
==============================================
Compatible with RAGAS 0.4.x

KEY DESIGN DECISIONS:
  - Testset generation  → llama-3.1-8b-instant  (500K TPD, all 6 keys)
  - Metric evaluation   → llama-3.3-70b-versatile (100K TPD × 6 keys = 600K)
  - RunConfig(max_workers=2) → throttles RAGAS concurrency, prevents 429 bursts
  - RotatingChatGroq    → auto-switches keys on any 429, no manual intervention
  - 50-doc cap          → keeps token cost predictable (~30K for extraction)
  - Snapshot files      → same 50 docs + same questions reused for advanced RAG run
                          so before/after comparison is perfectly clean

FILES WRITTEN:
  eval_docs_snapshot.json     ← 50 doc IDs locked in on first run, reused forever
  eval_testset_snapshot.json  ← questions + ground truths locked in, reused forever
  eval_results/<tag>_<ts>.json← scores for this run

USAGE:
  python evaluate_rag.py --tag baseline          # first run
  python evaluate_rag.py --tag advanced_rag      # after improvements (reuses snapshots)
  python evaluate_rag.py --compare eval_results/baseline_X.json eval_results/advanced_rag_X.json
  python evaluate_rag.py --reset-snapshots       # force regenerate questions (new day, new data)
"""

import os, sys, json, argparse, time, asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

# ── Project imports ────────────────────────────────────────────────────────────
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.outputs import ChatResult

from src.config.settings import (
    GROQ_API_KEY,    GROQ_API_KEY_2,  GROQ_API_KEY_3,
    GROQ_API_KEY_4,  GROQ_API_KEY_5,  GROQ_API_KEY_6,
    GROQ_API_KEY_7,  GROQ_API_KEY_8,  GROQ_API_KEY_9,
    GROQ_API_KEY_10, GROQ_API_KEY_11, GROQ_API_KEY_12,
)
from src.rag.vectordb import get_vectorstore, get_retriever, get_count
from src.rag.hybrid_retriever import retrieve as hybrid_retrieve

# ── RAGAS imports (evaluation only — TestsetGenerator bypassed) ───────────────
# Import from ragas.metrics (not .collections) — these are singleton instances,
# not classes. The deprecation warning is harmless; .collections returns modules.
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    )
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas import evaluate
from datasets import Dataset

try:
    from ragas import RunConfig
except ImportError:
    from ragas.run_config import RunConfig


# ══════════════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════════════

GEN_MODEL  = "llama-3.3-70b-versatile"  # testset generation — 70b follows JSON schema reliably
EVAL_MODEL = "llama-3.3-70b-versatile"  # metric evaluation  — same model, 6 keys = 600K TPD

DOCS_SNAPSHOT    = Path("eval_docs_snapshot.json")
TESTSET_SNAPSHOT = Path("eval_testset_snapshot.json")
EVAL_RESULTS_DIR = Path("eval_results")
EVAL_RESULTS_DIR.mkdir(exist_ok=True)

N_DOCS      = 50   # docs sampled from ChromaDB for testset generation
N_QUESTIONS = 50   # target QA pairs to generate


# ══════════════════════════════════════════════════════════════════════════════
# KEY LOADING  — from settings.py (all 6 keys)
# ══════════════════════════════════════════════════════════════════════════════

def _load_keys() -> List[str]:
    """Return all non-empty Groq API keys from settings.py."""
    keys = [
        k for k in [
            GROQ_API_KEY,    GROQ_API_KEY_2,  GROQ_API_KEY_3,
            GROQ_API_KEY_4,  GROQ_API_KEY_5,  GROQ_API_KEY_6,
            GROQ_API_KEY_7,  GROQ_API_KEY_8,  GROQ_API_KEY_9,
            GROQ_API_KEY_10, GROQ_API_KEY_11, GROQ_API_KEY_12,
        ]
        if k and k.strip()
    ]
    if not keys:
        raise ValueError("No GROQ_API_KEY found in .env / settings.py")
    return keys

ALL_KEYS = _load_keys()
print(f"   🔑 Loaded {len(ALL_KEYS)} Groq API key(s)")


# ══════════════════════════════════════════════════════════════════════════════
# ROTATING CHAT GROQ
# Wraps multiple ChatGroq instances; on 429, switches to the next key
# automatically. Works for both sync and async calls (RAGAS uses async).
# ══════════════════════════════════════════════════════════════════════════════

class RotatingChatGroq(BaseChatModel):
    """
    LangChain-compatible ChatModel that round-robins Groq API keys on 429.

    Because RAGAS calls _agenerate internally (async), both sync and async
    variants are implemented here.
    """
    llm_model: str
    api_keys: List[str]
    temp: float = 0.0

    # Private state — bypasses Pydantic validation
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, "_idx", 0)
        object.__setattr__(self, "_pool", [
            ChatGroq(api_key=k, model=self.llm_model, temperature=self.temp)
            for k in self.api_keys
        ])

    @property
    def _llm_type(self) -> str:
        return "rotating-groq"

    def _cur(self) -> ChatGroq:
        return self._pool[self._idx]

    def _next(self) -> None:
        new = (self._idx + 1) % len(self._pool)
        object.__setattr__(self, "_idx", new)
        print(f"\n   🔄 Rate limited → rotating to key {new + 1}/{len(self._pool)}")
        time.sleep(2)

    # ── Sync ──────────────────────────────────────────────────────────────────
    def _generate(
        self, messages: List[BaseMessage],
        stop=None, run_manager=None, **kwargs
    ) -> ChatResult:
        for _ in range(len(self._pool)):
            try:
                return self._cur()._generate(
                    messages, stop=stop, run_manager=run_manager, **kwargs
                )
            except Exception as e:
                if "429" in str(e) or "rate_limit_exceeded" in str(e):
                    self._next()
                else:
                    raise
        raise RuntimeError("All Groq API keys exhausted. Wait for limit reset.")

    # ── Async (used by RAGAS internally) ──────────────────────────────────────
    async def _agenerate(
        self, messages: List[BaseMessage],
        stop=None, run_manager=None, **kwargs
    ) -> ChatResult:
        for _ in range(len(self._pool)):
            try:
                return await self._cur()._agenerate(
                    messages, stop=stop, run_manager=run_manager, **kwargs
                )
            except Exception as e:
                if "429" in str(e) or "rate_limit_exceeded" in str(e):
                    self._next()
                    await asyncio.sleep(2)
                else:
                    raise
        raise RuntimeError("All Groq API keys exhausted. Wait for limit reset.")


# ══════════════════════════════════════════════════════════════════════════════
# LLM FACTORIES
# ══════════════════════════════════════════════════════════════════════════════

def gen_llm() -> RotatingChatGroq:
    """8b model — all 6 keys — for testset generation."""
    return RotatingChatGroq(llm_model=GEN_MODEL, api_keys=ALL_KEYS, temp=0.0)


def eval_llm() -> RotatingChatGroq:
    """70b model — all 6 keys — for RAGAS metric evaluation."""
    return RotatingChatGroq(llm_model=EVAL_MODEL, api_keys=ALL_KEYS, temp=0.0)


def rag_llm() -> ChatGroq:
    """Production RAG chain — 8b on key 1 — mirrors query_engine.py exactly."""
    return ChatGroq(api_key=ALL_KEYS[0], model="llama-3.1-8b-instant", temperature=0.3)


# ══════════════════════════════════════════════════════════════════════════════
# RAG PIPELINE  (mirrors query_engine.py exactly — no improvements here)
# ══════════════════════════════════════════════════════════════════════════════

_RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a cricket news assistant. Answer the user's question using "
        "only the context below. Be concise (2-4 sentences). "
        "If the context doesn't contain the answer, say so.\n\n"
        "CONTEXT:\n{context}"
    )),
    ("human", "{question}"),
])


def _fmt(docs) -> str:
    return "\n\n".join(
        f"[{d.metadata.get('source', 'unknown').upper()}] {d.page_content}"
        for d in docs
    )


def run_rag(question: str, retriever=None) -> dict:
    """
    Run one question through the advanced RAG pipeline.

    retriever arg kept for signature compatibility but unused —
    hybrid_retrieve() handles the full BM25+Dense+RRF→MMR→Reranker pipeline.
    session_id is None (eval mode) — query rewriting is skipped so results
    are clean and directly comparable to baseline.
    """
    docs    = hybrid_retrieve(question)
    context = _fmt(docs)
    answer  = (_RAG_PROMPT | rag_llm() | StrOutputParser()).invoke(
        {"context": context, "question": question}
    )
    return {
        "answer":   answer,
        "contexts": [d.page_content for d in docs],
    }


# ══════════════════════════════════════════════════════════════════════════════
# SNAPSHOT: 50 DOCS
# Locked on first run. Reused on every subsequent run so baseline and
# advanced_rag are always evaluated on identical source documents.
# ══════════════════════════════════════════════════════════════════════════════

def load_or_create_doc_snapshot() -> list:
    """
    Returns a list of 50 LangChain Document objects.
    First call: samples from ChromaDB and saves to DOCS_SNAPSHOT.
    Later calls: loads from file — same docs every time.
    """
    from langchain_core.documents import Document

    if DOCS_SNAPSHOT.exists():
        print(f"   📂 Loading doc snapshot from {DOCS_SNAPSHOT}  (reusing for consistency)")
        with open(DOCS_SNAPSHOT, encoding="utf-8") as f:
            saved = json.load(f)
        return [Document(page_content=d["text"], metadata=d["meta"]) for d in saved]

    print(f"   🆕 No snapshot found — sampling {N_DOCS} docs from ChromaDB")
    vs  = get_vectorstore()
    raw = vs.get(limit=300)

    if not raw["documents"]:
        raise ValueError("ChromaDB is empty. Run: python run_pipeline.py")

    import random
    random.seed(42)  # reproducible sample
    indices = random.sample(range(len(raw["documents"])), min(N_DOCS, len(raw["documents"])))

    docs = [
        Document(
            page_content=raw["documents"][i],
            metadata=raw["metadatas"][i] or {},
        )
        for i in indices
    ]

    # Save so future runs use the exact same docs
    with open(DOCS_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump([{"text": d.page_content, "meta": d.metadata} for d in docs], f, indent=2)

    print(f"   💾 Saved {len(docs)} docs → {DOCS_SNAPSHOT}")
    return docs


# ══════════════════════════════════════════════════════════════════════════════
# SNAPSHOT: TESTSET (questions + ground truths)
#
# WHY WE BYPASS RAGAS TestsetGenerator:
#   RAGAS 0.4.x SummaryExtractor sends a strict JSON-schema prompt to the LLM.
#   Groq models (even 70b) sometimes return plain text instead of JSON, causing
#   OutputParserException and crashing the entire generation pipeline.
#
# OUR APPROACH:
#   Use Groq's native json_object response_format — this guarantees valid JSON
#   at the API level, regardless of what the model "wants" to return. We write
#   our own prompt, get deterministic JSON back, and build the testset ourselves.
#   RAGAS is still used for metric evaluation — only generation is replaced.
# ══════════════════════════════════════════════════════════════════════════════

# Question type prompts — mix of factual, analytical, and comparative
# to cover a similar distribution to RAGAS's simple/reasoning/multi_context
_QA_PROMPTS = [
    # Factual — specific who/what/when/where
    """You are a cricket analyst. Read the article below and write ONE specific factual question
(about a player, score, team, match result, or event) that is clearly answered in the article.
Return ONLY a JSON object with two fields:
{{"question": "your question here", "ground_truth": "the complete answer from the article"}}

Article:
{text}""",

    # Analytical — why/how/implications
    """You are a cricket analyst. Read the article below and write ONE analytical question
(about why something happened, what it means, or what the impact is) that can be answered from the article.
Return ONLY a JSON object with two fields:
{{"question": "your analytical question here", "ground_truth": "the complete answer from the article"}}

Article:
{text}""",

    # Comparative/contextual — performance, trends, significance
    """You are a cricket analyst. Read the article below and write ONE question about
significance, performance quality, or comparison (e.g. "How significant was X?" or "How did X perform?")
that is clearly answered in the article.
Return ONLY a JSON object with two fields:
{{"question": "your question here", "ground_truth": "the complete answer from the article"}}

Article:
{text}""",
]

_QA_TYPES = ["factual", "analytical", "contextual"]


def _generate_one_qa(doc_text: str, prompt_template: str, q_type: str,
                     key_pool: list[str]) -> dict | None:
    """
    Generate one QA pair from a single doc using Groq JSON mode.
    Rotates keys on 429. Returns None if all keys fail.
    """
    prompt = prompt_template.format(text=doc_text[:1500])  # cap to avoid token overflow

    for attempt in range(len(key_pool) * 2):  # allow 2 full rotations
        key = key_pool[attempt % len(key_pool)]
        try:
            llm = ChatGroq(
                api_key=key,
                model=GEN_MODEL,
                temperature=0,
                model_kwargs={"response_format": {"type": "json_object"}},
            )
            response = llm.invoke([HumanMessage(content=prompt)])
            data = json.loads(response.content)

            q = data.get("question", "").strip()
            gt = data.get("ground_truth", "").strip()

            if q and gt and len(q) > 10 and len(gt) > 10:
                return {"question": q, "ground_truth": gt, "type": q_type}

        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit_exceeded" in err:
                print(f"\n   🔄 Rate limited on key {attempt % len(key_pool) + 1} → rotating...")
                time.sleep(3)
                continue
            # JSON parse error or other — skip this doc silently
            break

    return None


def load_or_create_testset(docs: list, n: int = N_QUESTIONS) -> list[dict]:
    """
    Returns list of {question, ground_truth, type} dicts.
    First call: generates using Groq JSON mode (guaranteed valid JSON).
    Later calls: loads from snapshot file.
    """
    if TESTSET_SNAPSHOT.exists():
        print(f"   📂 Loading testset snapshot from {TESTSET_SNAPSHOT}  (reusing for consistency)")
        with open(TESTSET_SNAPSHOT, encoding="utf-8") as f:
            return json.load(f)

    print(f"\n📋 Generating {n} QA pairs using Groq JSON mode...")
    print(f"   Model    : {GEN_MODEL}")
    print(f"   Strategy : json_object response_format (guaranteed valid JSON)")
    print(f"   Docs     : {len(docs)}, targeting {n} QA pairs")

    import random
    random.seed(42)

    # Cycle through question types for diversity
    results = []
    attempts = 0
    doc_pool = docs.copy()
    random.shuffle(doc_pool)

    for i, doc in enumerate(doc_pool):
        if len(results) >= n:
            break

        q_type_idx = i % len(_QA_PROMPTS)
        prompt     = _QA_PROMPTS[q_type_idx]
        q_type     = _QA_TYPES[q_type_idx]

        print(f"   [{len(results)+1}/{n}] Generating {q_type} question from doc {i+1}/{len(doc_pool)}...")

        qa = _generate_one_qa(doc.page_content, prompt, q_type, ALL_KEYS)
        if qa:
            results.append(qa)
        else:
            print(f"         ⚠️  Skipped doc {i+1} (could not generate valid QA)")

        time.sleep(0.5)  # gentle pacing

    print(f"\n   ✅ Generated {len(results)} QA pairs")

    with open(TESTSET_SNAPSHOT, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"   💾 Saved testset → {TESTSET_SNAPSHOT}")
    return results


# ══════════════════════════════════════════════════════════════════════════════
# EVALUATION
# ══════════════════════════════════════════════════════════════════════════════

def run_evaluation(testset: list[dict], retriever, tag: str) -> dict:
    """
    Step 1: Run every question through the RAG pipeline (contexts + answer).
    Step 2: Pass all rows to RAGAS evaluate() with the 70b eval LLM.
    """
    print(f"\n🔍 Running RAG pipeline on {len(testset)} questions...")

    rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for i, item in enumerate(testset, 1):
        q = item["question"]
        print(f"   [{i}/{len(testset)}] {q[:70]}...")
        r = run_rag(q, retriever)
        rows["question"].append(q)
        rows["answer"].append(r["answer"])
        rows["contexts"].append(r["contexts"])
        rows["ground_truth"].append(item["ground_truth"])
        time.sleep(1.5)   # sequential guard — keeps us under TPM

    print(f"\n⚖️  Running RAGAS metrics with {EVAL_MODEL}...")
    print(f"   RunConfig: max_workers=2, max_retries=10")

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        e_llm   = LangchainLLMWrapper(eval_llm())
        e_embed = LangchainEmbeddingsWrapper(
            HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        )
    run_cfg = RunConfig(max_workers=2, max_retries=10, timeout=180)
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]

    result = evaluate(
        Dataset.from_dict(rows),
        metrics=metrics,
        llm=e_llm,
        embeddings=e_embed,
        run_config=run_cfg,
        raise_exceptions=False,
    )

    # RAGAS 0.4.x returns an EvaluationResult object — convert to dict first
    result_dict = result.to_pandas().mean(numeric_only=True).to_dict()

    def _score(key: str) -> float:
        # try exact key, then lowercase, then default to 0
        for k in [key, key.lower()]:
            if k in result_dict:
                v = result_dict[k]
                return round(float(v), 4) if v == v else 0.0  # NaN guard
        return 0.0

    scores = {
        "faithfulness":      _score("faithfulness"),
        "answer_relevancy":  _score("answer_relevancy"),
        "context_precision": _score("context_precision"),
        "context_recall":    _score("context_recall"),
    }
    scores["average"] = round(sum(scores.values()) / 4, 4)

    return {
        "tag":             tag,
        "timestamp":       datetime.now().isoformat(),
        "rag_model":       GEN_MODEL,
        "eval_model":      EVAL_MODEL,
        "embedding_model": "all-MiniLM-L6-v2",
        "doc_count":       get_count(),
        "testset_size":    len(testset),
        "scores":          scores,
        "per_question": [
            {
                "question":      rows["question"][i],
                "answer":        rows["answer"][i],
                "ground_truth":  rows["ground_truth"][i],
                "contexts_used": len(rows["contexts"][i]),
                "type":          testset[i].get("type", ""),
            }
            for i in range(len(testset))
        ],
    }


# ══════════════════════════════════════════════════════════════════════════════
# OUTPUT
# ══════════════════════════════════════════════════════════════════════════════

def print_results(out: dict) -> None:
    s, sep, W = out["scores"], "=" * 56, 28
    print(f"\n{sep}")
    print(f"  RAG Evaluation  —  tag: {out['tag']}")
    print(sep)
    print(f"  Timestamp      : {out['timestamp']}")
    print(f"  RAG model      : {out['rag_model']}")
    print(f"  Eval model     : {out['eval_model']}")
    print(f"  Docs in DB     : {out['doc_count']}")
    print(f"  Questions      : {out['testset_size']}")
    print(f"  Keys available : {len(ALL_KEYS)}")
    print(sep)
    for metric, score in s.items():
        if metric == "average":
            print(f"  {'-'*(W+26)}")
        filled = int(score * W)
        bar    = "█" * filled + "░" * (W - filled)
        flag   = "🟢" if score >= 0.70 else ("🟡" if score >= 0.50 else "🔴")
        print(f"  {flag} {metric:<22} {bar}  {score:.4f}")
    print(sep)
    print("\n  🟢 ≥ 0.70 Good  |  🟡 0.50–0.69 Needs work  |  🔴 < 0.50 Poor")
    print()


def save_results(out: dict, tag: str) -> Path:
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = EVAL_RESULTS_DIR / f"{tag}_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    return path


def compare_results(fa: str, fb: str) -> None:
    with open(fa, encoding="utf-8") as f: a = json.load(f)
    with open(fb, encoding="utf-8") as f: b = json.load(f)
    print(f"\n{'='*62}")
    print(f"  {a['tag']}  →  {b['tag']}")
    print(f"{'='*62}")
    print(f"  {'Metric':<24} {'Before':>8}  {'After':>8}  {'Delta':>9}")
    print(f"  {'-'*54}")
    for m in ["faithfulness","answer_relevancy","context_precision","context_recall","average"]:
        bef = a["scores"].get(m, 0)
        aft = b["scores"].get(m, 0)
        d   = aft - bef
        arr = "▲" if d > 0 else ("▼" if d < 0 else "─")
        print(f"  {m:<24} {bef:>8.4f}  {aft:>8.4f}  {arr} {d:>+8.4f}")
    print(f"{'='*62}\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="Evaluate Cricket RAG pipeline with RAGAS")
    p.add_argument("--tag",              default="baseline",
                   help="Label for this run: 'baseline' or 'advanced_rag'")
    p.add_argument("--testset-size",     type=int, default=N_QUESTIONS,
                   help=f"QA pairs to generate (default {N_QUESTIONS})")
    p.add_argument("--compare",          nargs=2, metavar=("FILE_A", "FILE_B"),
                   help="Compare two saved result JSON files")
    p.add_argument("--reset-snapshots",  action="store_true",
                   help="Delete existing doc/testset snapshots and regenerate")
    args = p.parse_args()

    # ── Compare mode ──────────────────────────────────────────────────────────
    if args.compare:
        compare_results(*args.compare)
        return

    # ── Reset snapshots ───────────────────────────────────────────────────────
    if args.reset_snapshots:
        for f in [DOCS_SNAPSHOT, TESTSET_SNAPSHOT]:
            if f.exists():
                f.unlink()
                print(f"   🗑️  Deleted {f}")
        print("   Snapshots reset. Re-run without --reset-snapshots to regenerate.\n")
        return

    # ── Pre-flight ─────────────────────────────────────────────────────────────
    doc_count = get_count()
    print(f"\n🏏 Cricket RAG Evaluator")
    print(f"   ChromaDB docs  : {doc_count}")
    print(f"   Tag            : {args.tag}")
    print(f"   Gen model      : {GEN_MODEL}")
    print(f"   Eval model     : {EVAL_MODEL}")
    print(f"   Keys loaded    : {len(ALL_KEYS)}")

    if doc_count == 0:
        print("\n❌ ChromaDB is empty. Run the pipeline first:\n   python run_pipeline.py")
        sys.exit(1)

    # ── Snapshots ─────────────────────────────────────────────────────────────
    docs    = load_or_create_doc_snapshot()
    testset = load_or_create_testset(docs, n=args.testset_size)

    if not testset:
        print("❌ Testset is empty. Delete snapshots and retry:")
        print("   python evaluate_rag.py --reset-snapshots")
        sys.exit(1)

    print(f"\n✅ Testset ready — {len(testset)} questions")
    for i, item in enumerate(testset[:3], 1):
        print(f"   Sample {i}: {item['question'][:80]}")
    if len(testset) > 3:
        print(f"   ... and {len(testset) - 3} more")

    # ── Run evaluation ─────────────────────────────────────────────────────────
    out = run_evaluation(testset, retriever=None, tag=args.tag)

    # ── Print + save ───────────────────────────────────────────────────────────
    print_results(out)
    path = save_results(out, args.tag)
    print(f"💾 Results saved → {path}")

    if args.tag == "baseline":
        print(f"\n   ── Next steps ──────────────────────────────────────────")
        print(f"   Implement Advanced RAG changes, then:")
        print(f"   python evaluate_rag.py --tag advanced_rag")
        print(f"   python evaluate_rag.py --compare {path} eval_results/advanced_rag_<ts>.json")
    print()


if __name__ == "__main__":
    main()