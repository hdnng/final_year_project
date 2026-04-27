"""Session analysis page — frame grid with focus/sleeping counts."""

import math

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from components.app_sidebar import render_sidebar
from services.frame_api import get_frame_analysis
from services.history_api import get_all_sessions
from utils.auth_guard import require_auth
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.http import init_session_state
from utils.load_css import load_css

# ── Config ──────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Kết quả phân tích")

init_session_state()

if "analysis_page" not in st.session_state:
    st.session_state.analysis_page = 1

require_auth()

# ── Sidebar & Styles ────────────────────────────────────────
hide_sidebar()
render_sidebar(active="home")
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
st.markdown(load_css("styles/session_analysis.css"), unsafe_allow_html=True)

# ── Session ID ──────────────────────────────────────────────
session_id = st.session_state.get("session_id")
if not session_id:
    st.warning("Không có phiên học đang chạy.")
    st.stop()

# ── Get Class Name ──────────────────────────────────────────────
class_name = "UNKNOWN"
all_sessions = get_all_sessions(st.session_state.client)
for s in all_sessions:
    if s["session_id"] == session_id:
        class_name = s["class_id"]
        break

# ── Get Analysis Data ──────────────────────────────────────────────
frames = get_frame_analysis(st.session_state.client, session_id)

# ── Header ──────────────────────────────────────────────────
if st.button("← Danh sách khung hình"):
    st.switch_page("pages/home.py")

st.markdown(
    '<div class="page-title">Kết quả Phân tích Phiên học</div>',
    unsafe_allow_html=True,
)

st.markdown(f"""
<div class="header-meta">
    <span class="tag tag-blue">PHÒNG {session_id}</span>
    <span class="tag-text">Phiên học: {class_name}</span>
</div>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">Dòng thời gian trích xuất (Mỗi 30 giây)</div>',
    unsafe_allow_html=True,
)

if not frames:
    st.info("Chưa có dữ liệu phân tích.")
    st.stop()

# ── Pagination ──────────────────────────────────────────────
PER_PAGE = 6
total = len(frames)
pages = max(1, math.ceil(total / PER_PAGE))
page = min(st.session_state.analysis_page, pages)
st.session_state.analysis_page = page

start = (page - 1) * PER_PAGE
show_frames = frames[start:start + PER_PAGE]

# ── Grid (3 columns, 2 rows) ───────────────────────────────
# Split into rows of 3
row1 = show_frames[:3]
row2 = show_frames[3:6]


def render_card(item, col):
    """Render a single frame card inside a Streamlit column."""
    with col:
        is_alert = item["sleeping_count"] > 0
        card_cls = "frame-card alert" if is_alert else "frame-card"
        status_cls = "warning" if is_alert else "active"
        status_text = "CẢNH BÁO" if is_alert else "ĐANG HOẠT ĐỘNG"

        # Format time for overlay
        raw_time = str(item.get("extracted_at", ""))
        # Try to extract HH:MM:SS portion
        time_short = raw_time.split("T")[-1][:8] if "T" in raw_time else raw_time[:8]

        # Card open
        st.markdown(f'<div class="{card_cls}">', unsafe_allow_html=True)

        # Image with overlays
        st.markdown(f"""
        <div class="img-container">
            <div class="time-overlay">{time_short}</div>
            <div class="status-overlay {status_cls}">{status_text}</div>
        </div>
        """, unsafe_allow_html=True)

        st.image(item["image_path"], use_container_width=True)

        # Card info
        st.markdown(f"""
        <div class="card-info-title">Phân tích khung hình #{item["frame_id"]}</div>
        <div class="card-info-time">Trích xuất lúc {raw_time}</div>
        """, unsafe_allow_html=True)

        # Stats row
        sleep_cls = "stat-box alert-box" if is_alert else "stat-box"
        st.markdown(f"""
        <div class="stats-row">
            <div class="stat-box">
                <div class="stat-label">TẬP TRUNG</div>
                <div class="stat-value blue">{item["focus_count"]:02d}</div>
            </div>
            <div class="{sleep_cls}">
                <div class="stat-label">BUỒN NGỦ</div>
                <div class="stat-value red">{item["sleeping_count"]:02d}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Detail button
        if st.button("Xem chi tiết", use_container_width=True, key=f"detail_{item['frame_id']}"):
            st.session_state["frame_id"] = item["frame_id"]
            st.switch_page("pages/frame_detail.py")

        # Card close
        st.markdown("</div>", unsafe_allow_html=True)


# Render row 1
if row1:
    cols1 = st.columns(3)
    for i, item in enumerate(row1):
        render_card(item, cols1[i])

# Render row 2
if row2:
    cols2 = st.columns(3)
    for i, item in enumerate(row2):
        render_card(item, cols2[i])

# ── Pagination ──────────────────────────────────────────────
showing = len(show_frames)

# Build page buttons HTML
page_btns_html = ""
prev_cls = "disabled" if page <= 1 else ""
page_btns_html += f'<span class="pg-btn {prev_cls}">‹</span>'

max_show = 5
half = max_show // 2
p_start = max(1, page - half)
p_end = min(pages, p_start + max_show - 1)
if p_end - p_start + 1 < max_show:
    p_start = max(1, p_end - max_show + 1)

for p in range(p_start, p_end + 1):
    active = "active" if p == page else ""
    page_btns_html += f'<span class="pg-btn {active}">{p}</span>'

next_cls = "disabled" if page >= pages else ""
page_btns_html += f'<span class="pg-btn {next_cls}">›</span>'

st.markdown(f"""
<div class="pagination-bar">
    <span class="page-info">Hiển thị {showing} trong số {total} khung hình</span>
    <div class="page-btns">{page_btns_html}</div>
</div>
""", unsafe_allow_html=True)

# Functional pagination buttons
_, pg_prev, pg_num, pg_next, _ = st.columns([4, 1, 1, 1, 4])

with pg_prev:
    if st.button("‹", disabled=(page <= 1), key="pg_prev"):
        st.session_state.analysis_page -= 1
        st.rerun()
with pg_num:
    st.markdown(
        f"<div class='page-num-label'>{page}/{pages}</div>",
        unsafe_allow_html=True,
    )
with pg_next:
    if st.button("›", disabled=(page >= pages), key="pg_next"):
        st.session_state.analysis_page += 1
        st.rerun()

# ── Auto Refresh ────────────────────────────────────────────
if st.session_state.get("running", False):
    st_autorefresh(interval=10000, key="analysis_refresh")