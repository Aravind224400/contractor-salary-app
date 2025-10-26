import streamlit as st
import sqlite3
import pandas as pd
import os
import io
from datetime import date

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="💰", layout="wide")

st.title("🏗 Contractor Salary Tracker")

# ------------------------------------------------------------
# DATABASE SETUP (PERSISTENT)
# ------------------------------------------------------------
DB_PATH = os.path.join(os.getcwd(), "data.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    worker TEXT,
    category TEXT,
    hours REAL,
    salary REAL
)
""")
conn.commit()

# ------------------------------------------------------------
# ADMIN PASSWORDS
# ------------------------------------------------------------
ADMIN_PASS = "admin123"
VIEW_PASS = "view123"

# ------------------------------------------------------------
# LOGIN SYSTEM
# ------------------------------------------------------------
if "mode" not in st.session_state:
    st.session_state["mode"] = None

if st.session_state["mode"] is None:
    st.subheader("🔐 Login to Continue")
    col1, col2 = st.columns(2)
    with col1:
        password = st.text_input("Enter password", type="password")
    with col2:
        login_btn = st.button("Login")

    if login_btn:
        if password == ADMIN_PASS:
            st.session_state["mode"] = "admin"
            st.success("✅ Logged in as Admin")
            st.experimental_rerun()
        elif password == VIEW_PASS:
            st.session_state["mode"] = "viewer"
            st.success("👁️ Logged in as Viewer")
            st.experimental_rerun()
        else:
            st.error("❌ Incorrect password")

mode = st.session_state["mode"]

# ------------------------------------------------------------
# ADMIN DASHBOARD
# ------------------------------------------------------------
if mode == "admin":
    st.sidebar.header("⚙️ Admin Options")
    option = st.sidebar.radio("Select an option", ["Add Record", "View Records", "Edit Record", "Logout"])

    # ADD RECORD
    if option == "Add Record":
        st.subheader("➕ Add New Record")

        with st.form("add_form"):
            worker = st.text_input("Worker Name")
            category = st.text_input("Work Category")
            hours = st.number_input("Hours Worked", min_value=0.0, step=0.5)
            salary = st.number_input("Salary (₹)", min_value=0.0, step=100.0)
            record_date = st.date_input("Date", value=date.today())
            submit_btn = st.form_submit_button("Add Record")

        if submit_btn:
            if worker and category and hours and salary:
                c.execute(
                    "INSERT INTO records (date, worker, category, hours, salary) VALUES (?, ?, ?, ?, ?)",
                    (record_date.strftime("%Y-%m-%d"), worker, category, hours, salary)
                )
                conn.commit()
                st.success("✅ Record added successfully!")
            else:
                st.error("⚠️ Please fill in all fields.")

    # VIEW RECORDS
    elif option == "View Records":
        st.subheader("📅 View All Records")

        df = pd.read_sql("SELECT * FROM records", conn)

        if df.empty:
            st.info("No records found.")
        else:
            # Filter by date
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=df["date"].min() if not df.empty else date.today())
            with col2:
                end_date = st.date_input("End Date", value=df["date"].max() if not df.empty else date.today())

            filtered_df = df[
                (df["date"] >= str(start_date)) &
                (df["date"] <= str(end_date))
            ]

            st.dataframe(filtered_df, use_container_width=True)

            # Export button
            def to_excel(df):
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Records')
                processed_data = output.getvalue()
                return processed_data

            excel_data = to_excel(filtered_df)
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name="salary_records.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # EDIT RECORDS
    elif option == "Edit Record":
        st.subheader("✏️ Edit / Delete Record")

        df = pd.read_sql("SELECT * FROM records", conn)
        if df.empty:
            st.info("No records available.")
        else:
            record_id = st.selectbox("Select Record ID", df["id"])
            selected = df[df["id"] == record_id].iloc[0]

            with st.form("edit_form"):
                worker = st.text_input("Worker Name", value=selected["worker"])
                category = st.text_input("Work Category", value=selected["category"])
                hours = st.number_input("Hours Worked", value=float(selected["hours"]))
                salary = st.number_input("Salary (₹)", value=float(selected["salary"]))
                record_date = st.date_input("Date", value=pd.to_datetime(selected["date"]).date())

                col1, col2 = st.columns(2)
                with col1:
                    update_btn = st.form_submit_button("Update Record")
                with col2:
                    delete_btn = st.form_submit_button("Delete Record")

            if update_btn:
                c.execute(
                    "UPDATE records SET date=?, worker=?, category=?, hours=?, salary=? WHERE id=?",
                    (record_date.strftime("%Y-%m-%d"), worker, category, hours, salary, record_id)
                )
                conn.commit()
                st.success("✅ Record updated successfully!")
                st.experimental_rerun()

            if delete_btn:
                c.execute("DELETE FROM records WHERE id=?", (record_id,))
                conn.commit()
                st.warning("🗑️ Record deleted successfully!")
                st.experimental_rerun()

    # LOGOUT
    elif option == "Logout":
        st.session_state["mode"] = None
        st.experimental_rerun()

# ------------------------------------------------------------
# VIEWER DASHBOARD
# ------------------------------------------------------------
elif mode == "viewer":
    st.sidebar.header("👁️ View Mode")
    st.sidebar.info("You are in read-only mode")

    df = pd.read_sql("SELECT * FROM records", conn)

    if df.empty:
        st.info("No data available.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=df["date"].min() if not df.empty else date.today())
        with col2:
            end_date = st.date_input("End Date", value=df["date"].max() if not df.empty else date.today())

        filtered_df = df[
            (df["date"] >= str(start_date)) &
            (df["date"] <= str(end_date))
        ]
        st.dataframe(filtered_df, use_container_width=True)

    if st.button("🔙 Logout"):
        st.session_state["mode"] = None
        st.experimental_rerun()
