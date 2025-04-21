import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

st.set_page_config(layout="wide")
st.title("📋 Welcome Alice (Standard User Role)")

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.header("Filters")
    st.selectbox("Country / Region", options=["All", "Japan", "Jordan", "Oregon"])
    st.selectbox("Template", options=["All", "Template A", "Template B"])
    st.selectbox("User/Owner", options=["All", "Alice", "Bob"])
    st.selectbox("Client", options=["All", "Client A", "Client B"])
    st.selectbox("Jurisdiction", options=["All", "Federal", "Local"])
    st.text_input("Extra Filters")
    st.button("Generate / Submit")

# --- SESSION STATE INIT ---
if "registries" not in st.session_state:
    st.session_state.registries = []

if "editing_registry_id" not in st.session_state:
    st.session_state.editing_registry_id = None

# --- FILE UPLOAD ---
uploaded_files = st.file_uploader("Upload New Register(s) of Requirements (XLSX Only)", type=["xlsx"], accept_multiple_files=True)

if uploaded_files:
    for file in uploaded_files:
        try:
            df = pd.read_excel(file)
            registry_id = len(st.session_state.registries) + 1
            st.session_state.registries.append({
                "id": registry_id,
                "name": file.name.replace(".xlsx", ""),
                "approval": "Not Published",
                "comments": "N/A",
                "owner": "Alice",
                "requirements": df,
                "submitted": False  # To track public registry view
            })
        except Exception as e:
            st.error(f"❌ Failed to read {file.name}: {e}")

# --- MAIN PAGE OR EDIT MODE ---
if st.session_state.editing_registry_id is not None:
    reg = next((r for r in st.session_state.registries if r["id"] == st.session_state.editing_registry_id), None)
    if reg:
        render_edit_mode(reg)
    else:
        st.error("Registry not found.")
else:
    st.subheader("📑 All Draft Registries")

    if st.session_state.registries:
        df_main = pd.DataFrame([{
            "ID": reg["id"],
            "Registry Name": reg["name"],
            "Approval Status": reg["approval"],
            "Comments": reg["comments"],
            "Owner": reg["owner"]
        } for reg in st.session_state.registries])

        st.dataframe(df_main, use_container_width=True)

        # --- REGISTRY ACTIONS ---
        for reg in st.session_state.registries:
            with st.expander(f"🗂️ Registry #{reg['id']}: {reg['name']}"):
                col1, col2, col3 = st.columns(3)
                if col1.button("✏️ Edit", key=f"edit_{reg['id']}"):
                    st.session_state.editing_registry_id = reg["id"]
                    st.rerun()
                if col2.button("📤 Submit", key=f"submit_{reg['id']}"):
                    reg["submitted"] = True
                    reg["approval"] = "Q/A Q/C"
                    st.success(f"✅ Submitted registry #{reg['id']}")
                if col3.button("📎 Clone", key=f"clone_{reg['id']}"):
                    new_id = max([r["id"] for r in st.session_state.registries]) + 1
                    st.session_state.registries.append({
                        **reg,
                        "id": new_id,
                        "name": f"{reg['name']} (Clone)",
                        "approval": "Not Published",
                        "submitted": False
                    })
                    st.success(f"📎 Cloned registry #{reg['id']}")
                    st.rerun()
    else:
        st.info("📥 Upload XLSX files to begin.")

# --- EDIT MODE PAGE ---
def render_edit_mode(registry):
    st.header(f"✏️ Editing Registry: {registry['name']}")
    st.markdown(f"**Status:** {registry['approval']} &nbsp;&nbsp;|&nbsp;&nbsp; **Owner:** {registry['owner']}")

    # Search Bar and Filters
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    with col1:
        st.text_input("🔍 Type Ahead Filter - Search Bar", placeholder="Search requirements...", key="search_bar")
    with col2:
        st.selectbox("Files Uploaded", options=["File 1", "File 2", "File 3"], key="files_uploaded")
    with col3:
        st.selectbox("Country / Region", options=["All", "Japan", "Jordan", "Oregon"], key="country_region")
    with col4:
        st.selectbox("Status", options=["Q/A Q/C", "Waiting for Approval", "Not Submitted"], key="in_qa_qc")

    # Display Requirements Table (Non-editable)
    st.markdown("### 📋 Requirements")
    if "requirements" in registry:
        grid_options = GridOptionsBuilder.from_dataframe(registry["requirements"])
        grid_options.configure_selection("single")  # Allow single row selection
        grid_options.configure_default_column(editable=False)  # Make columns non-editable

        response = AgGrid(
            registry["requirements"],
            gridOptions=grid_options.build(),
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            fit_columns_on_grid_load=True,
            height=300,
            key="requirements_table"
        )

        # Capture selected row
        selected_rows = response.get("selected_rows")
    else:
        st.warning("No requirements data available.")

    # Process Section
    st.markdown("### ⚙️ Process")
    if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
        row = selected_rows.iloc[0]
        
         # Dynamically create text inputs for each column in the selected row
        updated_values = {}
        for key, value in row.items():
            updated_values[key] = st.text_input(f"{key}", value=value)

        # Save Button
        if st.button("✅ Save Changes"):
        # Ensure the "ID" column exists before attempting to find the row index
            if "ID" in registry["requirements"].columns:
                row_index = registry["requirements"].index[
                    registry["requirements"]["ID"] == row["ID"]
                ][0]
            
                # Update the selected row in the DataFrame
                for key, value in updated_values.items():
                    registry["requirements"].at[row_index, key] = value
                st.success("Changes saved successfully!")
            else:
                st.error("The 'ID' column is missing in the requirements DataFrame.")
    else:
        st.info("Select a row from the table to edit.")

    # Buttons for Navigation
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔙 Back to Registry List"):
            st.session_state.editing_registry_id = None
            st.rerun()
    with col2:
        if st.button("❌ Delete Entire File"):
            st.session_state.registries = [
                r for r in st.session_state.registries if r["id"] != registry["id"]
            ]
            st.success("Registry deleted successfully.")
            st.session_state.editing_registry_id = None
            st.rerun()
