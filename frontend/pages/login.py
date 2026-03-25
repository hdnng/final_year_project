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
    st.write("👉 BUTTON CLICKED")

    res = login(st.session_state.client, email, password)

    st.write("STATUS:", res.status_code)
    st.write("RESPONSE:", res.text)

    if res.status_code == 200:
        st.success("Login thành công")
        st.switch_page("pages/home.py")
    else:
        st.error("Sai tài khoản hoặc mật khẩu")

st.write("Chưa có tài khoản?")
if st.button("Đăng ký"):
    st.switch_page("pages/register.py")


res = login(st.session_state.client, email, password)

st.write("LOGIN:", res.status_code)

res2 = st.session_state.client.get("http://127.0.0.1:8000/profile")

st.write("PROFILE:", res2.status_code)
st.write("PROFILE TEXT:", res2.text)