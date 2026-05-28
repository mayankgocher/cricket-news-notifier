"""
Home Page - Landing page with project intro
"""

import streamlit as st
import requests


def render():
    st.title("🏏 Cricket Daily Digest")
    st.markdown("### Your Daily Source for Cricket News")
    
    st.markdown("---")
    
    # Hero section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## Never Miss a Cricket Update!
        
        Get the latest cricket news delivered to your inbox or Telegram every morning at **8 AM IST**.
        
        **What you'll receive:**
        - 📰 Top 25-30 cricket headlines daily
        - 🎭 Sentiment analysis (Positive/Neutral/Negative)
        - 📊 Executive summary of the day's news
        - 🔍 AI-powered chat to ask questions
        
        **News Sources:**
        - ESPN Cricinfo
        - Reddit r/Cricket
        - Twitter Cricket Community
        """)
        
        if st.button("Subscribe Now →", type="primary"):
            st.switch_page("pages/subscribe.py") if hasattr(st, 'switch_page') else st.info("Go to Subscribe page from sidebar")
    
    with col2:
        st.markdown("""
        ### 📊 Quick Stats
        """)
        
        # Fetch stats from API
        try:
            response = requests.get("http://localhost:8000/subscribers/count", timeout=5)
            if response.status_code == 200:
                data = response.json()
                st.metric("Total Subscribers", data.get("total", 0))
                st.metric("Email Subscribers", data.get("email", 0))
                st.metric("Telegram Subscribers", data.get("telegram", 0))
            else:
                st.info("Stats unavailable")
        except:
            st.info("Connect to API for stats")
    
    st.markdown("---")
    
    # Features section
    st.markdown("## ✨ Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📧 Email Newsletter
        - Daily digest at 8 AM
        - Clean, readable format
        - One-click unsubscribe
        """)
    
    with col2:
        st.markdown("""
        ### 📱 Telegram Bot
        - Instant delivery
        - Ask questions anytime
        - Simple /subscribe command
        """)
    
    with col3:
        st.markdown("""
        ### 🤖 AI Chat
        - Ask about any news
        - Powered by RAG
        - Get detailed answers
        """)
    
    st.markdown("---")
    
    # Sample newsletter
    st.markdown("## 📰 Sample Newsletter")
    
    with st.expander("Click to see sample newsletter"):
        st.markdown("""
```
        🏏 CRICKET DAILY DIGEST - January 31, 2025
        =============================================
        
        📋 EXECUTIVE SUMMARY
        Today's cricket news is dominated by India's 
        historic series win against Australia...
        
        =============================================
        📰 TODAY'S NEWS
        =============================================
        
        1. 🟢 India wins Test series against Australia 3-1
           [ESPN]
        
        2. 🟢 Kohli scores century in final Test
           [REDDIT]
        
        3. 🔴 Bumrah ruled out with back injury
           [TWITTER]
        
        ...
```
        """)