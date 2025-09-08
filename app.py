# app.py — robust version
import streamlit as st
import pandas as pd
import io
import re
from sklearn.ensemble import RandomForestRegressor
import numpy as np

st.set_page_config(page_title="Dự báo sinh khối rừng (robust)", layout="centered")
st.title("🌳 Ứng dụng dự báo sinh khối rừng — debug & tolerant")

st.markdown("""
**Hướng dẫn ngắn:** Upload file Excel có 2 sheet: `data` (có `AGB_t_ha` hoặc `V (m3/ha)`) và `new_data` (các ô cần dự báo).  
Nếu tên cột khác nhau, app sẽ cố gắng dò và thông báo.
""")

# Helpers
def normalize(name):
    # strip, lower, remove diacritics-ish characters, keep letters+digits+_
    if not isinstance(name, str):
        return ""
    s = name.strip()
    s = s.lower()
    s = s.replace(" ", "_")
    s = re.sub(r"[^\w]", "", s)  # remove punctuation (keeps letters, digits, underscore)
    return s

def find_col_by_keywords(cols_norm, keywords_list):
    # find first column that contains any keyword
    for key in keywords_list:
        for col_norm, col_orig in cols_norm.items():
            if key in col_norm:
                return col_orig
    return None

# expected keys (normalized)
expected_features = {
    "mean_d": ["meand", "dbq", "dbqcm", "dmean", "d"],
    "h_mean": ["hmean", "hhb", "h", "height"],
    "density_ha": ["densityha", "n_cay_ha", "ncayha", "ncay", "density", "n"],
    "V": ["v", "v_m3_ha", "volume", "v(m3ha)", "v(m3/ha)"],
    "AGB_t_ha": ["agbtha", "agb", "agb_t_ha"]
}

uploaded_file = st.file_uploader("Tải lên file Excel (forest_data.xlsx)", type=["xlsx"])
rho = st.number_input("Khối lượng riêng gỗ ρ (t/m³) — để tính AGB từ V nếu cần", value=0.60, step=0.01, format="%.2f")
bef = st.number_input("BEF (Biomass Expansion Factor)", value=1.30, step=0.01, format="%.2f")
plot_area_ha = st.number_input("Diện tích ô (ha)", value=0.05, step=0.01, format="%.4f")

if uploaded_file is None:
    st.info("Bạn chưa upload file. Nếu muốn test nhanh, upload forest_data.xlsx với 2 sheet: 'data' và 'new_data'.")
    st.stop()

# read sheets defensively
try:
    df_train = pd.read_excel(uploaded_file, sheet_name="data")
    uploaded_file.seek(0)
    df_new = pd.read_excel(uploaded_file, sheet_name="new_data")
except Exception as e:
    st.error("Không đọc được 2 sheet 'data' và 'new_data'. Kiểm tra tên sheet và upload lại.")
    st.stop()

# show read columns (debug)
st.subheader("Tên cột (đã đọc từ Excel)")
st.write("Sheet `data`:", list(df_train.columns))
st.write("Sheet `new_data`:", list(df_new.columns))

# build normalized mapping original_name -> normalized
cols_train = { normalize(col): col for col in df_train.columns }
cols_new   = { normalize(col): col for col in df_new.columns }

# try to map features
mapped = {}
for key, keywords in expected_features.items():
    # first look in training, then in new
    col = find_col_by_keywords(cols_train, keywords)
    if col is None:
        col = find_col_by_keywords(cols_new, keywords)
    if col is None:
        mapped[key] = None
    else:
        mapped[key] = col

st.subheader("Kết quả dò tên cột (mapping)")
st.write(mapped)

