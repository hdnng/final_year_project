import streamlit as st 
from services.auth_api import login
import requests

# ===== CONFIG =====
st.set_page_config(layout="centered", initial_sidebar_state="collapsed")

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

    res = login(st.session_state.client, email, password)

    if res.status_code == 200:
        st.session_state["is_login"] = True
        st.success("Login thành công")
        st.switch_page("pages/home.py")
    else:
        st.error("Sai tài khoản hoặc mật khẩu")

st.write("Chưa có tài khoản?")
if st.button("Đăng ký"):
    st.switch_page("pages/register.py")
