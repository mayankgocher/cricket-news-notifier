"""
Main Streamlit App - Entry point with navigation
"""

import streamlit as st

# Page config (must be first)
st.set_page_config(
    page_title="Cricket Daily Digest",
    page_icon="🏏",
    layout="wide"
)

# Navigation
st.sidebar.title("🏏 Cricket Daily Digest")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigate",
    ["Home", "Subscribe", "Archive", "Chat", "Admin"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ for Cricket Fans")

# Route to pages
if page == "Home":
    from pages.home import render
    render()

elif page == "Subscribe":
    from pages.subscribe import render
    render()

elif page == "Archive":
    from pages.archive import render
    render()

elif page == "Chat":
    from pages.chat import render
    render()

elif page == "Admin":
    from pages.admin import render
    render()