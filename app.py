import streamlit as st
from datetime import date
from supabase import create_client, Client
import pandas as pd

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# --------------------------
# Secrets (Passwords & DB)
# --------------------------
ADMIN_PASSWORD = st.secrets["admin_password"]
VIEWER_PASSWORD = st.secrets["viewer_password"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------
# Helper Functions (New)
# --------------------------
@st.cache_data(ttl=60)
def fetch_workers():
    """Fetches list of registered workers."""
    response = supabase.table("workers").select("name").execute()
    return [d["name"] for d in response.data]

@st.cache_data(ttl=60)
def fetch_salaries():
    """Fetches all salary records."""
    response = supabase.table("salaries").select("*").order("date", desc=True).execute()
    return pd.DataFrame(response.data)

def delete_session():
    """Clears the session state for logout."""
    st.session_state.clear()
    st.experimental_rerun()

# --------------------------
# Login
# --------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.mode = None

st.title("🏗 Contractor Salary Tracker")

if not st.session_state.logged_in:
    with st.form("login_form"):
        password = st.text_input("Enter Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if password == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.mode = "admin"
            st.success("Admin login successful ✅")
            st.experimental_rerun()
        elif password == VIEWER_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.mode = "viewer"
            st.success("Viewer login successful 👀")
            st.experimental_rerun()
        else:
            st.error("Incorrect password. Try again.")

# --------------------------
# Main App (After Login)
# --------------------------
if st.session_state.logged_in:
    mode = st.session_state.mode

    # --- Worker Registration & Entry (Admin Only) ---
    if mode == "admin":
        tab1, tab2, tab3 = st.tabs(["✍️ Data Entry", "📋 View & Edit Records", "👷 Worker Registration"])
        
        # --- TAB 1: Data Entry ---
        with tab1:
            st.subheader("✍️ Add Worker Salary Record")
            
            # Fetch registered workers for suggest
            registered_workers = fetch_workers()

            with st.form("salary_form"):
                # Use st.selectbox for name suggestion
                name = st.selectbox("Worker Name (Select or type a new name)", 
                                    options=["--- Add New Worker ---"] + registered_workers,
                                    index=0)
                
                # If "--- Add New Worker ---" is selected, allow free text input
                if name == "--- Add New Worker ---":
                    name = st.text_input("Enter New Worker Name")

                work_date = st.date_input("Date", date.today())
                salary = st.number_input("Salary (₹)", min_value=0.0, step=100.0)
                note = st.text_area("Note (optional)")
                submitted = st.form_submit_button("Save Record")

            if submitted and name and name != "--- Add New Worker ---":
                data = {"date": str(work_date), "worker_name": name, "salary": salary, "notes": note}
                supabase.table("salaries").insert(data).execute()
                st.success(f"✅ Record for **{name}** saved permanently!")
                st.cache_data.clear() # Clear cache to refresh data in other tabs
                st.experimental_rerun()

        # --- TAB 3: Worker Registration ---
        with tab3:
            st.subheader("👷 Register New Worker")
            with st.form("worker_registration"):
                new_worker_name = st.text_input("New Worker Name to Register").strip()
                register_submitted = st.form_submit_button("Register Worker")

            if register_submitted and new_worker_name:
                if new_worker_name in registered_workers:
                    st.warning(f"Worker '{new_worker_name}' is already registered.")
                else:
                    try:
                        supabase.table("workers").insert({"name": new_worker_name}).execute()
                        st.success(f"✅ Worker **{new_worker_name}** registered!")
                        st.cache_data.clear() # Clear cache to refresh data in other tabs
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error registering worker: {e}")

        # --- TAB 2: View & Edit Records (Admin) ---
        with tab2:
            st.subheader("📋 View & Edit Records")
            df = fetch_salaries() # Use cached function
            
            # Admin Edit Form Placeholder
            if 'edit_id' not in st.session_state:
                st.session_state.edit_id = None

            if st.session_state.edit_id:
                record = df[df['id'] == st.session_state.edit_id].iloc[0]
                st.markdown(f"### ✏️ Editing Record ID: {st.session_state.edit_id}")
                
                with st.form("edit_form"):
                    edit_name = st.text_input("Worker Name", value=record["worker_name"])
                    edit_date = st.date_input("Date", value=pd.to_datetime(record["date"]).date())
                    edit_salary = st.number_input("Salary (₹)", value=record["salary"], min_value=0.0, step=100.0)
                    edit_note = st.text_area("Note", value=record["notes"] if pd.notna(record["notes"]) else "")
                    
                    col_save, col_cancel = st.columns(2)
                    
                    if col_save.form_submit_button("Save Changes"):
                        update_data = {
                            "date": str(edit_date), 
                            "worker_name": edit_name, 
                            "salary": edit_salary, 
                            "notes": edit_note
                        }
                        supabase.table("salaries").update(update_data).eq("id", st.session_state.edit_id).execute()
                        st.success("✅ Record updated successfully!")
                        st.session_state.edit_id = None # Exit edit mode
                        st.cache_data.clear()
                        st.experimental_rerun()

                    if col_cancel.form_submit_button("Cancel"):
                        st.session_state.edit_id = None # Exit edit mode
                        st.experimental_rerun()
                st.markdown("---") # Separator for edit form
            
            # Check if dataframe is empty
            if df.empty:
                st.info("No records found yet.")
            else:
                # Proceed with filtering and viewing (shared logic)
                show_records(df, mode)
    
    # --- View Records (Viewer Only) ---
    elif mode == "viewer":
        st.subheader("📋 View Records")
        df = fetch_salaries() # Use cached function
        if df.empty:
            st.info("No records found yet.")
        else:
            show_records(df, mode)

    # --------------------------
    # Logout Button (Always Visible)
    # --------------------------
    st.markdown("---")
    st.button("🔒 Logout", on_click=delete_session)

# --------------------------
# Shared Viewing Function (New)
# --------------------------
def show_records(df, mode):
    """Handles filtering and displaying salary records."""
    
    df["date"] = pd.to_datetime(df["date"])
    
    # --------------------------
    # Date Filter (Always required for Viewer)
    # --------------------------
    st.markdown("### 📅 Filter by Date Range")
    col1, col2 = st.columns(2)
    
    # Ensure min/max dates are valid
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    
    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

    # Apply filter
    mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
    filtered_df = df.loc[mask]

    # --------------------------
    # Worker Name Filter (Optional)
    # --------------------------
    st.markdown("### 🧑 Filter by Worker Name (Optional)")
    all_workers = ["All Workers"] + sorted(filtered_df["worker_name"].unique().tolist())
    selected_worker = st.selectbox("Select Worker", all_workers)

    if selected_worker != "All Workers":
        filtered_df = filtered_df[filtered_df["worker_name"] == selected_worker]

    # --------------------------
    # Show filtered table
    # --------------------------
    # Prepare the dataframe for display
    display_df = filtered_df.copy()
    display_df["date"] = display_df["date"].dt.date # Show date only
    
    # Handle Admin Actions
    if mode == "admin":
        display_df = display_df.drop(columns=['id']) # Hide ID from main view
        
        # Add a column for the edit button
        def make_edit_button(row):
            """Creates a button to set the edit_id in session state."""
            if st.button("✏️ Edit", key=f"edit_{row['id']}"):
                st.session_state.edit_id = row['id']
                st.experimental_rerun()
        
        # This is a Streamlit hack to add buttons to a dataframe.
        # It's better to use st.data_editor in newer Streamlit versions, 
        # but this works universally with your current approach.
        col_list = display_df.columns.tolist()
        
        # Create a new column 'Action' for buttons
        st.dataframe(
            display_df,
            column_order=col_list,
            use_container_width=True,
            # Pass custom column configuration to render the button
            column_config={
                "id": st.column_config.Column("ID"),
                "worker_name": st.column_config.TextColumn("Worker Name"),
                "salary": st.column_config.NumberColumn("Salary (₹)", format="₹%f"),
                "notes": st.column_config.TextColumn("Note")
            }
        )
        
        # Render the edit buttons next to the table
        # We need a custom loop since we hid the ID column in the main dataframe
        st.markdown("##### Action: Edit Record")
        for index, row in filtered_df.iterrows():
            col_id, col_btn = st.columns([1, 10])
            col_id.write(f"ID: **{row['id']}**")
            # Use the make_edit_button helper to set the session state
            col_btn.button("✏️ Edit/View Details", key=f"edit_btn_{row['id']}", on_click=lambda id=row['id']: st.session_state.update(edit_id=id))


    else: # Viewer Mode
        st.dataframe(display_df.drop(columns=['id']), use_container_width=True) # Hide ID from viewer

    # --------------------------
    # Total Salary Summary
    # --------------------------
    st.markdown("### 💰 Total Salary per Worker")
    summary = filtered_df.groupby("worker_name")["salary"].sum().reset_index()
    summary = summary.rename(columns={"worker_name": "Worker", "salary": "Total Salary (₹)"})

    # Show grand total
    total_sum = summary["Total Salary (₹)"].sum()
    st.markdown(f"**🧾 Grand Total Paid in this Filtered View: ₹{total_sum:,.2f}**")

    # Show table
    st.dataframe(summary)

    # --------------------------
    # Download Buttons
    # --------------------------
    st.download_button("💾 Download Filtered CSV", filtered_df.to_csv(index=False), "filtered_salaries.csv")
    st.download_button("💾 Download Summary CSV", summary.to_csv(index=False), "salary_summary.csv")
    

