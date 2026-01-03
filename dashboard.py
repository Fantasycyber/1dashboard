import streamlit as st
import pandas as pd

# --- 1. ตั้งค่าหน้าเว็บ (Page Config) ---
st.set_page_config(page_title="CEO Financial Dashboard", layout="wide")

st.title("📊 CEO Financial Command Center")
st.markdown("---") 

# --- 2. โหลดข้อมูล (Load Data) ---
# ส่วนนี้ต้องทำงาน "ก่อน" ส่วนอื่นเสมอ
@st.cache_data
# --- แก้ไขส่วน load_data (เปลี่ยนจากไฟล์ Local เป็น Google Sheets) ---

# เพิ่ม ttl=60 (Time to live) แปลว่า "ให้จำข้อมูลแค่ 60 วินาทีพอ"
# ถ้าเกิน 60 วิ ให้ไปดึงข้อมูลจาก Google Sheets ใหม่ (นี่คือเคล็ดลับ Real-time!)
@st.cache_data(ttl=60)
def load_data():
    # 👇 ใส่ลิงก์ Google Sheets ของคุณเหมือนเดิม
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR4_1WjSASBgqsMytESxcIVpDz4ZfDCMh3LI0Od_-hY2EwyWl0zZhQ2HcR6KDhbENB88ldhn1fLqDQr/pub?output=csv"
    
    df = pd.read_csv(sheet_url)
    
    # --- แก้ไขตรงนี้ครับ ---
    if 'Date' in df.columns:
        # dayfirst=True : บอกว่าเลขหน้าคือ "วัน" (แก้ปัญหา 15/05)
        # errors='coerce' : ถ้าเจอช่องว่างหรือวันที่เพี้ยนๆ ให้เปลี่ยนเป็น NaT (Not a Time) แทนที่จะ Error
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        
        # ลบแถวที่วันที่อ่านไม่ออกทิ้งไป (Clean Data)
        df = df.dropna(subset=['Date'])
        
    # --- คำนวณกำไร ---
    df['Total_Sales'] = df['Sales_Price_Per_Unit'] * df['Quantity']
    df['Total_Cost'] = df['Cost_Per_Unit'] * df['Quantity']
    df['Gross_Profit'] = df['Total_Sales'] - df['Total_Cost']
    df['Margin_Percent'] = (df['Gross_Profit'] / df['Total_Sales']) * 100
    
    return df

# เรียกใช้ฟังก์ชัน เพื่อให้ได้ตัวแปร df มาใช้งาน
try:
    df = load_data()
except FileNotFoundError:
    st.error("❌ หาไฟล์ sales_data.csv ไม่เจอ! เช็คชื่อไฟล์และโฟลเดอร์อีกทีครับ")
    st.stop()

# --- 3. Sidebar Filter (ส่วนกรองข้อมูล) ---
# ตอนนี้ df มีตัวตนแล้ว เราจึงดึงข้อมูลมาทำตัวเลือกได้
st.sidebar.header("🔍 Filter Options")

# ดึงรายชื่อสินค้าทั้งหมด
product_list = df['Product_Name'].unique()

# สร้างกล่องเลือก
selected_products = st.sidebar.multiselect(
    "เลือกดูเฉพาะสินค้า (Select Products):",
    options=product_list,
    default=product_list # ค่าเริ่มต้นคือเลือกทั้งหมด
)

# *** หัวใจสำคัญ: กรองข้อมูล ***
# ถ้ามีการเลือกสินค้า ให้กรอง df ให้เหลือแค่สินค้านั้น
# ถ้าไม่ได้เลือกอะไรเลย (กล่องว่าง) ให้โชว์ทั้งหมด
if selected_products:
    df_filtered = df[df['Product_Name'].isin(selected_products)]
else:
    df_filtered = df # ถ้าไม่ได้เลือก ให้ใช้ข้อมูลทั้งหมด

# --- 4. แสดงผล (Visualization) ---
# *** หมายเหตุ: จากตรงนี้ไป เราจะใช้ df_filtered แทน df เพื่อโชว์เฉพาะสิ่งที่เลือก ***

# คำนวณ KPI จากข้อมูลที่กรองแล้ว
total_sales = df_filtered['Total_Sales'].sum()
total_profit = df_filtered['Gross_Profit'].sum()
avg_margin = df_filtered['Margin_Percent'].mean()

# แสดง KPI Cards
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="💰 Total Revenue", value=f"฿{total_sales:,.0f}")
with col2:
    st.metric(label="📈 Gross Profit", value=f"฿{total_profit:,.0f}")
with col3:
    st.metric(label="⚡ Avg Margin", value=f"{avg_margin:.2f}%")

st.markdown("---")

# ส่วนกราฟ
st.subheader("📅 Performance Trends")

# เตรียมข้อมูลกราฟจาก df_filtered
df_filtered['Month'] = df_filtered['Date'].dt.to_period('M').astype(str)
monthly_data = df_filtered.groupby('Month')[['Total_Sales', 'Gross_Profit']].sum()

# แสดงกราฟ
st.line_chart(monthly_data)

# แสดงตารางข้อมูลดิบ
with st.expander("ดูข้อมูลรายละเอียด (Data Detail)"):
    st.dataframe(df_filtered)