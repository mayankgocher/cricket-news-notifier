"""
Email Agent - Sends newsletters via Gmail SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.config.settings import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD


class EmailAgent:
    """Sends emails via SMTP"""
    
    def __init__(self):
        self.server = SMTP_SERVER
        self.port = SMTP_PORT
        self.email = SMTP_EMAIL
        self.password = SMTP_PASSWORD
    
    def send(self, to_email, content, subject="🏏 Cricket Daily Digest"):
        """
        Send newsletter email
        
        Args:
            to_email: Recipient email address
            content: Newsletter content (plain text)
            subject: Email subject
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not all([self.server, self.email, self.password]):
            print("⚠️ Email not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email
            msg["To"] = to_email
            
            # Plain text version
            text_part = MIMEText(content, "plain", "utf-8")
            msg.attach(text_part)
            
            # HTML version
            html_content = self._text_to_html(content)
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.sendmail(self.email, to_email, msg.as_string())
            
            return True
        
        except Exception as e:
            print(f"⚠️ Email error to {to_email}: {e}")
            return False
    
    def _text_to_html(self, text):
        """Convert plain text newsletter to beautiful HTML"""
        
        # Parse the text content
        lines = text.split('\n')
        
        html_body = ""
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Header
            if "CRICKET DAILY DIGEST" in line:
                html_body += f'<h1 style="color: #1e88e5; text-align: center;">{line}</h1>'
            
            # Section headers
            elif "EXECUTIVE SUMMARY" in line:
                html_body += f'<h2 style="color: #43a047; border-bottom: 2px solid #43a047; padding-bottom: 5px;">📋 Executive Summary</h2>'
            
            elif "TODAY\'S NEWS" in line or "TODAY'S NEWS" in line:
                html_body += f'<h2 style="color: #43a047; border-bottom: 2px solid #43a047; padding-bottom: 5px;">📰 Today\'s News</h2>'
            
            # Dividers
            elif line.startswith('='):
                html_body += '<hr style="border: 1px solid #e0e0e0; margin: 20px 0;">'
            
            # News items (numbered)
            elif line and line[0].isdigit() and '.' in line[:3]:
                # Extract emoji and headline
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    num = parts[0]
                    emoji = parts[1]
                    headline = parts[2]
                    
                    # Color based on sentiment
                    color = "#43a047" if emoji == "🟢" else "#e53935" if emoji == "🔴" else "#fb8c00"
                    
                    html_body += f'''
                    <div style="background: #f5f5f5; padding: 15px; margin: 10px 0; border-left: 4px solid {color}; border-radius: 4px;">
                        <strong style="color: {color};">{emoji} {headline}</strong>
                    '''
            
            # Summary line
            elif line.startswith('📝'):
                summary = line.replace('📝', '').strip()
                html_body += f'<p style="color: #666; margin: 8px 0; font-size: 14px;">{summary}</p>'
            
            # Source badge
            elif line.startswith('[') and line.endswith(']'):
                source = line[1:-1]
                html_body += f'<span style="background: #e3f2fd; color: #1565c0; padding: 2px 8px; border-radius: 12px; font-size: 12px;">{source}</span></div>'
            
            # Footer links
            elif "Want more details" in line or "unsubscribe" in line.lower():
                html_body += f'<p style="color: #888; font-size: 13px;">{line}</p>'
            
            # Regular text
            else:
                html_body += f'<p style="color: #333; line-height: 1.6;">{line}</p>'
        
        # Wrap in HTML template
        return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #fafafa;">
    <div style="background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        {html_body}
        
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
            <p style="color: #888; font-size: 12px;">
                🏏 Cricket Daily Digest<br>
                You're receiving this because you subscribed.
            </p>
        </div>
    </div>
</body>
</html>
'''
    
    def send_verification(self, to_email, token, site_url):
        """
        Send email verification link
        
        Args:
            to_email: Recipient email
            token: Verification token
            site_url: Base URL of the site
        
        Returns:
            True if sent successfully
        """
        verify_link = f"{site_url}/verify?token={token}"
        
        content = f"""
Welcome to Cricket Daily Digest! 🏏

Please verify your email by clicking the link below:

{verify_link}

This link expires in 24 hours.

If you didn't subscribe, please ignore this email.

---
Cricket Daily Digest Team
"""
        
        return self.send(to_email, content, subject="🏏 Verify your subscription")


# Test
if __name__ == "__main__":
    agent = EmailAgent()
    
    test_content = """
🏏 CRICKET DAILY DIGEST - Test

This is a test newsletter.

1. 🟢 India wins against Australia
   [ESPN]

2. 🔴 Player injured before match
   [REDDIT]

---
Thanks for subscribing!
"""
    
    # Uncomment to test (requires valid SMTP config)
    # success = agent.send("your_email@example.com", test_content)
    # print(f"Email sent: {success}")
    
    print("Email agent initialized. Configure .env to test sending.")