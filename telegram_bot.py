"""
Telegram Bot Handler - Listens for /subscribe commands
Run this separately: python telegram_bot.py
"""

import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.settings import TELEGRAM_BOT_TOKEN
from src.rag import query_engine
from backend.database import SessionLocal
from backend.models import Subscriber


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    welcome = """
🏏 Welcome to Cricket Daily Digest!

Commands:
/subscribe - Subscribe to daily cricket news
/unsubscribe - Unsubscribe from updates
/status - Check your subscription status

You can also ask me any cricket question!
Example: "What happened in yesterday's match?"
"""
    await update.message.reply_text(welcome)


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /subscribe command"""
    chat_id = str(update.effective_chat.id)

    db = SessionLocal()
    try:
        existing = db.query(Subscriber).filter(
            Subscriber.telegram_chat_id == chat_id
        ).first()

        if existing:
            existing.telegram_subscribed = True
            existing.is_active = True
            db.commit()
            await update.message.reply_text("✅ You're already subscribed! You'll receive daily cricket news at 8 AM IST.")
        else:
            subscriber = Subscriber(
                telegram_chat_id=chat_id,
                telegram_subscribed=True,
                is_active=True
            )
            db.add(subscriber)
            db.commit()
            await update.message.reply_text("✅ Subscribed successfully! You'll receive daily cricket news at 8 AM IST.")

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❌ Something went wrong. Please try again.")

    finally:
        db.close()


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /unsubscribe command"""
    chat_id = str(update.effective_chat.id)

    db = SessionLocal()
    try:
        existing = db.query(Subscriber).filter(
            Subscriber.telegram_chat_id == chat_id
        ).first()

        if existing:
            existing.telegram_subscribed = False
            existing.is_active = False
            db.commit()
            await update.message.reply_text("✅ Unsubscribed. You won't receive daily updates anymore.")
        else:
            await update.message.reply_text("ℹ️ You weren't subscribed.")

    finally:
        db.close()


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    chat_id = str(update.effective_chat.id)

    db = SessionLocal()
    try:
        existing = db.query(Subscriber).filter(
            Subscriber.telegram_chat_id == chat_id
        ).first()

        if existing and existing.telegram_subscribed:
            await update.message.reply_text("✅ You are subscribed to daily cricket news!")
        else:
            await update.message.reply_text("❌ You are not subscribed. Send /subscribe to get daily updates.")

    finally:
        db.close()


async def latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /latest command - Get latest news on demand"""
    await update.message.reply_text("🔍 Fetching latest cricket news...")

    try:
        from src.agents.rss_agent import RSSAgent
        rss = RSSAgent()
        news = rss.fetch_news(limit=5)

        if not news:
            await update.message.reply_text("❌ No news found. Try again later.")
            return

        message = "🏏 **LATEST CRICKET NEWS**\n\n"

        for i, item in enumerate(news[:5], 1):
            headline = item.get("headline", "")[:100]
            source = item.get("source", "unknown").upper()
            message += f"{i}. {headline}\n   [{source}]\n\n"

        message += "💬 Ask me any question about cricket!"

        await update.message.reply_text(message)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("❌ Something went wrong. Try again later.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages — RAG Q&A with per-user conversation history."""
    question = update.message.text
    chat_id  = str(update.effective_chat.id)
    session_id = f"telegram_{chat_id}"

    try:
        await update.message.reply_text("🔍 Searching...")

        answer = query_engine.answer(question, session_id=session_id)

        await update.message.reply_text(answer)

    except Exception as e:
        print(f"Error: {e}")
        await update.message.reply_text("Sorry, I couldn't find an answer. Try asking something else!")


def main():
    """Start the bot"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        return

    print("🤖 Starting Telegram Bot...")
    print("Press Ctrl+C to stop\n")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("latest", latest))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()