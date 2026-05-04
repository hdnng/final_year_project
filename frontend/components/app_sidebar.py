"""App sidebar component — navigation menu and logout."""

import streamlit as st
from services.auth_api import logout

def render_sidebar(active: str = "home") -> None:
    """
    Render the application sidebar with navigation and logout.
    Uses index-based CSS targeting to ensure the active item is highlighted correctly.
    """
    with st.sidebar:
        # Top spacer to offset from header
        st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
        
        # Navigation buttons
        # Note: The order here must match the indices in the CSS below
        btn_home = st.button("🎥 Giám sát", key="nav_home", use_container_width=True)
        btn_stats = st.button("📊 Thống kê", key="nav_statistics", use_container_width=True)
        btn_hist = st.button("🕘 Lịch sử", key="nav_history", use_container_width=True)
        btn_settings = st.button("⚙️ Cài đặt", key="nav_setting", use_container_width=True)

        # Logic for page switching
        if btn_home: st.switch_page("pages/home.py")
        if btn_stats: st.switch_page("pages/statistics.py")
        if btn_hist: st.switch_page("pages/history.py")
        if btn_settings: st.switch_page("pages/setting.py")

        # Map active key to the button index (1-based)
        # We use nth-of-type(n+2) because there's a spacer div at the top
        menu_map = {"home": 1, "statistics": 2, "history": 3, "setting": 4}
        active_idx = menu_map.get(active, 1)

        # Injecting dynamic CSS for the active state
        st.markdown(f"""
        <style>
        /* Target the Nth button container in the sidebar for the active state */
        /* Each st.button is wrapped in a div[data-testid="stButton"] */
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:nth-child({active_idx + 1}) button {{
            background-color: #1677ff !important;
            color: white !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 12px rgba(22, 119, 255, 0.2) !important;
        }}
        
        /* Ensure icons and text are white in active state */
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:nth-child({active_idx + 1}) button p {{
            color: white !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        # Logout button
        # This will be pushed to the bottom by the CSS in header.css
        if st.button("↪️ Đăng xuất", key="logout_btn", use_container_width=True):
            try:
                if "client" in st.session_state:
                    logout(st.session_state.client)
            except Exception:
                pass
            st.session_state.clear()
            st.switch_page("pages/login.py")