"""
Ingestion Node - Fetches news from all sources
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.agents.reddit_agent import RedditAgent
from src.agents.twitter_agent import TwitterAgent
from src.agents.rss_agent import RSSAgent


def ingestion_node(state):
    """
    Fetch news from Twitter, Reddit, and RSS feeds
    
    Args:
        state: Pipeline state dictionary
    
    Returns:
        Updated state with 'news_items' list
    """
    print("\n" + "="*50)
    print("📥 INGESTION NODE - Fetching news...")
    print("="*50)
    
    all_news = []
    
    # Fetch from Reddit
    try:
        reddit = RedditAgent()
        reddit_news = reddit.fetch_news(limit=30, min_upvotes=10)
        all_news.extend(reddit_news)
    except Exception as e:
        print(f"⚠️ Reddit failed: {e}")
    
    # Fetch from Twitter
    try:
        twitter = TwitterAgent()
        twitter_news = twitter.fetch_news(limit=30, min_likes=10)
        all_news.extend(twitter_news)
    except Exception as e:
        print(f"⚠️ Twitter failed: {e}")
    
    # Fetch from RSS feeds
    try:
        rss = RSSAgent()
        rss_news = rss.fetch_news(limit=110)
        all_news.extend(rss_news)
    except Exception as e:
        print(f"⚠️ RSS failed: {e}")
    
    print(f"\n✅ Total fetched: {len(all_news)} news items")
    
    state["news_items"] = all_news
    return state


# Test
if __name__ == "__main__":
    state = {}
    state = ingestion_node(state)
    print(f"\nSample items:")
    for item in state["news_items"][:3]:
        print(f"  - [{item['source']}] {item['headline'][:50]}...")