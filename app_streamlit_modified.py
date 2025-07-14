
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


# ====== تعديل التوزيع حسب المدارس الجديدة في الأعمدة مدرسة1،2،3 ======
def apply_priority_school_updates(supervisors_df, distribution_df, schools_df):
    updated_distribution = distribution_df.copy()
    schools_to_assign = []

    # استخراج المدارس الجديدة من الأعمدة الثلاثة
    for _, row in supervisors_df.iterrows():
        supervisor_id = row["رقم الهوية"]
        supervisor_name = row["المشرف"]
        gender = row["الجنس"]
        sector = row["القطاع"]
        fields = row["المجال"].strip()
        for col in ["مدرسة1", "مدرسة2", "مدرسة3"]:
            school_name = row.get(col)
            if pd.notna(school_name) and school_name.strip() != "":
                schools_to_assign.append((school_name.strip(), supervisor_id, supervisor_name, gender, sector, fields))

    for school_name, new_sup_id, new_sup_name, new_gender, new_sector, new_field in schools_to_assign:
        # تحقق إن كانت المدرسة موزعة حاليًا
        existing_rows = updated_distribution[updated_distribution["المدرسة"] == school_name]
        for _, old_row in existing_rows.iterrows():
            old_sup_id = old_row["رقم الهوية"]
            old_field = old_row["المجال"]
            if old_sup_id != new_sup_id and old_field == new_field:
                # حذف التوزيع السابق للمدرسة من المشرف القديم
                updated_distribution = updated_distribution[~(
                    (updated_distribution["رقم الهوية"] == old_sup_id) &
                    (updated_distribution["المدرسة"] == school_name)
                )]

                # محاولة تعويض المشرف القديم
                current_schools = updated_distribution[updated_distribution["رقم الهوية"] == old_sup_id]["المدرسة"].unique().tolist()
                available_schools = schools_df[
                    (schools_df["الجنس"] == old_row["الجنس"]) &
                    (schools_df["القطاع"] == old_row["القطاع"])
                ]
                available_schools = available_schools[~available_schools["المدرسة"].isin(current_schools)]
                for _, new_school in available_schools.iterrows():
                    if new_field in [new_school.get(f"المجال{i}") for i in range(1, 5)]:
                        # تعويض المشرف القديم بهذه المدرسة
                        for day in range(1, 15):
                            if not ((updated_distribution["رقم الهوية"] == old_sup_id) & (updated_distribution["اليوم"] == day)).any():
                                updated_distribution = pd.concat([updated_distribution, pd.DataFrame([{
                                    "اليوم": day,
                                    "رقم الهوية": old_sup_id,
                                    "المشرف": old_row["المشرف"],
                                    "الرقم الوزاري": new_school["الرقم الوزاري"],
                                    "المدرسة": new_school["المدرسة"],
                                    "المرحلة": new_school["المرحلة"],
                                    "الجنس": new_school["الجنس"],
                                    "القطاع": new_school["القطاع"],
                                    "المجال": new_field
                                }])], ignore_index=True)
                                break
                        break

        # إضافة المدرسة للمشرف الجديد إن لم تكن موجودة
        if not ((updated_distribution["رقم الهوية"] == new_sup_id) & (updated_distribution["المدرسة"] == school_name)).any():
            school_row = schools_df[schools_df["المدرسة"] == school_name]
            if not school_row.empty:
                school = school_row.iloc[0]
                for day in range(1, 15):
                    if not ((updated_distribution["رقم الهوية"] == new_sup_id) & (updated_distribution["اليوم"] == day)).any():
                        updated_distribution = pd.concat([updated_distribution, pd.DataFrame([{
                            "اليوم": day,
                            "رقم الهوية": new_sup_id,
                            "المشرف": new_sup_name,
                            "الرقم الوزاري": school["الرقم الوزاري"],
                            "المدرسة": school_name,
                            "المرحلة": school["المرحلة"],
                            "الجنس": new_gender,
                            "القطاع": new_sector,
                            "المجال": new_field
                        }])], ignore_index=True)
                        break
    return updated_distribution

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

    
        # ==== ملخص المدارس لكل مشرف ====
        summary_supervisors = distribution_df.groupby(['رقم الهوية', 'المشرف', 'الجنس', 'القطاع', 'المجال'])['المدرسة'] \
            .unique().reset_index()
        # تحويل قائمة المدارس إلى أعمدة منفصلة
        max_schools = summary_supervisors['المدرسة'].apply(len).max()
        for i in range(max_schools):
            summary_supervisors[f'مدرسة {i+1}'] = summary_supervisors['المدرسة'].apply(lambda x: x[i] if i < len(x) else "")
        summary_supervisors.drop(columns=["المدرسة"], inplace=True)
        summary_supervisors.to_excel(writer, sheet_name="ملخص المدارس لكل مشرف", index=False)

        # ==== ملخص المشرفين لكل مدرسة ====
        summary_schools = distribution_df.groupby(['المدرسة', 'الرقم الوزاري', 'المرحلة', 'الجنس', 'القطاع'])[['المشرف', 'المجال']] \
            .agg(lambda x: list(pd.unique(x))).reset_index()
        # تحويل قوائم المشرفين إلى نص مفصول بفواصل
        summary_schools['المشرفين'] = summary_schools['المشرف'].apply(lambda x: "، ".join(x))
        summary_schools['المجالات'] = summary_schools['المجال'].apply(lambda x: "، ".join(x))
        summary_schools.drop(columns=['المشرف', 'المجال'], inplace=True)
        summary_schools = summary_schools.sort_values('المدرسة')
        summary_schools.to_excel(writer, sheet_name="ملخص المشرفين لكل مدرسة", index=False)

        output.seek(0)
    st.success("✅ تم إنشاء الملف بنجاح! يمكنك تحميله من الزر أدناه.")
    st.download_button(
        label="📥 تحميل ملف خطة توزيع المشرفين",
        data=output,
        file_name="خطة توزيع المشرفين.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

st.markdown("""
<hr style="border-top: 1px solid #ccc; margin-top: 40px;" />
<div style="text-align: center; color: gray; font-size: 14px;">
جميع الحقوق محفوظة © 2025 - ماجد المنصوري<br>
<img src="https://sites.moe.gov.sa/assets/images/logo.png" width="80" />
</div>
""", unsafe_allow_html=True)