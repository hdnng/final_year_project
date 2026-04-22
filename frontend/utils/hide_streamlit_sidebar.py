"""Utility to hide Streamlit's default sidebar navigation."""

import streamlit as st

_HIDE_CSS = """
<style>
[data-testid="stSidebarNav"] {display: none;}
</style>
"""


def hide_sidebar() -> None:
    """Inject CSS to hide the default Streamlit sidebar navigation."""
    st.markdown(_HIDE_CSS, unsafe_allow_html=True)