"""
RSS Agent - Fetches cricket news from ESPN Cricinfo and other RSS feeds
"""

import feedparser
from datetime import datetime
import time


class RSSAgent:
    """Fetches cricket news from RSS feeds"""
    
    def __init__(self):
        # Cricket RSS feed URLs
        self.feeds = {
            # Indian sources (4)
            "hindustan_times": "https://www.hindustantimes.com/feeds/rss/cricket/rssfeed.xml",
            "india_today":     "https://www.indiatoday.in/rss/1206578",
            "indian_express":  "https://indianexpress.com/section/sports/cricket/feed/",
            "crictracker":     "https://www.crictracker.com/feed/",

            # International sources (3)
            "espn":            "https://www.espncricinfo.com/rss/content/story/feeds/0.xml",
            "bbc_cricket":     "http://feeds.bbci.co.uk/sport/cricket/rss.xml",
            "guardian_cricket":"https://www.theguardian.com/sport/cricket/rss",
        }
    
    def fetch_news(self, limit=100):
        """
        Fetch cricket news from RSS feeds
        
        Args:
            limit: Number of news items to return
        
        Returns:
            List of news dictionaries
        """
        print(f"📥 Fetching RSS feeds...")
        
        all_news = []
        
        for source, url in self.feeds.items():
            try:
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:15]:  # Max 15 per source
                    # Parse publish date
                    timestamp = None
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        timestamp = time.mktime(entry.published_parsed)
                    
                    # Get summary if available
                    summary = ""
                    if hasattr(entry, "summary"):
                        summary = entry.summary[:500]  # Limit summary length
                    
                    all_news.append({
                        "headline": entry.title,
                        "summary": summary,
                        "source": source,
                        "url": entry.link,
                        "timestamp": timestamp
                    })
                
                print(f"  ✓ {source}: {len(feed.entries[:10])} items")
            
            except Exception as e:
                print(f"  ✗ {source}: Error - {e}")
                continue
        
        # Sort by timestamp (newest first)
        all_news.sort(key=lambda x: x.get("timestamp") or 0, reverse=True)
        
        # Return limited results
        result = all_news[:limit]
        print(f"✅ Fetched {len(result)} RSS items total")
        return result


# Test
if __name__ == "__main__":
    agent = RSSAgent()
    news = agent.fetch_news(limit=5)
    for item in news:
        print(f"- [{item['source']}] {item['headline'][:50]}...")