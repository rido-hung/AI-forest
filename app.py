import streamlit as st
import pandas as pd

st.set_page_config(page_title="🌳 Forest Structure Demo", layout="wide")
st.title("🌲 Phân tích cấu trúc rừng từ Excel")

file = st.file_uploader("📥 Upload file Excel", type=["xlsx"])
if file:
    # Đọc sheet "Xử lý số liệu"
    df = pd.read_excel(file, sheet_name="Xử lý số liệu")

    # Giữ lại cột quan trọng
    cols_needed = ["Tên Việt Nam", "D1,3 (cm)", "C1,3 (cm)"]
    df = df[cols_needed].dropna()

    # Đổi tên cột cho dễ dùng
    df = df.rename(columns={
        "Tên Việt Nam": "Species",
        "D1,3 (cm)": "DBH",
        "C1,3 (cm)": "Height"
    })

    st.subheader("📋 Dữ liệu gốc")
    st.dataframe(df.head())

    # ===== Thống kê mô tả =====
    st.subheader("📊 Thống kê mô tả")
    n_trees = len(df)
    n_species = df["Species"].nunique()
    mean_dbh, min_dbh, max_dbh = df["DBH"].mean(), df["DBH"].min(), df["DBH"].max()
    mean_h = df["Height"].mean()

    st.markdown(f"""
    - **Tổng số cây**: {n_trees}  
    - **Số loài**: {n_species}  
    - **DBH TB**: {mean_dbh:.2f} cm (min: {min_dbh:.2f}, max: {max_dbh:.2f})  
    - **Chiều cao TB**: {mean_h:.2f} cm  
    """)

    # ===== Phân bố DBH =====
    st.subheader("📈 Phân bố đường kính (DBH)")
    dbh_bins = range(0, int(df["DBH"].max()) + 5, 5)
    dbh_dist = pd.cut(df["DBH"], bins=dbh_bins).value_counts().sort_index()
    st.dataframe(dbh_dist)
    st.bar_chart(dbh_dist)

    # ===== Phân bố loài =====
    st.subheader("🌱 Phân bố loài")
    species_count = df["Species"].value_counts()
    st.dataframe(species_count)
    st.bar_chart(species_count)
