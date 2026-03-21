import streamlit as st
from services.auth_api import register

st.set_page_config(layout="centered", initial_sidebar_state="collapsed")

# ẩn sidebar
st.markdown("""
<style>
[data-testid="stSidebar"] {display: none;}
</style>
""", unsafe_allow_html=True)

st.title("Đăng ký")

name = st.text_input("Họ tên")
email = st.text_input("Email")
password = st.text_input("Mật khẩu", type="password")
confirm = st.text_input("Xác nhận mật khẩu", type="password")

if st.button("Đăng ký"):
    if password != confirm:
        st.error("Mật khẩu không khớp")
    else:
        res = register(name, email, password)

        if res.status_code == 200:
            st.success("Đăng ký thành công")
            st.switch_page("pages/login.py")
        else:
            st.error("Đăng ký thất bại")

if st.button("Quay lại đăng nhập"):
    st.switch_page("pages/login.py")