"""
Telegram Agent - Sends newsletters via Telegram Bot
"""

import requests
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.settings import TELEGRAM_BOT_TOKEN


class TelegramAgent:
    """Sends messages via Telegram Bot API"""
    
    def __init__(self):
        self.token = TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send(self, chat_id, content):
        """
        Send message to a Telegram chat
        
        Args:
            chat_id: Telegram chat ID
            content: Message content
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.token:
            print("⚠️ Telegram bot token not configured")
            return False
        
        try:
            # Telegram has 4096 character limit
            # Split long messages if needed
            messages = self._split_message(content, max_length=4000)
            
            for msg in messages:
                response = requests.post(
                    f"{self.base_url}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": msg,
                        "parse_mode": "HTML"
                    }
                )
                
                if response.status_code != 200:
                    print(f"⚠️ Telegram error: {response.text}")
                    return False
            
            return True
        
        except Exception as e:
            print(f"⚠️ Telegram error to {chat_id}: {e}")
            return False
    
    def _split_message(self, text, max_length=4000):
        """Split long message into chunks"""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            
            # Find last newline before limit
            split_point = text.rfind("\n", 0, max_length)
            if split_point == -1:
                split_point = max_length
            
            chunks.append(text[:split_point])
            text = text[split_point:].lstrip()
        
        return chunks
    
    def get_updates(self):
        """
        Get recent messages sent to the bot
        Used to capture chat_ids from /subscribe commands
        
        Returns:
            List of updates
        """
        if not self.token:
            return []
        
        try:
            response = requests.get(f"{self.base_url}/getUpdates")
            
            if response.status_code == 200:
                data = response.json()
                return data.get("result", [])
            
            return []
        
        except Exception as e:
            print(f"⚠️ Error getting updates: {e}")
            return []
    
    def process_subscribe_commands(self):
        """
        Process /subscribe commands and return new chat_ids
        
        Returns:
            List of chat_ids that sent /subscribe
        """
        updates = self.get_updates()
        
        new_subscribers = []
        
        for update in updates:
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")
            
            if text.lower() == "/subscribe" and chat_id:
                new_subscribers.append(str(chat_id))
                
                # Send confirmation
                self.send(chat_id, "✅ You are now subscribed to Cricket Daily Digest!\n\nYou will receive daily cricket news at 8 AM IST.")
        
        return new_subscribers
    
    def send_welcome(self, chat_id):
        """Send welcome message to new subscriber"""
        welcome = """
🏏 Welcome to Cricket Daily Digest!

You will receive:
- Daily cricket news at 8 AM IST
- Headlines from ESPN, Reddit, Twitter
- Sentiment analysis for each news

Commands:
/subscribe - Subscribe to daily digest
/unsubscribe - Unsubscribe

You can also ask questions about cricket news and I'll answer using AI!

Example: "What happened in yesterday's India match?"
"""
        return self.send(chat_id, welcome)


# Test
if __name__ == "__main__":
    agent = TelegramAgent()
    
    if agent.token:
        print("Telegram agent configured.")
        print("\nTo test:")
        print("1. Message your bot with /subscribe")
        print("2. Run: agent.process_subscribe_commands()")
        
        # Uncomment to see updates
        # updates = agent.get_updates()
        # print(f"\nRecent updates: {len(updates)}")
    else:
        print("⚠️ Telegram bot token not configured in .env")