# If AGB missing in training but V present -> compute AGB_t_ha from V
if mapped["AGB_t_ha"] is None and mapped["V"] is not None:
    st.warning("Sheet 'data' thiếu AGB_t_ha nhưng có V. App sẽ tính AGB_t_ha = V * rho * BEF.")
    # compute and add AGB_t_ha to df_train
    vcol = mapped["V"]
    # ensure numeric (replace comma decimals)
    df_train[vcol] = df_train[vcol].astype(str).str.replace(",", ".")
    df_train[vcol] = pd.to_numeric(df_train[vcol], errors="coerce")
    df_train["AGB_t_ha"] = df_train[vcol] * float(rho) * float(bef)
    mapped["AGB_t_ha"] = "AGB_t_ha"
    st.write("Đã tính AGB_t_ha cho sheet data (xem 5 dòng đầu):")
    st.write(df_train.head())

# final check: required features for training X and for new X
required_train_cols = []
required_new_cols = []
# we need mean_d, h_mean, density_ha to build X; AGB_t_ha for y
for feat in ["mean_d", "h_mean", "density_ha"]:
    if mapped.get(feat) is None:
        st.error(f"Thiếu cột cần thiết: {feat}. Vui lòng sửa header trong Excel (ví dụ 'mean_D (cm)', 'H_mean (m)', 'density_ha (c/ha)').")
        st.stop()
    required_train_cols.append(mapped[feat])
    required_new_cols.append(mapped[feat])

if mapped.get("AGB_t_ha") is None:
    st.error("Sheet 'data' phải có cột 'AGB_t_ha' (hoặc có 'V' để app tự tính). Hiện chưa tìm thấy.")
    st.stop()

# prepare numeric conversion (replace comma decimals, coerce)
for col in set(required_train_cols + [mapped["AGB_t_ha"]]):
    df_train[col] = df_train[col].astype(str).str.replace(",", ".")
    df_train[col] = pd.to_numeric(df_train[col], errors="coerce")

for col in required_new_cols:
    df_new[col] = df_new[col].astype(str).str.replace(",", ".")
    df_new[col] = pd.to_numeric(df_new[col], errors="coerce")

# check for NaNs
if df_train[required_train_cols + [mapped["AGB_t_ha"]]].isnull().any().any():
    st.warning("Có giá trị không phải số (NaN) trong dữ liệu huấn luyện. Kiểm tra và loại/hàm thay thế nếu cần.")
    st.write(df_train[required_train_cols + [mapped["AGB_t_ha"]]].isnull().sum())

if df_new[required_new_cols].isnull().any().any():
    st.warning("Có giá trị NaN trong sheet new_data (các cột đầu vào). Kiểm tra định dạng số trong Excel.")
    st.write(df_new[required_new_cols].isnull().sum())

# Build X,y
X = df_train[required_train_cols]
y = df_train[mapped["AGB_t_ha"]]

# Train model
model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X, y)

# # Predict
# X_new = df_new[required_new_cols]
# df_new["AGB_du_bao"] = model.predict(X_new)

# st.subheader("Kết quả dự báo (new_data)")
# st.dataframe(df_new)

# # allow download
# to_write = io.BytesIO()
# df_new.to_excel(to_write, index=False, sheet_name="predictions")
# to_write.seek(0)
# st.download_button("📥 Tải kết quả Excel", to_write, file_name="forest_prediction.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Predict (chỉ khi có dữ liệu)
X_new = df_new[required_new_cols].copy()
X_new = X_new.apply(pd.to_numeric, errors="coerce")

if X_new.shape[0] == 0:
    st.warning("⚠️ Sheet 'new_data' không có dữ liệu để dự báo. Hãy nhập ít nhất 1 dòng.")
else:
    if X_new.isnull().any().any():
        st.warning("Có giá trị NaN trong new_data, sẽ thay bằng 0.")
        X_new = X_new.fillna(0)

    df_new["AGB_du_bao"] = model.predict(X_new)

    st.subheader("Kết quả dự báo (new_data)")
    st.dataframe(df_new)

    # allow download
    to_write = io.BytesIO()
    df_new.to_excel(to_write, index=False, sheet_name="predictions")
    to_write.seek(0)
    st.download_button(
        "📥 Tải kết quả Excel",
        to_write,
        file_name="forest_prediction.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
