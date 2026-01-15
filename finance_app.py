import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection  # Thư viện kết nối Google Sheets

# --- 1. CẤU HÌNH BẢO MẬT ---
PASSWORD = "qltaichinhcanhan"

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Hệ thống bảo mật")
        pwd = st.text_input("Vui lòng nhập mật khẩu để truy cập:", type="password")
        if st.button("Đăng nhập"):
            if pwd == PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu sai rồi!")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. KẾT NỐI GOOGLE SHEETS ---
# Khởi tạo kết nối
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Đọc dữ liệu từ Sheet có tên là 'Transactions'
    # ttl=0 để đảm bảo mỗi lần load đều lấy dữ liệu mới nhất, không lấy từ bộ nhớ đệm
    return conn.read(worksheet="Transactions", ttl=0)

st.set_page_config(page_title="Wallet x QBO", layout="wide")
st.title("💰 Finance Dashboard & Ledger (Cloud)")

# --- 3. XỬ LÝ DỮ LIỆU ---
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
    
    if st.button("Lưu lên Google Sheets", use_container_width=True):
        # Tạo DataFrame dòng mới
        new_row = pd.DataFrame([{
            "Ngày": date.strftime("%Y-%m-%d"),
            "Tài khoản": account,
            "Loại": t_type,
            "Hạng mục": category,
            "Số tiền": amount,
            "Ghi chú": note
        }])
        
        # Kết hợp dữ liệu cũ và mới
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # Ghi đè toàn bộ dữ liệu mới lên Google Sheets
        conn.update(worksheet="Transactions", data=updated_df)
        
        st.success("✅ Đã ghi sổ lên Google Sheets!")
        st.rerun()

    st.markdown("---")
    st.header("🗑️ Quản lý dữ liệu")
    if not df.empty:
        index_to_delete = st.number_input("Nhập STT dòng muốn xóa:", min_value=0, max_value=len(df)-1, step=1)
        if st.button("Xóa dòng này", type="primary"):
            # Xóa dòng theo index
            updated_df = df.drop(df.index[index_to_delete])
            # Cập nhật lại Google Sheets
            conn.update(worksheet="Transactions", data=updated_df)
            st.warning(f"Đã xóa dòng số {index_to_delete}")
            st.rerun()

# --- 4. HIỂN THỊ BÁO CÁO ---
if not df.empty:
    # Chuyển đổi cột Số tiền sang kiểu số (phòng trường hợp Google Sheets trả về string)
    df["Số tiền"] = pd.to_numeric(df["Số tiền"], errors='coerce')
    
    total_income = df[df['Loại'] == 'Thu nhập']['Số tiền'].sum()
    total_expense = df[df['Loại'] == 'Chi phí']['Số tiền'].sum()
    
    c1, c2, c3 = st.columns(3)
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
        st.subheader("📜 Nhật ký (Google Sheets)")
        st.dataframe(df.style.format({"Số tiền": "{:,.2f}"}), use_container_width=True, height=400)
else:
    st.info("Sổ cái trên Google Sheets hiện tại chưa có dữ liệu.")
