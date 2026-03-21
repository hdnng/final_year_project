import streamlit as st

# nếu chưa login → về login
if "token" not in st.session_state:
    st.switch_page("pages/login.py")
else:
    st.switch_page("pages/home.py")