import streamlit as st
from services.auth_api import register
import requests

# ===== INIT CLIENT =====
if "client" not in st.session_state:
    st.session_state.client = requests.Session()
if "access_token_value" not in st.session_state:
    st.session_state["access_token_value"] = None
if "refresh_token_value" not in st.session_state:
    st.session_state["refresh_token_value"] = None

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

# ===== PASSWORD STRENGTH CHECK =====
if password:
    if len(password) < 6:
        st.warning("🔴 Mật khẩu phải ít nhất 6 ký tự")
    elif not any(c.isupper() for c in password):
        st.warning("🟡 Mật khẩu phải chứa ít nhất 1 ký tự in hoa")
    elif not any(c.isdigit() for c in password):
        st.warning("🟡 Mật khẩu phải chứa ít nhất 1 chữ số")
    else:
        st.success("🟢 Mật khẩu mạnh")

if st.button("Đăng ký"):
    # ===== VALIDATION =====
    if not name or not email or not password or not confirm:
        st.error("❌ Vui lòng nhập đầy đủ thông tin")
    elif password != confirm:
        st.error("❌ Mật khẩu không khớp")
    elif len(password) < 6:
        st.error("❌ Mật khẩu phải ít nhất 6 ký tự")
    elif not any(c.isupper() for c in password):
        st.error("❌ Mật khẩu phải chứa ít nhất 1 ký tự in hoa")
    elif not any(c.isdigit() for c in password):
        st.error("❌ Mật khẩu phải chứa ít nhất 1 chữ số")
    else:
        with st.spinner("Đang đăng ký..."):
            res = register(st.session_state.client, name, email, password)

            if res.status_code == 200:
                st.success("✅ Đăng ký thành công! Vui lòng đăng nhập")
                st.switch_page("pages/login.py")

            elif res.status_code == 409:
                st.error("❌ Email này đã được đăng ký")

            elif res.status_code == 429:
                try:
                    detail = res.json().get("detail", "Quá nhiều yêu cầu đăng ký")
                except Exception:
                    detail = "Quá nhiều yêu cầu đăng ký. Vui lòng thử lại sau"
                st.error(f"🔒 {detail}")

            elif res.status_code == 422:
                st.error("❌ Dữ liệu không hợp lệ")

            else:
                try:
                    detail = res.json().get("detail", res.text)
                except Exception:
                    detail = res.text
                st.error(f"❌ Lỗi: {detail}")

st.divider()

if st.button("⬅️ Quay lại đăng nhập", use_container_width=True):
    st.switch_page("pages/login.py")
