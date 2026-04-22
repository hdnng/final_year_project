import streamlit as st
import requests
import pandas as pd
import plotly.express as px

from components.app_sidebar import render_sidebar
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.auth_guard import require_auth
from utils.load_css import load_css

# ================= CONFIG =================
st.set_page_config(layout="wide", page_title="Chi tiết khung hình")

# ================= INIT =================
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

if "edit_result_id" not in st.session_state:
    st.session_state.edit_result_id = None

require_auth()
hide_sidebar()
render_sidebar(active="home")

st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000/camera"


# ================= AUTH =================
def get_auth_headers():
    token = st.session_state.get("access_token_value") or st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


# ================= FRAME ID =================
frame_id = st.session_state.get("frame_id")

if not frame_id:
    st.warning("Không có frame để xem.")
    st.stop()


# ================= LOAD DATA =================
def load_data():
    res = st.session_state.client.get(
        f"{API_URL}/frame-detail/{frame_id}",
        headers=get_auth_headers()
    )

    if res.status_code != 200:
        st.error("Không lấy được dữ liệu frame.")
        st.stop()

    return res.json()


data = load_data()


# ================= HEADER =================
if st.button("← Quay lại danh sách frame"):
    st.switch_page("pages/session_analysis.py")

st.markdown(
    f'<div class="title">Chi tiết khung hình #{frame_id}</div>',
    unsafe_allow_html=True
)


# ================= TOP =================
left, right = st.columns([1.4, 1])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.image(data["image_path"], use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    r1, r2 = st.columns(2)

    with r1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">TỔNG HỌC SINH</div>
            <div class="metric-value">{data.get("total_students",0)}</div>
        </div>
        """, unsafe_allow_html=True)

    with r2:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">BUỒN NGỦ</div>
            <div class="metric-value red">{data.get("sleeping_count",0)}</div>
        </div>
        """, unsafe_allow_html=True)

    r3, r4 = st.columns(2)

    with r3:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">TẬP TRUNG</div>
            <div class="metric-value green">{data.get("focus_count",0)}</div>
        </div>
        """, unsafe_allow_html=True)

    with r4:
        conf = round(data.get("avg_confidence", 0) * 100, 1)
        st.markdown(f"""
        <div class="metric">
            <div class="metric-title">ĐỘ TIN CẬY</div>
            <div class="metric-value">{conf}%</div>
        </div>
        """, unsafe_allow_html=True)

    chart_data = pd.DataFrame({
        "Trạng thái": ["Tập trung", "Buồn ngủ"],
        "Số lượng": [data.get("focus_count",0), data.get("sleeping_count",0)]
    })

    fig = px.pie(chart_data, names="Trạng thái", values="Số lượng", hole=0.45)
    fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=320)

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ================= TABLE =================
st.markdown("### Danh sách phát hiện")

if st.session_state.get("frame_cache_id") != frame_id:
    st.session_state.edit_result_id = None
    st.session_state.frame_cache_id = frame_id


for row in data.get("detections", []):

    result_id = row.get("result_id")
    if not result_id:
        continue  # tránh crash

    # ================= FINAL STATUS =================
    status = row.get("user_label")
    if status is None or status == "":
        status = row.get("status", "Unknown")

    is_edit = st.session_state.edit_result_id == result_id

    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    # ================= VIEW =================
    if not is_edit:

        with col1:
            st.write(row.get("student_id", "-"))

        with col2:
            color = "green" if status == "Normal" else "red"
            st.markdown(
                f"<span style='color:{color};font-weight:600'>{status}</span>",
                unsafe_allow_html=True
            )

        with col3:
            st.write(f"{row.get('confidence',0)*100:.1f}%")

        with col4:
            if st.button("✏️", key=f"edit_{result_id}"):
                st.session_state.edit_result_id = result_id
                st.rerun()


    # ================= EDIT =================
    else:

        with col1:
            st.write(row.get("student_id", "-"))

        with col2:
            new_status = st.selectbox(
                "Trạng thái",
                ["Normal", "Sleeping"],
                index=0 if status == "Normal" else 1,
                key=f"edit_{result_id}"
            )

        with col3:
            st.write(f"{row.get('confidence',0)*100:.1f}%")

        with col4:
            c1, c2 = st.columns(2)

            # SAVE
            with c1:
                if st.button("💾", key=f"save_{result_id}"):

                    res = st.session_state.client.patch(
                        f"{API_URL.replace('/camera','')}/ai-result/{result_id}",
                        json={"status": new_status},
                        headers=get_auth_headers()
                    )

                    if res.status_code == 200:
                        st.success("Đã cập nhật")

                        # reload data để tránh stale UI
                        data = load_data()

                        st.session_state.edit_result_id = None
                        st.rerun()

            # CANCEL
            with c2:
                if st.button("❌", key=f"cancel_{result_id}"):
                    st.session_state.edit_result_id = None
                    st.rerun()