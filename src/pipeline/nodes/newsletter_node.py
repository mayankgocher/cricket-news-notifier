"""
Newsletter Node - Prepares newsletter content with summaries.
Uses the refactored summarizer_agent (LCEL batch for parallel calls).
"""

import os
import sys
from datetime import datetime
import pytz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.tools.summarizer import summarizer_agent as summarizer
from src.config.settings import TIMEZONE, FRONTEND_URL


def newsletter_node(state: dict) -> dict:
    """
    Prepare newsletter content with executive summary and per-item summaries.

    Args:
        state: Pipeline state with 'news_items'

    Returns:
        Updated state with 'newsletter_content' and 'executive_summary'
    """
    print("\n" + "=" * 50)
    print("📰 NEWSLETTER NODE - Preparing content...")
    print("=" * 50)

    news_items = state.get("news_items", [])

    if not news_items:
        print("⚠️ No news items for newsletter")
        state["newsletter_content"] = "No cricket news available today."
        return state

    try:
        # Executive summary
        executive_summary = summarizer.generate_executive_summary(news_items)

        # Batch-generate all item summaries in parallel (one LLM call batch)
        print("  Generating summaries (batch)...")
        summaries = summarizer.summarize_batch(news_items)
        for item, short_summary in zip(news_items, summaries):
            item["short_summary"] = short_summary

        # Current date in IST
        tz = pytz.timezone(TIMEZONE)
        today = datetime.now(tz).strftime("%B %d, %Y")

        # Build newsletter body
        content = (
            f"\n🏏 CRICKET DAILY DIGEST - {today}\n"
            f"{'=' * 45}\n\n"
            f"📋 EXECUTIVE SUMMARY\n{executive_summary}\n\n"
            f"{'=' * 45}\n📰 TODAY'S NEWS\n{'=' * 45}\n\n"
        )

        sentiment_emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}

        for i, item in enumerate(news_items, 1):
            emoji = sentiment_emoji.get(item.get("sentiment", "neutral"), "🟡")
            source = item.get("source", "unknown").upper()
            summary = item.get("short_summary", "")

            content += f"{i}. {emoji} {item['headline']}\n"
            if summary and summary != item["headline"]:
                content += f"   📝 {summary}\n"
            content += f"   [{source}]\n\n"

        content += (
            f"\n{'=' * 45}\n\n"
            f"💬 Want more details?\n   → Ask questions: {FRONTEND_URL}\n\n"
            f"🔕 Unsubscribe:\n"
            f"   → Email users: {FRONTEND_URL} (go to Subscribe page)\n"
            f"   → Telegram users: Send /unsubscribe\n\n"
            f"{'=' * 45}\n"
        )

        print(f"✅ Newsletter prepared with {len(news_items)} items")
        state["newsletter_content"] = content
        state["executive_summary"] = executive_summary

    except Exception as e:
        print(f"⚠️ Newsletter error: {e}")
        state["newsletter_content"] = "Error preparing newsletter."

    return state