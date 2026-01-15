import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. CẤU HÌNH ---
PASSWORD = "qltaichinhcanhan"
# ID file Google Sheets của bạn (Lấy từ link bạn gửi)
SHEET_ID = "1h0kefkyiK49GyOyZ9OON1U7k2AGynWoc_2mWM-8Oz-I"
SHEET_NAME = "Transactions" # Tên Tab phải chính xác
# Đường dẫn ép buộc Google xuất file CSV
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={SHEET_NAME}"

# --- 2. HỆ THỐNG BẢO MẬT ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔐 Hệ thống bảo mật")
        pwd = st.text_input("Vui lòng nhập mật khẩu:", type="password")
        if st.button("Đăng nhập"):
            if pwd == PASSWORD:
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu sai!")
        return False
    return True

if not check_password():
    st.stop()

# --- 3. KẾT NỐI (Đọc & Ghi) ---
# Kết nối dùng để GHI dữ liệu (Vẫn cần cấu hình Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # Cách mới: Đọc trực tiếp từ đường dẫn CSV (Né lỗi 400 của thư viện)
        df = pd.read_csv(CSV_URL)
        # Đảm bảo các cột quan trọng luôn tồn tại
        required_cols = ["Ngày", "Tài khoản", "Loại", "Hạng mục", "Số tiền", "Ghi chú"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = "" # Tạo cột trống nếu thiếu
        return df
    except Exception as e:
        st.error(f"⚠️ Không đọc được dữ liệu: {e}")
        return pd.DataFrame(columns=["Ngày", "Tài khoản", "Loại", "Hạng mục", "Số tiền", "Ghi chú"])

st.set_page_config(page_title="Wallet x QBO", layout="wide")
st.title("💰 Finance Dashboard (Direct Mode)")

# --- 4. XỬ LÝ DỮ LIỆU ---
df = load_data()

# --- SIDEBAR: NHẬP LIỆU ---
with st.sidebar:
    st.header("📝 Nhập giao dịch")
    date = st.date_input("Ngày", datetime.now())
    amount = st.number_input("Số tiền (VND)", min_value=0.0, step=1000.0, format="%.2f")
    t_type = st.selectbox("Loại", ["Chi phí", "Thu nhập"])
    category = st.selectbox("Hạng mục", ["Ăn uống", "Lương", "Xăng xe", "Mua sắm", "Giải trí", "Khác"])
    account = st.selectbox("Tài khoản", ["Tiền mặt", "Vietcombank", "Momo"])
    note = st.text_input("Ghi chú")
    
    if st.button("Lưu lên Google Sheets", use_container_width=True):
        # Tạo dòng mới
        new_row = pd.DataFrame([{
            "Ngày": date.strftime("%Y-%m-%d"),
            "Tài khoản": account,
            "Loại": t_type,
            "Hạng mục": category,
            "Số tiền": amount,
            "Ghi chú": note
        }])
        
        # Nối vào dữ liệu cũ
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # Ghi đè lên Google Sheets (Dùng conn để ghi)
        try:
            conn.update(worksheet=SHEET_NAME, data=updated_df)
            st.success("✅ Đã ghi sổ thành công!")
            st.rerun()
        except Exception as e:
            st.error(f"Lỗi khi lưu: {e}")

    st.markdown("---")
    st.header("🗑️ Quản lý")
    if not df.empty:
        index_to_delete = st.number_input("STT muốn xóa:", min_value=0, max_value=len(df)-1 if len(df)>0 else 0, step=1)
        if st.button("Xóa dòng này", type="primary"):
            updated_df = df.drop(df.index[index_to_delete])
            try:
                conn.update(worksheet=SHEET_NAME, data=updated_df)
                st.warning(f"Đã xóa dòng {index_to_delete}")
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi khi xóa: {e}")

# --- 5. BÁO CÁO ---
if not df.empty:
    # Chuyển đổi số tiền phòng khi nó bị hiểu là chữ
    df["Số tiền"] = pd.to_numeric(df["Số tiền"], errors='coerce').fillna(0)
    
    total_income = df[df['Loại'] == 'Thu nhập']['Số tiền'].sum()
    total_expense = df[df['Loại'] == 'Chi phí']['Số tiền'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng Thu", f"{total_income:,.0f} đ")
    c2.metric("Tổng Chi", f"{total_expense:,.0f} đ")
    c3.metric("Số dư", f"{(total_income - total_expense):,.0f} đ")

    st.markdown("---")
    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        st.subheader("📊 Tỷ trọng chi tiêu")
        df_exp = df[df['Loại'] == 'Chi phí']
        if not df_exp.empty:
            fig = px.pie(df_exp, values='Số tiền', names='Hạng mục', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("📜 Sổ cái")
        st.dataframe(df.style.format({"Số tiền": "{:,.0f}"}), use_container_width=True, height=400)
else:
    st.info("Chưa có dữ liệu. Hãy đảm bảo file Google Sheets đã có tiêu đề cột!")
