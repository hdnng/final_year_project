"""History page — session list with search, pagination, and deletion."""

import streamlit as st

from components.app_sidebar import render_sidebar
from config import API_BASE_URL
from services.history_api import delete_session
from utils.auth_guard import require_auth
from utils.hide_streamlit_sidebar import hide_sidebar
from utils.http import init_session_state, get_auth_headers
from utils.load_css import load_css

# ── Config ──────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="Lịch sử")

st.markdown(load_css("styles/sidebar.css"), unsafe_allow_html=True)
st.markdown(load_css("styles/history.css"), unsafe_allow_html=True)

init_session_state()
require_auth()

PAGE_SIZE = 5


# ── API ─────────────────────────────────────────────────────
def get_history(session, search: str = "", page: int = 1) -> dict | None:
    """Fetch session list and summary counts."""
    try:
        headers = get_auth_headers()
        skip = (page - 1) * PAGE_SIZE
        params = {"skip": skip, "limit": PAGE_SIZE}
        if search.strip():
            params["search"] = search.strip()

        sessions_res = session.get(
            f"{API_BASE_URL}/history/sessions",
            headers=headers,
            params=params,
        )
        summary_res = session.get(
            f"{API_BASE_URL}/history/summary",
            headers=headers,
        )

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
        if st.button("❌ Hủy", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("🗑 Xóa", type="primary", use_container_width=True):
            handle_delete(session_id)


# ── Sidebar ─────────────────────────────────────────────────
hide_sidebar()
render_sidebar(active="history")

# ── Session state for pagination ────────────────────────────
if "hist_page" not in st.session_state:
    st.session_state.hist_page = 1
if "hist_search" not in st.session_state:
    st.session_state.hist_search = ""

# ── Header ──────────────────────────────────────────────────
st.markdown('<div class="page-title">Lịch sử phân tích</div>', unsafe_allow_html=True)

# ── Load Data ───────────────────────────────────────────────
data = get_history(
    st.session_state.client,
    search=st.session_state.hist_search,
    page=st.session_state.hist_page,
)
if not data:
    st.stop()

# ── Summary Cards ───────────────────────────────────────────
col_s1, col_s2, col_s3 = st.columns([1, 1, 2])

with col_s1:
    st.markdown(f"""
    <div class="summary-card">
        <div class="label">TỔNG PHIÊN PHÂN TÍCH</div>
        <div class="value">{data['total_sessions']:,}</div>
        <div class="trend up">📈 +12%</div>
    </div>
    """, unsafe_allow_html=True)

with col_s2:
    st.markdown(f"""
    <div class="summary-card">
        <div class="label">PHIÊN TRONG THÁNG</div>
        <div class="value">{data['month_sessions']:,}</div>
        <div class="trend neutral">📊 Tháng hiện tại</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("")  # spacer

# ── Search ──────────────────────────────────────────────────
search_val = st.text_input(
    "Tìm kiếm",
    value=st.session_state.hist_search,
    placeholder="🔍  Tìm theo mã phiên hoặc tên lớp học...",
    label_visibility="collapsed",
)

# If search changed, reset to page 1
if search_val != st.session_state.hist_search:
    st.session_state.hist_search = search_val
    st.session_state.hist_page = 1
    st.rerun()

# ── Data ────────────────────────────────────────────────────
sessions = data["sessions"]
total_sessions_count = data["total_sessions"]
total_pages = max((total_sessions_count - 1) // PAGE_SIZE + 1, 1)
current_page = st.session_state.hist_page

# ── Table ───────────────────────────────────────────────────
st.markdown('<div class="table-card">', unsafe_allow_html=True)

# Table header
st.markdown("""
<div class="table-header-row">
    <span>MÃ PHIÊN</span>
    <span>LỚP HỌC</span>
    <span>NGÀY THỰC HIỆN</span>
    <span>SỐ LẦN PHÂN TÍCH</span>
    <span style="text-align:right">THAO TÁC</span>
</div>
""", unsafe_allow_html=True)

# Table rows
if not sessions:
    st.markdown("""
    <div style="padding:40px 24px; text-align:center; color:#9ca3af;">
        <div style="font-size:40px; margin-bottom:8px;">📭</div>
        <div style="font-size:14px; font-weight:500;">Không tìm thấy phiên nào</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for sess in sessions:
        sid = sess["session_id"]
        class_id = sess["class_id"]
        date_str = sess["date"]
        frame_count = sess["frame_count"]

        # Table row with popover action menu
        row_cols = st.columns([1.2, 2, 1.5, 1.2, 0.5])
        with row_cols[0]:
            st.markdown(f'<span class="cell-session-id">#SESS-{sid}</span>', unsafe_allow_html=True)
        with row_cols[1]:
            st.markdown(f'<span class="cell-class">{class_id}</span>', unsafe_allow_html=True)
        with row_cols[2]:
            st.markdown(f'<span class="cell-date">{date_str}</span>', unsafe_allow_html=True)
        with row_cols[3]:
            st.markdown(f'<span class="cell-count">{frame_count}</span>', unsafe_allow_html=True)
        with row_cols[4]:
            with st.popover("⋮", use_container_width=False):
                if st.button("👁 Xem chi tiết", key=f"view_{sid}", use_container_width=True):
                    st.session_state.selected_session = sid
                    st.switch_page("pages/session_detail.py")
                if st.button("🗑 Xóa phiên", key=f"del_{sid}", use_container_width=True):
                    confirm_delete(sid)

# ── Pagination ──────────────────────────────────────────────
start_idx = (current_page - 1) * PAGE_SIZE + 1
end_idx = min(current_page * PAGE_SIZE, total_sessions_count)

# Build pagination HTML
page_buttons = []
page_buttons.append(f'<span class="page-btn {"disabled" if current_page <= 1 else ""}" id="pg-prev">‹</span>')

# Show max 5 page buttons
if total_pages <= 7:
    page_range = range(1, total_pages + 1)
else:
    if current_page <= 3:
        page_range = list(range(1, 5)) + [-1, total_pages]
    elif current_page >= total_pages - 2:
        page_range = [1, -1] + list(range(total_pages - 3, total_pages + 1))
    else:
        page_range = [1, -1, current_page - 1, current_page, current_page + 1, -1, total_pages]

for p in page_range:
    if p == -1:
        page_buttons.append('<span class="page-ellipsis">…</span>')
    else:
        active = "active" if p == current_page else ""
        page_buttons.append(f'<span class="page-btn {active}">{p}</span>')

page_buttons.append(f'<span class="page-btn {"disabled" if current_page >= total_pages else ""}" id="pg-next">›</span>')

st.markdown(f"""
<div class="pagination-bar">
    <span class="pagination-info">Hiển thị {start_idx} - {end_idx} của {total_sessions_count} kết quả</span>
    <div class="pagination-controls">
        {''.join(page_buttons)}
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Streamlit pagination controls (hidden visually but functional)
pg_cols = st.columns([1, 6, 1])
with pg_cols[0]:
    if current_page > 1:
        if st.button("⬅️ Trước", key="pg_prev_btn", use_container_width=True):
            st.session_state.hist_page -= 1
            st.rerun()
with pg_cols[2]:
    if current_page < total_pages:
        if st.button("Sau ➡️", key="pg_next_btn", use_container_width=True):
            st.session_state.hist_page += 1
            st.rerun()