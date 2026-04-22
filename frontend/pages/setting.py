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
st.markdown(
    '<div class="page-title">Cài đặt tài khoản</div>',
    unsafe_allow_html=True,
)

# ── Account Info Card ───────────────────────────────────────
with st.container():
    st.markdown("""
    <div id="account-card-marker"></div>
    <div class="card-title">Thông tin tài khoản</div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 6])
    with col1:
        st.image("https://i.pravatar.cc/150", width=80)
    with col2:
        st.markdown(f'<div class="profile-name">{full_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="profile-email">{email}</div>', unsafe_allow_html=True)
        st.button("Thay đổi ảnh")
        

    
    c1, c2 = st.columns(2)
    with c1:
        name_input = st.text_input("Họ và Tên", value=full_name)
    with c2:
        email_input = st.text_input("Email", value=email)
        
    col_empty, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button("Lưu thay đổi", type="primary", use_container_width=True):
            if not name_input or not email_input:
                st.warning("⚠️ Vui lòng nhập đầy đủ thông tin")
            else:
                with st.spinner("Đang cập nhật..."):
                    success, res = update_user(client, name_input, email_input)
                if success:
                    st.toast("✅ Cập nhật thành công!")
                    st.rerun()
                else:
                    st.error(f"❌ {res}")

# ── Security Card ───────────────────────────────────────────
with st.container():
    st.markdown("""
    <div id="security-card-marker"></div>
    <div class="card-title">Bảo mật</div>
    """, unsafe_allow_html=True)
    
    col_icon, col_text, col_btn = st.columns([0.5, 4, 1])
    with col_icon:
        st.markdown("""
        <div id="security-row-marker"></div>
        <div class="security-icon-wrapper">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="5" y="11" width="14" height="10" rx="2" stroke="#f59e0b" stroke-width="2"/>
                <path d="M8 11V7C8 4.79086 9.79086 3 12 3C14.2091 3 16 4.79086 16 7V11" stroke="#f59e0b" stroke-width="2"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    with col_text:
        st.markdown('<div class="security-title">Đổi mật khẩu</div>', unsafe_allow_html=True)
        st.markdown('<div class="security-subtitle">Cập nhật mật khẩu để bảo vệ tài khoản tốt hơn</div>', unsafe_allow_html=True)
    with col_btn:
        if st.button("Thay đổi", use_container_width=True):
            st.session_state.show_pw_change = not st.session_state.get("show_pw_change", False)
            
    if st.session_state.get("show_pw_change", False):
        st.markdown('<hr style="margin: 16px 0; border-color: #e2e8f0;">', unsafe_allow_html=True)
        
        show_pass = st.checkbox("Hiển thị mật khẩu")
        pw_type = "text" if show_pass else "password"

        pw1, pw2, pw3 = st.columns(3)
        with pw1:
            old_pw = st.text_input("Mật khẩu cũ", type=pw_type)
        with pw2:
            new_pw = st.text_input("Mật khẩu mới", type=pw_type)
        with pw3:
            confirm_pw = st.text_input("Xác nhận mật khẩu", type=pw_type)

        col_space, col_pw_btn = st.columns([4, 1])
        with col_pw_btn:
            if st.button("Cập nhật mật khẩu", type="primary", use_container_width=True):
                if not old_pw or not new_pw or not confirm_pw:
                    st.warning("⚠️ Vui lòng nhập đầy đủ thông tin")
                elif new_pw != confirm_pw:
                    st.error("❌ Mật khẩu xác nhận không khớp")
                elif len(new_pw) < 6:
                    st.warning("⚠️ Mật khẩu phải ít nhất 6 ký tự")
                else:
                    with st.spinner("Đang cập nhật..."):
                        success, res = change_password(client, old_pw, new_pw)
                    if success:
                        st.toast("✅ Đổi mật khẩu thành công!")
                        st.session_state.show_pw_change = False
                        st.rerun()
                    else:
                        st.error(f"❌ {res}")