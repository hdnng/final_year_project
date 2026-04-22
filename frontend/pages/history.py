"""History page — session list with search, pagination, and deletion."""

import streamlit as st
import pandas as pd

from components.app_sidebar import render_sidebar
from config import API_BASE_URL
from services.history_api import delete_session
from utils.auth_guard import require_auth
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.http import init_session_state, get_auth_headers
from utils.load_css import load_css

# ── Config ──────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Lịch sử")

st.markdown(load_css("styles/history.css"), unsafe_allow_html=True)

init_session_state()
require_auth()


# ── API ─────────────────────────────────────────────────────
def get_history(session) -> dict | None:
    """Fetch session list and summary counts."""
    try:
        headers = get_auth_headers()
        sessions_res = session.get(f"{API_BASE_URL}/history/sessions", headers=headers)
        summary_res = session.get(f"{API_BASE_URL}/history/summary", headers=headers)

        if sessions_res.status_code == 401 or summary_res.status_code == 401:
            st.error("❌ Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại")
            return None

        if sessions_res.status_code == 200 and summary_res.status_code == 200:
            summary = summary_res.json()
            return {
                "sessions": sessions_res.json(),
                "total_sessions": summary.get("total_sessions", 0),
                "month_sessions": summary.get("month_sessions", 0),
            }

        st.error(f"❌ Lỗi API: {sessions_res.status_code}")
        return None

    except Exception as exc:
        st.error(f"❌ Lỗi kết nối: {exc}")
        return None


def handle_delete(session_id: int) -> None:
    """Execute session deletion and show result."""
    res = delete_session(session_id)
    if not res:
        st.error("❌ Không kết nối được server")
        return
    if res.status_code == 200:
        st.success("✅ Xóa phiên thành công")
        st.rerun()
    elif res.status_code == 400:
        st.error("❌ Không thể xóa phiên đang chạy")
    elif res.status_code == 404:
        st.error("❌ Không tìm thấy session")
    else:
        st.error(f"❌ Lỗi server: {res.text}")


@st.dialog("⚠️ Xác nhận xóa session")
def confirm_delete(session_id: int):
    st.warning("Bạn có chắc muốn xóa session này không?")
    st.caption("Hành động này sẽ xóa toàn bộ frames và dữ liệu liên quan.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("❌ Hủy"):
            st.rerun()
    with c2:
        if st.button("🗑 Xóa", type="primary"):
            handle_delete(session_id)


# ── Sidebar ─────────────────────────────────────────────────
hide_sidebar()
st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
render_sidebar(active="history")

# ── Load Data ───────────────────────────────────────────────
data = get_history(st.session_state.client)
if not data:
    st.stop()

df = pd.DataFrame(data["sessions"])

# ── Header ──────────────────────────────────────────────────
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

# ── Search ──────────────────────────────────────────────────
search = st.text_input("🔍 Tìm theo mã phiên hoặc lớp học")
if search:
    df = df[
        df["class_id"].astype(str).str.contains(search, case=False, na=False)
        | df["session_id"].astype(str).str.contains(search)
    ]

# ── Format ──────────────────────────────────────────────────
df["Mã phiên"] = df["session_id"].apply(lambda x: f"#SESS-{x}")
df["Lớp học"] = df["class_id"]
df["Ngày"] = df["date"]
df["Số lần"] = df["frame_count"]

# ── Pagination ──────────────────────────────────────────────
PAGE_SIZE = 5
total_rows = len(df)
total_pages = max((total_rows - 1) // PAGE_SIZE + 1, 1)

if "page" not in st.session_state:
    st.session_state.page = 1

start = (st.session_state.page - 1) * PAGE_SIZE
end = start + PAGE_SIZE
df_page = df.iloc[start:end]

# ── Table ───────────────────────────────────────────────────
st.markdown("### Danh sách phiên")
st.markdown('<div class="table-container">', unsafe_allow_html=True)

header = st.columns([2, 3, 2, 2, 1])
for col, title in zip(header, ["Mã phiên", "Lớp học", "Ngày", "Số lần", "Thao tác"]):
    col.markdown(f'<div class="cell header">{title}</div>', unsafe_allow_html=True)

for i, row in df_page.iterrows():
    cols = st.columns([2, 3, 2, 2, 1])
    cols[0].markdown(f'<div class="cell">{row["Mã phiên"]}</div>', unsafe_allow_html=True)
    cols[1].markdown(f'<div class="cell">{row["Lớp học"]}</div>', unsafe_allow_html=True)
    cols[2].markdown(f'<div class="cell">{row["Ngày"]}</div>', unsafe_allow_html=True)
    cols[3].markdown(f'<div class="cell">{row["Số lần"]}</div>', unsafe_allow_html=True)

    with cols[4]:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("👁", key=f"view_{i}"):
                st.session_state.selected_session = int(row["session_id"])
                st.switch_page("pages/session_detail.py")
        with c2:
            if st.button("🗑", key=f"del_{i}"):
                confirm_delete(int(row["session_id"]))

st.markdown("</div>", unsafe_allow_html=True)

# ── Pagination Footer ──────────────────────────────────────
st.caption(f"Hiển thị {start + 1}-{min(end, total_rows)} / {total_rows}")

col_prev, col_mid, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("⬅️") and st.session_state.page > 1:
        st.session_state.page -= 1
        st.rerun()
with col_mid:
    st.markdown(
        f"<div style='text-align:center'>Trang {st.session_state.page}/{total_pages}</div>",
        unsafe_allow_html=True,
    )
with col_next:
    if st.button("➡️") and st.session_state.page < total_pages:
        st.session_state.page += 1
        st.rerun()