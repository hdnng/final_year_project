import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="Thống kê")

# ================= SIDEBAR =================
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎓 EduVision AI")
        st.caption("Phân tích hành vi người học")

        st.markdown("---")

        st.button("📹 Giám sát")
        st.button("📊 Thống kê")
        st.button("🕘 Lịch sử")
        st.button("⚙️ Cài đặt")

render_sidebar()

# ================= HEADER =================
st.markdown("## Thống kê phân tích")

# ================= MOCK DATA =================
dates = [datetime.now() - timedelta(days=i) for i in range(10)]
values = np.random.randint(10, 50, size=10)

df = pd.DataFrame({
    "Ngày": dates[::-1],
    "Số phiên": values[::-1]
})

# ================= LAYOUT =================
left, right = st.columns([3, 1])

# ================= BAR CHART =================
with left:
    st.markdown("### Số phiên phân tích theo ngày")

    st.bar_chart(df.set_index("Ngày"))

# ================= CALENDAR =================
with right:
    st.markdown("### 📅 Chọn ngày")

    selected_date = st.date_input(
        "",
        value=datetime.now()
    )

    st.markdown(f"""
    <div style="margin-top:20px; padding:10px; border-radius:10px; background:#f5f7fb;">
        <b>Ngày đã chọn:</b><br>
        {selected_date.strftime("%d/%m/%Y")}
    </div>
    """, unsafe_allow_html=True)

# ================= EXTRA STATS =================
st.markdown("### Tổng quan")

col1, col2, col3 = st.columns(3)

col1.metric("Tổng phiên", "1,248", "+12%")
col2.metric("Hôm nay", "32", "+5%")
col3.metric("Trung bình/ngày", "28", "+2%")