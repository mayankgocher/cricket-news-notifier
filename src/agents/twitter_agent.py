"""
Twitter Agent - Fetches cricket tweets
"""

import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.settings import TWITTER_BEARER_TOKEN


class TwitterAgent:
    """Fetches cricket-related tweets"""
    
    def __init__(self):
        self.bearer_token = TWITTER_BEARER_TOKEN
        self.base_url = "https://api.twitter.com/2/tweets/search/recent"
    
    def fetch_news(self, limit=30, min_likes=10):
        """
        Fetch cricket-related tweets
        
        Args:
            limit: Number of tweets to return
            min_likes: Minimum likes to filter quality tweets
        
        Returns:
            List of news dictionaries
        """
        print(f"📥 Fetching Twitter posts...")
        
        if not self.bearer_token:
            print("⚠️ Twitter Bearer Token not configured")
            return []
        
        try:
            # Cricket-focused search query
            query = (
                "(cricket OR IPL OR #Cricket OR #IPL OR "
                "BCCI OR ICC OR #CricketTwitter) "
                "lang:en -is:retweet -is:reply"
            )
            
            headers = {
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "query": query,
                "max_results": min(limit * 3, 100),  # Fetch more to filter
                "tweet.fields": "created_at,public_metrics,author_id",
                "expansions": "author_id",
                "user.fields": "username"
            }
            
            response = requests.get(self.base_url, headers=headers, params=params)
            
            if response.status_code == 429:
                print("⚠️ Twitter rate limit reached")
                return []
            
            if response.status_code != 200:
                print(f"❌ Twitter API error: {response.status_code}")
                return []
            
            data = response.json()
            
            if "data" not in data:
                print("⚠️ No tweets found")
                return []
            
            # Parse users
            users = {}
            if "includes" in data and "users" in data["includes"]:
                for user in data["includes"]["users"]:
                    users[user["id"]] = user["username"]
            
            # Parse tweets
            news = []
            for tweet in data["data"]:
                metrics = tweet.get("public_metrics", {})
                likes = metrics.get("like_count", 0)
                retweets = metrics.get("retweet_count", 0)
                
                # Skip low engagement
                if likes < min_likes:
                    continue
                
                author = users.get(tweet.get("author_id"), "unknown")
                
                news.append({
                    "headline": tweet["text"],
                    "source": "twitter",
                    "url": f"https://twitter.com/{author}/status/{tweet['id']}",
                    "likes": likes,
                    "retweets": retweets,
                    "timestamp": tweet.get("created_at", "")
                })
                
                if len(news) >= limit:
                    break
            
            print(f"✅ Fetched {len(news)} tweets")
            return news
        
        except Exception as e:
            print(f"❌ Twitter error: {e}")
            return []


# Test
if __name__ == "__main__":
    agent = TwitterAgent()
    news = agent.fetch_news(limit=5)
    for item in news:
        print(f"- {item['headline'][:60]}... ({item['likes']} likes)")