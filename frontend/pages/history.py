import streamlit as st
import pandas as pd

# ================= CONFIG =================
st.set_page_config(layout="wide", page_title="Lịch sử")

# ================= SIDEBAR =================
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎓 EduVision AI")
        st.caption("Phân tích hành vi người học")

        st.markdown("---")

        if st.button("📹 Giám sát"):
            pass
        if st.button("📊 Thống kê"):
            pass
        if st.button("🕘 Lịch sử"):
            pass
        if st.button("⚙️ Cài đặt"):
            pass

render_sidebar()

# ================= HEADER =================
st.markdown("## Lịch sử phân tích")

# ================= STATS =================
col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    st.markdown("""
    <div style="padding:15px; border-radius:10px; background:#f5f7fb;">
        <div style="font-size:13px; color:gray;">TỔNG PHIÊN PHÂN TÍCH</div>
        <div style="font-size:26px; font-weight:bold;">1,248</div>
        <div style="color:green; font-size:12px;">+12%</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="padding:15px; border-radius:10px; background:#f5f7fb;">
        <div style="font-size:13px; color:gray;">PHIÊN TRONG THÁNG</div>
        <div style="font-size:26px; font-weight:bold;">156</div>
        <div style="color:green; font-size:12px;">+4%</div>
    </div>
    """, unsafe_allow_html=True)

# ================= SEARCH =================
search = st.text_input("🔍 Tìm theo mã phiên hoặc lớp học...")

# ================= MOCK DATA =================
data = [
    ["#SESS-8921", "Phòng 302 - Vật lý", "24/10/2023", 32],
    ["#SESS-8915", "Phòng 101 - Toán", "24/10/2023", 28],
    ["#SESS-8910", "Phòng 205 - Hóa học", "23/10/2023", 30],
    ["#SESS-8904", "Phòng 102 - Sinh học", "23/10/2023", 25],
    ["#SESS-8898", "Phòng 301 - Tiếng Anh", "22/10/2023", 35],
]

df = pd.DataFrame(data, columns=[
    "Mã phiên", "Lớp học", "Ngày thực hiện", "Số lần phân tích"
])

# ================= FILTER =================
if search:
    df = df[df.apply(lambda row: search.lower() in str(row).lower(), axis=1)]

# ================= TABLE =================
st.markdown("### ")

for index, row in df.iterrows():
    col1, col2, col3, col4, col5 = st.columns([2, 3, 2, 2, 2])

    with col1:
        st.markdown(f"**{row['Mã phiên']}**")

    with col2:
        st.write(row["Lớp học"])

    with col3:
        st.write(row["Ngày thực hiện"])

    with col4:
        st.markdown(f"""
        <div style="
            background:#eef2ff;
            padding:5px 10px;
            border-radius:20px;
            text-align:center;
            width:50px;
        ">
            {row['Số lần phân tích']}
        </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(
            f"<a href='#' style='color:#1f77ff;'>Xem chi tiết</a>",
            unsafe_allow_html=True
        )

    st.markdown("---")

# ================= PAGINATION =================
st.markdown("""
<div style="text-align:center; margin-top:20px;">
    <button style="padding:6px 12px;">1</button>
    <button style="padding:6px 12px;">2</button>
    <button style="padding:6px 12px;">3</button>
    ...
    <button style="padding:6px 12px;">10</button>
</div>
""", unsafe_allow_html=True)