"""
DuckDuckGo Agent - Searches web for detailed news content
Free and unlimited - no API key needed
"""

from ddgs import DDGS
import requests
from bs4 import BeautifulSoup


class DuckDuckGoAgent:
    """Searches DuckDuckGo for additional news content"""
    
    def __init__(self):
        self.ddgs = DDGS()
    
    def search(self, query, max_results=3):
        """
        Search for news related to query
        
        Args:
            query: Search query
            max_results: Number of results to return
        
        Returns:
            List of search results with title, url, snippet
        """
        try:
            results = list(self.ddgs.news(
                query,
                max_results=max_results,
                region="wt-wt"  # Worldwide
            ))
            
            parsed = []
            for r in results:
                parsed.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("body", "")[:300],
                    "source": r.get("source", "")
                })
            
            return parsed
        
        except Exception as e:
            print(f"⚠️ DuckDuckGo error: {e}")
            return []
    
    def fetch_article_content(self, url, max_chars=2000):
        """
        Fetch full article content from URL
        
        Args:
            url: Article URL
            max_chars: Maximum characters to return
        
        Returns:
            Article text content
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                return ""
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove unwanted elements
            for tag in soup(["script", "style", "nav", "header", "footer", "aside", "iframe"]):
                tag.decompose()
            
            # Try to find article content
            article = soup.find("article")
            if article:
                text = article.get_text(separator=" ", strip=True)
            else:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all("p")
                text = " ".join([p.get_text(strip=True) for p in paragraphs])
            
            # Clean up text
            text = " ".join(text.split())  # Remove extra whitespace
            
            return text[:max_chars]
        
        except Exception as e:
            print(f"⚠️ Fetch error for {url}: {e}")
            return ""
    
    def enrich_news(self, headline):
        """
        Get detailed content for a news headline
        
        Args:
            headline: News headline to search for
        
        Returns:
            Enriched content string
        """
        try:
            # Search for the headline
            results = self.search(headline, max_results=2)
            
            if not results:
                return ""
            
            # Try to fetch full article from first result
            for result in results:
                url = result.get("url", "")
                if url:
                    full_content = self.fetch_article_content(url, max_chars=2000)
                    if len(full_content) > 200:  # Got meaningful content
                        return full_content
            
            # Fallback: combine snippets if full fetch failed
            content = ""
            for r in results:
                if r["snippet"]:
                    content += r["snippet"] + " "
            
            return content.strip()[:1000]
        
        except Exception as e:
            print(f"⚠️ Enrichment error: {e}")
            return ""
    
    def enrich_batch(self, news_items):
        """
        Enrich multiple news items with detailed content
        
        Args:
            news_items: List of news dictionaries with 'headline' key
        
        Returns:
            List of news items with added 'enriched_content' field
        """
        print(f"🔍 Enriching {len(news_items)} news items...")
        
        for i, item in enumerate(news_items):
            print(f"  Enriching {i+1}/{len(news_items)}...", end="\r")
            item["enriched_content"] = self.enrich_news(item["headline"])
        
        print(f"✅ Enriched {len(news_items)} news items    ")
        return news_items


# Test
if __name__ == "__main__":
    agent = DuckDuckGoAgent()
    
    # Test search
    results = agent.search("India cricket World Cup 2024", max_results=3)
    print("Search results:")
    for r in results:
        print(f"  - {r['title'][:50]}...")
    
    print("\n" + "="*50 + "\n")
    
    # Test enrichment
    headline = "Virat Kohli scores century against Australia"
    content = agent.enrich_news(headline)
    print(f"Headline: {headline}")
    print(f"Enriched: {content[:200]}...")