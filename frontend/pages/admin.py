"""
Admin Page - Pipeline control and monitoring
"""

import streamlit as st
import requests
from datetime import datetime

API_URL = "http://localhost:8000"


def render():
    st.title("⚙️ Admin Panel")
    st.markdown("Monitor and control the news pipeline")
    
    st.markdown("---")
    
    # Pipeline status
    st.markdown("### 📊 Pipeline Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        try:
            response = requests.get(f"{API_URL}/pipeline/status", timeout=5)
            
            if response.status_code == 200:
                status = response.json()
                
                if status["running"]:
                    st.warning("🔄 Pipeline is currently running...")
                else:
                    st.success("✅ Pipeline idle")
                
                if status["last_run"]:
                    st.markdown(f"**Last run:** {status['last_run']}")
                
                if status["last_result"]:
                    result = status["last_result"]
                    if result.get("success"):
                        st.markdown(f"**News processed:** {result.get('news_count', 0)}")
                        st.markdown(f"**Emails sent:** {result.get('emails_sent', 0)}")
                        st.markdown(f"**Telegram sent:** {result.get('telegram_sent', 0)}")
                    else:
                        st.error(f"Last run failed: {result.get('error', 'Unknown error')}")
            else:
                st.info("Status unavailable")
        
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to server")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with col2:
        # Subscriber stats
        try:
            response = requests.get(f"{API_URL}/subscribers/count", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                st.metric("Total Subscribers", data.get("total", 0))
                st.metric("Email", data.get("email", 0))
                st.metric("Telegram", data.get("telegram", 0))
        except:
            st.info("Subscriber stats unavailable")
    
    st.markdown("---")
    
    # Run pipeline button
    st.markdown("### 🚀 Run Pipeline")
    
    st.warning("⚠️ This will fetch news, send newsletters, and update the database.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Run Pipeline (Background)", type="primary"):
            try:
                response = requests.post(f"{API_URL}/pipeline/run", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success(data.get("message", "Pipeline started!"))
                    st.info("Refresh the page to see status updates")
                else:
                    st.error("Failed to start pipeline")
            
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to server")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("Run Pipeline (Wait for completion)"):
            try:
                with st.spinner("Running pipeline... This may take a few minutes"):
                    response = requests.post(f"{API_URL}/pipeline/run-sync", timeout=300)
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data.get('message', 'Pipeline completed!')}")
                        if data.get("news_count"):
                            st.info(f"Processed {data['news_count']} news items")
                    else:
                        st.error("Pipeline failed")
            
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to server")
            except requests.exceptions.Timeout:
                st.error("Pipeline timed out")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    
    # RAG status
    st.markdown("### 🧠 RAG System")
    
    try:
        response = requests.get(f"{API_URL}/chat/status", timeout=5)
        
        if response.status_code == 200:
            status = response.json()
            
            col1, col2 = st.columns(2)
            
            with col1:
                if status.get("status") == "online":
                    st.success("✅ RAG System Online")
                else:
                    st.error("❌ RAG System Offline")
            
            with col2:
                st.metric("Documents Indexed", status.get("documents_indexed", 0))
    
    except:
        st.info("RAG status unavailable")
    
    st.markdown("---")
    
    # API health
    st.markdown("### 🏥 API Health")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            st.success("✅ API is healthy")
        else:
            st.error("❌ API unhealthy")
    
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API server")
        st.info("Make sure to run: `uvicorn backend.main:app --reload`")
    except Exception as e:
        st.error(f"Error: {str(e)}")