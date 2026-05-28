"""
Reddit Agent - Fetches cricket news from r/Cricket
"""

import praw
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.settings import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT


class RedditAgent:
    """Fetches top cricket posts from Reddit"""
    
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
    
    def fetch_news(self, limit=30, min_upvotes=10):
        """
        Fetch top cricket posts from r/Cricket
        
        Args:
            limit: Number of posts to fetch
            min_upvotes: Minimum upvotes to filter quality posts
        
        Returns:
            List of news dictionaries
        """
        print(f"📥 Fetching Reddit posts...")
        
        try:
            subreddit = self.reddit.subreddit("Cricket")
            posts = subreddit.hot(limit=limit * 2)  # Fetch more to filter
            
            news = []
            for post in posts:
                # Skip low engagement posts
                if post.score < min_upvotes:
                    continue
                
                # Skip stickied posts (announcements)
                if post.stickied:
                    continue
                
                news.append({
                    "headline": post.title,
                    "source": "reddit",
                    "url": f"https://reddit.com{post.permalink}",
                    "upvotes": post.score,
                    "comments": post.num_comments,
                    "timestamp": post.created_utc
                })
                
                if len(news) >= limit:
                    break
            
            print(f"✅ Fetched {len(news)} Reddit posts")
            return news
        
        except Exception as e:
            print(f"❌ Reddit error: {e}")
            return []


# Test
if __name__ == "__main__":
    agent = RedditAgent()
    news = agent.fetch_news(limit=5)
    for item in news:
        print(f"- {item['headline'][:60]}... ({item['upvotes']} upvotes)")