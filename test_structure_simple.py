"""
Simple test: are articles naturally divided into paragraphs?
Run: python test_structure_simple.py
"""

import requests
from bs4 import BeautifulSoup
from langchain_community.tools import DuckDuckGoSearchResults

_search_tool = DuckDuckGoSearchResults(backend="news", num_results=3, output_format="list")

TEST_HEADLINES = [
    "Virat Kohli century IPL 2026",
    "Jasprit Bumrah wickets test 2026",
    "Vaibhav Suryavanshi IPL debut century",
]

def fetch_paragraphs(url: str) -> list[str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
            tag.decompose()
        return [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 40]
    except Exception as e:
        return []

for headline in TEST_HEADLINES:
    print("\n" + "█" * 70)
    print(f"HEADLINE: {headline}")
    print("█" * 70)

    results = _search_tool.run(f"cricket {headline}")

    for r in results:
        source = r.get("source", "?")
        url = r.get("link", "")
        paragraphs = fetch_paragraphs(url)

        if not paragraphs:
            print(f"\n  [{source}] ⛔ blocked or empty")
            continue

        print(f"\n  [{source}] ✅ {len(paragraphs)} paragraphs found")
        for i, p in enumerate(paragraphs):
            print(f"  P{i+1}: {p}")
        print()