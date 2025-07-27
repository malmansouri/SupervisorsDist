
import streamlit as st
import pandas as pd
import os
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="الإدارة العامة للتعليم بمحافظة الطائف", layout="centered")
st.title("📊 نظام توزيع زيارات المشرفين على المدارس ")
st.markdown("""
مرحبًا بكم في نظام توزيع زيارات المشرفين التربويين على المدارس.  
يمكنك من خلال هذه الصفحة رفع **قالب التوزيع**، وتنفيذ خطة زيارات المشرفين بشكل تلقائي.
""")
st.markdown("""
<hr style="border-top: 1px solid #ccc; margin-top: 40px;" />
<div style="text-align: center; color: gray; font-size: 14px;">
</div>

""", unsafe_allow_html=True)
uploaded_file = st.file_uploader("📥 الرجاء رفع ملف Excel (قالب بيانات التوزيع)", type=["xlsx"])
def distribute_supervisors_relaxed_fields_fixed(supervisors, schools, num_days=14):
    distribution = []
    field_school_visited = {}
    school_day_visits = {day: set() for day in range(1, num_days + 1)}
    priority_school_map = {}
    for _, row in supervisors.iterrows():
        supervisor_id = row['رقم الهوية']
        priorities = [row.get(col) for col in ['مدرسة1', 'مدرسة2', 'مدرسة3'] if pd.notna(row.get(col))]
        priority_school_map[supervisor_id] = priorities
    supervisors = supervisors.copy()
    supervisors['أولوية'] = supervisors['المجالات'].apply(lambda fields: 0 if 'نواتج التعلم' in fields else 1)
    supervisors = supervisors.sort_values(by='أولوية')

    for _, supervisor in supervisors.iterrows():
        supervisor_id = supervisor['رقم الهوية']
        name = supervisor['المشرف']
        fields = supervisor['المجالات']
        gender = supervisor['الجنس']
        sector = supervisor['القطاع']
        preferred_schools = priority_school_map.get(supervisor_id, [])
        eligible_schools = []

        for school_name in preferred_schools:
            school_row = schools[schools['المدرسة'] == school_name]
            if school_row.empty:
                continue
            school = school_row.iloc[0]
            if school['الجنس'] != gender or school['القطاع'] != sector:
                continue
            school_fields = school['المجالات']
            if 'نواتج التعلم' in fields:
                if 'نواتج التعلم' not in school_fields:
                    continue
                assigned_field = 'نواتج التعلم'
            else:
                assigned_field = fields[0]
            if school_name in field_school_visited.get(assigned_field, set()):
                continue
            eligible_schools.append((school['الرقم الوزاري'], school_name, school['المرحلة'], assigned_field))

        for _, school in schools.iterrows():
            school_name = school['المدرسة']
            if school_name in [s[1] for s in eligible_schools]:
                continue
            if school['الجنس'] != gender or school['القطاع'] != sector:
                continue
            school_fields = school['المجالات']
            if 'نواتج التعلم' in fields:
                if 'نواتج التعلم' not in school_fields:
                    continue
                assigned_field = 'نواتج التعلم'
            else:
                assigned_field = fields[0]
            if school_name in field_school_visited.get(assigned_field, set()):
                continue
            eligible_schools.append((school['الرقم الوزاري'], school_name, school['المرحلة'], assigned_field))

        eligible_schools = eligible_schools[:3]
        if len(eligible_schools) < 3:
            continue

        for _, _, _, field in eligible_schools:
            field_school_visited.setdefault(field, set()).update(
                [s[1] for s in eligible_schools if s[3] == field]
            )

        assigned_counts = {school[1]: 0 for school in eligible_schools}
        day_assignments = []
        day = 1
        max_attempts = num_days * 2
        while len(day_assignments) < num_days and day <= max_attempts:
            if day not in school_day_visits:
                school_day_visits[day] = set()
            sorted_schools = sorted(eligible_schools, key=lambda s: assigned_counts[s[1]])
            for school_id, school_name, school_stage, assigned_field in sorted_schools:
                if school_name not in school_day_visits[day]:
                    school_day_visits[day].add(school_name)
                    assigned_counts[school_name] += 1
                    day_assignments.append({
                        'اليوم': day,
                        'رقم الهوية': supervisor_id,
                        'المشرف': name,
                        'الرقم الوزاري': school_id,
                        'المدرسة': school_name,
                        'المرحلة': school_stage,
                        'الجنس': gender,
                        'القطاع': sector,
                        'المجال': assigned_field
                    })
                    break
            day += 1
        if len(day_assignments) < num_days:
            continue
        distribution.extend(day_assignments)
    return pd.DataFrame(distribution)

