"""
Query Engine — Answers user questions using advanced RAG pipeline.

Full pipeline:
  1. Query rewriting  — resolve pronouns/context using conversation history
  2. Hybrid retrieval — BM25 + Dense + RRF → MMR → Cross-encoder reranker
  3. LLM answer       — Groq llama-3.3-70b-versatile

For evaluation (no session_id): query rewriting is skipped, raw question
goes directly to retrieval so eval results are clean and comparable.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config.settings import GROQ_API_KEY
from src.rag.hybrid_retriever import retrieve
from src.rag.conversation_history import init_table, get_history, save_turn

# Initialise conversation history table on import
init_table()

# --- LLM (answer generation) ---
_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile", temperature=0.3)

# --- LLM (query rewriting — small fast model, saves rate limit budget) ---
_rewrite_llm = ChatGroq(api_key=GROQ_API_KEY, model="llama-3.1-8b-instant", temperature=0.0)

# --- Answer prompt ---
_answer_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a cricket news assistant. Answer the user's question using "
        "only the context below. Be concise (2-4 sentences). "
        "If the context doesn't contain the answer, say so.\n\n"
        "CONTEXT:\n{context}"
    )),
    ("human", "{question}"),
])

# --- Query rewriting prompt ---
_rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a query rewriter for a cricket news assistant.\n"
        "Given a conversation history and the latest user query, rewrite the query "
        "into a standalone, self-contained question that resolves all pronouns and "
        "references using the conversation history.\n"
        "If the query is already standalone and clear, return it unchanged.\n"
        "Return ONLY the rewritten query — no explanation, no preamble."
    )),
    ("human", (
        "Conversation history:\n{history}\n\n"
        "Latest query: {query}\n\n"
        "Rewritten standalone query:"
    )),
])


def _format_docs(docs) -> str:
    return "\n\n".join(
        f"[{doc.metadata.get('source', 'unknown').upper()}] {doc.page_content}"
        for doc in docs
    )


def _format_history(history: list[dict]) -> str:
    """Format conversation history turns for the rewrite prompt."""
    if not history:
        return "No previous conversation."
    lines = []
    for turn in history:
        role = "User" if turn["role"] == "user" else "Assistant"
        lines.append(f"{role}: {turn['message']}")
    return "\n".join(lines)


def _rewrite_query(question: str, session_id: str) -> str:
    """
    Rewrite query to resolve pronouns/context from conversation history.
    Returns original question if no history exists.
    """
    history = get_history(session_id)
    if not history:
        return question  # nothing to resolve

    rewritten = (
        _rewrite_prompt
        | _rewrite_llm
        | StrOutputParser()
    ).invoke({
        "history": _format_history(history),
        "query": question,
    })
    return rewritten.strip()


def answer(question: str, session_id: str | None = None) -> str:
    """
    Answer a question using the advanced RAG pipeline.

    Args:
        question:   User's raw question
        session_id: Session identifier for conversation history.
                    Pass None (eval mode) to skip query rewriting.

    Returns:
        Answer string
    """
    try:
        # Step 1 — Query rewriting (skip in eval mode)
        if session_id:
            retrieval_query = _rewrite_query(question, session_id)
        else:
            retrieval_query = question

        # Step 2 — Hybrid retrieval (BM25 + Dense + RRF → MMR → Reranker)
        docs = retrieve(retrieval_query)

        # Step 3 — LLM answer generation
        context = _format_docs(docs)
        ans = (_answer_prompt | _llm | StrOutputParser()).invoke({
            "context": context,
            "question": question,  # original question for answer generation
        })

        # Step 4 — Persist turn to history (production only)
        if session_id:
            save_turn(session_id, question, ans)

        return ans

    except Exception as e:
        print(f"⚠️ Query engine error: {e}")
        return "Sorry, I encountered an error while processing your question. Please try again."


def answer_with_sources(question: str, session_id: str | None = None) -> dict:
    """
    Answer a question and return source documents used.

    Args:
        question:   User's raw question
        session_id: Session identifier. Pass None to skip rewriting.

    Returns:
        Dict with 'answer' and 'sources'
    """
    try:
        # Query rewriting
        if session_id:
            retrieval_query = _rewrite_query(question, session_id)
        else:
            retrieval_query = question

        # Hybrid retrieval
        docs = retrieve(retrieval_query)

        # LLM answer
        context = _format_docs(docs)
        ans = (_answer_prompt | _llm | StrOutputParser()).invoke({
            "context": context,
            "question": question,
        })

        # Persist history
        if session_id:
            save_turn(session_id, question, ans)

        sources = [
            {
                "headline": doc.metadata.get("headline", ""),
                "source": doc.metadata.get("source", "unknown"),
            }
            for doc in docs
        ]

        return {"answer": ans, "sources": sources}

    except Exception as e:
        print(f"⚠️ Query engine error: {e}")
        return {"answer": "Sorry, an error occurred. Please try again.", "sources": []}
