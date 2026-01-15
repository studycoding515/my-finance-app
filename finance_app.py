import streamlit as st
import pandas as pd
import os
import plotly.express as px
from datetime import datetime

# --- CẤU HÌNH ---
DATA_FILE = "so_cai_tai_chinh.csv"

def load_data():
    if not os.path.exists(DATA_FILE):
        df = pd.DataFrame(columns=["Ngày", "Tài khoản", "Loại", "Hạng mục", "Số tiền", "Ghi chú"])
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
    return pd.read_csv(DATA_FILE)

st.set_page_config(page_title="Wallet x QBO", layout="wide")
st.title("💰 Finance Dashboard & Ledger")

# --- XỬ LÝ DỮ LIỆU ---
df = load_data()

# --- THANH SIDEBAR: NHẬP LIỆU ---
with st.sidebar:
    st.header("📝 Nhập giao dịch")
    date = st.date_input("Ngày", datetime.now())
    amount = st.number_input("Số tiền (VND)", min_value=0.0, step=1000.0, format="%.2f")
    t_type = st.selectbox("Loại", ["Chi phí", "Thu nhập"])
    category = st.selectbox("Hạng mục", ["Ăn uống", "Lương", "Xăng xe", "Mua sắm", "Giải trí", "Khác"])
    account = st.selectbox("Tài khoản", ["Tiền mặt", "Vietcombank", "Momo"])
    note = st.text_input("Ghi chú")
    
    if st.button("Lưu giao dịch", use_container_width=True):
        new_row = pd.DataFrame([[date, account, t_type, category, amount, note]], 
                               columns=df.columns)
        new_row.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
        st.success("Đã ghi sổ!")
        st.rerun()

    st.markdown("---")
    st.header("🗑️ Quản lý dữ liệu")
    if not df.empty:
        index_to_delete = st.number_input("Nhập STT dòng muốn xóa:", min_value=0, max_value=len(df)-1, step=1)
        if st.button("Xóa dòng này", type="primary"):
            df = df.drop(df.index[index_to_delete])
            df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            st.warning(f"Đã xóa dòng số {index_to_delete}")
            st.rerun()

# --- HIỂN THỊ BÁO CÁO ---
if not df.empty:
    # Tính toán KPIs
    total_income = df[df['Loại'] == 'Thu nhập']['Số tiền'].sum()
    total_expense = df[df['Loại'] == 'Chi phí']['Số tiền'].sum()
    
    c1, c2, c3 = st.columns(3)
    # Định dạng hiển thị số thập phân ở phần Metric
    c1.metric("Tổng Thu", f"{total_income:,.2f} đ")
    c2.metric("Tổng Chi", f"{total_expense:,.2f} đ")
    c3.metric("Số dư", f"{(total_income - total_expense):,.2f} đ")

    st.markdown("---")
    
    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        st.subheader("📊 Tỷ trọng chi tiêu")
        df_exp = df[df['Loại'] == 'Chi phí']
        if not df_exp.empty:
            fig = px.pie(df_exp, values='Số tiền', names='Hạng mục', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("📜 Nhật ký giao dịch (Sổ cái)")
        # ĐỊNH DẠNG SỐ THẬP PHÂN TRONG BẢNG:
        # .style.format("{:,.2f}"): Thêm dấu phẩy hàng ngàn và 2 chữ số thập phân
        st.dataframe(df.style.format({"Số tiền": "{:,.2f}"}), use_container_width=True, height=400)
else:
    st.info("Chưa có dữ liệu.")