if uploaded_file:
    excel_data = pd.ExcelFile(uploaded_file)
    supervisors_df = pd.read_excel(excel_data, sheet_name="بيانات المشرفين")
    schools_df = pd.read_excel(excel_data, sheet_name="بيانات المدارس")

    supervisors_df['المجالات'] = supervisors_df['المجال'].apply(lambda x: [x.strip()] if pd.notna(x) else [])
    school_field_cols = ['المجال1', 'المجال2', 'المجال3', 'المجال4']
    schools_df['المجالات'] = schools_df[school_field_cols].values.tolist()
    schools_df['المجالات'] = schools_df['المجالات'].apply(lambda fields: [f.strip() for f in fields if pd.notna(f)])

    distribution_df = distribute_supervisors_relaxed_fields_fixed(supervisors_df, schools_df, num_days=14)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        distribution_df.to_excel(writer, sheet_name="خطة المشرفين", index=False)
        distribution_df.sort_values(['المدرسة', 'اليوم']).to_excel(writer, sheet_name="خطة المدارس", index=False)
        supervisors_df.to_excel(writer, sheet_name="بيانات المشرفين", index=False)
        schools_df.to_excel(writer, sheet_name="بيانات المدارس", index=False)

        covered_fields = distribution_df.groupby("المدرسة")["المجال"].apply(set).reset_index()
        covered_fields.columns = ["المدرسة", "المجالات المغطاة"]
        school_fields = schools_df[["المدرسة", "المجال1", "المجال2", "المجال3", "المجال4"]].copy()
        school_fields["المجالات المطلوبة"] = school_fields[["المجال1", "المجال2", "المجال3", "المجال4"]].values.tolist()
        school_fields["المجالات المطلوبة"] = school_fields["المجالات المطلوبة"].apply(lambda lst: [x for x in lst if pd.notna(x)])
        result = pd.merge(school_fields[["المدرسة", "المجالات المطلوبة"]], covered_fields, on="المدرسة", how="left")
        result["المجالات المغطاة"] = result["المجالات المغطاة"].apply(lambda x: x if isinstance(x, set) else set())
        result["المجالات غير المغطاة"] = result.apply(lambda row: [field for field in row["المجالات المطلوبة"] if field not in row["المجالات المغطاة"]], axis=1)
        result.to_excel(writer, sheet_name="المجالات غير المغطاة", index=False)
        filtered_result = result[result["المجالات غير المغطاة"].apply(lambda x: isinstance(x, list) and len(x) > 0)].copy()
        filtered_result.to_excel(writer, sheet_name="المدارس الناقصة فقط", index=False)

    output.seek(0)
    st.success("✅ تم إنشاء الملف بنجاح! يمكنك تحميله من الزر أدناه.")
    st.download_button(
        label="📥 تحميل ملف خطة توزيع المشرفين",
        data=output,
        file_name="خطة توزيع المشرفين.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.header("📧 Automated Email Notifications")

smtp_server = st.text_input("SMTP Server")
smtp_port = st.number_input("SMTP Port", value=587)
smtp_user = st.text_input("SMTP Username")
smtp_password = st.text_input("SMTP Password", type="password")

if st.button("Send Emails to Supervisors"):
    if smtp_server and smtp_port and smtp_user and smtp_password:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.base import MIMEBase
        from email import encoders

        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)

            for supervisor_email in distribution_df['البريد الإلكتروني'].unique():
                supervisor_plan = distribution_df[distribution_df['البريد الإلكتروني'] == supervisor_email]

                msg = MIMEMultipart()
                msg['From'] = smtp_user
                msg['To'] = supervisor_email
                msg['Subject'] = "Your Personalized Visit Plan"

                body = "Please find your visit plan attached."
                msg.attach(MIMEText(body, 'plain'))

                output_supervisor = BytesIO()
                with pd.ExcelWriter(output_supervisor, engine="openpyxl") as writer:
                    supervisor_plan.to_excel(writer, index=False)
                output_supervisor.seek(0)

                part = MIMEBase('application', 'octet-stream')
                part.set_payload(output_supervisor.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', "attachment; filename=visit_plan.xlsx")
                msg.attach(part)

                server.send_message(msg)

            st.success("Emails sent successfully!")
            server.quit()
        except Exception as e:
            st.error(f"Failed to send emails: {e}")
    else:
        st.warning("Please configure SMTP settings.")

st.markdown("""
<hr style="border-top: 1px solid #ccc; margin-top: 40px;" />
<div style="text-align: center; color: gray; font-size: 14px;">
جميع الحقوق محفوظة © 2025 - ماجد المنصوري<br>
<img src="https://sites.moe.gov.sa/assets/images/logo.png" width="80" />
</div>
""", unsafe_allow_html=True)