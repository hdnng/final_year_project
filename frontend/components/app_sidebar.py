import streamlit as st

def render_sidebar(active=None):

    with st.sidebar:

        st.markdown("## 📊 EduVision AI")
        st.caption("Phân tích hành vi học")

        st.divider()

        if st.button("📊 Giám sát", use_container_width=True):
            st.switch_page("pages/home.py")

        if st.button("📈 Thống kê", use_container_width=True):
            pass

        if st.button("📅 Lịch sử", use_container_width=True):
            pass

        if st.button("⚙️ Cài đặt", use_container_width=True):
            st.switch_page("pages/setting.py")

        st.divider()

        if st.button("🚪 Đăng xuất", use_container_width=True):
            try:
                st.session_state.client.post("http://127.0.0.1:8000/logout")
            except:
                pass  # tránh crash nếu API lỗi

            st.session_state.clear()
            st.switch_page("pages/login.py")