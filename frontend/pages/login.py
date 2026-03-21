import streamlit as st
from services.auth_api import login

# ===== CONFIG =====
st.set_page_config(layout="centered", initial_sidebar_state="collapsed")

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
    res = login(email, password)
    data = res.json()

    if "access_token" in data:
        st.session_state["token"] = data["access_token"]
        st.success("Login thành công")
        st.switch_page("pages/home.py")
    else:
        st.error("Sai tài khoản hoặc mật khẩu")

st.write("Chưa có tài khoản?")
if st.button("Đăng ký"):
    st.switch_page("pages/register.py")