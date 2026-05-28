"""
Summarizer Agent - Generates summaries using LangChain LCEL + ChatGroq.
Uses 3 Groq API keys in round-robin rotation to avoid 30 RPM rate limits.
No sleep/halting — keys cycle automatically on every request.
"""

import sys
import os
import itertools

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.config.settings import GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3


# ── Key rotation setup ────────────────────────────────────────────────────────
# Filter out any keys that are not configured
_available_keys = [k for k in [GROQ_API_KEY, GROQ_API_KEY_2, GROQ_API_KEY_3] if k]

if not _available_keys:
    raise ValueError("No GROQ API keys configured. Set at least GROQ_API_KEY in .env")

print(f"  🔑 Summarizer using {len(_available_keys)} Groq key(s) — {len(_available_keys) * 30} RPM total")

_key_cycle = itertools.cycle(_available_keys)


def _get_llm() -> ChatGroq:
    """Return a ChatGroq instance using the next key in rotation."""
    return ChatGroq(
        api_key=next(_key_cycle),
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=100,
    )


# ── Prompts ───────────────────────────────────────────────────────────────────
_item_prompt = ChatPromptTemplate.from_messages([
    ("human", (
        "Summarize this cricket news in 1-2 short sentences:\n\n"
        "Headline: {headline}\n"
        "Details: {content}\n\n"
        "Summary:"
    ))
])

_exec_prompt = ChatPromptTemplate.from_messages([
    ("human", (
        "Here are today's cricket news headlines:\n\n{headlines}\n\n"
        "Write a brief executive summary (3-4 sentences) highlighting "
        "the main themes and most important news:"
    ))
])


# ── Public API ────────────────────────────────────────────────────────────────

def summarize(headline: str, content: str = "") -> str:
    """
    Generate a short summary for a single news item.

    Args:
        headline: News headline
        content: Additional content/context (optional)

    Returns:
        Summary string (1-2 sentences)
    """
    try:
        chain = _item_prompt | _get_llm() | StrOutputParser()
        return chain.invoke({
            "headline": headline,
            "content": content or headline,
        })
    except Exception as e:
        print(f"⚠️ Summarizer error: {e}")
        return headline


def summarize_batch(news_items: list[dict]) -> list[str]:
    """
    Generate summaries for multiple news items.
    Each item in the batch uses the next key in rotation — no halting.

    For N items across 3 keys:
        item 0 → key1, item 1 → key2, item 2 → key3,
        item 3 → key1, item 4 → key2 ... and so on

    Args:
        news_items: List of dicts with 'headline' and optionally 'content'

    Returns:
        List of summary strings in the same order
    """
    if not news_items:
        return []

    results = []
    for item in news_items:
        try:
            chain = _item_prompt | _get_llm() | StrOutputParser()
            summary = chain.invoke({
                "headline": item["headline"],
                "content": item.get("enriched_content") or item.get("summary") or item["headline"],
            })
            results.append(summary)
        except Exception as e:
            print(f"⚠️ Summarizer error on '{item['headline'][:50]}': {e}")
            results.append(item["headline"])  # fallback to headline

    return results


def generate_executive_summary(news_items: list[dict]) -> str:
    """
    Generate an overall executive summary of all news items.

    Args:
        news_items: List of dicts with 'headline' key

    Returns:
        Executive summary string (3-4 sentences)
    """
    try:
        headlines = "\n".join(f"- {item['headline']}" for item in news_items[:15])
        chain = (_exec_prompt
                 | ChatGroq(api_key=_available_keys[0], model="llama-3.3-70b-versatile",
                             temperature=0.3, max_tokens=200)
                 | StrOutputParser())
        return chain.invoke({"headlines": headlines})
    except Exception as e:
        print(f"⚠️ Executive summary error: {e}")
        return "Today's cricket news covers various updates from around the world."