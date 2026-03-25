import streamlit as st

def require_auth():
    client = st.session_state.get("client")

    if not client:
        st.switch_page("pages/login.py")

    res = client.get("http://127.0.0.1:8000/profile")

    if res.status_code != 200:
        st.switch_page("pages/login.py")