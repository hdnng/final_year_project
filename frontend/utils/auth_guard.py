import streamlit as st

def require_auth():
    if not st.session_state.get("is_login"):
        st.switch_page("pages/login.py")