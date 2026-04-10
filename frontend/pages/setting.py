import streamlit as st
import requests
from components.app_sidebar import render_sidebar
from utils.load_css import load_css
from services.user_api import change_password, update_user, get_user
from utils.auth_guard import require_auth

# ===== CONFIG =====
st.set_page_config(layout="wide")

# ===== INIT SESSION STATE (CRITICAL!) =====
if "is_login" not in st.session_state:
    st.session_state["is_login"] = False
if "access_token_value" not in st.session_state:
    st.session_state["access_token_value"] = None
if "refresh_token_value" not in st.session_state:
    st.session_state["refresh_token_value"] = None
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

# ===== AUTH CHECK =====
require_auth()

# ===== SIDEBAR =====
from utils.hide_streamlit_sidebar import hide_sidebar

hide_sidebar()
from utils.load_css import load_css
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
render_sidebar(active="setting")

# ===== LOAD CSS =====
st.markdown(load_css("styles/setting.css"), unsafe_allow_html=True)

# ===== LOAD USER DATA =====
client = st.session_state.client
user = get_user(client)

if not user:
    st.error("❌ Không thể tải thông tin người dùng. Vui lòng đạng nhập lại")
    if st.button("🔄 Đăng nhập lại"):
        st.session_state.clear()
        st.switch_page("pages/login.py")
    st.stop()

# ===== GET FIELDS (support both full_name and name) =====
full_name = user.get("full_name") or user.get("name", "")
email = user.get("email", "")

# ===== SUCCESS MESSAGE =====
if st.session_state.get("update_success"):
    st.success("✅ Cập nhật thành công!")
    st.session_state.update_success = False

# ===== UI =====
st.title("⚙️ Cài đặt tài khoản")
st.caption("Quản lý thông tin cá nhân và thiết lập bảo mật của bạn.")

st.divider()

# ===== ACCOUNT INFO =====
st.subheader("Thông tin tài khoản")

col1, col2 = st.columns([1, 3])

with col1:
    st.image("https://i.pravatar.cc/100")

with col2:
    st.write(f"**{full_name}**")
    st.caption(email)

# ===== FORM UPDATE USER =====
st.subheader("Chỉnh sửa thông tin")

with st.form("update_user_form"):
    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Họ và tên", value=full_name)

    with col2:
        email_input = st.text_input("Email", value=email)

    submitted = st.form_submit_button("💾 Lưu thay đổi", use_container_width=True)

    if submitted:
        if not name or not email_input:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin")
        else:
            with st.spinner("Đang cập nhật..."):
                success, res = update_user(client, name, email_input)

            if success:
                st.session_state.update_success = True
                st.rerun()
            else:
                st.error(f"❌ {res}")

st.divider()

# ===== SECURITY =====
st.subheader("🔒 Bảo mật")

with st.expander("Đổi mật khẩu"):

    with st.form("change_password_form"):

        # ===== TOGGLE SHOW PASSWORD =====
        show_pass = st.checkbox("Hiển thị mật khẩu")
        password_type = "text" if show_pass else "password"

        # ===== INPUT =====
        old_password = st.text_input("Mật khẩu cũ", type=password_type)
        new_password = st.text_input("Mật khẩu mới", type=password_type)
        confirm_password = st.text_input("Xác nhận mật khẩu", type=password_type)

        # ===== PASSWORD STRENGTH =====
        if new_password:
            if len(new_password) < 6:
                st.error("🔴 Mật khẩu yếu (< 6 ký tự)")
            elif len(new_password) < 10:
                st.warning("🟡 Mật khẩu trung bình (6-10 ký tự)")
            else:
                st.success("🟢 Mật khẩu mạnh (> 10 ký tự)")

        # ===== SUBMIT =====
        submitted_pass = st.form_submit_button("Cập nhật mật khẩu", use_container_width=True)

        if submitted_pass:

            if not old_password or not new_password or not confirm_password:
                st.warning("⚠️ Vui lòng nhập đầy đủ thông tin")

            elif new_password != confirm_password:
                st.error("❌ Mật khẩu xác nhận không khớp")

            elif len(new_password) < 6:
                st.warning("⚠️ Mật khẩu phải ít nhất 6 ký tự")

            else:
                with st.spinner("Đang cập nhật mật khẩu..."):
                    success, res = change_password(client, old_password, new_password)

                if success:
                    st.toast("✅ Đổi mật khẩu thành công!")
                    st.rerun()
                else:
                    st.error(f"❌ {res}")