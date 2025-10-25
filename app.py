import streamlit as st
from datetime import date
import pandas as pd
import psycopg2 # PostgreSQL driver
from contextlib import contextmanager
from typing import List

# --------------------------
# Config & Secrets 🔑
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

try:
    ADMIN_PASSWORD = st.secrets["admin_password"]
    VIEWER_PASSWORD = st.secrets["viewer_password"]
    
    # PostgreSQL Secrets
    DB_HOST = st.secrets["DB_HOST"]
    DB_NAME = st.secrets["DB_NAME"]
    DB_USER = st.secrets["DB_USER"]
    DB_PASSWORD = st.secrets["DB_PASSWORD"]
    DB_PORT = st.secrets["DB_PORT"]
except KeyError as e:
    st.error(f"Configuration Error: Missing secret key {e}. Please check your .streamlit/secrets.toml file.")
    st.stop() 

# --------------------------
# Database Connection Utilities 🛠️
# --------------------------
@contextmanager
def get_db_cursor():
    """Provides a connection cursor, ensuring connection is closed afterwards."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()
        yield cursor, conn
    except psycopg2.Error as e:
        st.error(f"Database Connection Error: Could not connect to PostgreSQL. Check credentials. Details: {e}")
        raise
    finally:
        if conn:
            conn.close()

# --------------------------
# Database CRUD Functions 💾
# --------------------------
@st.cache_data(ttl=60)
def fetch_workers() -> List[str]:
    """Fetches list of registered worker names."""
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute("SELECT name FROM workers;")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        st.warning("Could not fetch worker list. Check 'workers' table existence and permissions.")
        return []

@st.cache_data(ttl=60)
def fetch_salaries() -> pd.DataFrame:
    """Fetches all salary records."""
    try:
        with get_db_cursor() as (cursor, conn):
            # Columns match the schema: id, date, worker_name, salary, notes
            cursor.execute("SELECT id, date, worker_name, salary, notes FROM salaries ORDER BY date DESC;")
            columns = [desc[0] for desc in cursor.description]
            return pd.DataFrame(cursor.fetchall(), columns=columns)
    except Exception as e:
        st.warning("Could not fetch salary records. Check 'salaries' table existence and permissions.")
        return pd.DataFrame()

def insert_record(data: dict):
    """Inserts a new salary record."""
    sql = "INSERT INTO salaries (date, worker_name, salary, notes) VALUES (%s, %s, %s, %s);"
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(sql, (data['date'], data['worker_name'], data['salary'], data['notes']))
            conn.commit()
            st.cache_data.clear()
            st.success(f"✅ Record for **{data['worker_name']}** saved permanently!")
    except Exception as e:
        st.error(f"Error saving record: {e}")

def update_record(record_id: int, data: dict):
    """Updates an existing salary record."""
    sql = """
        UPDATE salaries SET 
        date = %s, worker_name = %s, salary = %s, notes = %s 
        WHERE id = %s;
    """
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(sql, (data['date'], data['worker_name'], data['salary'], data['notes'], record_id))
            conn.commit()
            st.cache_data.clear()
            st.success("✅ Record updated successfully!")
    except Exception as e:
        st.error(f"Error updating record: {e}")

def delete_record_db(record_id: int):
    """Deletes a salary record."""
    sql = "DELETE FROM salaries WHERE id = %s;"
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(sql, (record_id,))
            conn.commit()
            st.cache_data.clear()
            st.experimental_rerun()
    except Exception as e:
        st.error(f"Error deleting record: {e}")

def register_worker_db(name: str):
    """Registers a new worker."""
    sql = "INSERT INTO workers (name) VALUES (%s);"
    try:
        with get_db_cursor() as (cursor, conn):
            cursor.execute(sql, (name,))
            conn.commit()
            st.cache_data.clear()
            st.success(f"✅ Worker **{name}** registered!")
    except Exception as e:
        st.error(f"Error registering worker: {e}")

def delete_session():
    """Clears the session state for logout."""
    st.session_state.clear()
    st.experimental_rerun()

# --------------------------
# Login and Initialization 🚪
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
            st.experimental_rerun()
        elif password == VIEWER_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.mode = "viewer"
            st.experimental_rerun()
        else:
            st.error("Incorrect password. Try again.")

# --------------------------
# Main App (After Login) 🚀
# --------------------------
if st.session_state.logged_in:
    mode = st.session_state.mode
    df = fetch_salaries()

    # --- ADMIN INTERFACE (Tabs) ---
    if mode == "admin":
        tab1, tab2, tab3 = st.tabs(["✍️ Data Entry", "📋 View & Edit Records", "👷 Worker Registration"])
        
        # --- TAB 1: Data Entry ---
        with tab1:
            st.subheader("✍️ Add Worker Salary Record")
            registered_workers = fetch_workers()

            with st.form("salary_form"):
                name_select = st.selectbox("Worker Name (Select or type a new name)", 
                                    options=["--- Add New Worker ---"] + registered_workers,
                                    index=0)
                
                name = st.text_input("Enter New Worker Name").strip() if name_select == "--- Add New Worker ---" else name_select

                work_date = st.date_input("Date", date.today())
                salary = st.number_input("Salary (₹)", min_value=0.0, step=100.0)
                note = st.text_area("Note (optional)")
                submitted = st.form_submit_button("Save Record")

            if submitted and name and name != "--- Add New Worker ---":
                data = {"date": str(work_date), "worker_name": name, "salary": salary, "notes": note}
                insert_record(data)
                st.experimental_rerun()

        # --- TAB 3: Worker Registration ---
        with tab3:
            st.subheader("👷 Register New Worker")
            registered_workers_display = fetch_workers()
            if registered_workers_display:
                st.info(f"Currently Registered ({len(registered_workers_display)}): {', '.join(registered_workers_display)}")

            with st.form("worker_registration"):
                new_worker_name = st.text_input("New Worker Name to Register").strip()
                register_submitted = st.form_submit_button("Register Worker")

            if register_submitted and new_worker_name:
                if new_worker_name in registered_workers_display:
                    st.warning(f"Worker '{new_worker_name}' is already registered.")
                else:
                    register_worker_db(new_worker_name)
                    st.experimental_rerun()

        # --- TAB 2: View & Edit Records (Admin) ---
        with tab2:
            st.subheader("📋 View & Edit Records")
            
            if 'edit_id' not in st.session_state:
                st.session_state.edit_id = None

            if st.session_state.edit_id and not df.empty:
                record = df[df['id'] == st.session_state.edit_id].iloc[0]
                st.markdown(f"### ✏️ Editing Record ID: {st.session_state.edit_id}")
                
                with st.form("edit_form"):
                    edit_name = st.text_input("Worker Name", value=record["worker_name"])
                    edit_date_val = pd.to_datetime(record["date"]).date()
                    edit_date = st.date_input("Date", value=edit_date_val)
                    edit_salary = st.number_input("Salary (₹)", value=record["salary"], min_value=0.0, step=100.0)
                    edit_note_val = record["notes"] if pd.notna(record["notes"]) else ""
                    edit_note = st.text_area("Note", value=edit_note_val)
                    
                    col_save, col_cancel = st.columns(2)
                    
                    if col_save.form_submit_button("Save Changes"):
                        update_data = {"date": str(edit_date), "worker_name": edit_name, "salary": edit_salary, "notes": edit_note}
                        update_record(st.session_state.edit_id, update_data)
                        st.session_state.edit_id = None 
                        st.experimental_rerun()

                    if col_cancel.form_submit_button("Cancel"):
                        st.session_state.edit_id = None 
                        st.experimental_rerun()
                st.markdown("---") 

            if df.empty:
                st.info("No records found yet.")
            else:
                show_records(df, mode)
    
    # --- VIEWER INTERFACE (No Tabs, just records) ---
    elif mode == "viewer":
        st.subheader("📋 View Records")
        if df.empty:
            st.info("No records found yet.")
        else:
            show_records(df, mode)

    # --------------------------
    # Logout Button 🔒
    # --------------------------
    st.markdown("---")
    st.button("🔒 Logout", on_click=delete_session)

# --------------------------
# Shared Viewing/Filtering Function
# --------------------------
def show_records(df: pd.DataFrame, mode: str):
    """Handles filtering and displaying salary records for both Admin and Viewer."""
    
    df["date"] = pd.to_datetime(df["date"])
    
    # --- Filters ---
    st.markdown("### 📅 Filter by Date Range")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
    with col2:
        end_date = st.date_input("To", value=max_date, min_value=min_date, max_value=max_date)

    mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
    filtered_df = df.loc[mask].copy()

    st.markdown("### 🧑 Filter by Worker Name (Optional)")
    all_workers = ["All Workers"] + sorted(filtered_df["worker_name"].unique().tolist())
    selected_worker = st.selectbox("Select Worker", all_workers)

    if selected_worker != "All Workers":
        filtered_df = filtered_df[filtered_df["worker_name"] == selected_worker]
        
    # --- Metrics ---
    total_records = len(filtered_df)
    total_salary_paid = filtered_df["salary"].sum()
    unique_workers = filtered_df["worker_name"].nunique()

    st.markdown("### 📈 Key Metrics for Filtered Data")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Records", total_records)
    col_b.metric("Total Salary Paid", f"₹{total_salary_paid:,.2f}")
    col_c.metric("Unique Workers", unique_workers)
    st.markdown("---")

    # --- Display Table & Controls ---
    display_df = filtered_df.copy()
    display_df["date"] = display_df["date"].dt.date
    display_df = display_df.drop(columns=['id'])

    if mode == "admin":
        st.markdown("##### Full Records (Admin Mode)")
        st.dataframe(display_df, use_container_width=True)

        st.markdown("##### Action: Edit/Delete (Use buttons below)")
        
        for index, row in filtered_df.iterrows():
            col_id, col_btn_edit, col_btn_delete = st.columns([1, 2, 2])
            col_id.write(f"ID: **{row['id']}**")
            
            col_btn_edit.button("✏️ Edit/View Details", key=f"edit_btn_{row['id']}", 
                                on_click=lambda id=row['id']: st.session_state.update(edit_id=id))

            if col_btn_delete.button("🗑 Delete", key=f"delete_btn_{row['id']}"):
                delete_record_db(row['id'])

    else: # Viewer Mode
        st.dataframe(display_df, use_container_width=True) 

    st.markdown("---")
    
    # --- Summary ---
    st.markdown("### 💰 Total Salary per Worker")
    summary = filtered_df.groupby("worker_name")["salary"].sum().reset_index()
    summary = summary.rename(columns={"worker_name": "Worker", "salary": "Total Salary (₹)"})
    total_sum = summary["Total Salary (₹)"].sum()
    st.markdown(f"**🧾 Grand Total Paid in this Filtered View: ₹{total_sum:,.2f}**")
    st.dataframe(summary)

    # --- Download ---
    st.download_button("💾 Download Filtered CSV", filtered_df.to_csv(index=False), "filtered_salaries.csv")
    st.download_button("💾 Download Summary CSV", summary.to_csv(index=False), "salary_summary.csv")
