import streamlit as st
import pandas as pd

st.set_page_config(page_title="🌳 Forest Data Demo", layout="wide")

st.title("🌲 Demo ứng dụng phân tích dữ liệu rừng")

uploaded_file = st.file_uploader("📥 Upload file Excel dữ liệu rừng", type=["xlsx"])

if uploaded_file:
    # Đọc dữ liệu
    df = pd.read_excel(uploaded_file)
    st.success("✅ Đã đọc dữ liệu thành công!")

    # Hiển thị bảng dữ liệu
    st.subheader("📋 Dữ liệu gốc")
    st.dataframe(df.head())

    # Thống kê cơ bản
    st.subheader("📊 Thống kê cơ bản")
    st.write(df.describe())

    # Vẽ biểu đồ tự động nếu có cột DBH (đường kính)
    if "DBH" in df.columns:
        st.subheader("📈 Phân bố đường kính (DBH)")
        st.bar_chart(df["DBH"].value_counts().sort_index())

    # Vẽ biểu đồ tự động nếu có cột Height (chiều cao)
    if "Height" in df.columns:
        st.subheader("🌲 Phân bố chiều cao")
        st.line_chart(df["Height"])
