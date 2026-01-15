import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. HỆ THỐNG BẢO MẬT ---
PASSWORD = "qltaichinhcanhan"

def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Hệ thống bảo mật")
        pwd = st.text_input("Mật khẩu:", type="password")
        if st.button("Đăng nhập"):
            if pwd == PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("Sai mật khẩu!")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. KẾT NỐI SERVICE ACCOUNT ---
conn = st.connection("gsheets", type=GSheetsConnection)
SHEET_NAME = "Transactions"

st.set_page_config(page_title="Finance App", layout="wide")
st.title("💰 Sổ Cái Tài Chính (Service Account)")

# --- 3. XỬ LÝ DỮ LIỆU ---
try:
    # ttl=0 để luôn lấy dữ liệu mới nhất
    df = conn.read(worksheet=SHEET_NAME, ttl=0)
    # Xử lý trường hợp file trống hoặc thiếu cột
    required_cols = ["Ngày", "Tài khoản", "Loại", "Hạng mục", "Số tiền", "Ghi chú"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = pd.Series(dtype='object')
            
    # Lọc bỏ các dòng trống hoàn toàn (Fix lỗi warning)
    df = df.dropna(how='all')
    df = df[required_cols]
    
except Exception as e:
    st.error(f"⚠️ Lỗi kết nối: {e}")
    st.stop()

# --- 4. NHẬP LIỆU ---
with st.sidebar:
    st.header("📝 Nhập mới")
    with st.form("entry_form", clear_on_submit=True):
        date = st.date_input("Ngày", datetime.now())
        amount = st.number_input("Số tiền", min_value=0.0, step=1000.0, format="%.0f")
        t_type = st.selectbox("Loại", ["Chi phí", "Thu nhập"])
        category = st.selectbox("Hạng mục", ["Ăn uống", "Lương", "Di chuyển", "Nhà cửa", "Khác"])
        account = st.selectbox("Tài khoản", ["Tiền mặt", "Vietcombank", "Thẻ tín dụng"])
        note = st.text_input("Ghi chú")
        
        submitted = st.form_submit_button("Lưu Giao Dịch")
        
        if submitted:
            new_entry = pd.DataFrame([{
                "Ngày": date.strftime("%Y-%m-%d"),
                "Tài khoản": account,
                "Loại": t_type,
                "Hạng mục": category,
                "Số tiền": amount,
                "Ghi chú": note
            }])
            
            # --- ĐOẠN FIX LỖI FUTUREWARNING ---
            if df.empty:
                updated_df = new_entry
            else:
                updated_df = pd.concat([df, new_entry], ignore_index=True)
            
            try:
                conn.update(worksheet=SHEET_NAME, data=updated_df)
                st.success("✅ Đã lưu thành công!")
                st.rerun()
            except Exception as e:
                # Nếu lỗi này hiện ra nghĩa là Secrets vẫn chưa chuẩn
                st.error(f"❌ Lỗi Ghi: {e}")
                st.info("Hãy kiểm tra lại file Secrets. Đảm bảo bạn đã copy đúng Client Email và Private Key.")

# --- 5. BÁO CÁO ---
if not df.empty:
    # Chuyển đổi số tiền an toàn
    df["Số tiền"] = pd.to_numeric(df["Số tiền"], errors='coerce').fillna(0)
    
    income = df[df['Loại'] == 'Thu nhập']['Số tiền'].sum()
    expense = df[df['Loại'] == 'Chi phí']['Số tiền'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng Thu", f"{income:,.0f} đ")
    c2.metric("Tổng Chi", f"{expense:,.0f} đ")
    c3.metric("Số dư", f"{(income - expense):,.0f} đ")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Biểu đồ chi phí")
        df_chart = df[df['Loại'] == 'Chi phí']
        if not df_chart.empty:
            fig = px.pie(df_chart, values='Số tiền', names='Hạng mục', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
    with col2:
        st.subheader("Nhật ký")
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
