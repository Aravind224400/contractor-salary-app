import streamlit as st
import pandas as pd
import sqlite3
import os
import io
from datetime import date

# ------------------------------------------------------------
# STREAMLIT CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# ------------------------------------------------------------
# DATABASE SETUP (PERMANENT AND SAFE)
# ------------------------------------------------------------
DATA_DIR = os.path.join(os.getcwd(), "data_storage")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "data.db")

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute("""
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    category TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    worker TEXT,
    category TEXT,
    hours REAL,
    salary REAL,
    notes TEXT
)
""")

conn.commit()

# ------------------------------------------------------------
# LOGIN SYSTEM
# ------------------------------------------------------------
ADMIN_PASSWORD = "admin123"
VIEW_PASSWORD = "view123"

mode = st.sidebar.radio("Login as", ["Admin", "Viewer"])
password = st.sidebar.text_input("Enter Password", type="password")
login_btn = st.sidebar.button("🔓 Login")

# ------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------
def load_workers():
    return pd.read_sql("SELECT * FROM workers", conn)

def load_records():
    return pd.read_sql("SELECT * FROM records", conn)

def add_worker(name, category):
    try:
        c.execute("INSERT INTO workers (name, category) VALUES (?, ?)", (name, category))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def add_record(date_str, worker, category, hours, salary, notes):
    c.execute(
        "INSERT INTO records (date, worker, category, hours, salary, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (date_str, worker, category, hours, salary, notes),
    )
    conn.commit()

def update_record(record_id, date_str, worker, category, hours, salary, notes):
    c.execute("""
        UPDATE records
        SET date=?, worker=?, category=?, hours=?, salary=?, notes=?
        WHERE id=?
    """, (date_str, worker, category, hours, salary, notes, record_id))
    conn.commit()

def delete_record(record_id):
    c.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.commit()

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# ------------------------------------------------------------
# MAIN APP
# ------------------------------------------------------------
if login_btn:
    if (mode == "Admin" and password == ADMIN_PASSWORD) or (mode == "Viewer" and password == VIEW_PASSWORD):
        st.success(f"✅ Logged in as {mode}")

        tab1, tab2, tab3 = st.tabs(["📋 View Records", "➕ Add Record", "👷 Manage Workers"])

        # --------------------------------------------------------
        # TAB 1: VIEW & EDIT RECORDS
        # --------------------------------------------------------
        with tab1:
            st.subheader("📋 All Records")

            df = load_records()
            if df.empty:
                st.info("No records yet.")
            else:
                st.dataframe(df)

                if mode == "Admin":
                    st.write("### ✏️ Edit or Delete Records")
                    record_id = st.selectbox("Select Record ID", df["id"].tolist())

                    record = df[df["id"] == record_id].iloc[0]

                    with st.form("edit_form"):
                        date_str = st.date_input("Date", pd.to_datetime(record["date"])).strftime("%Y-%m-%d")
                        worker = st.text_input("Worker", record["worker"])
                        category = st.text_input("Category", record["category"])
                        hours = st.number_input("Hours", value=float(record["hours"]))
                        salary = st.number_input("Salary", value=float(record["salary"]))
                        notes = st.text_area("Notes", record["notes"])
                        save_btn = st.form_submit_button("💾 Update Record")
                        delete_btn = st.form_submit_button("🗑 Delete Record")

                    if save_btn:
                        update_record(record_id, date_str, worker, category, hours, salary, notes)
                        st.success("✅ Record updated successfully!")
                        st.rerun()

                    if delete_btn:
                        delete_record(record_id)
                        st.warning("⚠️ Record deleted.")
                        st.rerun()

                # Download section
                excel_data = to_excel(df)
                st.download_button(
                    "⬇️ Download All Records (Excel)",
                    excel_data,
                    "salary_records.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

        # --------------------------------------------------------
        # TAB 2: ADD RECORD
        # --------------------------------------------------------
        with tab2:
            st.subheader("➕ Add New Record")

            workers_df = load_workers()
            workers_list = workers_df["name"].tolist() if not workers_df.empty else []

            with st.form("add_record_form"):
                today = date.today()
                date_str = st.date_input("Date", today).strftime("%Y-%m-%d")
                worker = st.selectbox("Select Worker", workers_list)
                if worker:
                    cat = workers_df.loc[workers_df["name"] == worker, "category"].values[0]
                else:
                    cat = ""
                hours = st.number_input("Hours Worked", min_value=0.0)
                salary = st.number_input("Salary (₹)", min_value=0.0)
                notes = st.text_area("Notes (Work details, site, etc.)")
                add_btn = st.form_submit_button("💾 Add Record")

            if add_btn:
                if worker:
                    add_record(date_str, worker, cat, hours, salary, notes)
                    st.success("✅ Record added successfully!")
                else:
                    st.warning("Please select a worker.")

        # --------------------------------------------------------
        # TAB 3: WORKER MANAGEMENT
        # --------------------------------------------------------
        with tab3:
            st.subheader("👷 Worker Management")

            with st.form("worker_form"):
                name = st.text_input("Worker Name")
                category = st.selectbox("Category", ["Mason", "Painter", "Helper", "Electrician", "Other"])
                submit_worker = st.form_submit_button("Add Worker")

            if submit_worker:
                if add_worker(name, category):
                    st.success(f"✅ Worker '{name}' added successfully!")
                else:
                    st.warning("⚠️ Worker already exists!")

            st.write("### Registered Workers")
            st.dataframe(load_workers())

    else:
        st.error("❌ Invalid password.")
else:
    st.info("👈 Please log in using the sidebar to continue.")
