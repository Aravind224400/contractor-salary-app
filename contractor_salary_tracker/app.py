import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --------------------------------------
# DATABASE SETUP
# --------------------------------------
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

# --------------------------------------
# APP CONFIG
# --------------------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="💰", layout="wide")
st.title("🏗 Contractor Salary Tracker")

ADMIN_PASSWORD = "admin123"
VIEW_PASSWORD = "view123"

# --------------------------------------
# LOGIN SYSTEM
# --------------------------------------
if "role" not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.subheader("🔐 Login")
    role = st.selectbox("Select role", ["Admin", "Viewer"])
    password = st.text_input("Enter password", type="password")
    if st.button("Login"):
        if (role == "Admin" and password == ADMIN_PASSWORD) or (role == "Viewer" and password == VIEW_PASSWORD):
            st.session_state.role = role
            try:
                st.rerun()
            except:
                st.experimental_rerun()
        else:
            st.error("❌ Incorrect password!")

else:
    role = st.session_state.role
    st.success(f"✅ Logged in as {role}")

    # Logout Button
    if st.button("Logout"):
        st.session_state.role = None
        try:
            st.rerun()
        except:
            st.experimental_rerun()

    # --------------------------------------
    # ADMIN PANEL
    # --------------------------------------
    if role == "Admin":
        st.subheader("👷 Manage Workers")
        with st.form("add_worker_form"):
            name = st.text_input("Worker Name")
            category = st.text_input("Category")
            submitted = st.form_submit_button("Add Worker")
            if submitted:
                if name and category:
                    try:
                        c.execute("INSERT INTO workers (name, category) VALUES (?, ?)", (name, category))
                        conn.commit()
                        st.success(f"✅ Added worker: {name}")
                    except sqlite3.IntegrityError:
                        st.warning("⚠️ Worker already exists.")
                else:
                    st.warning("Please fill all fields.")

        st.divider()
        st.subheader("💵 Add Salary Record")

        workers = [row[0] for row in c.execute("SELECT name FROM workers").fetchall()]

        if workers:
            with st.form("add_record_form"):
                pay_date = st.date_input("Payment Date", value=date.today())
                worker = st.selectbox("Select Worker", workers)
                c.execute("SELECT category FROM workers WHERE name=?", (worker,))
                category = c.fetchone()[0] if c.fetchone() else ""
                salary = st.number_input("Salary Amount", min_value=0.0)
                notes = st.text_area("Notes (optional)")
                submitted = st.form_submit_button("Save Record")

                if submitted:
                    c.execute(
                        "INSERT INTO records (pay_date, worker, category, salary, notes) VALUES (?, ?, ?, ?, ?)",
                        (str(pay_date), worker, category, salary, notes)
                    )
                    conn.commit()
                    st.success("✅ Record saved successfully!")
        else:
            st.info("No workers found. Please add a worker first.")

        st.divider()
        st.subheader("🗂 View & Edit Records")

        records = pd.read_sql_query("SELECT * FROM records", conn)

        if not records.empty:
            selected_date = st.date_input("Filter by Date", value=date.today())
            filtered = records[records["pay_date"] == str(selected_date)]

            if not filtered.empty:
                st.dataframe(filtered)

                edit_id = st.selectbox("Select Record ID to Edit/Delete", filtered["id"])
                record = filtered[filtered["id"] == edit_id].iloc[0]

                st.write("### ✏️ Edit Record")
                new_salary = st.number_input("Edit Salary", value=float(record["salary"]))
                new_notes = st.text_area("Edit Notes", value=record["notes"])

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Record"):
                        c.execute("UPDATE records SET salary=?, notes=? WHERE id=?", (new_salary, new_notes, edit_id))
                        conn.commit()
                        st.success("✅ Record updated successfully!")
                        st.rerun()
                with col2:
                    if st.button("Delete Record"):
                        c.execute("DELETE FROM records WHERE id=?", (edit_id,))
                        conn.commit()
                        st.warning("🗑️ Record deleted.")
                        st.rerun()
            else:
                st.info("No records found for selected date.")
        else:
            st.info("No records available yet.")

    # --------------------------------------
    # VIEWER PANEL
    # --------------------------------------
    elif role == "Viewer":
        st.subheader("📅 View Records by Date")

        records = pd.read_sql_query("SELECT * FROM records", conn)
        if not records.empty:
            selected_date = st.date_input("Select Date", value=date.today())
            filtered = records[records["pay_date"] == str(selected_date)]
            if not filtered.empty:
                st.dataframe(filtered)
            else:
                st.info("No records found for that date.")
        else:
            st.info("No data found yet.")
