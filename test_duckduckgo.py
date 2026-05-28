"""
Test DuckDuckGo Agent - Check search and enrichment quality
"""

from src.tools.websearch.duckduckgo_agent import DuckDuckGoAgent

agent = DuckDuckGoAgent()

# Test 1: Search
print("="*60)
print("TEST 1: Search for cricket news")
print("="*60)

results = agent.search("India vs Australia cricket 2024", max_results=3)

for i, r in enumerate(results, 1):
    print(f"\n--- Result {i} ---")
    print(f"Title: {r['title']}")
    print(f"Source: {r['source']}")
    print(f"Snippet: {r['snippet']}")

# Test 2: Enrich a headline
print("\n" + "="*60)
print("TEST 2: Enrich a headline")
print("="*60)

headline = "Virat Kohli scores century against New Zealand in ODIs"
enriched = agent.enrich_news(headline)

print(f"\nHeadline: {headline}")
print(f"\nEnriched content ({len(enriched)} characters):")
print("-"*40)
print(enriched)
print("-"*40)

# Test 3: Another headline
print("\n" + "="*60)
print("TEST 3: Enrich another headline")
print("="*60)

headline2 = "IPL 2025 auction mega players list"
enriched2 = agent.enrich_news(headline2)

print(f"\nHeadline: {headline2}")
print(f"\nEnriched content ({len(enriched2)} characters):")
print("-"*40)
print(enriched2)
print("-"*40)