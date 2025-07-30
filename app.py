import streamlit as st
import pandas as pd

# --- การตั้งค่าหน้าเว็บหลัก ---
st.set_page_config(
    page_title="Student Grade System",
    page_icon="🎓",
    layout="wide"
)

# --- ส่วนหัวของแอปพลิเคชัน ---
st.title("🎓 Student Grade System (เวอร์ชันสำเร็จรูป)")
st.info("ระบบนี้ดึงข้อมูลจาก Google Sheets ของ Teacher โดยอัตโนมัติ")

# --- ส่วนที่แก้ไข: ฝังลิงก์ถาวรไว้ในโค้ดโดยตรง ---
STUDENT_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStgwhz14o2i0lBP_Br158jQkBtLfA8bgp5HaEkvYfu6HHQAQG58QpD7aJkoQUEWG-dSJCWq9LVO24n/pub?gid=0&single=true&output=csv"
SCORE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8q-bDIaQDcms2q7zJky_bLBUFAllpEIxkG66rcKjMtPP1FPaGo01UCZy3mZ8k0U-BJKQu--Vn8z8o/pub?gid=0&single=true&output=csv"


# --- ฟังก์ชันสำหรับคำนวณเกรด ---
def calculate_grade(score, max_score=100):
    if max_score == 0: return 0.0
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
try:
    # อ่านข้อมูลจาก URL ที่เราฝังไว้โดยตรง
    df_students = pd.read_csv(STUDENT_SHEET_URL)
    df_scores = pd.read_csv(SCORE_SHEET_URL)
    final_df = pd.merge(df_students, df_scores, on=['student_id', 'class_no'])

    score_columns = [col for col in df_scores.columns if col not in ['class_no', 'student_id']]
    subjects = sorted(list(set([col.split('_')[0] for col in score_columns])))
    
    # คำนวณคะแนนและเกรดสำหรับทุกวิชาที่ตรวจพบ
    for subject in subjects:
        total_col = f'{subject}_total'
        grade_col = f'{subject}_grade'
        subject_score_cols = [col for col in score_columns if col.startswith(subject)]
        final_df[total_col] = final_df[subject_score_cols].sum(axis=1)
        final_df[grade_col] = final_df[total_col].apply(lambda s: calculate_grade(s))

    st.header("✅ Dashboard: ภาพรวมข้อมูลนักเรียนและผลการเรียน")
    st.dataframe(final_df)

    st.header("📊 การวิเคราะห์ข้อมูล")
    selected_subject = st.selectbox("เลือกวิชาเพื่อดูการวิเคราะห์:", subjects)

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
    st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
    st.warning("กรุณาตรวจสอบว่าลิงก์ในโค้ดถูกต้อง และไฟล์ Google Sheets ได้รับการ 'Publish to web' แล้ว")
