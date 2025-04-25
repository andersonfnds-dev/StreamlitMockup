import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from mongo_connection import get_mongo_client, get_database

st.set_page_config(layout="wide")

# Establish connection
client = get_mongo_client()
if client:
    db = get_database(client)
    if db is not None:
        st.success("Connected to MongoDB!")
        # Example: Access a collection
        collection = db["requirements"]

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

if "editing_requirement_id" not in st.session_state:
    st.session_state.editing_requirement_id = None

if "submitted_requirements" not in st.session_state:
    st.session_state.submitted_requirements = []

# --- MOCK DATA GENERATORS ---
def generate_mock_requirements(owner, start_id=1):
    return [
        {
            "ID": f"REQ-{start_id + i:03d}",
            "attributes": {
                "Interpretation": "Example of attribute value",
                "Jurisdiction": "Example of attribute value",
                "Effective Date": f"2025-04-{i+1:02d}"
            },
            "Status": "Draft",
            "Comment": "N/A",
            "Owner": owner,
        }
        for i in range(2)
    ]

def generate_mock_registries():
    return [
        {
            "id": 1,
            "name": "Registry A",
            "approval": "Not Published",
            "comments": "N/A",
            "owner": "Alice",
            "requirements": generate_mock_requirements("Alice", start_id=1),
            "submitted": False,
        },
        {
            "id": 2,
            "name": "Registry B",
            "approval": "Not Published",
            "comments": "N/A",
            "owner": "Bob",
            "requirements": generate_mock_requirements("Bob", start_id=3),
            "submitted": False,
        },
    ]

def generate_mock_submitted():
    return [
        {
            "Registry Name": "Registry A",
            "Requirement ID": "REQ-010",
            "Owner": "Alice",
            "Status": "Submitted",
            "Effective Date": "2025-04-10",
            "Jurisdiction": "Federal",
            "Interpretation": "Section 12, Article B"
        },
        {
            "Registry Name": "Registry B",
            "Requirement ID": "REQ-011",
            "Owner": "Alice",
            "Status": "Q/A Q/C",
            "Effective Date": "2025-04-11",
            "Jurisdiction": "Local",
            "Interpretation": "Updated guideline for emissions"
        }
    ]

def generate_mock_comments():
    return [
        {"Level": "Document", "Comment": "This is a document-level comment.", "Author": "Bob", "Created At": "2025-04-01"},
        {"Level": "Row", "Row ID": "row-uuid-1", "Comment": "This is a row-level comment.", "Author": "Bob", "Created At": "2025-04-02"},
        {"Level": "Cell", "Row ID": "row-uuid-1", "Attribute": "Title", "Comment": "This is a cell-level comment.", "Author": "Bob", "Created At": "2025-04-03"},
    ]

# --- LOAD MOCK DATA IF EMPTY ---
if not st.session_state.registries:
    st.session_state.registries = generate_mock_registries()

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

# --- UI SECTIONS ---
def display_comments_section():
    st.markdown("### 💬 Comments at All Levels")
    comments_df = pd.DataFrame(generate_mock_comments())
    st.dataframe(comments_df, use_container_width=True)

def display_filters():
    st.markdown("### Filters and Actions")
    col1, col2, col3, col4, = st.columns(4)
    with col1:
        st.text_input("🔍 Type Ahead Filter - Search Bar", placeholder="Search requirements...")
    with col2:
        st.selectbox("Files Uploaded", options=[r["name"] for r in st.session_state.registries])
    with col3:
        st.selectbox("Country / Region", options=["All", "USA", "Canada", "Germany"])
    with col4:
        st.selectbox("Status", options=["In QA/QC", "Waiting for Approval", "Not Submitted"])

    st.button("❌ Delete Entire File")

def flatten_requirements():
    flat_data = []
    for reg in st.session_state.registries:
        for req in reg["requirements"]:
            flat = {
                "Registry Name": reg["name"],
                "Requirement ID": req["ID"],
                "Owner": req["Owner"],
                "Status": req.get("Status", ""),
                "Comment": req.get("Comment", ""),
            }
            flat.update(req.get("attributes", {}))
            flat_data.append(flat)
    return pd.DataFrame(flat_data)

def display_requirements_table():
    st.markdown("### Requirements Table")
    df = flatten_requirements()
    go = GridOptionsBuilder.from_dataframe(df)
    go.configure_selection("single", use_checkbox=True)
    go.configure_default_column(editable=False)
    response = AgGrid(df, gridOptions=go.build(), update_mode=GridUpdateMode.SELECTION_CHANGED, height=300)
    return response.get("selected_rows")

def display_edit_form(selected_req):
    st.markdown(f"**Editing Requirement ID:** {selected_req['ID']}")
    st.text_input("ID", value=selected_req["ID"], disabled=True)
    attributes = selected_req.get("attributes", {})
    for key, val in attributes.items():
        attributes[key] = st.text_input(key, value=val)
    st.text_area("Comment", value=selected_req.get("Comment", ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Changes"):
            st.success("Changes saved successfully!")
            st.session_state.editing_requirement_id = None
            st.rerun()
    with col2:
        if st.button("🔙 Return"):
            st.session_state.editing_requirement_id = None
            st.rerun()

# --- MAIN LOGIC ---
if st.session_state.editing_requirement_id:
    registry = next((r for r in st.session_state.registries if r["id"] == st.session_state.editing_registry_id), None)
    if registry:
        display_comments_section()
        display_filters()
        selected_rows = display_requirements_table()
        if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
            selected = selected_rows.iloc[0]
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Submit Selected for Approval"):
                    st.success(f"Requirement {selected['Requirement ID']} submitted successfully!")
            with col2:
                if st.button("📎 Clone Requirement"):
                    st.success(f"Requirement {selected['Requirement ID']} cloned successfully!")
        selected_req = next((r for r in registry["requirements"] if r["ID"] == st.session_state.editing_requirement_id), None)
        if selected_req:
            display_edit_form(selected_req)
        else:
            st.error("Requirement not found.")
else:
    st.subheader("📑 All Draft Requirements (Not submitted)")
    df_all = flatten_requirements()
    go = GridOptionsBuilder.from_dataframe(df_all)
    go.configure_selection("single")
    go.configure_default_column(editable=False)
    response = AgGrid(df_all, gridOptions=go.build(), update_mode=GridUpdateMode.SELECTION_CHANGED, height=400)
    selected_rows = response.get("selected_rows")

    if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
        selected = selected_rows.iloc[0]
        st.markdown(f"**Selected Requirement:** {selected['Requirement ID']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Edit Requirement"):
                st.session_state.editing_registry_id = next(
                    (r["id"] for r in st.session_state.registries if r["name"] == selected["Registry Name"]), None
                )
                st.session_state.editing_requirement_id = selected["Requirement ID"]
                st.rerun()
        with col2:
            if st.button("📤 Submit Requirement"):
                st.success(f"✅ Submitted requirement #{selected['Requirement ID']}")
                st.rerun()
    else:
        st.info("Select a requirement from the table to edit or submit.")

    st.subheader("✅ Submitted Requirements")
    if st.button("🔄 Load Sample Submitted"):
        st.session_state.submitted_requirements = generate_mock_submitted()
        st.rerun()

    if st.session_state.submitted_requirements:
        df_sub = pd.DataFrame(st.session_state.submitted_requirements)
        go = GridOptionsBuilder.from_dataframe(df_sub)
        go.configure_default_column(editable=False, sortable=True, filter=True)
        AgGrid(df_sub, gridOptions=go.build(), update_mode=GridUpdateMode.NO_UPDATE, height=350)
    else:
        st.info("No submitted requirements available.")
