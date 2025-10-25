import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

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
    pay_date TEXT,
    worker TEXT,
    category TEXT,
    salary REAL,
    notes TEXT
)
""")

conn.commit()

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def generate_pdf(worker, salary, note, pay_date):
    """Generate a salary slip PDF."""
    filename = f"SalarySlip_{worker}_{pay_date}.pdf"
    cpdf = canvas.Canvas(filename, pagesize=A4)
    cpdf.setFont("Helvetica-Bold", 18)
    cpdf.drawString(200, 800, "Salary Slip")

    cpdf.setFont("Helvetica", 12)
    cpdf.drawString(100, 750, f"Date: {pay_date}")
    cpdf.drawString(100, 720, f"Worker: {worker}")
    cpdf.drawString(100, 690, f"Salary: ₹{salary}")
    cpdf.drawString(100, 660, f"Notes: {note}")
    cpdf.line(100, 600, 400, 600)
    cpdf.drawString(100, 580, "Signature: _____________________")

    cpdf.save()
    return filename


# -----------------------------
# AUTHENTICATION
# -----------------------------
ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "admin123")
VIEW_PASS = st.secrets.get("VIEW_PASSWORD", "view123")

role = st.sidebar.radio("Login as", ["Admin", "Viewer"])
password = st.sidebar.text_input("Enter Password", type="password")
login = st.sidebar.button("Login")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if login:
    if (role == "Admin" and password == ADMIN_PASS) or (role == "Viewer" and password == VIEW_PASS):
        st.session_state.logged_in = True
        st.session_state.role = role
        st.success(f"✅ Logged in as {role}")
    else:
        st.error("❌ Incorrect password")

# -----------------------------
# MAIN APP
# -----------------------------
if st.session_state.get("logged_in", False):
    st.title("🏗 Contractor Salary Tracker")

    tab1, tab2, tab3, tab4 = st.tabs(["📅 Dashboard", "💵 Add Record", "👷 Manage Workers", "🔍 View Records"])

    # ======================================================
    # TAB 1: DASHBOARD
    # ======================================================
    with tab1:
        st.subheader("📅 Daily Summary")

        df = pd.read_sql("SELECT * FROM records", conn)
        if not df.empty:
            today = date.today().strftime("%Y-%m-%d")
            today_df = df[df["pay_date"] == today]

            total_today = today_df["salary"].sum()
            worker_count = today_df["worker"].nunique()

            col1, col2 = st.columns(2)
            col1.metric("Total Paid Today", f"₹{total_today}")
            col2.metric("Workers Paid", worker_count)

            st.divider()
            st.subheader("🧾 All Records Summary")
            st.dataframe(df)
        else:
            st.info("No records found yet.")

    # ======================================================
    # TAB 2: ADD RECORD (ADMIN ONLY)
    # ======================================================
    with tab2:
        if st.session_state.role == "Admin":
            st.subheader("💵 Add Salary Record")

            workers = [row[0] for row in c.execute("SELECT name FROM workers").fetchall()]

            if workers:
                with st.form("add_record_form"):
                    pay_date = st.date_input("Payment Date", value=date.today())
                    worker = st.selectbox("Select Worker", workers)
                    result = c.execute("SELECT category FROM workers WHERE name=?", (worker,)).fetchone()
                    category = result[0] if result else ""

                    salary = st.number_input("Salary Amount (₹)", min_value=0.0)
                    notes = st.text_area("Notes (optional)")

                    submitted = st.form_submit_button("Save Record")

                    if submitted:
                        c.execute(
                            "INSERT INTO records (pay_date, worker, category, salary, notes) VALUES (?, ?, ?, ?, ?)",
                            (str(pay_date), worker, category, salary, notes)
                        )
                        conn.commit()
                        st.success("✅ Record added successfully!")

                        pdf_file = generate_pdf(worker, salary, notes, str(pay_date))
                        with open(pdf_file, "rb") as f:
                            st.download_button("⬇️ Download Salary Slip (PDF)", f, file_name=pdf_file)
            else:
                st.info("No workers found. Please add a worker first in 'Manage Workers' tab.")
        else:
            st.warning("Only Admin can add salary records.")

    # ======================================================
    # TAB 3: MANAGE WORKERS (ADMIN ONLY)
    # ======================================================
    with tab3:
        if st.session_state.role == "Admin":
            st.subheader("👷 Worker Management")

            with st.form("add_worker_form"):
                name = st.text_input("Worker Name")
                category = st.selectbox("Category", ["Mason", "Painter", "Helper", "Electrician", "Other"])
                add_btn = st.form_submit_button("Add Worker")

                if add_btn and name:
                    try:
                        c.execute("INSERT INTO workers (name, category) VALUES (?, ?)", (name, category))
                        conn.commit()
                        st.success(f"✅ Worker '{name}' added successfully!")
                    except sqlite3.IntegrityError:
                        st.warning("⚠️ Worker already exists.")

            st.divider()
            st.write("### 👷 Registered Workers")
            workers_df = pd.read_sql("SELECT * FROM workers", conn)
            st.dataframe(workers_df)

            st.divider()
            delete_name = st.selectbox("Select Worker to Delete", ["None"] + workers_df["name"].tolist())
            if delete_name != "None":
                if st.button("🗑 Delete Worker"):
                    c.execute("DELETE FROM workers WHERE name=?", (delete_name,))
                    conn.commit()
                    st.warning(f"Worker '{delete_name}' deleted!")
        else:
            st.warning("Only Admin can manage workers.")

    # ======================================================
    # TAB 4: VIEW / EDIT RECORDS
    # ======================================================
    with tab4:
        st.subheader("🔍 Search and Filter Records")

        df = pd.read_sql("SELECT * FROM records", conn)

        if not df.empty:
            col1, col2 = st.columns(2)
            workers_list = ["All"] + df["worker"].unique().tolist()
            worker_filter = col1.selectbox("Select Worker", workers_list)
            date_filter = col2.date_input("Select Date (optional)")

            filtered_df = df.copy()
            if worker_filter != "All":
                filtered_df = filtered_df[filtered_df["worker"] == worker_filter]
            if date_filter:
                filtered_df = filtered_df[filtered_df["pay_date"] == str(date_filter)]

            st.dataframe(filtered_df)

            if st.session_state.role == "Admin" and not filtered_df.empty:
                edit_id = st.number_input("Enter Record ID to Edit", min_value=1, step=1)
                record = c.execute("SELECT * FROM records WHERE id=?", (edit_id,)).fetchone()
                if record:
                    with st.form("edit_record_form"):
                        new_salary = st.number_input("Update Salary", value=record[4])
                        new_notes = st.text_area("Update Notes", value=record[5])
                        update_btn = st.form_submit_button("Update Record")

                        if update_btn:
                            c.execute("UPDATE records SET salary=?, notes=? WHERE id=?", (new_salary, new_notes, edit_id))
                            conn.commit()
                            st.success("✅ Record updated successfully!")
                else:
                    st.info("Enter a valid record ID.")
        else:
            st.info("No records available to view or edit.")
else:
    st.info("Please log in to access the app.")
