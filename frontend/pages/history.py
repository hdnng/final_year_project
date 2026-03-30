import streamlit as st
import pandas as pd
import requests


API_URL = "http://localhost:8000"

# ================= API =================
def get_history():
    try:
        sessions = requests.get(f"{API_URL}/history/sessions").json()
        summary = requests.get(f"{API_URL}/history/summary").json()

        return {
            "sessions": sessions,
            "total_sessions": summary["total_sessions"],
            "month_sessions": summary["month_sessions"]
        }
    except:
        return None


# ================= CONFIG =================
st.set_page_config(layout="wide", page_title="Lịch sử")

# ================= SIDEBAR =================
from utils.hide_streamlit_sidebar import hide_sidebar
hide_sidebar()

from utils.load_css import load_css
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)

from components.app_sidebar import render_sidebar
render_sidebar(active="history")

# ================= LOAD DATA =================
data = get_history()

if not data:
    st.error("Không có dữ liệu")
    st.stop()

df = pd.DataFrame(data["sessions"])

# ================= HEADER =================
st.markdown('<div class="title"> Lịch sử phân tích</div>', unsafe_allow_html=True)

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
        df["class_id"].str.contains(search, case=False, na=False) |
        df["session_id"].astype(str).str.contains(search)
    ]

# ================= FORMAT =================
df["Mã phiên"] = df["session_id"].apply(lambda x: f"#SESS-{x}")
df["Lớp học"] = df["class_id"]
df["Ngày thực hiện"] = df["date"]
df["Số lần phân tích"] = df["frame_count"]

df_display = df[["Mã phiên", "Lớp học", "Ngày thực hiện", "Số lần phân tích"]]

# ================= PAGINATION =================
page_size = 5
total_rows = len(df_display)
total_pages = max((total_rows - 1) // page_size + 1, 1)

if "page" not in st.session_state:
    st.session_state.page = 1

start = (st.session_state.page - 1) * page_size
end = start + page_size

df_page = df.iloc[start:end]

# ================= TABLE CUSTOM =================
st.markdown("### Danh sách phiên")

# Header
col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 1])
col1.markdown("**Mã phiên**")
col2.markdown("**Lớp học**")
col3.markdown("**Ngày**")
col4.markdown("**Số lần phân tích**")
col5.markdown("")

# Rows
for i, row in df_page.iterrows():
    c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])

    c1.write(row["Mã phiên"])
    c2.write(row["Lớp học"])
    c3.write(row["Ngày thực hiện"])
    c4.write(row["Số lần phân tích"])

    if c5.button("Xem", key=f"view_{i}"):
        session_id = int(row["Mã phiên"].replace("#SESS-", ""))
        #st.query_params["session_id"] = session_id
        st.session_state.selected_session = session_id
        st.switch_page("pages/session_detail.py")

# Caption
st.caption(f"Hiển thị {start+1}-{min(end, total_rows)} / {total_rows} kết quả")

# ================= PAGINATION UI =================
col_prev, col_mid, col_next = st.columns([1, 2, 1])

with col_prev:
    if st.button("⬅️ Trang trước") and st.session_state.page > 1:
        st.session_state.page -= 1

with col_mid:
    st.markdown(
        f"<div style='text-align:center'>Trang {st.session_state.page} / {total_pages}</div>",
        unsafe_allow_html=True
    )

with col_next:
    if st.button("Trang sau ➡️") and st.session_state.page < total_pages:
        st.session_state.page += 1