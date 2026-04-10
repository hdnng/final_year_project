import streamlit as st
import requests
from streamlit_cookies_manager import EncryptedCookieManager

def require_auth():
    cookies = EncryptedCookieManager(password="secret_key")
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
        st.error("❌ Chưa đăng nhập")
        st.switch_page("pages/login.py")
        st.stop()

    try:
        res = client.get("http://127.0.0.1:8000/users/profile", timeout=5)

        if res.status_code != 200:
            cookies.clear()
            st.error("❌ Phiên hết hạn")
            st.switch_page("pages/login.py")
            st.stop()

    except:
        st.error("❌ Lỗi kết nối")
        st.switch_page("pages/login.py")
        st.stop()