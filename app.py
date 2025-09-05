import streamlit as st
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

st.title("🌳 Ứng dụng dự báo sinh khối rừng")

uploaded_file = st.file_uploader("Tải lên file Excel", type=["xlsx"])
if uploaded_file:
    # Đọc sheet "data" (dữ liệu huấn luyện)
    df = pd.read_excel(uploaded_file, sheet_name="data")
    X = df[["mean_D (cm)", "H_mean (m)", "density_ha (c/ha)"]]
    y = df["AGB_t_ha"]

    # Huấn luyện mô hình
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    # Đọc sheet "new_data" (dữ liệu dự báo)
    new_df = pd.read_excel(uploaded_file, sheet_name="new_data")
    X_new = new_df[["mean_D (cm)", "H_mean (m)", "density_ha (c/ha)"]]
    new_df["AGB_du_bao"] = model.predict(X_new)

    # Hiển thị kết quả
    st.subheader("📊 Kết quả dự báo")
    st.dataframe(new_df)
