"""App sidebar component — navigation menu and logout."""

import streamlit as st

from services.auth_api import logout


def render_sidebar(active: str = "home") -> None:
    """
    Render the application sidebar with navigation and logout.

    Args:
        active: Key of the currently active menu item for highlighting.
    """
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <h2>🎓 EduVision AI</h2>
            <p>Student Behavior Analysis</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation items
        _menu_item("Monitoring", "📹", "pages/home.py", "home")
        _menu_item("Statistics", "📊", "pages/statistics.py", "statistics")
        _menu_item("History", "🕘", "pages/history.py", "history")
        _menu_item("Settings", "⚙️", "pages/setting.py", "setting")

        st.markdown("---")

        # Logout
        if st.button("🚪 Logout", use_container_width=True):
            try:
                if "client" in st.session_state:
                    res = logout(st.session_state.client)
                    if res and res.status_code == 200:
                        st.info("Logged out successfully")
                    else:
                        st.warning("Could not reach API, logging out locally...")
            except Exception:
                st.warning("Connection error, logging out...")

            st.session_state.clear()
            st.switch_page("pages/login.py")

        # Highlight active menu item
        st.markdown(f"""
        <style>
        div[data-testid="stButton"][key="{active}"] button {{
            background: rgba(0, 0, 0, 0.1) !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
        }}
        </style>
        """, unsafe_allow_html=True)


def _menu_item(label: str, icon: str, page: str, key: str) -> None:
    """Render a single sidebar navigation button."""
    if st.button(f"{icon} {label}", key=key, use_container_width=True):
        st.switch_page(page)