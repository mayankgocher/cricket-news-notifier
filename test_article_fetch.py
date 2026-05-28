"""
Quick test: see exactly what DDG finds and what BeautifulSoup scrapes.
Run: python test_article_fetch.py
"""

import requests
from bs4 import BeautifulSoup
from langchain_community.tools import DuckDuckGoSearchResults

_search_tool = DuckDuckGoSearchResults(backend="news", num_results=2, output_format="list")

TEST_HEADLINES = [
    "Virat Kohli century IPL 2025",
    "Rohit Sharma test cricket retirement",
]

def fetch_article(url: str) -> str:
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
    except Exception as e:
        return f"[FETCH ERROR: {e}]"


for headline in TEST_HEADLINES:
    print("\n" + "█" * 70)
    print(f"HEADLINE: {headline}")
    print("█" * 70)

    results = _search_tool.run(f"cricket {headline}")

    for i, r in enumerate(results):
        print(f"\n  ── DDG Result {i+1} ──")
        print(f"  Title  : {r.get('title', '')}")
        print(f"  Source : {r.get('source', '')}  |  Date: {r.get('date', '')}")
        print(f"  URL    : {r.get('link', '')}")
        print(f"  Snippet: {r.get('snippet', '')}")

        url = r.get("link", "")
        if url:
            print(f"\n  Scraping full article...")
            content = fetch_article(url)
            print(f"  Length : {len(content)} chars")
            print(f"\n  ── SCRAPED CONTENT ──")
            print(content if content else "  [EMPTY]")
            print(f"  ── END ──")