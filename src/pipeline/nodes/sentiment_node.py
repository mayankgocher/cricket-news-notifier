"""
Sentiment Node - Analyzes sentiment of news items
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.tools.sentiment.sentiment_agent import SentimentAgent


def sentiment_node(state):
    """
    Analyze sentiment of each news item
    
    Args:
        state: Pipeline state with 'news_items'
    
    Returns:
        Updated state with sentiment added to each item
    """
    print("\n" + "="*50)
    print("🎭 SENTIMENT NODE - Analyzing sentiment...")
    print("="*50)
    
    news_items = state.get("news_items", [])
    
    if not news_items:
        print("⚠️ No news items to analyze")
        return state
    
    try:
        agent = SentimentAgent()
        
        for i, item in enumerate(news_items):
            print(f"  Analyzing {i+1}/{len(news_items)}...", end="\r")
            
            result = agent.analyze(item["headline"])
            item["sentiment"] = result["sentiment"]
            item["sentiment_confidence"] = result["confidence"]
        
        # Count sentiments
        positive = sum(1 for item in news_items if item["sentiment"] == "positive")
        negative = sum(1 for item in news_items if item["sentiment"] == "negative")
        neutral = sum(1 for item in news_items if item["sentiment"] == "neutral")
        
        print(f"\n✅ Sentiment analysis complete")
        print(f"   🟢 Positive: {positive} | 🟡 Neutral: {neutral} | 🔴 Negative: {negative}")
        
        state["news_items"] = news_items
        return state
    
    except Exception as e:
        print(f"⚠️ Sentiment error: {e}")
        # Set neutral for all if error
        for item in news_items:
            item["sentiment"] = "neutral"
            item["sentiment_confidence"] = 0.5
        state["news_items"] = news_items
        return state


# Test
if __name__ == "__main__":
    state = {
        "news_items": [
            {"headline": "India wins the World Cup! Historic victory!"},
            {"headline": "Team suffers embarrassing defeat"},
            {"headline": "Match scheduled for tomorrow at 3 PM"}
        ]
    }
    
    state = sentiment_node(state)
    for item in state["news_items"]:
        emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}[item["sentiment"]]
        print(f"{emoji} {item['headline'][:40]}... → {item['sentiment']}")