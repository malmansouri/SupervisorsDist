import streamlit as st
import pandas as pd

st.set_page_config(page_title="Manual Override", layout="wide")

st.title("✏️ Manual Override and Conflict Resolution")

uploaded_file = st.file_uploader("📥 Upload the distribution plan Excel file", type=["xlsx"])

if uploaded_file:
    try:
        distribution_df = pd.read_excel(uploaded_file, sheet_name="خطة المشرفين")

        if 'edited_df' not in st.session_state:
            st.session_state.edited_df = distribution_df.copy()

        st.header("Edit Visit Plan")

        edited_df = st.data_editor(st.session_state.edited_df, num_rows="dynamic")

        st.session_state.edited_df = edited_df

        # Conflict Detection
        conflicts = edited_df[edited_df.duplicated(['اليوم', 'المشرف'], keep=False)]

        if not conflicts.empty:
            st.header("Conflicts Detected")
            st.warning("The following supervisors are assigned to multiple schools on the same day:")
            st.dataframe(conflicts)
        else:
            st.success("No conflicts detected.")

        if st.button("Save Changes"):
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                st.session_state.edited_df.to_excel(writer, sheet_name="خطة المشرفين", index=False)
            output.seek(0)
            st.download_button(
                label="📥 Download Modified Plan",
                data=output,
                file_name="modified_plan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"An error occurred: {e}")
