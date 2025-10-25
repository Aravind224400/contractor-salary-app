import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# -------------------------------------
# DATABASE CONNECTION
# -------------------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
c.execute('''
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    category TEXT
)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pay_date TEXT,
    worker TEXT,
    category TEXT,
    salary REAL,
    notes TEXT
)
''')

conn.commit()

# -------------------------------------
# APP CONFIG
# -------------------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="💰", layout="wide")
st.title("🏗 Contractor Salary Tracker")

# -------------------------------------
# LOGIN SYSTEM
# -------------------------------------
ADMIN_PASS = "admin123"
VIEW_PASS = "view123"

if "role" not in st.session_state:
    st.session_state.role = None

if not st.session_state.role:
    st.subheader("🔐 Login")

    password = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if password == ADMIN_PASS:
            st.session_state.role = "admin"
            st.success("Logged in as Admin ✅")
            st.experimental_rerun()
        elif password == VIEW_PASS:
            st.session_state.role = "viewer"
            st.success("Logged in as Viewer 👁️")
            st.experimental_rerun()
        else:
            st.error("Incorrect password ❌")
    st.stop()

# -------------------------------------
# ADMIN FUNCTIONS
# -------------------------------------
def add_worker(name, category):
    try:
        c.execute("INSERT INTO workers (name, category) VALUES (?, ?)", (name, category))
        conn.commit()
        st.success(f"Worker '{name}' added successfully!")
    except sqlite3.IntegrityError:
        st.warning("Worker already exists.")

def get_workers():
    c.execute("SELECT name, category FROM workers")
    return c.fetchall()

def add_record(pay_date, worker, category, salary, notes):
    c.execute("INSERT INTO records (pay_date, worker, category, salary, notes) VALUES (?, ?, ?, ?, ?)",
              (pay_date, worker, category, salary, notes))
    conn.commit()
    st.success("Record added successfully!")

def get_records():
    return pd.read_sql_query("SELECT * FROM records", conn)

def update_record(record_id, pay_date, worker, category, salary, notes):
    c.execute("""
        UPDATE records 
        SET pay_date=?, worker=?, category=?, salary=?, notes=?
        WHERE id=?
    """, (pay_date, worker, category, salary, notes, record_id))
    conn.commit()
    st.success("Record updated successfully!")

# -------------------------------------
# APP LAYOUT
# -------------------------------------
st.sidebar.header("Navigation")
menu = ["Add Worker", "Add Record", "View Records", "Edit Record", "Logout"]
choice = st.sidebar.selectbox("Select Option", menu)

# -------------------------------------
# LOGOUT
# -------------------------------------
if choice == "Logout":
    st.session_state.role = None
    st.experimental_rerun()

# -------------------------------------
# ADD WORKER
# -------------------------------------
elif choice == "Add Worker" and st.session_state.role == "admin":
    st.subheader("➕ Add New Worker")
    name = st.text_input("Worker Name")
    category = st.text_input("Category")
    if st.button("Add Worker"):
        if name and category:
            add_worker(name, category)
        else:
            st.warning("Please fill all fields")

# -------------------------------------
# ADD RECORD
# -------------------------------------
elif choice == "Add Record" and st.session_state.role == "admin":
    st.subheader("🧾 Add Salary Record")

    workers = [w[0] for w in get_workers()]
    if not workers:
        st.warning("Please add a worker first in 'Add Worker' tab.")
    else:
        pay_date = st.date_input("Date", value=date.today())
        worker = st.selectbox("Select Worker", workers)
        category = st.text_input("Category")
        salary = st.number_input("Salary", min_value=0.0)
        notes = st.text_area("Notes (optional)")
        if st.button("Add Record"):
            add_record(str(pay_date), worker, category, salary, notes)

# -------------------------------------
# VIEW RECORDS
# -------------------------------------
elif choice == "View Records":
    st.subheader("📊 View All Records")
    df = get_records()

    if df.empty:
        st.info("No records found.")
    else:
        # Filter by date range
        start = st.date_input("Start Date", value=date.today().replace(day=1))
        end = st.date_input("End Date", value=date.today())
        filtered = df[(df["pay_date"] >= str(start)) & (df["pay_date"] <= str(end))]

        st.dataframe(filtered, use_container_width=True)

# -------------------------------------
# EDIT RECORD (ADMIN ONLY)
# -------------------------------------
elif choice == "Edit Record" and st.session_state.role == "admin":
    st.subheader("✏️ Edit Salary Record")
    df = get_records()

    if df.empty:
        st.info("No records to edit.")
    else:
        record_id = st.selectbox("Select Record ID", df["id"])
        record = df[df["id"] == record_id].iloc[0]

        new_date = st.date_input("Date", value=pd.to_datetime(record["pay_date"]).date())
        new_worker = st.text_input("Worker", record["worker"])
        new_category = st.text_input("Category", record["category"])
        new_salary = st.number_input("Salary", value=record["salary"])
        new_notes = st.text_area("Notes", record["notes"])

        if st.button("Update Record"):
            update_record(record_id, str(new_date), new_worker, new_category, new_salary, new_notes)
