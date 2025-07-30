import streamlit as st
import pandas as pd
from streamlit_gsheets.connection import GSheetsConnection

# --- การตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="Student Grade System", page_icon="📝", layout="wide")
st.title("📝 Student Grade System (เวอร์ชันจัดการข้อมูล)")

# --- การเชื่อมต่อฐานข้อมูล ---
# เชื่อมต่อกับ Google Sheets โดยใช้กุญแจจาก Secrets โดยอัตโนมัติ
try:
    conn = st.connection("gcs", type=GSheetsConnection)
except Exception as e:
    st.error("ไม่สามารถเชื่อมต่อกับ Google Sheets ได้")
    st.error(f"Error: {e}")
    st.stop()


# --- ฟังก์ชันสำหรับโหลดข้อมูล (พร้อม Cache) ---
@st.cache_data(ttl=60) # เก็บข้อมูลใน Cache เป็นเวลา 60 วินาที
def load_data(worksheet_name):
    df = conn.read(worksheet=worksheet_name, usecols=list(range(30)), ttl=5)
    df = df.dropna(how="all")
    return df

# --- โหลดข้อมูลเริ่มต้น ---
try:
    students_df = load_data("student_master")
    scores_df = load_data("scores_master")
except Exception as e:
    st.error(f"ไม่สามารถโหลดข้อมูลจาก Worksheet ได้: {e}")
    st.info("กรุณาตรวจสอบว่าชื่อ Worksheet ใน Google Sheets ของท่านคือ 'student_master' และ 'scores_master'")
    st.stop()


# --- ฟอร์มสำหรับเพิ่มนักเรียนใหม่ ---
st.header("เพิ่มนักเรียนใหม่")
with st.form(key="add_student_form", clear_on_submit=True):
    st.write("กรอกข้อมูลนักเรียนใหม่ที่นี่")
    col1, col2, col3 = st.columns(3)
    with col1:
        new_class_no = st.number_input("เลขที่", min_value=1, step=1)
        new_title = st.selectbox("คำนำหน้าชื่อ", ["เด็กชาย", "เด็กหญิง"])
    with col2:
        new_student_id = st.number_input("เลขประจำตัว", min_value=1000, step=1)
        new_first_name = st.text_input("ชื่อจริง")
    with col3:
        st.text_input("ห้องเรียน (ค่าเริ่มต้น)", value="ป.1/1", disabled=True)
        new_last_name = st.text_input("นามสกุล")

    submit_button = st.form_submit_button(label="✔️ บันทึกนักเรียนใหม่")

    if submit_button:
        if new_first_name and new_last_name and new_student_id > 0:
            # สร้างแถวข้อมูลใหม่สำหรับทั้งสองชีต
            new_student_data = pd.DataFrame([{
                "class_no": new_class_no, "student_id": new_student_id, "title": new_title,
                "first_name": new_first_name, "last_name": new_last_name, "class": "ป.1/1", "status": "ปกติ"
            }])

            # สร้างแถวคะแนนเปล่า (ทุกช่องเป็น 0)
            score_columns = {col: 0 for col in scores_df.columns if col not in ['class_no', 'student_id']}
            new_score_data = pd.DataFrame([{"class_no": new_class_no, "student_id": new_student_id, **score_columns}])

            # อัปเดตข้อมูลใน Google Sheets
            conn.update(worksheet="student_master", data=pd.concat([students_df, new_student_data], ignore_index=True))
            conn.update(worksheet="scores_master", data=pd.concat([scores_df, new_score_data], ignore_index=True))

            st.success("บันทึกข้อมูลนักเรียนใหม่เรียบร้อยแล้ว!")
            st.cache_data.clear() # ล้าง Cache เพื่อโหลดข้อมูลใหม่
            st.experimental_rerun() # รีเฟรชหน้าเว็บ
        else:
            st.warning("กรุณากรอกข้อมูลให้ครบถ้วน (เลขที่, เลขประจำตัว, ชื่อ, นามสกุล)")

# --- ส่วนของการแสดงผลและลบข้อมูล ---
st.header("ตารางข้อมูลนักเรียนทั้งหมด")

# เพิ่มคอลัมน์ "delete" สำหรับสร้างปุ่มลบ
students_df_display = students_df.copy()
students_df_display["delete"] = [False] * len(students_df_display)

edited_df = st.data_editor(
    students_df_display,
    column_config={"delete": st.column_config.CheckboxColumn("ต้องการลบ?")},
    disabled=students_df_display.columns[:-1], # ทำให้แก้ไขข้อมูลในตารางไม่ได้ ยกเว้นช่องติ๊กลบ
    hide_index=True,
)

# หาแถวที่ถูกติ๊กว่าต้องการลบ
rows_to_delete = edited_df[edited_df["delete"]]
if not rows_to_delete.empty:
    st.warning("คุณต้องการลบข้อมูลนักเรียนต่อไปนี้ใช่หรือไม่?")
    st.dataframe(rows_to_delete[['class_no', 'student_id', 'title', 'first_name', 'last_name']])
    if st.button("ยืนยันการลบข้อมูล"):
        # กรองข้อมูลเก่าเอาแถวที่ต้องการลบออก
        students_df_updated = students_df[~students_df["student_id"].isin(rows_to_delete["student_id"])]
        scores_df_updated = scores_df[~scores_df["student_id"].isin(rows_to_delete["student_id"])]

        # อัปเดตข้อมูลใหม่ลงใน Google Sheets
        conn.update(worksheet="student_master", data=students_df_updated)
        conn.update(worksheet="scores_master", data=scores_df_updated)

        st.success("ลบข้อมูลสำเร็จ!")
        st.cache_data.clear() # ล้าง Cache
        st.experimental_rerun() # รีเฟรชหน้าเว็บ
