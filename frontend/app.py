import streamlit as st

# ===== INIT =====
if "is_login" not in st.session_state:
    st.session_state["is_login"] = False

# ===== ROUTING =====
if st.session_state["is_login"]:
    st.switch_page("pages/home.py")
else:
    st.switch_page("pages/login.py")