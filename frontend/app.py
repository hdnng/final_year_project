import streamlit as st
import requests

# ===== INIT CLIENT =====
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

client = st.session_state.client

# ===== CHECK LOGIN =====
try:
    res = client.get("http://127.0.0.1:8000/profile")

    if res.status_code == 200:
        st.switch_page("pages/home.py")
    else:
        st.switch_page("pages/login.py")

except:
    st.switch_page("pages/login.py")