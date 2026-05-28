"""
Chat Page - RAG-powered Q&A about cricket news
"""

import streamlit as st
import requests

API_URL = "http://localhost:8000"


def render():
    st.title("💬 Ask About Cricket News")
    st.markdown("Chat with AI about recent cricket updates")
    
    st.markdown("---")
    
    # Check RAG status
    try:
        status_response = requests.get(f"{API_URL}/chat/status", timeout=5)
        if status_response.status_code == 200:
            status = status_response.json()
            doc_count = status.get("documents_indexed", 0)
            
            if doc_count > 0:
                st.success(f"✅ RAG Online - {doc_count} news articles indexed")
            else:
                st.warning("⚠️ No news indexed yet. Run the pipeline first.")
        else:
            st.warning("RAG status unavailable")
    except:
        st.info("Connect to API to check RAG status")
    
    st.markdown("---")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about cricket news..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = requests.post(
                        f"{API_URL}/chat/with-sources",
                        json={"question": prompt},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get("answer", "Sorry, I couldn't find an answer.")
                        sources = data.get("sources", [])
                        
                        st.markdown(answer)
                        
                        # Show sources
                        if sources:
                            st.markdown("---")
                            st.markdown("**Sources:**")
                            for s in sources:
                                st.markdown(f"- {s['headline'][:60]}... [{s['source'].upper()}]")
                        
                        # Save to history
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })
                    
                    else:
                        error_msg = "Sorry, I encountered an error. Please try again."
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                
                except requests.exceptions.ConnectionError:
                    error_msg = "Cannot connect to server. Make sure backend is running."
                    st.error(error_msg)
                
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
    
    # Sample questions
    st.markdown("---")
    st.markdown("### 💡 Sample Questions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        - Who won the recent India vs Australia series?
        - What happened in yesterday's match?
        - Is any player injured?
        """)
    
    with col2:
        st.markdown("""
        - When is the next IPL auction?
        - How many centuries did Kohli score?
        - What are the latest ICC updates?
        """)
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()