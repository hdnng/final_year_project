"""Frame detail page — individual detections with inline editing."""

import streamlit as st

from components.app_sidebar import render_sidebar
from config import API_BASE_URL
from utils.auth_guard import require_auth
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.http import init_session_state, get_auth_headers
from utils.load_css import load_css

# ── Config ──────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Chi tiết khung hình")

init_session_state()

if "edit_result_id" not in st.session_state:
    st.session_state.edit_result_id = None

require_auth()

# ── Sidebar & Styles ───────────────────────────────────────
hide_sidebar()
render_sidebar(active="home")
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
st.markdown(load_css("styles/frame_detail.css"), unsafe_allow_html=True)

# ── Frame ID ────────────────────────────────────────────────
frame_id = st.session_state.get("frame_id")
if not frame_id:
    st.warning("Không có frame để xem.")
    st.stop()


# ── Load Data ───────────────────────────────────────────────
def load_data() -> dict:
    res = st.session_state.client.get(
        f"{API_BASE_URL}/frames/detail/{frame_id}",
        headers=get_auth_headers(),
    )
    if res.status_code != 200:
        st.error("Không lấy được dữ liệu frame.")
        st.stop()
    return res.json()


data = load_data()

total = data.get("total_students", 0)
sleeping = data.get("sleeping_count", 0)
focus = data.get("focus_count", 0)
conf = round(data.get("avg_confidence", 0) * 100, 1)

# Percentages for distribution
focus_pct = round(focus / total * 100) if total else 0
sleeping_pct = round(sleeping / total * 100) if total else 0
other_pct = max(0, 100 - focus_pct - sleeping_pct)

# ── Header ──────────────────────────────────────────────────
if st.button(f"← Chi tiết khung hình #{frame_id}"):
    st.switch_page("pages/session_analysis.py")

# ── Main Layout ─────────────────────────────────────────────
left_col, right_col = st.columns([1.6, 1], gap="medium")

