import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import date

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# ------------------------------------------------------------
# DATABASE SETUP (PERSISTENT)
# ------------------------------------------------------------
DB_PATH = "/mount/data/data.db"  # ✅ Streamlit permanent storage path
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
# FUNCTIONS
# ------------------------------------------------------------
def add_record(date, worker, category, hours, salary):
    c.execute("INSERT INTO records (date, worker, category, hours, salary) VALUES (?, ?, ?, ?, ?)",
              (date, worker, category, hours, salary))
    conn.commit()

def get_all_records():
    df = pd.read_sql_query("SELECT * FROM records ORDER BY date DESC", conn)
    return df

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    processed_data = output.getvalue()
    return processed_data

# ------------------------------------------------------------
# AUTHENTICATION
# ------------------------------------------------------------
st.sidebar.header("🔐 Login")

mode = st.sidebar.radio("Select mode", ["Admin", "Viewer"])
password = st.sidebar.text_input("Enter password", type="password")

ADMIN_PASS = "admin123"
VIEW_PASS = "view123"

if (mode == "Admin" and password == ADMIN_PASS) or (mode == "Viewer" and password == VIEW_PASS):

    st.title("🏗 Contractor Salary Tracker")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📋 Add Record", "📅 View Records", "📊 Summary"])

    # ------------------------------------------------------------
    # TAB 1: ADD RECORD
    # ------------------------------------------------------------
    with tab1:
        st.subheader("➕ Add New Record")
        with st.form("add_record_form"):
            col1, col2 = st.columns(2)
            with col1:
                record_date = st.date_input("Date", date.today())
                worker = st.text_input("Worker Name")
                category = st.text_input("Category (e.g., Mason, Painter)")
            with col2:
                hours = st.number_input("Hours Worked", min_value=0.0, step=0.5)
                salary = st.number_input("Salary", min_value=0.0, step=100.0)

            submitted = st.form_submit_button("✅ Submit Record")

            if submitted:
                if worker and category:
                    add_record(str(record_date), worker, category, hours, salary)
                    st.success(f"Record added successfully for **{worker}** on {record_date}")
                else:
                    st.warning("Please fill in all required fields.")

    # ------------------------------------------------------------
    # TAB 2: VIEW RECORDS
    # ------------------------------------------------------------
    with tab2:
        st.subheader("📅 View All Records")

        df = get_all_records()
        if df.empty:
            st.info("No records available yet.")
        else:
            # Date filter
            with st.expander("🔍 Filter Options", expanded=True):
                unique_dates = sorted(df["date"].unique())
                date_filter = st.multiselect("Select Date(s)", unique_dates, default=unique_dates)

            filtered_df = df[df["date"].isin(date_filter)]
            st.dataframe(filtered_df, use_container_width=True)

            # Download Excel
            excel_data = to_excel(filtered_df)
            st.download_button(
                label="📥 Download as Excel",
                data=excel_data,
                file_name="contractor_records.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ------------------------------------------------------------
    # TAB 3: SUMMARY
    # ------------------------------------------------------------
    with tab3:
        st.subheader("📊 Summary Dashboard")

        df = get_all_records()
        if not df.empty:
            total_salary = df["salary"].sum()
            total_workers = df["worker"].nunique()
            total_days = df["date"].nunique()

            col1, col2, col3 = st.columns(3)
            col1.metric("💰 Total Salary", f"₹{total_salary:,.0f}")
            col2.metric("👷 Total Workers", total_workers)
            col3.metric("📆 Total Days Recorded", total_days)

            st.bar_chart(df.groupby("date")["salary"].sum())
        else:
            st.info("No data to summarize yet.")

else:
    st.warning("Please enter a valid password to continue.")
