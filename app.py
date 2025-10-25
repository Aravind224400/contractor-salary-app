import streamlit as st
from datetime import date
from supabase import create_client, Client
import pandas as pd
import pandas as pd # Re-import pandas for clarity

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# --------------------------
# Secrets (Passwords & DB)
# --------------------------
# Make sure these 4 keys are correctly defined in your .streamlit/secrets.toml
try:
    ADMIN_PASSWORD = st.secrets["admin_password"]
    VIEWER_PASSWORD = st.secrets["viewer_password"]
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except KeyError as e:
    st.error(f"Configuration Error: Missing secret key {e}. Please check your .streamlit/secrets.toml file or Streamlit Cloud secrets.")
    st.stop() # Stop execution if secrets are missing

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------
# Helper Functions
# --------------------------
@st.cache_data(ttl=60)
def fetch_workers():
    """Fetches list of registered workers from the 'workers' table."""
    try:
        response = supabase.table("workers").select("name").execute()
        return [d["name"] for d in response.data]
    except Exception as e:
        st.error(f"Error fetching workers: {e}")
        return []

@st.cache_data(ttl=60)
def fetch_salaries():
    """Fetches all salary records from the 'salaries' table."""
    try:
        response = supabase.table("salaries").select("*").order("date", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching salaries: {e}")
        return pd.DataFrame()

def delete_session():
    """Clears the session state for logout."""
    st.session_state.clear()
    # No st.experimental_rerun() here, as clearing state forces a rerun.

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
            st.experimental_rerun() # Reruns to hide login and show tabs
        elif password == VIEWER_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.mode = "viewer"
            st.success("Viewer login successful 👀")
            st.experimental_rerun() # Reruns to hide login and show viewer content
        else:
            st.error("Incorrect password. Try again.")

# --------------------------
# Main App (After Login)
# --------------------------
if st.session_state.logged_in:
    mode = st.session_state.mode
    df = fetch_salaries() # Fetch data once after login

    # --- ADMIN INTERFACE (Tabs) ---
    if mode == "admin":
        tab1, tab2, tab3 = st.tabs(["✍️ Data Entry", "📋 View & Edit Records", "👷 Worker Registration"])
        
        # --- TAB 1: Data Entry ---
        with tab1:
            st.subheader("✍️ Add Worker Salary Record")
            
            # Fetch registered workers for suggest
            registered_workers = fetch_workers()

            with st.form("salary_form"):
                # Use st.selectbox for name suggestion
                name_select = st.selectbox("Worker Name (Select or type a new name)", 
                                    options=["--- Add New Worker ---"] + registered_workers,
                                    index=0)
                
                # If "--- Add New Worker ---" is selected, allow free text input
                if name_select == "--- Add New Worker ---":
                    name = st.text_input("Enter New Worker Name").strip()
                else:
                    name = name_select

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
            registered_workers_display = fetch_workers()
            if registered_workers_display:
                st.info(f"Currently Registered: {', '.join(registered_workers_display)}")

            with st.form("worker_registration"):
                new_worker_name = st.text_input("New Worker Name to Register").strip()
                register_submitted = st.form_submit_button("Register Worker")

            if register_submitted and new_worker_name:
                if new_worker_name in registered_workers_display:
                    st.warning(f"Worker '{new_worker_name}' is already registered.")
                else:
                    try:
                        # Attempt to insert, ensuring the 'workers' table exists with a 'name' column
                        supabase.table("workers").insert({"name": new_worker_name}).execute()
                        st.success(f"✅ Worker **{new_worker_name}** registered!")
                        st.cache_data.clear() # Clear cache to refresh the select box
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error registering worker. Check your Supabase table schema: {e}")

        # --- TAB 2: View & Edit Records (Admin) ---
        with tab2:
            st.subheader("📋 View & Edit Records")
            
            # Admin Edit Form
            if 'edit_id' not in st.session_state:
                st.session_state.edit_id = None

            if st.session_state.edit_id and not df.empty:
                try:
                    record = df[df['id'] == st.session_state.edit_id].iloc[0]
                    st.markdown(f"### ✏️ Editing Record ID: {st.session_state.edit_id}")
                    
                    with st.form("edit_form"):
                        edit_name = st.text_input("Worker Name", value=record["worker_name"])
                        # Convert Supabase string date to Python date object for date_input
                        edit_date_val = pd.to_datetime(record["date"]).date()
                        edit_date = st.date_input("Date", value=edit_date_val)
                        edit_salary = st.number_input("Salary (₹)", value=record["salary"], min_value=0.0, step=100.0)
                        # Handle potential NaN in notes
                        edit_note_val = record["notes"] if pd.notna(record["notes"]) else ""
                        edit_note = st.text_area("Note", value=edit_note_val)
                        
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
                    st.markdown("---") 
                except IndexError:
                    st.error("Record ID not found for editing.")
                    st.session_state.edit_id = None
                    st.experimental_rerun()


            if df.empty:
                st.info("No records found yet.")
            else:
                # Call shared function to handle filtering and display
                show_records(df, mode)
    
    # --- VIEWER INTERFACE (No Tabs, just records) ---
    elif mode == "viewer":
        st.subheader("📋 View Records")
        if df.empty:
            st.info("No records found yet.")
        else:
            # Call shared function to handle filtering and display
            show_records(df, mode)

    # --------------------------
    # Logout Button (Always Visible)
    # --------------------------
    st.markdown("---")
    st.button("🔒 Logout", on_click=delete_session)

# --------------------------
# Shared Viewing/Filtering Function
# --------------------------
def show_records(df, mode):
    """Handles filtering and displaying salary records for both Admin and Viewer."""
    
    # Ensure date column is datetime
    df["date"] = pd.to_datetime(df["date"])
    
    # --------------------------
    # Date Filter
    # --------------------------
    st.markdown("### 📅 Filter by Date Range")
    
    # Ensure min/max dates are valid
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

    # Apply date filter
    mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
    filtered_df = df.loc[mask].copy() # Use .copy() to avoid SettingWithCopyWarning later

    # --------------------------
    # Worker Name Filter
    # --------------------------
    st.markdown("### 🧑 Filter by Worker Name (Optional)")
    all_workers = ["All Workers"] + sorted(filtered_df["worker_name"].unique().tolist())
    selected_worker = st.selectbox("Select Worker", all_workers)

    if selected_worker != "All Workers":
        filtered_df = filtered_df[filtered_df["worker_name"] == selected_worker]
        
    # --------------------------
    # Key Metrics
    # --------------------------
    total_records = len(filtered_df)
    total_salary_paid = filtered_df["salary"].sum()
    unique_workers = filtered_df["worker_name"].nunique()

    st.markdown("### 📈 Key Metrics for Filtered Data")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Records", total_records)
    col_b.metric("Total Salary Paid", f"₹{total_salary_paid:,.2f}")
    col_c.metric("Unique Workers", unique_workers)
    
    st.markdown("---")

    # --------------------------
    # Show filtered table
    # --------------------------
    display_df = filtered_df.copy()
    display_df["date"] = display_df["date"].dt.date # Show date only
    
    # Drop the ID column for display (Admins will see buttons, Viewers won't need it)
    display_df = display_df.drop(columns=['id'])

    if mode == "admin":
        st.markdown("##### Full Records (Admin Mode - Use 'Edit/View Details' buttons below to modify notes/data)")
        
        # Display the dataframe
        st.dataframe(display_df, use_container_width=True)

        # Create separate buttons for editing linked by ID
        st.markdown("##### Action: Edit/Delete")
        
        for index, row in filtered_df.iterrows():
            col_id, col_btn_edit, col_btn_delete = st.columns([1, 2, 2])
            
            col_id.write(f"ID: **{row['id']}**")
            
            # Edit Button: Sets the edit_id in session state to show the edit form
            col_btn_edit.button("✏️ Edit/View Details", key=f"edit_btn_{row['id']}", 
                                on_click=lambda id=row['id']: st.session_state.update(edit_id=id))

            # Delete Button: Executes deletion and reruns
            if col_btn_delete.button("🗑 Delete", key=f"delete_btn_{row['id']}"):
                try:
                    supabase.table("salaries").delete().eq("id", row['id']).execute()
                    st.success(f"🗑 Record ID {row['id']} deleted.")
                    st.cache_data.clear()
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error deleting record: {e}")

    else: # Viewer Mode
        st.dataframe(display_df, use_container_width=True) 

    st.markdown("---")
    
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
    
