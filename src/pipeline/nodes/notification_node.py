"""
Notification Node - Sends newsletter to subscribers
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from src.notifiers.email_agent import EmailAgent
from src.notifiers.telegram_agent import TelegramAgent
from backend.database import SessionLocal
from backend.models import Subscriber, Newsletter


def notification_node(state):
    """
    Send newsletter to all active subscribers
    
    Args:
        state: Pipeline state with 'newsletter_content'
    
    Returns:
        Updated state with send statistics
    """
    print("\n" + "="*50)
    print("📤 NOTIFICATION NODE - Sending newsletter...")
    print("="*50)
    
    content = state.get("newsletter_content", "")
    
    if not content:
        print("⚠️ No content to send")
        return state
    
    # Initialize agents
    email_agent = EmailAgent()
    telegram_agent = TelegramAgent()
    
    # Get subscribers from database
    db = SessionLocal()
    
    try:
        subscribers = db.query(Subscriber).filter(Subscriber.is_active == True).all()
        
        email_count = 0
        telegram_count = 0
        
        for sub in subscribers:
            # Send email if subscribed and verified
            if sub.email_subscribed and sub.email_verified and sub.email:
                success = email_agent.send(sub.email, content)
                if success:
                    email_count += 1
            
            # Send telegram if subscribed
            if sub.telegram_subscribed and sub.telegram_chat_id:
                success = telegram_agent.send(sub.telegram_chat_id, content)
                if success:
                    telegram_count += 1
        
        print(f"\n✅ Newsletter sent!")
        print(f"   📧 Email: {email_count} subscribers")
        print(f"   📱 Telegram: {telegram_count} subscribers")
        
        # Save newsletter to archive
        newsletter = Newsletter(
            content=content,
            headlines_count=len(state.get("news_items", [])),
            subscriber_count=email_count + telegram_count
        )
        db.add(newsletter)
        db.commit()
        
        state["email_sent"] = email_count
        state["telegram_sent"] = telegram_count
        
        return state
    
    except Exception as e:
        print(f"⚠️ Notification error: {e}")
        return state
    
    finally:
        db.close()


# Test
if __name__ == "__main__":
    state = {
        "newsletter_content": "Test newsletter content",
        "news_items": [{"headline": "Test"}]
    }
    
    print("Testing notification node...")
    print("(Will only work if subscribers exist in database)")
    # state = notification_node(state)