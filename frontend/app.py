"""
Application entry point — cookie restoration and routing.
"""

import requests
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from config import API_BASE_URL, COOKIE_PASSWORD

# ── Cookie Manager ──────────────────────────────────────────
cookies = EncryptedCookieManager(password=COOKIE_PASSWORD)
if not cookies.ready():
    st.stop()

# ── Initialize HTTP Client ──────────────────────────────────
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

# ── Restore Tokens from Cookies ─────────────────────────────
access_token = cookies.get("access_token")
refresh_token = cookies.get("refresh_token")

if access_token:
    st.session_state["access_token_value"] = access_token
    st.session_state.client.cookies.set("access_token", access_token)

if refresh_token:
    st.session_state["refresh_token_value"] = refresh_token
    st.session_state.client.cookies.set("refresh_token", refresh_token)

# ── Validate Session ────────────────────────────────────────
is_login = False

if access_token:
    try:
        res = st.session_state.client.get(
            f"{API_BASE_URL}/users/profile", timeout=5
        )
        if res.status_code == 200:
            is_login = True
        else:
            cookies.clear()
    except requests.RequestException:
        is_login = False

# ── Route ───────────────────────────────────────────────────
if is_login:
    st.switch_page("pages/home.py")
else:
    st.switch_page("pages/login.py")