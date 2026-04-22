import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go

from utils.auth_guard import require_auth
from utils.load_css import load_css
from utils.hide_streamlit_sidebar import hide_sidebar

# ================= CONFIG =================
st.set_page_config(layout="wide", page_title="Chi tiết phiên")

# ================= INIT SESSION =================
if "is_login" not in st.session_state:
    st.session_state["is_login"] = False
if "access_token_value" not in st.session_state:
    st.session_state["access_token_value"] = None
if "refresh_token_value" not in st.session_state:
    st.session_state["refresh_token_value"] = None
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

require_auth()

API_URL = "http://127.0.0.1:8000"

# ================= SIDEBAR =================
hide_sidebar()
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

from components.app_sidebar import render_sidebar
render_sidebar(active="history")

# ================= CSS =================
st.markdown(load_css("styles/session_detail.css"), unsafe_allow_html=True)

# ================= GET SESSION =================
session_id = st.session_state.get("selected_session")

if not session_id:
    st.error("Thiếu session_id")
    st.stop()

# ================= API =================
def get_auth_headers():
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def get_detail():
    try:
        res = st.session_state.client.get(
            f"{API_URL}/history/session/{session_id}",
            headers=get_auth_headers()
        )
        if res.status_code == 200:
            return res.json()
        st.error("Không lấy được dữ liệu")
        return None
    except Exception as e:
        st.error(str(e))
        return None

data = get_detail()
if not data:
    st.stop()

frames = data.get("frames", [])

# ================= HEADER =================
st.markdown(f"""
<div class='title-main'>
Chi tiết phiên #SESS-{session_id}
</div>
""", unsafe_allow_html=True)

# ================= TOP GRID =================
left, right = st.columns([1, 2.3], gap="large")

# ---------- LEFT CHART ----------
with left:
    total_students = data.get("total_students", 0)
    sleeping = data.get("sleeping", 0)
    focus = max(total_students - sleeping, 0)

    fig = go.Figure(data=[go.Pie(
        labels=["Tập trung", "Buồn ngủ"],
        values=[focus, max(sleeping,1)],
        hole=.72,
        marker=dict(colors=["#1677ff", "#ef4444"]),
        textinfo="none"
    )])

    fig.update_layout(
        height=260,
        margin=dict(l=0,r=0,t=0,b=0),
        showlegend=False,
        annotations=[
            dict(
                text=f"Tập trung<br><b>{data.get('focus_rate',0)*100:.0f}%</b>",
                showarrow=False,
                font=dict(size=16)
            )
        ]
    )

    # ✅ container thật (QUAN TRỌNG)
    chart_box = st.container()

    with chart_box:
        st.markdown("### 🎯 Phân bố hành vi")

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": False}
        )

        st.markdown(f"""
        <div style="margin-top:10px;">
            <div>🔵 Tập trung <b style='float:right'>{data.get('focus_rate',0)*100:.0f}%</b></div>
            <div style='margin-top:6px;'>🔴 Buồn ngủ <b style='float:right'>{sleeping}</b></div>
        </div>
        """, unsafe_allow_html=True)
# ---------- RIGHT KPI ----------
with right:
    row1 = st.columns(2, gap="large")
    row2 = st.columns(2, gap="large")

    with row1[0]:
        st.markdown(f"""
        <div class='card'>
            <div class='sub'>Tổng số sinh viên</div>
            <div class='metric'>{data.get("total_students",0)}</div>
        </div>
        """, unsafe_allow_html=True)

    with row1[1]:
        st.markdown(f"""
        <div class='card'>
            <div class='sub'>Độ chính xác trung bình</div>
            <div class='metric metric-blue'>{data.get("focus_rate",0)*100:.1f}%</div>
            <div class='small-note'>Tính từ AI Recognition</div>
        </div>
        """, unsafe_allow_html=True)

    with row2[0]:
        st.markdown(f"""
        <div class='card'>
            <div class='sub'>Tổng số cảnh báo</div>
            <div class='metric metric-orange'>{data.get("alerts",0)}</div>
        </div>
        """, unsafe_allow_html=True)

    with row2[1]:
        st.markdown(f"""
        <div class='card'>
            <div class='sub'>Thời gian học thực tế</div>
            <div class='metric'>{data.get("duration",0)}</div>
            <div class='small-note'>phút</div>
        </div>
        """, unsafe_allow_html=True)

# ================= TABLE =================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='table-box'>", unsafe_allow_html=True)
st.markdown("### Danh sách khung hình")

if not frames:
    st.info("Chưa có dữ liệu frame")
else:
    df = pd.DataFrame(frames)

    page_size = 5
    total_rows = len(df)
    total_pages = max((total_rows - 1)//page_size + 1, 1)

    if "detail_page" not in st.session_state:
        st.session_state.detail_page = 1

    start = (st.session_state.detail_page - 1) * page_size
    end = start + page_size
    df_page = df.iloc[start:end]

    head = st.columns(6)
    titles = ["Mốc thời gian","Trạng thái","Số SV","Độ chính xác","Buồn ngủ","Thao tác"]

    for i, t in enumerate(titles):
        head[i].markdown(f"<div class='head'>{t}</div>", unsafe_allow_html=True)

    for idx, row in df_page.iterrows():
        cols = st.columns(6)

        badge = "badge-alert" if row["status"] != "Bình thường" else "badge-ok"

        cols[0].markdown(f"<div class='cell'>{row['time']}</div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='cell'><span class='{badge}'>{row['status']}</span></div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='cell'>{row['students']} SV</div>", unsafe_allow_html=True)

        cols[3].markdown(f"""
        <div class='cell'>
            <b>{row['accuracy']}%</b>
            <div class='progress'>
                <div class='progress-bar' style='width:{row["accuracy"]}%'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        cols[4].markdown(f"<div class='cell'>{row['sleeping']}</div>", unsafe_allow_html=True)

        with cols[5]:
            if st.button("Xem", key=f"{row['frame_id']}"):
                st.session_state["frame_id"] = row["frame_id"]
                st.switch_page("pages/frame_detail.py")

st.markdown("</div>", unsafe_allow_html=True)

# ================= PAGINATION =================
st.markdown("<br>", unsafe_allow_html=True)
p1,p2,p3 = st.columns([1,2,1])

with p1:
    if st.button("⬅️") and st.session_state.detail_page > 1:
        st.session_state.detail_page -= 1
        st.rerun()

with p2:
    st.markdown(
        f"<div style='text-align:center'>Trang {st.session_state.detail_page}/{total_pages}</div>",
        unsafe_allow_html=True
    )

with p3:
    if st.button("➡️") and st.session_state.detail_page < total_pages:
        st.session_state.detail_page += 1
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)