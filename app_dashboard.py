import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("📊 Interactive Dashboard for Visit Plan Analysis")

uploaded_file = st.file_uploader("📥 Upload the distribution plan Excel file", type=["xlsx"])

if uploaded_file:
    try:
        distribution_df = pd.read_excel(uploaded_file, sheet_name="خطة المشرفين")

        st.header("Filters")
        col1, col2, col3 = st.columns(3)

        with col1:
            supervisors = ['All'] + sorted(distribution_df['المشرف'].unique())
            selected_supervisor = st.selectbox("Filter by Supervisor", supervisors)

        with col2:
            schools = ['All'] + sorted(distribution_df['المدرسة'].unique())
            selected_school = st.selectbox("Filter by School", schools)

        with col3:
            sectors = ['All'] + sorted(distribution_df['القطاع'].unique())
            selected_sector = st.selectbox("Filter by Sector", sectors)

        # Apply filters
        filtered_df = distribution_df.copy()
        if selected_supervisor != 'All':
            filtered_df = filtered_df[filtered_df['المشرف'] == selected_supervisor]
        if selected_school != 'All':
            filtered_df = filtered_df[filtered_df['المدرسة'] == selected_school]
        if selected_sector != 'All':
            filtered_df = filtered_df[filtered_df['القطاع'] == selected_sector]

        st.header("Visit Plan")
        st.dataframe(filtered_df)

        st.header("Statistics")

        # Visits per supervisor
        supervisor_visits = filtered_df['المشرف'].value_counts().reset_index()
        supervisor_visits.columns = ['Supervisor', 'Number of Visits']
        st.bar_chart(supervisor_visits.set_index('Supervisor'))

        # Uncovered areas (example, needs data from the original file)
        try:
            uncovered_df = pd.read_excel(uploaded_file, sheet_name="المدارس الناقصة فقط")
            st.header("Uncovered Areas")
            st.dataframe(uncovered_df)
        except Exception as e:
            st.warning(f"Could not load 'المدارس الناقصة فقط' sheet: {e}")

    except Exception as e:
        st.error(f"An error occurred: {e}")
