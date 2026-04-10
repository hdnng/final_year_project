import streamlit as st
from services.auth_api import login
import requests
from streamlit_cookies_manager import EncryptedCookieManager

# ===== CONFIG =====
st.set_page_config(layout="centered", initial_sidebar_state="collapsed")

# ===== COOKIE =====
cookies = EncryptedCookieManager(password="secret_key")
if not cookies.ready():
    st.stop()

# ===== INIT CLIENT =====
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

# ẩn sidebar
st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.title("Đăng nhập")

email = st.text_input("Email")
password = st.text_input("Mật khẩu", type="password")

if st.button("Đăng nhập"):
    if not email or not password:
        st.error("❌ Vui lòng nhập đầy đủ email và mật khẩu")
    else:
        with st.spinner("Đang kiểm tra..."):
            res = login(st.session_state.client, email, password)

        if res.status_code == 200:
            data = res.json()

            access_token = data.get("access_token")
            refresh_token = data.get("refresh_token")

            if access_token:
                # ✅ Lưu vào cookie (QUAN TRỌNG)
                cookies["access_token"] = access_token
                if refresh_token:
                    cookies["refresh_token"] = refresh_token
                cookies.save()

                # ✅ Lưu tạm vào session
                st.session_state["access_token_value"] = access_token
                st.session_state["refresh_token_value"] = refresh_token
                st.session_state["is_login"] = True

                # set cookie cho client gọi API
                st.session_state.client.cookies.set("access_token", access_token)
                if refresh_token:
                    st.session_state.client.cookies.set("refresh_token", refresh_token)

                st.success("✅ Đăng nhập thành công")
                st.switch_page("pages/home.py")

        elif res.status_code == 401:
            st.error("❌ Email hoặc mật khẩu không chính xác")
        else:
            st.error(f"❌ Lỗi: {res.text}")


st.divider() 
col1, col2 = st.columns(2) 
with col1: 
    st.write("Chưa có tài khoản?") 
    if st.button("📝 Đăng ký", use_container_width=True): 
        st.switch_page("pages/register.py") 

with col2: 
    st.write("") 
    if st.button("🔧 Quên mật khẩu?", use_container_width=True): 
        st.info("Tính năng đang phát triển")