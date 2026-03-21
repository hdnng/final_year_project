import streamlit as st
from components.sidebar import render_sidebar
from utils.load_css import load_css

def render_layout(active=None):

    st.markdown(load_css("styles/global.css"), unsafe_allow_html=True)

    # hide default sidebar
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
    </style>
    """, unsafe_allow_html=True)

    # 👉 CHIA 2 CỘT CHUẨN
    sidebar_col, content_col = st.columns([1, 4], gap="large")

    with sidebar_col:
        render_sidebar(active)

    with content_col:
        st.markdown('<div class="content">', unsafe_allow_html=True)

        return content_col  # để dùng tiếp nếu cần


def end_layout():
    st.markdown('</div>', unsafe_allow_html=True)