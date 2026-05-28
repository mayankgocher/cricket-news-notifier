"""
Enrichment Node - Enriches news with web content and stores in VectorDB.
Uses LangChain DuckDuckGoSearchResults for search; keeps custom article
scraping for full-text fetch (not covered by the LangChain tool).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import requests
from bs4 import BeautifulSoup
from langchain_community.tools import DuckDuckGoSearchResults

import src.rag.vectordb as vectordb


# FIX: output_format="list" makes .run() return a real Python list of dicts
# instead of a formatted string like:
#   "[snippet: ..., title: ..., link: https://..., date: 2026-05-16T16:15:32+00:00, source: AOL, ...]"
# The old code tried json.loads() on that string, which always failed (not valid JSON),
# so it fell into the else branch and embedded the raw string — metadata noise and all.
_search_tool = DuckDuckGoSearchResults(backend="news", num_results=2, output_format="list")


def _fetch_article(url: str) -> str:
    """Scrape full article text from a URL — no char cap, full story."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
            tag.decompose()
        article = soup.find("article")
        text = article.get_text(" ", strip=True) if article else " ".join(
            p.get_text(strip=True) for p in soup.find_all("p")
        )
        return " ".join(text.split())
    except Exception:
        return ""


def _enrich_headline(headline: str, verbose: bool = False) -> str:
    """Search DuckDuckGo and return enriched content for one headline."""
    try:
        # With output_format="list", raw is always a Python list of dicts.
        # Each dict has keys: snippet, title, link, date, source
        results = _search_tool.run(f"cricket {headline}")

        if verbose:
            print(f"\n  📡 DDG raw results for: '{headline}'")
            for i, r in enumerate(results):
                print(f"    Result {i+1}:")
                print(f"      title   : {r.get('title', '')}")
                print(f"      snippet : {r.get('snippet', '')}")
                print(f"      link    : {r.get('link', '')}")
                print(f"      date    : {r.get('date', '')}")
                print(f"      source  : {r.get('source', '')}")

        if not results:
            return ""

        # Priority 1: scrape the full article — no char cap, full story.
        # Chunking in vectordb.add_documents handles the embedding size limit.
        for r in results:
            url = r.get("link") or r.get("url", "")
            if url:
                content = _fetch_article(url)
                if verbose:
                    if len(content) > 200:
                        print(f"\n  ✅ WILL EMBED (full article, {len(content)} chars):")
                        print(f"     {content[:300]}...")
                    else:
                        print(f"\n  ⚠️  Article scrape too short ({len(content)} chars), trying next...")
                if len(content) > 200:
                    return content

        # Priority 2: article scrape failed — fall back to snippets only.
        # Only 'snippet' values are joined; title/link/date/source are ignored.
        snippets_only = " ".join(r.get("snippet", "") for r in results)[:1000]
        if verbose:
            print(f"\n  ⚠️  WILL EMBED (snippets only fallback, {len(snippets_only)} chars):")
            print(f"     {snippets_only[:300]}...")
        return snippets_only

    except Exception as e:
        print(f"⚠️ Enrichment search error: {e}")
        return ""


def enrichment_node(state: dict) -> dict:
    """
    Enrich news items with web content and store in VectorDB.

    Args:
        state: Pipeline state with 'news_items'

    Returns:
        Updated state with 'enrichment_complete'
    """
    print("\n" + "=" * 50)
    print("🔍 ENRICHMENT NODE - Getting detailed content...")
    print("=" * 50)

    news_items = state.get("news_items", [])

    if not news_items:
        print("⚠️ No news items to enrich")
        return state

    try:
        enriched_items = []
        for i, item in enumerate(news_items):
            print(f"  Enriching {i + 1}/{len(news_items)}...", end="\r")
            detailed = _enrich_headline(item["headline"])
            full_content = f"{item['headline']}\n\n{detailed}" if detailed else item["headline"]
            enriched_items.append({
                "id": i,
                "headline": item["headline"],
                "content": full_content,
                "source": item.get("source", "unknown"),
                "sentiment": item.get("sentiment", "neutral"),
            })

        print(f"\n💾 Storing {len(enriched_items)} items in VectorDB...")
        vectordb.add_documents(enriched_items)

        print(f"✅ Enriched and stored {len(enriched_items)} items")
        state["enrichment_complete"] = True

    except Exception as e:
        print(f"⚠️ Enrichment error: {e}")
        state["enrichment_complete"] = False

    return state