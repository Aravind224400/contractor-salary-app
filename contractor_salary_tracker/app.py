import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ----------------------------------------------------
# Streamlit Config
# ----------------------------------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# ----------------------------------------------------
# Database Setup
# ----------------------------------------------------
def get_connection():
    conn = sqlite3.connect("data.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS workers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    category TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pay_date TEXT,
                    worker TEXT,
                    category TEXT,
                    salary REAL,
                    notes TEXT)''')
    conn.commit()
    return conn

conn = get_connection()

# ----------------------------------------------------
# Utility Functions
# ----------------------------------------------------
def safe_rerun():
    """Safe rerun for all Streamlit versions."""
    try:
        st.rerun()
    except Exception:
        pass  # ignore rerun in restricted environments

def generate_pdf(worker, salary, note, pay_date):
    filename = f"SalarySlip_{worker}_{pay_date}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(200, 800, "Salary Slip")

    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Date: {pay_date}")
    c.drawString(100, 720, f"Worker: {worker}")
    c.drawString(100, 690, f"Salary: ₹{salary}")
    c.drawString(100, 660, f"Notes: {note}")

    c.line(100, 600, 400, 600)
    c.drawString(100, 580, "Signature: _____________________")
    c.save()
    return filename

def load_workers():
    return pd.read_sql("SELECT * FROM workers", conn)

def load_records():
    return pd.read_sql("SELECT * FROM records", conn)

# ----------------------------------------------------
# Authentication
# ----------------------------------------------------
ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "admin123")
VIEW_PASS = st.secrets.get("VIEW_PASSWORD", "view123")

if "mode" not in st.session_state:
    st.session_state["mode"] = None
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ----------------------------------------------------
# Login UI
# ----------------------------------------------------
if not st.session_state["logged_in"]:
    st.title("🏗 Contractor Salary Tracker")
    mode = st.radio("Login as", ["Admin", "Viewer"])
    password = st.text_input("Enter Password", type="password")
    if st.button("🔑 Login"):
        if (mode == "Admin" and password == ADMIN_PASS) or (mode == "Viewer" and password == VIEW_PASS):
            st.session_state["logged_in"] = True
            st.session_state["mode"] = mode
            st.success(f"✅ Logged in as {mode}")
            safe_rerun()
        else:
            st.error("❌ Incorrect password.")
    st.stop()

# ----------------------------------------------------
# After Login
# ----------------------------------------------------
mode = st.session_state["mode"]
st.sidebar.success(f"Logged in as {mode}")
if st.sidebar.button("🚪 Logout"):
    st.session_state["logged_in"] = False
    safe_rerun()

tabs = st.tabs(["📅 View Records", "➕ Add Record", "👷 Manage Workers"])

# ----------------------------------------------------
# Tab 1: View Records
# ----------------------------------------------------
with tabs[0]:
    st.subheader("📅 All Payment Records")
    records = load_records()

    if records.empty:
        st.info("No records found yet.")
    else:
        workers = load_workers()
        col1, col2 = st.columns(2)
        with col1:
            worker_filter = st.selectbox("Filter by Worker", ["All"] + workers["name"].tolist())
        with col2:
            date_filter = st.date_input("Filter by Date", value=None)

        filtered = records.copy()
        if worker_filter != "All":
            filtered = filtered[filtered["worker"] == worker_filter]
        if date_filter:
            filtered = filtered[filtered["pay_date"] == date_filter.strftime("%Y-%m-%d")]

        st.dataframe(filtered)

        if mode == "Admin":
            st.write("### ✏️ Edit Records")
            record_ids = filtered["id"].tolist()
            if record_ids:
                selected_id = st.selectbox("Select Record ID to Edit", record_ids)
                record = filtered[filtered["id"] == selected_id].iloc[0]

                new_salary = st.number_input("Edit Salary", value=float(record["salary"]))
                new_notes = st.text_area("Edit Notes", value=record["notes"])
                if st.button("💾 Update Record"):
                    conn.execute("UPDATE records SET salary=?, notes=? WHERE id=?", (new_salary, new_notes, selected_id))
                    conn.commit()
                    st.success("Record updated successfully!")
                    safe_rerun()

# ----------------------------------------------------
# Tab 2: Add Record
# ----------------------------------------------------
with tabs[1]:
    if mode != "Admin":
        st.warning("Only Admin can add records.")
    else:
        st.subheader("➕ Add New Salary Record")
        workers = load_workers()

        if workers.empty:
            st.warning("No workers available. Please add workers first.")
        else:
            with st.form("add_record_form"):
                pay_date = st.date_input("Payment Date", value=date.today())
                worker = st.selectbox("Select Worker", workers["name"].tolist())
                category = workers.loc[workers["name"] == worker, "category"].values[0]
                salary = st.number_input("Salary Amount (₹)", min_value=0.0)
                notes = st.text_area("Notes (Work done, site, etc.)")
                submit = st.form_submit_button("💾 Add Record")

                if submit:
                    conn.execute(
                        "INSERT INTO records (pay_date, worker, category, salary, notes) VALUES (?, ?, ?, ?, ?)",
                        (pay_date.strftime("%Y-%m-%d"), worker, category, salary, notes)
                    )
                    conn.commit()
                    st.success("Record added successfully!")

                    pdf_file = generate_pdf(worker, salary, notes, pay_date.strftime("%Y-%m-%d"))
                    with open(pdf_file, "rb") as f:
                        st.download_button("⬇️ Download Salary Slip (PDF)", f, file_name=pdf_file)

# ----------------------------------------------------
# Tab 3: Worker Management
# ----------------------------------------------------
with tabs[2]:
    st.subheader("👷 Worker Management")
    if mode != "Admin":
        st.warning("Only Admin can manage workers.")
    else:
        with st.form("worker_form"):
            name = st.text_input("Worker Name")
            category = st.selectbox("Category", ["Mason", "Painter", "Helper", "Electrician", "Other"])
            add_btn = st.form_submit_button("Add Worker")

            if add_btn and name:
                try:
                    conn.execute("INSERT INTO workers (name, category) VALUES (?, ?)", (name, category))
                    conn.commit()
                    st.success(f"Worker '{name}' added successfully!")
                except sqlite3.IntegrityError:
                    st.warning("Worker already exists.")

        st.write("### 👷 Registered Workers")
        st.dataframe(load_workers())
