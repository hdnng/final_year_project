"""Session detail page — KPI cards, donut chart, and frame table."""

import math

import streamlit as st
import plotly.graph_objects as go

from components.app_sidebar import render_sidebar
from services.history_api import get_session_detail
from utils.auth_guard import require_auth
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.http import init_session_state
from utils.load_css import load_css

# ── Config ──────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Chi tiết phiên")

init_session_state()
require_auth()

if "detail_page" not in st.session_state:
    st.session_state.detail_page = 1

# ── Sidebar & Styles ────────────────────────────────────────
hide_sidebar()
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
render_sidebar(active="history")
st.markdown(load_css("styles/session_detail.css"), unsafe_allow_html=True)

# ── Session ID ──────────────────────────────────────────────
session_id = st.session_state.get("selected_session")
if not session_id:
    st.error("Thiếu session_id")
    st.stop()


# ── Load Data ───────────────────────────────────────────────
data = get_session_detail(st.session_state.client, session_id)
if not data:
    st.error("Không lấy được dữ liệu")
    st.stop()

frames = data.get("frames", [])
total_students = data.get("total_students", 0)
sleeping = data.get("sleeping", 0)
alerts = data.get("alerts", 0)
duration = data.get("duration", 0)
focus_rate = data.get("focus_rate", 0)
class_id = data.get("class_id", "N/A")

# Compute percentages for chart
focus_pct = round(focus_rate * 100)
sleeping_pct = 100 - focus_pct

# ── Back Button ─────────────────────────────────────────────
if st.button("← Chi tiết lịch sử phiên"):
    st.switch_page("pages/history.py")

# ── Page Header ─────────────────────────────────────────────
status_class = "status-done" if duration > 0 else "status-running"
status_text = "HOÀN THÀNH" if duration > 0 else "ĐANG CHẠY"

st.markdown(f"""
<div class="page-header">
    <span class="title">Chi tiết phiên #SESS-{session_id}</span>
    <span class="status-badge {status_class}">{status_text}</span>
</div>
""", unsafe_allow_html=True)

# ── Top Row: Chart + 2 KPI Cards ────────────────────────────
top1, top2, top3 = st.columns([1, 1, 1], gap="medium")

# -- Donut Chart --
with top1:
    fig = go.Figure(data=[go.Pie(
        labels=["Tập trung", "Buồn ngủ"],
        values=[max(focus_pct, 1), max(sleeping_pct, 1)],
        hole=0.72,
        marker=dict(colors=["#1677ff", "#ef4444"]),
        textinfo="none",
        hoverinfo="label+percent",
        sort=False,
    )])
    fig.update_layout(
        height=200,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        annotations=[dict(
            text=f"Tập trung<br><b style='font-size:28px'>{focus_pct}%</b>",
            showarrow=False,
            font=dict(size=13, color="#475569"),
        )],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.markdown("""
    <div class="chart-card">
        <div class="card-title">🎯 Phân bổ hành vi</div>
    """, unsafe_allow_html=True)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(f"""
        <div class="legend-list">
            <div class="legend-item">
                <span><span class="legend-dot blue"></span>Tập trung</span>
                <span class="legend-val">{focus_pct}%</span>
            </div>
            <div class="legend-item">
                <span><span class="legend-dot red"></span>Buồn ngủ</span>
                <span class="legend-val">{sleeping_pct}%</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# -- Right column: Tổng số sinh viên + Tổng số cảnh báo --
with top2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Tổng số sinh viên</div>
        <div>
            <span class="kpi-value">{total_students}</span>
            <span class="kpi-unit">người</span>
        </div>
        <div class="kpi-sub green">↗ Đầy đủ 100%</div>
    </div>
    """, unsafe_allow_html=True)

    warn_sub = "⚠ Cần lưu ý" if alerts > 0 else "✓ Tốt"
    warn_cls = "warn" if alerts > 0 else "green"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Tổng số cảnh báo</div>
        <div>
            <span class="kpi-value orange">{alerts:02d}</span>
            <span class="kpi-unit">lần</span>
        </div>
        <div class="kpi-sub {warn_cls}">{warn_sub}</div>
    </div>
    """, unsafe_allow_html=True)

# -- Right column: Độ chính xác + Thời gian học --
with top3:
    avg_acc = focus_rate * 100
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Độ chính xác trung bình</div>
        <div>
            <span class="kpi-value blue">{avg_acc:.1f}</span>
            <span class="kpi-unit">%</span>
        </div>
        <div class="kpi-sub">Tính dựa trên dữ liệu AI Recognition</div>
    </div>
    """, unsafe_allow_html=True)

    time_sub = "Bắt đầu đúng giờ" if duration > 0 else "Đang diễn ra"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Thời gian học thực tế</div>
        <div>
            <span class="kpi-value">{duration}</span>
            <span class="kpi-unit">phút</span>
        </div>
        <div class="kpi-sub green">{time_sub}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Frame Table ─────────────────────────────────────────────
