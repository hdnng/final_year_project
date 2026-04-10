import streamlit as st
import pandas as pd
import requests

from utils.load_css import load_css
from utils.auth_guard import require_auth

st.markdown(load_css("styles/history.css"), unsafe_allow_html=True)

# ===== INIT SESSION STATE (CRITICAL!) =====
if "is_login" not in st.session_state:
    st.session_state["is_login"] = False
if "access_token_value" not in st.session_state:
    st.session_state["access_token_value"] = None
if "refresh_token_value" not in st.session_state:
    st.session_state["refresh_token_value"] = None
if "client" not in st.session_state:
    st.session_state.client = requests.Session()

# ===== AUTH CHECK =====
require_auth()

API_URL = "http://127.0.0.1:8000"

# ================= API =================
def get_auth_headers():
    """Get authorization headers if token exists"""
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def get_history(session):
    """Lấy lịch sử phiên phân tích"""
    try:
        headers = get_auth_headers()
        sessions_res = session.get(f"{API_URL}/history/sessions", headers=headers)
        summary_res = session.get(f"{API_URL}/history/summary", headers=headers)

        if sessions_res.status_code == 401 or summary_res.status_code == 401:
            st.error("❌ Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại")
            return None

        if sessions_res.status_code == 200 and summary_res.status_code == 200:
            return {
                "sessions": sessions_res.json(),
                "total_sessions": summary_res.json().get("total_sessions", 0),
                "month_sessions": summary_res.json().get("month_sessions", 0)
            }
        else:
            st.error(f"❌ Lỗi: Sessions={sessions_res.status_code}, Summary={summary_res.status_code}")
            return None

    except Exception as e:
        st.error(f"❌ Lỗi kết nối: {str(e)}")
        return None

# ================= CONFIG =================
st.set_page_config(layout="wide", page_title="Lịch sử")

# ================= SIDEBAR =================
from utils.hide_streamlit_sidebar import hide_sidebar
hide_sidebar()

st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

from components.app_sidebar import render_sidebar
render_sidebar(active="history")

# ================= LOAD DATA =================
client = st.session_state.client
data = get_history(client)

if not data:
    st.stop()

df = pd.DataFrame(data["sessions"])

# ================= HEADER =================
st.markdown('<div class="title">Lịch sử phân tích</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

col1.markdown(f"""
<div class="card">
    <div class="sub">TỔNG PHIÊN PHÂN TÍCH</div>
    <div class="metric">{data['total_sessions']}</div>
</div>
""", unsafe_allow_html=True)

col2.markdown(f"""
<div class="card">
    <div class="sub">PHIÊN TRONG THÁNG</div>
    <div class="metric">{data['month_sessions']}</div>
</div>
""", unsafe_allow_html=True)

# ================= SEARCH =================
search = st.text_input("🔍 Tìm theo mã phiên hoặc lớp học")

if search:
    df = df[
        df["class_id"].astype(str).str.contains(search, case=False, na=False) |
        df["session_id"].astype(str).str.contains(search)
    ]

# ================= FORMAT =================
df["Mã phiên"] = df["session_id"].apply(lambda x: f"#SESS-{x}")
df["Lớp học"] = df["class_id"]
df["Ngày"] = df["date"]
df["Số lần"] = df["frame_count"]

# ================= PAGINATION =================
page_size = 5
total_rows = len(df)
total_pages = max((total_rows - 1) // page_size + 1, 1)

if "page" not in st.session_state:
    st.session_state.page = 1

start = (st.session_state.page - 1) * page_size
end = start + page_size

df_page = df.iloc[start:end]

# ================= TABLE =================
st.markdown("### Danh sách phiên")

# ===== TABLE CONTAINER =====
st.markdown('<div class="table-container">', unsafe_allow_html=True)

# ===== HEADER =====
header = st.columns([2, 3, 2, 2, 1])
header[0].markdown('<div class="cell header">Mã phiên</div>', unsafe_allow_html=True)
header[1].markdown('<div class="cell header">Lớp học</div>', unsafe_allow_html=True)
header[2].markdown('<div class="cell header">Ngày</div>', unsafe_allow_html=True)
header[3].markdown('<div class="cell header">Số lần</div>', unsafe_allow_html=True)
header[4].markdown('<div class="cell header">Thao tác</div>', unsafe_allow_html=True)

# ===== ROWS =====
for i, row in df_page.iterrows():
    cols = st.columns([2, 3, 2, 2, 1])

    cols[0].markdown(f'<div class="cell">{row["Mã phiên"]}</div>', unsafe_allow_html=True)
    cols[1].markdown(f'<div class="cell">{row["Lớp học"]}</div>', unsafe_allow_html=True)
    cols[2].markdown(f'<div class="cell">{row["Ngày"]}</div>', unsafe_allow_html=True)
    cols[3].markdown(f'<div class="cell">{row["Số lần"]}</div>', unsafe_allow_html=True)

    with cols[4]:
        st.markdown('<div class="cell">', unsafe_allow_html=True)
        if st.button("Xem", key=f"view_{i}"):
            st.session_state.selected_session = int(row["session_id"])
            st.switch_page("pages/session_detail.py")
        st.markdown('</div>', unsafe_allow_html=True)

# ===== END TABLE =====
st.markdown('</div>', unsafe_allow_html=True)

# ================= FOOTER =================
st.caption(f"Hiển thị {start+1}-{min(end, total_rows)} / {total_rows}")

col_prev, col_mid, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("⬅️") and st.session_state.page > 1:
        st.session_state.page -= 1
        st.rerun()

with col_mid:
    st.markdown(
        f"<div style='text-align:center'>Trang {st.session_state.page}/{total_pages}</div>",
        unsafe_allow_html=True
    )

with col_next:
    if st.button("➡️") and st.session_state.page < total_pages:
        st.session_state.page += 1
        st.rerun()