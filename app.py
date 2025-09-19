import streamlit as st
import pandas as pd

st.set_page_config(page_title="🌳 Forest Structure Demo", layout="wide")
st.title("🌲 Ứng dụng phân tích cấu trúc rừng")

file = st.file_uploader("📥 Upload Excel", type=["xlsx"])
if file:
    df = pd.read_excel(file)
    st.success("✅ Đã đọc dữ liệu")

    st.subheader("📋 Dữ liệu gốc")
    st.dataframe(df.head())

    st.subheader("📊 Thống kê mô tả")
    st.dataframe(df.describe().T)

    if "DBH" in df.columns:
        st.markdown(f"**DBH TB**: {df['DBH'].mean():.2f} cm")
        dbh_dist = pd.cut(df["DBH"], bins=range(0, int(df["DBH"].max())+5, 5)).value_counts().sort_index()
        st.dataframe(dbh_dist); st.bar_chart(dbh_dist)

    if "Height" in df.columns:
        st.markdown(f"**H TB**: {df['Height'].mean():.2f} m")
        h_dist = pd.cut(df["Height"], bins=range(0, int(df["Height"].max())+2, 2)).value_counts().sort_index()
        st.dataframe(h_dist); st.bar_chart(h_dist)

    if "Species" in df.columns:
        species_count = df["Species"].value_counts()
        st.subheader("🌱 Phân bố loài")
        st.dataframe(species_count); st.bar_chart(species_count)
