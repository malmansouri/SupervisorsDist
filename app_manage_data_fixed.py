
import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="نظام إدارة بيانات التوزيع", layout="wide")
st.title("📋 نظام إدارة بيانات التوزيع")

# تحميل القالب الأساسي
template_path = "قالب بيانات التوزيع.xlsx"
xl = pd.ExcelFile(template_path)
supervisors_df = xl.parse("بيانات المشرفين")
schools_df = xl.parse("بيانات المدارس")

# جلسة بيانات قابلة للتعديل
if 'supervisors_data' not in st.session_state:
    st.session_state.supervisors_data = supervisors_df.copy()

if 'schools_data' not in st.session_state:
    st.session_state.schools_data = schools_df.copy()

if 'search_term' not in st.session_state:
    st.session_state.search_term = ""
if 'school_search_term' not in st.session_state:
    st.session_state.school_search_term = ""

tabs = st.tabs(["🧑‍🏫 بيانات المشرفين", "🏫 بيانات المدارس", "📤 حفظ واستعراض"])

# --- تبويب المشرفين ---
with tabs[0]:
    st.header("🧑‍🏫 نموذج بيانات المشرف")
    with st.form("supervisor_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("اسم المشرف")
            id_num = st.text_input("رقم الهوية")
            gender = st.selectbox("الجنس", ["بنين", "بنات"])
        with col2:
            field = st.selectbox("المجال", ["نواتج التعلم", "الصفوف الأولية", "الصفوف العليا", "العلوم", "الرياضيات"])
            sector = st.selectbox("القطاع", ["شرق", "غرب", "شمال", "جنوب", "وسط"])
        with col3:
            school1 = st.text_input("مدرسة1 (اختيارية)")
            school2 = st.text_input("مدرسة2 (اختيارية)")
            school3 = st.text_input("مدرسة3 (اختيارية)")
        submitted = st.form_submit_button("➕ إضافة المشرف")
        if submitted and name and id_num:
            st.session_state.supervisors_data = pd.concat([st.session_state.supervisors_data, pd.DataFrame([{
                "المشرف": name,
                "رقم الهوية": id_num,
                "الجنس": gender,
                "المجال": field,
                "القطاع": sector,
                "مدرسة1": school1,
                "مدرسة2": school2,
                "مدرسة3": school3
            }])], ignore_index=True)
            st.success("✅ تم إضافة المشرف بنجاح")

    # البحث والتعديل والحذف للمشرفين
    st.subheader("🔍 بحث عن مشرف")
    col_search, col_btn = st.columns([3, 1])
    with col_search:
        st.session_state.search_term = st.text_input("أدخل اسم المشرف للبحث", value=st.session_state.search_term)
    with col_btn:
        if st.button("🔍 بحث"):
            filtered_df = st.session_state.supervisors_data[
                st.session_state.supervisors_data["المشرف"].str.contains(st.session_state.search_term, na=False)
            ]
        else:
            filtered_df = st.session_state.supervisors_data.copy()

    st.dataframe(filtered_df, use_container_width=True)

    if not filtered_df.empty:
        st.markdown("### ✏️ تعديل أو حذف مشرف")
        selected_index = st.selectbox("اختر الصف", filtered_df.index.tolist(), format_func=lambda i: filtered_df.at[i, "المشرف"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ حذف المشرف"):
                st.session_state.supervisors_data.drop(index=selected_index, inplace=True)
                st.session_state.supervisors_data.reset_index(drop=True, inplace=True)
                st.success("✅ تم حذف المشرف بنجاح")
        with col2:
            if True:
                row = filtered_df.loc[selected_index]
                with st.form("edit_form"):
                    new_name = st.text_input("اسم المشرف", value=row["المشرف"])
                    new_id = st.text_input("رقم الهوية", value=row["رقم الهوية"])
                    new_gender = st.selectbox("الجنس", ["بنين", "بنات"], index=["بنين", "بنات"].index(row["الجنس"].strip()))
                    field_options = ["نواتج التعلم", "الصفوف الأولية", "الصفوف العليا", "العلوم", "الرياضيات"]
                    new_field = st.selectbox("المجال", field_options, index=field_options.index(row["المجال"].strip()))
                    sector_options = ["شرق", "غرب", "شمال", "جنوب", "وسط"]
                    new_sector = st.selectbox("القطاع", sector_options, index=sector_options.index(row["القطاع"].strip()))
                    new_sch1 = st.text_input("مدرسة1", value=row.get("مدرسة1", ""))
                    new_sch2 = st.text_input("مدرسة2", value=row.get("مدرسة2", ""))
                    new_sch3 = st.text_input("مدرسة3", value=row.get("مدرسة3", ""))
                    save_btn = st.form_submit_button("💾 حفظ التعديلات")
                    if save_btn:
                        st.session_state.supervisors_data.loc[selected_index] = {
                            "المشرف": new_name,
                            "رقم الهوية": new_id,
                            "الجنس": new_gender,
                            "المجال": new_field,
                            "القطاع": new_sector,
                            "مدرسة1": new_sch1,
                            "مدرسة2": new_sch2,
                            "مدرسة3": new_sch3
                        }
                        st.success("✅ تم تحديث البيانات")
                    if save_btn:
                        st.session_state.supervisors_data.loc[selected_index] = {
                            "المشرف": new_name,
                            "رقم الهوية": new_id,
                            "الجنس": new_gender,
                            "المجال": new_field,
                            "القطاع": new_sector,
                            "مدرسة1": new_sch1,
                            "مدرسة2": new_sch2,
                            "مدرسة3": new_sch3
                        }
                        st.success("✅ تم تحديث البيانات")

# --- تبويب المدارس ---
with tabs[1]:
    st.header("🏫 نموذج بيانات المدرسة")
    with st.form("school_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            name = st.text_input("اسم المدرسة")
            edu_num = st.text_input("الرقم الوزاري")
            gender = st.selectbox("جنس المدرسة", ["بنين", "بنات"])
        with col2:
            stage = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"])
            sector = st.selectbox("القطاع", ["شرق", "غرب", "شمال", "جنوب", "وسط"])
        with col3:
            f1 = st.selectbox("المجال1", ["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"])
            f2 = st.selectbox("المجال2", ["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"])
            f3 = st.selectbox("المجال3", ["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"])
            f4 = st.selectbox("المجال4", ["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"])
        submitted = st.form_submit_button("➕ إضافة المدرسة")
        if submitted and name and edu_num:
            st.session_state.schools_data = pd.concat([st.session_state.schools_data, pd.DataFrame([{
                "المدرسة": name,
                "الرقم الوزاري": edu_num,
                "الجنس": gender,
                "المرحلة": stage,
                "القطاع": sector,
                "المجال1": f1,
                "المجال2": f2,
                "المجال3": f3,
                "المجال4": f4
            }])], ignore_index=True)
            st.success("✅ تم إضافة المدرسة بنجاح")

    st.subheader("🔍 بحث عن مدرسة")
    col_search_sch, col_btn_sch = st.columns([3, 1])
    with col_search_sch:
        st.session_state.school_search_term = st.text_input("أدخل اسم المدرسة للبحث", value=st.session_state.school_search_term)
    with col_btn_sch:
        if st.button("🔍 بحث", key="search_school"):
            filtered_schools = st.session_state.schools_data[
                st.session_state.schools_data["المدرسة"].str.contains(st.session_state.school_search_term, na=False)
            ]
        else:
            filtered_schools = st.session_state.schools_data.copy()

    st.dataframe(filtered_schools, use_container_width=True)

    if not filtered_schools.empty:
        st.markdown("### ✏️ تعديل أو حذف مدرسة")
        selected_index = st.selectbox("اختر المدرسة", filtered_schools.index.tolist(), format_func=lambda i: filtered_schools.at[i, "المدرسة"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ حذف المدرسة"):
                st.session_state.schools_data.drop(index=selected_index, inplace=True)
                st.session_state.schools_data.reset_index(drop=True, inplace=True)
                st.success("✅ تم حذف المدرسة بنجاح")
        with col2:
            if st.button("✏️ تعديل المدرسة"):
                row = filtered_schools.loc[selected_index]
                with st.form("edit_school_form"):
                    new_name = st.text_input("اسم المدرسة", value=row["المدرسة"])
                    new_num = st.text_input("الرقم الوزاري", value=row["الرقم الوزاري"])
                    new_gender = st.selectbox("الجنس", ["بنين", "بنات"], index=["بنين", "بنات"].index(row["الجنس"]))
                    new_stage = st.selectbox("المرحلة", ["ابتدائي", "متوسط", "ثانوي"], index=["ابتدائي", "متوسط", "ثانوي"].index(row["المرحلة"]))
                    new_sector = st.selectbox("القطاع", ["شرق", "غرب", "شمال", "جنوب", "وسط"], index=["شرق", "غرب", "شمال", "جنوب", "وسط"].index(row["القطاع"]))
                    new_f1 = st.selectbox("المجال1", ["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"], index=["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"].index(row.get("المجال1", "")))
                    new_f2 = st.selectbox("المجال2", ["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"], index=["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"].index(row.get("المجال2", "")))
                    new_f3 = st.selectbox("المجال3", ["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"], index=["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"].index(row.get("المجال3", "")))
                    new_f4 = st.selectbox("المجال4", ["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"], index=["", "نواتج التعلم", "الرياضيات", "العلوم", "الصفوف الأولية", "الصفوف العليا"].index(row.get("المجال4", "")))
                    save_btn = st.form_submit_button("💾 حفظ التعديلات")
                    if save_btn:
                        st.session_state.schools_data.loc[selected_index] = {
                            "المدرسة": new_name,
                            "الرقم الوزاري": new_num,
                            "الجنس": new_gender,
                            "المرحلة": new_stage,
                            "القطاع": new_sector,
                            "المجال1": new_f1,
                            "المجال2": new_f2,
                            "المجال3": new_f3,
                            "المجال4": new_f4
                        }
                        st.success("✅ تم تحديث بيانات المدرسة")

# --- تبويب الحفظ ---
with tabs[2]:
    st.header("📤 حفظ البيانات كملف Excel")
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        st.session_state.supervisors_data.to_excel(writer, sheet_name="بيانات المشرفين", index=False)
        st.session_state.schools_data.to_excel(writer, sheet_name="بيانات المدارس", index=False)
    output.seek(0)
    st.download_button(
        label="⬇️ تحميل الملف الناتج",
        data=output,
        file_name="قالب بيانات التوزيع.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