# ── LEFT: Image Card ────────────────────────────────────────
with left_col:
    st.markdown(f"""
    <div class="img-card">
        <div class="img-card-header">
            <span class="cam-label">
                <span class="icon">📹</span>
                Camera Phòng Học 01 - Khung hình #{frame_id}
            </span>
            <span class="live-badge"><span class="dot"></span> TRỰC TIẾP</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.image(data["image_path"], use_container_width=True)

# ── RIGHT: Stats + Distribution ─────────────────────────────
with right_col:
    # Section title
    st.markdown('<div class="right-section-title">Thống số khung hình</div>', unsafe_allow_html=True)

    # KPI: Tổng học sinh
    st.markdown(f"""
    <div class="kpi-mini">
        <div class="kpi-left">
            <div class="kpi-label">TỔNG HỌC SINH</div>
            <div class="kpi-val">{total}</div>
        </div>
        <span class="kpi-change up">↗ 01%</span>
    </div>
    """, unsafe_allow_html=True)

    # KPI: Buồn ngủ
    sleep_change_cls = "down" if sleeping > 0 else "up"
    st.markdown(f"""
    <div class="kpi-mini alert">
        <div class="kpi-left">
            <div class="kpi-label">HỌC SINH BUỒN NGỦ</div>
            <div class="kpi-val red">{sleeping:02d}</div>
        </div>
        <span class="kpi-change {sleep_change_cls}">↑ +{sleeping_pct}%</span>
    </div>
    """, unsafe_allow_html=True)

    # KPI: Confidence
    st.markdown(f"""
    <div class="kpi-mini">
        <div class="kpi-left">
            <div class="kpi-label">ĐỘ TIN CẬY AI</div>
            <div class="kpi-val blue">{conf}%</div>
        </div>
        <span class="kpi-change neutral">~ 0.0%</span>
    </div>
    """, unsafe_allow_html=True)

    # Distribution section
    st.markdown('<div class="dist-section">', unsafe_allow_html=True)
    st.markdown('<div class="dist-title">Phân bổ trạng thái</div>', unsafe_allow_html=True)

    # Tập trung
    st.markdown(f"""
    <div class="dist-row">
        <span class="dist-label">Tập trung</span>
        <span class="dist-pct">{focus_pct}%</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(focus_pct / 100 if focus_pct > 0 else 0)

    # Buồn ngủ
    st.markdown(f"""
    <div class="dist-row">
        <span class="dist-label">Buồn ngủ</span>
        <span class="dist-pct">{sleeping_pct}%</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(sleeping_pct / 100 if sleeping_pct > 0 else 0)

    # Xao nhãng
    st.markdown(f"""
    <div class="dist-row">
        <span class="dist-label">Xao nhãng</span>
        <span class="dist-pct">{other_pct}%</span>
    </div>
    """, unsafe_allow_html=True)
    st.progress(other_pct / 100 if other_pct > 0 else 0)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Detections Table ────────────────────────────────────────
st.markdown("""
<div class="table-card">
    <div class="table-card-title">Danh sách phát hiện</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.get("frame_cache_id") != frame_id:
    st.session_state.edit_result_id = None
    st.session_state.frame_cache_id = frame_id

detections = data.get("detections", [])

if not detections:
    st.info("Không có kết quả phát hiện.")
else:
    # Table header
    h1, h2, h3, h4, h5 = st.columns([1.2, 1.5, 1.2, 1.2, 0.8])
    h1.markdown("<div class='tbl-head'>ID HỌC SINH</div>", unsafe_allow_html=True)
    h2.markdown("<div class='tbl-head'>HỌ VÀ TÊN</div>", unsafe_allow_html=True)
    h3.markdown("<div class='tbl-head'>TRẠNG THÁI</div>", unsafe_allow_html=True)
    h4.markdown("<div class='tbl-head'>ĐỘ TIN CẬY</div>", unsafe_allow_html=True)
    h5.markdown("<div class='tbl-head'>THAO TÁC</div>", unsafe_allow_html=True)

    # Table rows
    for row in detections:
        result_id = row.get("result_id")
        if not result_id:
            continue

        status = row.get("user_label") or row.get("status", "Unknown")
        is_edit = st.session_state.edit_result_id == result_id
        confidence = row.get("confidence", 0) * 100

        c1, c2, c3, c4, c5 = st.columns([1.2, 1.5, 1.2, 1.2, 0.8])

        if not is_edit:
            # View mode
            c1.markdown(
                f"<div class='tbl-cell'>{row.get('student_id', '-')}</div>",
                unsafe_allow_html=True,
            )

            # Generate a display name
            idx = row.get("student_id", "HS0").replace("HS", "")
            c2.markdown(
                f"<div class='tbl-cell'>Học sinh {idx}</div>",
                unsafe_allow_html=True,
            )

            # Status badge
            if "Sleeping" in status:
                tag_cls = "sleeping"
                tag_text = "Buồn ngủ"
            elif "Normal" in status:
                tag_cls = "normal"
                tag_text = "Tập trung"
            else:
                tag_cls = "distracted"
                tag_text = "Xao nhãng"

            c3.markdown(
                f"<div class='tbl-cell'><span class='status-tag {tag_cls}'>{tag_text}</span></div>",
                unsafe_allow_html=True,
            )

            c4.markdown(
                f"<div class='tbl-cell'>{confidence:.1f}%</div>",
                unsafe_allow_html=True,
            )

            with c5:
                if st.button("✏️", key=f"edit_{result_id}"):
                    st.session_state.edit_result_id = result_id
                    st.rerun()
        else:
            # Edit mode
            c1.markdown(
                f"<div class='tbl-cell'>{row.get('student_id', '-')}</div>",
                unsafe_allow_html=True,
            )

            idx = row.get("student_id", "HS0").replace("HS", "")
            c2.markdown(
                f"<div class='tbl-cell'>Học sinh {idx}</div>",
                unsafe_allow_html=True,
            )

            with c3:
                new_status = st.selectbox(
                    "Trạng thái",
                    ["Normal", "Sleeping"],
                    index=0 if status == "Normal" else 1,
                    key=f"sel_{result_id}",
                    label_visibility="collapsed",
                )

            c4.markdown(
                f"<div class='tbl-cell'>{confidence:.1f}%</div>",
                unsafe_allow_html=True,
            )

            with c5:
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾", key=f"save_{result_id}"):
                        res = st.session_state.client.patch(
                            f"{API_BASE_URL}/ai-result/{result_id}",
                            json={"status": new_status},
                            headers=get_auth_headers(),
                        )
                        if res.status_code == 200:
                            st.success("Đã cập nhật")
                            st.session_state.edit_result_id = None
                            st.rerun()
                with bc2:
                    if st.button("❌", key=f"cancel_{result_id}"):
                        st.session_state.edit_result_id = None
                        st.rerun()