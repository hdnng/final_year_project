"""
Authentication guard — redirects unauthenticated users to login.
"""

import requests
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

from config import API_BASE_URL, COOKIE_PASSWORD


def require_auth() -> None:
    """
    Verify the user is authenticated.

    Restores tokens from cookies into the HTTP client, then validates
    against the backend. Redirects to login on failure.
    """
    cookies = EncryptedCookieManager(password=COOKIE_PASSWORD)
    if not cookies.ready():
        st.stop()

    if "client" not in st.session_state:
        st.session_state.client = requests.Session()

    client = st.session_state.client

    access_token = cookies.get("access_token")
    refresh_token = cookies.get("refresh_token")

    if access_token:
        client.cookies.set("access_token", access_token)
    if refresh_token:
        client.cookies.set("refresh_token", refresh_token)

    if not access_token:
        st.error("Please log in to continue")
        st.switch_page("pages/login.py")
        st.stop()

    try:
        res = client.get(f"{API_BASE_URL}/users/profile", timeout=5)
        if res.status_code != 200:
            cookies.clear()
            st.error("Session expired")
            st.switch_page("pages/login.py")
            st.stop()
    except requests.RequestException:
        st.error("Connection error")
        st.switch_page("pages/login.py")
        st.stop()