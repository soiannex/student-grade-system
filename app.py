import streamlit as st
import pandas as pd

# --- การตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(page_title="Student Grade System", page_icon="🎓", layout="wide")
st.title("🎓 Student Grade System")
st.write("เวอร์ชันสุดท้าย (Final): ระบบ Dynamic ตรวจจับรายวิชาและคำนวณเกรดอัตโนมัติ")

# --- ส่วนของการเชื่อมต่อกับ Google Sheets ---
st.header("1. เชื่อมต่อฐานข้อมูล (Connect to Database)")
st.info("นำลิงก์ที่ได้จากการ 'Publish to web' (เป็น .csv) ของ Google Sheets มาวางในช่องด้านล่าง")

col1, col2 = st.columns(2)
with col1:
    student_sheet_url = st.text_input("ลิงก์ CSV ของไฟล์ student_master")
with col2:
    score_sheet_url = st.text_input("ลิงก์ CSV ของไฟล์ scores_master")

# --- ฟังก์ชันสำหรับคำนวณเกรด ---
def calculate_grade(score, max_score=100):
    # คำนวณคะแนนเป็นเปอร์เซ็นต์
    percent_score = (score / max_score) * 100
    if percent_score >= 80: return 4.0
    if percent_score >= 75: return 3.5
    if percent_score >= 70: return 3.0
    if percent_score >= 65: return 2.5
    if percent_score >= 60: return 2.0
    if percent_score >= 55: return 1.5
    if percent_score >= 50: return 1.0
    return 0.0

# --- ส่วนของการประมวลผลและแสดงผล ---
if student_sheet_url and score_sheet_url:
    try:
        df_students = pd.read_csv(student_sheet_url)
        df_scores = pd.read_csv(score_sheet_url)
        final_df = pd.merge(df_students, df_scores, on=['student_id', 'class_no'])

        # --- ส่วนใหม่: Dynamic Subject Detection ---
        # ค้นหารายวิชาทั้งหมดจากชื่อคอลัมน์ในไฟล์ scores_master
        score_columns = [col for col in df_scores.columns if col not in ['class_no', 'student_id']]
        subjects = sorted(list(set([col.split('_')[0] for col in score_columns])))
        
        st.success(f"ตรวจพบ {len(subjects)} รายวิชาในไฟล์คะแนน: {', '.join(subjects)}")

        # คำนวณคะแนนและเกรดสำหรับทุกวิชาที่ตรวจพบ
        for subject in subjects:
            total_col = f'{subject}_total'
            grade_col = f'{subject}_grade'
            
            # หาคอลัมน์คะแนนย่อยของวิชานั้นๆ
            subject_score_cols = [col for col in score_columns if col.startswith(subject)]
            
            # คำนวณคะแนนรวม
            final_df[total_col] = final_df[subject_score_cols].sum(axis=1)
            # คำนวณเกรด (สมมติว่าคะแนนรวมทุกช่องย่อยคือ 100)
            final_df[grade_col] = final_df[total_col].apply(lambda score: calculate_grade(score, max_score=100))

        st.header("✅ Dashboard: ภาพรวมข้อมูลนักเรียนและผลการเรียน")
        st.dataframe(final_df)

        st.header("📊 การวิเคราะห์ข้อมูล")
        # สร้าง selectbox ให้ผู้ใช้เลือกวิชาที่จะดู
        selected_subject = st.selectbox("เลือกวิชาเพื่อดูการวิเคราะห์:", subjects)

        # แสดงผลข้อมูลสรุปและกราฟสำหรับวิชาที่เลือก
        if selected_subject:
            total_col_selected = f'{selected_subject}_total'
            grade_col_selected = f'{selected_subject}_grade'

            kpi1, kpi2, kpi3 = st.columns(3)
            kpi1.metric(f"คะแนนเฉลี่ย ({selected_subject})", f"{final_df[total_col_selected].mean():.2f}")
            kpi2.metric(f"เกรดเฉลี่ย ({selected_subject})", f"{final_df[grade_col_selected].mean():.2f}")
            kpi3.metric(f"คะแนนสูงสุด ({selected_subject})", f"{final_df[total_col_selected].max()}")
            
            st.subheader(f"กราฟแสดงการกระจายของเกรดวิชา: {selected_subject}")
            grade_distribution = final_df[grade_col_selected].value_counts().sort_index()
            st.bar_chart(grade_distribution)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
else:
    st.warning("กรุณาวางลิงก์ข้อมูลจาก Google Sheets ทั้ง 2 ไฟล์เพื่อเริ่มต้น")