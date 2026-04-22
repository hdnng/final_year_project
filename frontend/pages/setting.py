"""Settings page — profile editing and password change."""

import streamlit as st

from components.app_sidebar import render_sidebar
from services.user_api import change_password, get_user, update_user
from utils.auth_guard import require_auth
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.http import init_session_state
from utils.load_css import load_css

# ── Config ──────────────────────────────────────────────────
st.set_page_config(layout="wide")

init_session_state()
require_auth()

# ── Sidebar ─────────────────────────────────────────────────
hide_sidebar()
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
render_sidebar(active="setting")

# ── Styles ──────────────────────────────────────────────────
st.markdown(load_css("styles/setting.css"), unsafe_allow_html=True)

# ── Load User ───────────────────────────────────────────────
client = st.session_state.client
user = get_user(client)

if not user:
    st.error("❌ Không thể tải thông tin người dùng. Vui lòng đăng nhập lại")
    if st.button("🔄 Đăng nhập lại"):
        st.session_state.clear()
        st.switch_page("pages/login.py")
    st.stop()

full_name = user.get("full_name") or user.get("name", "")
email = user.get("email", "")

# ── Success Flash ───────────────────────────────────────────
if st.session_state.get("update_success"):
    st.success("✅ Cập nhật thành công!")
    st.session_state.update_success = False

# ── Header ──────────────────────────────────────────────────
st.title("⚙️ Cài đặt tài khoản")
st.caption("Quản lý thông tin cá nhân và thiết lập bảo mật của bạn.")
st.divider()

# ── Account Info ────────────────────────────────────────────
st.subheader("Thông tin tài khoản")

col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://i.pravatar.cc/100")
with col2:
    st.write(f"**{full_name}**")
    st.caption(email)

# ── Profile Form ────────────────────────────────────────────
st.subheader("Chỉnh sửa thông tin")

with st.form("update_user_form"):
    c1, c2 = st.columns(2)
    with c1:
        name_input = st.text_input("Họ và tên", value=full_name)
    with c2:
        email_input = st.text_input("Email", value=email)

    submitted = st.form_submit_button("💾 Lưu thay đổi", use_container_width=True)

    if submitted:
        if not name_input or not email_input:
            st.warning("⚠️ Vui lòng nhập đầy đủ thông tin")
        else:
            with st.spinner("Đang cập nhật..."):
                success, res = update_user(client, name_input, email_input)
            if success:
                st.session_state.update_success = True
                st.rerun()
            else:
                st.error(f"❌ {res}")

st.divider()

# ── Security ────────────────────────────────────────────────
st.subheader("🔒 Bảo mật")

with st.expander("Đổi mật khẩu"):
    with st.form("change_password_form"):
        show_pass = st.checkbox("Hiển thị mật khẩu")
        pw_type = "text" if show_pass else "password"

        old_pw = st.text_input("Mật khẩu cũ", type=pw_type)
        new_pw = st.text_input("Mật khẩu mới", type=pw_type)
        confirm_pw = st.text_input("Xác nhận mật khẩu", type=pw_type)

        if new_pw:
            if len(new_pw) < 6:
                st.error("🔴 Mật khẩu yếu (< 6 ký tự)")
            elif len(new_pw) < 10:
                st.warning("🟡 Mật khẩu trung bình (6-10 ký tự)")
            else:
                st.success("🟢 Mật khẩu mạnh (> 10 ký tự)")

        submitted_pass = st.form_submit_button("Cập nhật mật khẩu", use_container_width=True)

        if submitted_pass:
            if not old_pw or not new_pw or not confirm_pw:
                st.warning("⚠️ Vui lòng nhập đầy đủ thông tin")
            elif new_pw != confirm_pw:
                st.error("❌ Mật khẩu xác nhận không khớp")
            elif len(new_pw) < 6:
                st.warning("⚠️ Mật khẩu phải ít nhất 6 ký tự")
            else:
                with st.spinner("Đang cập nhật mật khẩu..."):
                    success, res = change_password(client, old_pw, new_pw)
                if success:
                    st.toast("✅ Đổi mật khẩu thành công!")
                    st.rerun()
                else:
                    st.error(f"❌ {res}")