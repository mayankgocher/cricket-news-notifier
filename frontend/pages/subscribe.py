"""
Subscribe Page - Email and Telegram subscription
"""

import streamlit as st
import requests

API_URL = "http://localhost:8000"


def render():
    st.title("📬 Subscribe to Cricket Daily Digest")
    st.markdown("Get daily cricket news delivered to you!")
    
    st.markdown("---")
    
    # Subscription form
    st.markdown("### Choose Your Subscription")
    
    col1, col2 = st.columns(2)
    
    # Email subscription
    with col1:
        st.markdown("#### 📧 Email Newsletter")
        
        email = st.text_input("Enter your email", placeholder="you@example.com")
        email_subscribe = st.checkbox("Subscribe via Email", value=True)
        
        if st.button("Subscribe with Email", type="primary"):
            if not email:
                st.error("Please enter your email")
            elif not email_subscribe:
                st.error("Please check the subscription box")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/subscribers/subscribe",
                        json={
                            "email": email,
                            "email_subscribe": True,
                            "telegram_subscribe": False
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(data.get("message", "Subscribed successfully!"))
                    else:
                        error = response.json().get("detail", "Subscription failed")
                        st.error(error)
                
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to server. Make sure backend is running.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Telegram subscription
    with col2:
        st.markdown("#### 📱 Telegram Bot")
        
        st.markdown("""
        **Steps to subscribe via Telegram:**
        
        1. Open Telegram
        2. Search for our bot: `@YourCricketBot`
        3. Start the bot
        4. Send `/subscribe`
        5. Done! ✅
        """)
        
        st.info("💡 You can subscribe to both Email and Telegram!")
        
        # Telegram deep link (update with actual bot username)
        st.link_button(
            "Open Telegram Bot",
            "https://t.me/Cricket_daily_digest_bot",
            type="secondary"
        )
    
    st.markdown("---")
    
    # Unsubscribe section
    st.markdown("### 🔕 Unsubscribe")
    
    with st.expander("Click to unsubscribe"):
        unsub_email = st.text_input("Email to unsubscribe", key="unsub_email")
        
        if st.button("Unsubscribe"):
            if not unsub_email:
                st.error("Please enter your email")
            else:
                try:
                    response = requests.post(
                        f"{API_URL}/subscribers/unsubscribe",
                        params={"email": unsub_email},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        st.success("Unsubscribed successfully!")
                    else:
                        error = response.json().get("detail", "Unsubscribe failed")
                        st.error(error)
                
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to server")
                except Exception as e:
                    st.error(f"Error: {str(e)}")