import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

# --------------------------
# Streamlit Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="💰", layout="wide")

# --------------------------
# Database Setup
# --------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

# Create tables if they don't exist
c.execute("""
CREATE TABLE IF NOT EXISTS workers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker TEXT,
    category TEXT,
    salary REAL,
    notes TEXT,
    pay_date TEXT
)
""")
conn.commit()

# --------------------------
# App Modes
# --------------------------
mode = st.sidebar.radio("Select Mode", ["🧾 Dashboard", "➕ Add Record", "👷 Register Worker", "📅 View by Date"])

st.title("🏗 Contractor Salary Tracker")

# ======================================================
# TAB 1: DASHBOARD
# ======================================================
if mode == "🧾 Dashboard":
    st.subheader("📅 Daily Summary")

    df = pd.read_sql("SELECT * FROM records", conn)

    if not df.empty:
        today = date.today().strftime("%Y-%m-%d")
        today_df = df[df["pay_date"] == today]

        total_today = today_df["salary"].sum()
        worker_count = today_df["worker"].nunique()

        col1, col2 = st.columns(2)
        col1.metric("Total Paid Today", f"₹{total_today:,.2f}")
        col2.metric("Workers Paid", worker_count)

        st.divider()
        st.subheader("🧾 All Records Summary")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No records found yet.")

# ======================================================
# TAB 2: ADD RECORD
# ======================================================
elif mode == "➕ Add Record":
    st.subheader("➕ Add New Payment Record")

    workers = [w[0] for w in c.execute("SELECT name FROM workers").fetchall()]

    if not workers:
        st.warning("No workers registered yet. Please add workers in 'Register Worker' tab.")
    else:
        with st.form("add_record_form"):
            worker = st.selectbox("👷 Worker Name", workers)
            category = st.text_input("💼 Work Category")
            salary = st.number_input("💰 Salary (₹)", min_value=0.0, step=100.0)
            notes = st.text_area("📝 Notes (optional)")
            pay_date = st.date_input("📅 Payment Date", date.today())

            submitted = st.form_submit_button("💾 Save Record")

            if submitted:
                c.execute("INSERT INTO records (worker, category, salary, notes, pay_date) VALUES (?, ?, ?, ?, ?)",
                          (worker, category, salary, notes, str(pay_date)))
                conn.commit()
                st.success(f"✅ Record added for {worker} on {pay_date}.")

# ======================================================
# TAB 3: REGISTER WORKER
# ======================================================
elif mode == "👷 Register Worker":
    st.subheader("👷 Add New Worker")

    with st.form("register_form"):
        name = st.text_input("Enter Worker Name")
        add_worker = st.form_submit_button("➕ Add Worker")

        if add_worker:
            if name.strip() == "":
                st.error("Worker name cannot be empty.")
            else:
                try:
                    c.execute("INSERT INTO workers (name) VALUES (?)", (name.strip(),))
                    conn.commit()
                    st.success(f"✅ Worker '{name}' added successfully!")
                except sqlite3.IntegrityError:
                    st.warning("⚠️ This worker is already registered.")

    st.divider()
    st.subheader("👥 Registered Workers")

    workers_df = pd.read_sql("SELECT name FROM workers", conn)
    if not workers_df.empty:
        st.dataframe(workers_df, hide_index=True, use_container_width=True)
    else:
        st.info("No workers registered yet.")

# ======================================================
# TAB 4: VIEW BY DATE
# ======================================================
elif mode == "📅 View by Date":
    st.subheader("📅 View Payments by Date")

    df = pd.read_sql("SELECT * FROM records", conn)

    if not df.empty:
        selected_date = st.date_input("Select a Date")
        filtered = df[df["pay_date"] == str(selected_date)]

        if not filtered.empty:
            st.success(f"✅ Showing {len(filtered)} record(s) for {selected_date}")
            st.dataframe(filtered, use_container_width=True, hide_index=True)
        else:
            st.warning("No records found for this date.")
    else:
        st.info("No records found in the database yet.")
