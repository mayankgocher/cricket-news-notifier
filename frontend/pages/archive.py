"""
Archive Page - View past newsletters
"""

import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"


def render():
    st.title("📚 Newsletter Archive")
    st.markdown("Browse past cricket news digests")
    
    st.markdown("---")
    
    # Fetch newsletters
    try:
        response = requests.get(f"{API_URL}/newsletters/", timeout=10)
        
        if response.status_code == 200:
            newsletters = response.json()
            
            if not newsletters:
                st.info("No newsletters yet. Check back after the first digest is sent!")
                return
            
            # Display newsletters
            for nl in newsletters:
                sent_at = datetime.fromisoformat(nl["sent_at"].replace("Z", "+00:00"))
                date_str = sent_at.strftime("%B %d, %Y at %I:%M %p")
                
                with st.expander(f"📰 {date_str} - {nl['headlines_count']} headlines"):
                    st.markdown(f"**Sent to:** {nl['subscriber_count']} subscribers")
                    st.markdown("---")
                    
                    # Fetch full content
                    detail_response = requests.get(
                        f"{API_URL}/newsletters/{nl['id']}",
                        timeout=10
                    )
                    
                    if detail_response.status_code == 200:
                        detail = detail_response.json()
                        st.text(detail["content"])
                    else:
                        st.warning("Could not load newsletter content")
        
        else:
            st.error("Failed to fetch newsletters")
    
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to server. Make sure backend is running.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # Latest newsletter quick view
    st.markdown("### 🆕 Latest Newsletter")
    
    try:
        response = requests.get(f"{API_URL}/newsletters/latest/one", timeout=10)
        
        if response.status_code == 200:
            latest = response.json()
            sent_at = datetime.fromisoformat(latest["sent_at"].replace("Z", "+00:00"))
            
            st.success(f"Last sent: {sent_at.strftime('%B %d, %Y at %I:%M %p')}")
            st.metric("Headlines", latest["headlines_count"])
            
            with st.expander("View Content"):
                st.text(latest["content"])
        
        elif response.status_code == 404:
            st.info("No newsletters sent yet")
        
        else:
            st.warning("Could not fetch latest newsletter")
    
    except requests.exceptions.ConnectionError:
        st.info("Connect to API to view latest newsletter")
    except Exception as e:
        st.warning(f"Error: {str(e)}")