PAGE_SIZE = 5
total_rows = len(frames)
total_pages = max(1, math.ceil(total_rows / PAGE_SIZE))

# Clamp page
st.session_state.detail_page = min(st.session_state.detail_page, total_pages)
page = st.session_state.detail_page

start = (page - 1) * PAGE_SIZE
end = start + PAGE_SIZE
page_frames = frames[start:end]

st.markdown(f"""
<div class="table-section">
    <div class="table-header">
        <span class="table-title">Danh sách khung hình (Interval 30s)</span>
    </div>
</div>
""", unsafe_allow_html=True)

if not frames:
    st.info("Chưa có dữ liệu frame")
else:
    # Table header
    h1, h2, h3, h4, h5, h6 = st.columns([1.2, 1.2, 1, 1.5, 1, 1])
    h1.markdown("<div class='tbl-head'>MỐC THỜI GIAN</div>", unsafe_allow_html=True)
    h2.markdown("<div class='tbl-head'>TRẠNG THÁI</div>", unsafe_allow_html=True)
    h3.markdown("<div class='tbl-head'>SỐ LƯỢNG SINH VIÊN</div>", unsafe_allow_html=True)
    h4.markdown("<div class='tbl-head'>ĐỘ CHÍNH XÁC</div>", unsafe_allow_html=True)
    h5.markdown("<div class='tbl-head'>CA BUỒN NGỦ</div>", unsafe_allow_html=True)
    h6.markdown("<div class='tbl-head'>THAO TÁC</div>", unsafe_allow_html=True)

    # Table rows
    for row in page_frames:
        c1, c2, c3, c4, c5, c6 = st.columns([1.2, 1.2, 1, 1.5, 1, 1])

        # Time
        c1.markdown(
            f"<div class='tbl-cell'>{row['time']}</div>",
            unsafe_allow_html=True,
        )

        # Status badge
        is_alert = row["status"] != "Normal"
        badge_cls = "badge-warning" if is_alert else "badge-normal"
        badge_text = "CẢNH BÁO" if is_alert else "BÌNH THƯỜNG"
        c2.markdown(
            f"<div class='tbl-cell'><span class='badge {badge_cls}'>{badge_text}</span></div>",
            unsafe_allow_html=True,
        )

        # Students
        c3.markdown(
            f"<div class='tbl-cell'>{row['students']} SV</div>",
            unsafe_allow_html=True,
        )

        # Accuracy with progress bar
        acc = row["accuracy"]
        c4.markdown(f"""
        <div class='tbl-cell'>
            <div class="accuracy-bar">
                <div class="bar-track"><div class="bar-fill" style="width:{acc}%"></div></div>
                <span class="bar-value">{acc}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Sleeping count
        sl = row["sleeping"]
        if sl > 0:
            c5.markdown(
                f"<div class='tbl-cell'><span class='sleep-count'>{sl:02d} ca</span></div>",
                unsafe_allow_html=True,
            )
        else:
            c5.markdown(
                "<div class='tbl-cell'><span class='sleep-none'>—</span></div>",
                unsafe_allow_html=True,
            )

        # Action
        with c6:
            if st.button("Xem chi tiết", key=f"view_{row['frame_id']}"):
                st.session_state["frame_id"] = row["frame_id"]
                st.switch_page("pages/frame_detail.py")

    # ── Pagination ──────────────────────────────────────────
    showing = len(page_frames)

    # Build pagination HTML
    page_btns = ""

    # Prev button
    prev_cls = "disabled" if page <= 1 else ""
    page_btns += f'<span class="page-btn {prev_cls}">‹</span>'

    # Page numbers (show max 5)
    max_show = 5
    half = max_show // 2
    p_start = max(1, page - half)
    p_end = min(total_pages, p_start + max_show - 1)
    if p_end - p_start + 1 < max_show:
        p_start = max(1, p_end - max_show + 1)

    for p in range(p_start, p_end + 1):
        active = "active" if p == page else ""
        page_btns += f'<span class="page-btn {active}">{p}</span>'

    # Next button
    next_cls = "disabled" if page >= total_pages else ""
    page_btns += f'<span class="page-btn {next_cls}">›</span>'

    st.markdown(f"""
    <div class="pagination-row">
        <span class="page-info">Hiển thị {showing} trên {total_rows} khung hình</span>
        <div class="page-buttons">{page_btns}</div>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit pagination buttons (functional)
    _, pg_prev, pg_num, pg_next, _ = st.columns([4, 1, 1, 1, 4])

    with pg_prev:
        if st.button("‹", disabled=(page <= 1), key="page_prev"):
            st.session_state.detail_page -= 1
            st.rerun()
    with pg_num:
        st.markdown(
            f"<div class='page-num-label'>{page}/{total_pages}</div>",
            unsafe_allow_html=True,
        )
    with pg_next:
        if st.button("›", disabled=(page >= total_pages), key="page_next"):
            st.session_state.detail_page += 1
            st.rerun()