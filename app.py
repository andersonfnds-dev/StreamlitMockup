import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
 
df = pd.DataFrame({
    "Id": ["1", "2", "3"],
    "Country": ["US", "DE", "JP"],
    "Regulation": ["OSHA 1910", "ChemG 2024", "ISO-45001"],
    "Effective Date": ["2024-05-01", "2024-06-15", "2024-07-01"]
})
 
st.title("🧾 Registry Review & Approval Interface")
 
st.subheader("📊 Current Registry Data")
st.dataframe(df, use_container_width=True)
 
st.subheader("✅ Approval Decision")
 
action = st.radio("Select an action:", ["Approve", "Reprove"], horizontal=True)
 
if action == "Approve":
    st.success("✅ Document approved!")
else:
    st.warning("❌ Document marked for review. Please leave comments below.")
 
    st.markdown("---")
 
    with st.expander("💬 Document-Level Comment", expanded=True):
        doc_comment = st.text_area("Leave a comment about the overall document:")
        if st.button("Save Document Comment"):
            st.success("📄 Document-level comment saved.")
 
    st.subheader("📄 Registry Table with Row-Level Comments")
    st.write("Click on the row you want to select")
 
 
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_grid_options(domLayout='normal')
    gb.configure_selection('single')
    grid_options = gb.build()
 
    response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        height=300
    )
 
    selected_rows = response.get('selected_rows')
 
    if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
        row = selected_rows.iloc[0]
        st.write(f"Selected Row: {row.to_dict()}")
        row_comment = st.text_area("Add a row-level comment:")
        if st.button("Save Row Comment"):
            st.success(f"Row-level comment saved for {row['Country']}.")
 
    st.subheader("✏️ Optional: Cell-Level Comment (Prototype)")
    with st.expander("🧪 Cell-Level Commenting (Experimental)"):
        selected_country = st.selectbox("Select Row", df["Id"])
        selected_column = st.selectbox("Select Column", df.columns)
        cell_comment = st.text_area(f"Comment for cell [{selected_country}] / [{selected_column}]:")
        if st.button("Save Cell Comment"):
            st.success("Cell-level comment saved.")
 
 