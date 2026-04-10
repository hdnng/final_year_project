import streamlit as st
from services.auth_api import logout

def render_sidebar(active="home"):
    with st.sidebar:

        st.markdown("""
        <div class="sidebar-logo">
            <h2>🎓 EduVision AI</h2>
            <p>Phân tích hành vi người học</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # ===== MENU FUNCTION =====
        def menu(label, icon, page, key):
            if st.button(f"{icon} {label}", key=key, use_container_width=True):
                st.switch_page(page)

        menu("Giám sát", "📹", "pages/home.py", "home")
        menu("Thống kê", "📊", "pages/statistics.py", "statistics")
        menu("Lịch sử", "🕘", "pages/history.py", "history")
        menu("Cài đặt", "⚙️", "pages/setting.py", "setting")

        st.markdown("---")

        if st.button("🚪 Đăng xuất", use_container_width=True):
            # Call logout API to blacklist token
            try:
                if "client" in st.session_state:
                    logout_res = logout(st.session_state.client)
                    if logout_res and logout_res.status_code == 200:
                        st.info("✅ Đăng xuất thành công")
                    else:
                        st.warning("⚠️ Không thể kết nối API, đang đăng xuất cục bộ...")
            except Exception as e:
                print(f"Logout API error: {e}")
                st.warning("⚠️ Lỗi kết nối, đang đăng xuất...")

            # Clear session and redirect
            st.session_state.clear()
            st.switch_page("pages/login.py")

        # ===== ACTIVE STYLE =====
        st.markdown(f"""
        <style>
        div[data-testid="stButton"][key="{active}"] button {{
            background: rgba(0, 0, 0, 0.1) !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
        }}
        </style>
        """, unsafe_allow_html=True)