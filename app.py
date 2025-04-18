import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
from datetime import datetime

 
 
st.title("File Upload")

file = st.file_uploader("Choose your file", type=["csv", "xlsx"])

if file is not None:
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
        else:
            st.warning("Not supported format.")
        
        st.subheader("📊 Current Registry Data")
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error on reading file {e}")
        # st.write("Data Preview:")
        # st.dataframe(df)
        # st.subheader("📊 Current Registry Data")
        # st.dataframe(df, use_container_width=True)


#file_uploader(file)
st.title("🧾 Registry Review & Approval Interface")
  
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
            st.success(f"Row-level comment saved for {row['ID']}.")
 
    st.subheader("✏️ Optional: Cell-Level Comment (Prototype)")
    with st.expander("🧪 Cell-Level Commenting (Experimental)"):
        selected_country = st.selectbox("Select Row", df["ID"])
        selected_column = st.selectbox("Select Column", df.columns)
        cell_comment = st.text_area(f"Comment for cell [{selected_country}] / [{selected_column}]:")
        if st.button("Save Cell Comment"):
            st.success("Cell-level comment saved.")
 
 
if "data" not in st.session_state:
    st.session_state["data"] = pd.DataFrame(columns=[
        "ID", "Name", "Registry Data", "QA/QC User", "QA/QC Status", "Comments"
    ])


# -------------------------

# Add or Edit Registry 


# QA/QC Assignment 
st.title("QA/QC Step")

for idx, row in st.session_state["data"].iterrows():
    with st.expander(f"🔍 {row['ID']} - {row['Name']}"):
        qa_user = st.text_input(f"Assign QA/QC User for {row['ID']}", key=f"user_{idx}")
        status = st.selectbox(f"Status", ["Pending", "Reviewed", "Approved"], key=f"status_{idx}")
        comment = st.text_area("Add Comment", key=f"comment_{idx}")

        if st.button(f"Update {row['ID']}", key=f"update_{idx}"):
            st.session_state["data"].at[idx, "QA/QC User"] = qa_user
            st.session_state["data"].at[idx, "QA/QC Status"] = status
            if comment:
                st.session_state["data"].at[idx, "Comments"].append({
                    "timestamp": datetime.now(),
                    "comment": comment
                })
            st.success("Updated!")

# Report Output 
st.subheader("📝 Report & Comments")

for idx, row in st.session_state["data"].iterrows():
    with st.expander(f"📄 {row['ID']} - Comments Summary"):
        st.write(f"**Name**: {row['Name']}")
        st.write(f"**QA/QC User**: {row['QA/QC User']}")
        st.write(f"**Status**: {row['QA/QC Status']}")
        st.write("**Comments:**")
        if row["Comments"]:
            for comment in row["Comments"]:
                st.markdown(f"- `{comment['timestamp']}`: {comment['comment']}")
        else:
            st.write("No comments yet.")

# Optional: Download as CSV
show_comments = st.button("Show Comments")
if show_comments:
    st.write(f"Document comment: {doc_comment}")
    st.write(f"Row comment: {row_comment}")
    st.write(f"Cell Coment: {cell_comment}")
    comment_df = pd.DataFrame([{'Document': doc_comment, 'Row': row_comment, 'Cell':cell_comment}])
    st.dataframe(comment_df)


    st.download_button("Download Full Report", comment_df.to_csv(index=False), file_name="report.csv")