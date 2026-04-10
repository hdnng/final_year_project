import streamlit as st
import requests
from streamlit_cookies_manager import EncryptedCookieManager

# ===== COOKIE =====
cookies = EncryptedCookieManager(password="secret_key")
if not cookies.ready():
    st.stop()

# ===== INIT SESSION =====
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

# ===== RESTORE FROM COOKIE =====
access_token = cookies.get("access_token")
refresh_token = cookies.get("refresh_token")

if access_token:
    st.session_state["access_token_value"] = access_token
    st.session_state.client.cookies.set("access_token", access_token)

if refresh_token:
    st.session_state["refresh_token_value"] = refresh_token
    st.session_state.client.cookies.set("refresh_token", refresh_token)

# ===== VALIDATION =====
client = st.session_state.client

is_login = False

if access_token:
    try:
        res = client.get("http://127.0.0.1:8000/users/profile", timeout=5)

        if res.status_code == 200:
            is_login = True
        else:
            cookies.clear()
    except:
        is_login = False

# ===== ROUTING =====
if is_login:
    st.switch_page("pages/home.py")
else:
    st.switch_page("pages/login.py")