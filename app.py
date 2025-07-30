import streamlit as st
import pandas as pd
from streamlit_gsheets.connection import GSheetsConnection

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Student Grade System", page_icon="📝", layout="wide")
st.title("📝 Student Grade System (เวอร์ชันจัดการข้อมูล)")

# --- การเชื่อมต่อฐานข้อมูล ---
# พยายามเชื่อมต่อกับ Google Sheets โดยใช้กุญแจจาก Secrets
try:
    conn = st.connection("gcs", type=GSheetsConnection)
except Exception as e:
    st.error("ไม่สามารถเชื่อมต่อกับ Google Sheets ได้ กรุณาตรวจสอบการตั้งค่า Secrets")
    st.error(f"Error: {e}")
    st.stop() # หยุดการทำงานของแอปถ้าเชื่อมต่อไม่ได้

# --- ฟังก์ชันสำหรับโหลดข้อมูล (พร้อม Cache) ---
@st.cache_data(ttl=60) # เก็บข้อมูลใน Cache เป็นเวลา 60 วินาที เพื่อไม่ให้โหลดข้อมูลบ่อยเกินไป
def load_data(worksheet_name):
    try:
        df = conn.read(worksheet=worksheet_name, usecols=list(range(30)), ttl=5)
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูลจาก Worksheet '{worksheet_name}' ได้")
        st.info("กรุณาตรวจสอบว่าชื่อ Worksheet ใน Google Sheets ของท่านถูกต้อง")
        return pd.DataFrame() # คืนค่า DataFrame ว่างเปล่าถ้าเกิดข้อผิดพลาด

# --- โหลดข้อมูลเริ่มต้น ---
students_df = load_data("student_master")
scores_df = load_data("scores_master")

# ตรวจสอบว่าโหลดข้อมูลสำเร็จหรือไม่
if students_df.empty:
    st.error("ไม่สามารถแสดงผลได้เนื่องจากข้อมูลนักเรียนว่างเปล่า")
    st.stop()

# --- ฟอร์มสำหรับเพิ่มนักเรียนใหม่ ---
with st.expander("📝 **คลิกที่นี่เพื่อเพิ่มนักเรียนใหม่**"):
    with st.form(key="add_student_form", clear_on_submit=True):
        st.write("กรอกข้อมูลนักเรียนใหม่")
        col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
        with col1:
            new_class_no = st.number_input("เลขที่", min_value=1, step=1, format="%d")
        with col2:
            new_student_id = st.number_input("เลขประจำตัว", min_value=1000, step=1, format="%d")
        with col3:
            new_title = st.selectbox("คำนำหน้าชื่อ", ["เด็กชาย", "เด็กหญิง"])
        with col4:
            new_first_name = st.text_input("ชื่อจริง")
            new_last_name = st.text_input("นามสกุล")

        submit_button = st.form_submit_button(label="✔️ บันทึกนักเรียนใหม่")

        if submit_button:
            if new_first_name and new_last_name and new_student_id > 0:
                new_student_data = pd.DataFrame([{
                    "class_no": new_class_no, "student_id": new_student_id, "title": new_title,
                    "first_name": new_first_name, "last_name": new_last_name, "class": "ป.1/1", "status": "ปกติ"
                }])
                
                score_columns = {col: 0 for col in scores_df.columns if col not in ['class_no', 'student_id']}
                new_score_data = pd.DataFrame([{"class_no": new_class_no, "student_id": new_student_id, **score_columns}])
                
                # อัปเดตข้อมูลใน Google Sheets
                conn.update(worksheet="student_master", data=pd.concat([students_df, new_student_data], ignore_index=True))
                conn.update(works_sheet="scores_master", data=pd.concat([scores_df, new_score_data], ignore_index=True))

                st.success(f"บันทึกข้อมูลนักเรียนใหม่: {new_title} {new_first_name} เรียบร้อยแล้ว!")
                st.cache_data.clear()
            else:
                st.warning("กรุณากรอกข้อมูลให้ครบถ้วน")

# --- ส่วนของการแสดงผลและลบข้อมูล ---
st.header("ตารางข้อมูลนักเรียนทั้งหมด")

# เพิ่มคอลัมน์ "delete" สำหรับสร้างปุ่มลบ
students_df_display = students_df.copy()
students_df_display["ลบ"] = [False] * len(students_df_display)

# จัดเรียงคอลัมน์ใหม่เพื่อความสวยงาม
cols_to_display = ["ลบ", "class_no", "student_id", "title", "first_name", "last_name", "class", "status"]
edited_df = st.data_editor(
    students_df_display[cols_to_display],
    column_config={"ลบ": st.column_config.CheckboxColumn("ต้องการลบ?")},
    disabled=students_df_display.columns.difference(['ลบ']),
    hide_index=True,
)

# หาแถวที่ถูกติ๊กว่าต้องการลบ
rows_to_delete = edited_df[edited_df["ลบ"]]
if not rows_to_delete.empty:
    st.warning("คุณต้องการลบข้อมูลนักเรียนต่อไปนี้ใช่หรือไม่?")
    st.dataframe(rows_to_delete[['class_no', 'student_id', 'first_name', 'last_name']])
    
    if st.button("ยืนยันการลบข้อมูล"):
        # กรองข้อมูลเก่าเอาแถวที่ต้องการลบออก
        students_df_updated = students_df[~students_df["student_id"].isin(rows_to_delete["student_id"])]
        scores_df_updated = scores_df[~scores_df["student_id"].isin(rows_to_delete["student_id"])]

        # อัปเดตข้อมูลใหม่ลงใน Google Sheets
        conn.update(worksheet="student_master", data=students_df_updated)
        conn.update(worksheet="scores_master", data=scores_df_updated)

        st.success("ลบข้อมูลสำเร็จ!")
        st.cache_data.clear()
        st.experimental_rerun()
