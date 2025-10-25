import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
from io import BytesIO

# -----------------------------
# Page Config
# -----------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="💰", layout="wide")
st.title("🏗 Contractor Salary Tracker")

# -----------------------------
# Database Setup
# -----------------------------
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

# Create tables if not exist
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

# -----------------------------
# Authentication
# -----------------------------
ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "admin123")
VIEW_PASS = st.secrets.get("VIEW_PASSWORD", "view123")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

role = st.session_state.get("role", None)

with st.sidebar:
    st.header("🔐 Login")
    selected_role = st.radio("Select Role", ["Admin", "Viewer"])
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if (selected_role == "Admin" and password == ADMIN_PASS) or (selected_role == "Viewer" and password == VIEW_PASS):
            st.session_state.logged_in = True
            st.session_state.role = selected_role
            st.success(f"✅ Logged in as {selected_role}")
        else:
            st.error("❌ Incorrect password")

if st.session_state.logged_in:
    role = st.session_state.role
    st.sidebar.success(f"Logged in as {role}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.experimental_rerun()

    # -----------------------------
    # Tabs
    # -----------------------------
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Dashboard", "➕ Add Record", "👷 Manage Workers", "🔍 View & Edit Records"])

    # ===================== TAB 1: Dashboard =====================
    with tab1:
        st.subheader("📊 Daily Summary")
        df = pd.read_sql("SELECT * FROM records", conn)
        if not df.empty:
            today = date.today().strftime("%Y-%m-%d")
            today_df = df[df["pay_date"] == today]

            total_today = today_df["salary"].sum() if not today_df.empty else 0
            worker_count = today_df["worker"].nunique() if not today_df.empty else 0

            col1, col2 = st.columns(2)
            col1.metric("Total Paid Today", f"₹{total_today:,.2f}")
            col2.metric("Workers Paid Today", worker_count)

            st.divider()
            st.subheader("🧾 All Records")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No records found yet.")

    # ===================== TAB 2: Add Record =====================
    with tab2:
        if role == "Admin":
            st.subheader("💵 Add Salary Record")
            workers = [row[0] for row in c.execute("SELECT name FROM workers").fetchall()]
            if not workers:
                st.warning("No workers registered yet. Add workers in 'Manage Workers' tab.")
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
                        st.success(f"✅ Record added for {worker} on {pay_date}")
        else:
            st.warning("Only Admin can add salary records.")

    # ===================== TAB 3: Manage Workers =====================
    with tab3:
        if role == "Admin":
            st.subheader("👷 Worker Management")
            with st.form("add_worker_form"):
                name = st.text_input("Worker Name")
                add_worker = st.form_submit_button("➕ Add Worker")
                if add_worker:
                    if name.strip() == "":
                        st.error("Worker name cannot be empty")
                    else:
                        try:
                            c.execute("INSERT INTO workers (name) VALUES (?)", (name.strip(),))
                            conn.commit()
                            st.success(f"✅ Worker '{name}' added!")
                        except sqlite3.IntegrityError:
                            st.warning("⚠️ Worker already exists.")

            st.divider()
            st.subheader("👥 Registered Workers")
            workers_df = pd.read_sql("SELECT * FROM workers", conn)
            st.dataframe(workers_df, use_container_width=True, hide_index=True)

            st.divider()
            delete_worker = st.selectbox("Select Worker to Delete", ["None"] + workers_df["name"].tolist())
            if delete_worker != "None" and st.button("🗑 Delete Worker"):
                c.execute("DELETE FROM workers WHERE name=?", (delete_worker,))
                conn.commit()
                st.warning(f"Worker '{delete_worker}' deleted!")
        else:
            st.warning("Only Admin can manage workers.")

    # ===================== TAB 4: View & Edit Records =====================
    with tab4:
        st.subheader("🔍 View / Edit Records")
        df = pd.read_sql("SELECT * FROM records", conn)
        if not df.empty:
            col1, col2 = st.columns(2)
            workers_list = ["All"] + df["worker"].unique().tolist()
            worker_filter = col1.selectbox("Filter by Worker", workers_list)
            date_filter = col2.date_input("Filter by Date (optional)")

            filtered_df = df.copy()
            if worker_filter != "All":
                filtered_df = filtered_df[filtered_df["worker"] == worker_filter]
            if date_filter:
                filtered_df = filtered_df[filtered_df["pay_date"] == str(date_filter)]

            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            # Export to Excel
            def to_excel(df):
                output = BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, index=False, sheet_name='Records')
                writer.save()
                processed_data = output.getvalue()
                return processed_data

            if not filtered_df.empty:
                excel_data = to_excel(filtered_df)
                st.download_button(label="⬇️ Download Excel", data=excel_data, file_name="salary_records.xlsx")

            # Admin Edit / Delete
            if role == "Admin" and not filtered_df.empty:
                edit_id = st.number_input("Enter Record ID to Edit/Delete", min_value=1, step=1)
                record = c.execute("SELECT * FROM records WHERE id=?", (edit_id,)).fetchone()
                if record:
                    with st.form("edit_record_form"):
                        new_salary = st.number_input("Update Salary", value=record[3])
                        new_notes = st.text_area("Update Notes", value=record[4])
                        update_btn = st.form_submit_button("Update Record")
                        delete_btn = st.form_submit_button("Delete Record")

                        if update_btn:
                            c.execute("UPDATE records SET salary=?, notes=? WHERE id=?", (new_salary, new_notes, edit_id))
                            conn.commit()
                            st.success("✅ Record updated successfully")
                        if delete_btn:
                            c.execute("DELETE FROM records WHERE id=?", (edit_id,))
                            conn.commit()
                            st.warning("🗑 Record deleted")
        else:
            st.info("No records found yet.")

else:
    st.info("Please log in to access the app.")
