import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --------------------------
# App Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# --------------------------
# File Setup
# --------------------------
DATA_FILE = "data.csv"
WORKER_FILE = "workers.csv"

if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["date", "worker_name", "category", "salary", "notes"]).to_csv(DATA_FILE, index=False)
if not os.path.exists(WORKER_FILE):
    pd.DataFrame(columns=["worker_name", "category"]).to_csv(WORKER_FILE, index=False)

# --------------------------
# Passwords
# --------------------------
ADMIN_PASS = "dada"
VIEW_PASS = "work"

# --------------------------
# Helper Functions
# --------------------------
def load_data():
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_workers():
    return pd.read_csv(WORKER_FILE)

def save_workers(df):
    df.to_csv(WORKER_FILE, index=False)

def generate_pdf(record):
    """Create a PDF salary slip for a record"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 14)
    c.drawString(200, 800, "🏗 Contractor Salary Slip")
    c.line(50, 795, 550, 795)

    c.setFont("Helvetica", 12)
    y = 760
    for key, val in record.items():
        c.drawString(80, y, f"{key.title()}: {val}")
        y -= 25

    c.drawString(80, y - 10, "Signature: ___________________")
    c.save()
    buffer.seek(0)
    return buffer

# --------------------------
# Login System
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🏗 Contractor Salary Tracker Login")
    password = st.text_input("Enter Password", type="password")
    if st.button("Login"):
        if password == ADMIN_PASS:
            st.session_state.logged_in = True
            st.session_state.role = "admin"
        elif password == VIEW_PASS:
            st.session_state.logged_in = True
            st.session_state.role = "viewer"
        else:
            st.error("Incorrect password.")
    st.stop()

role = st.session_state.role

# --------------------------
# Load data
# --------------------------
df = load_data()
workers_df = load_workers()

st.title("🏗 Contractor Salary Tracker")

# --------------------------
# Tabs
# --------------------------
if role == "admin":
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Daily Dashboard", "✍️ Add Record", "👷 Manage Workers", "📋 View/Search Records"])
else:
    tab1, tab4 = st.tabs(["📅 Daily Dashboard", "📋 View/Search Records"])

# --------------------------
# Tab 1 - Dashboard
# --------------------------
with tab1:
    st.subheader("📊 Daily Summary Dashboard")

    if df.empty:
        st.info("No records yet.")
    else:
        df["date"] = pd.to_datetime(df["date"])
        today = pd.Timestamp.today().normalize()
        today_data = df[df["date"] == today]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Records", len(today_data))
        col2.metric("Total Salary Paid Today", f"₹{today_data['salary'].sum():,.2f}")
        if not today_data.empty:
            col3.metric("Highest Salary", f"₹{today_data['salary'].max():,.2f}")
            col4.metric("Lowest Salary", f"₹{today_data['salary'].min():,.2f}")

        st.markdown("### 📅 Salary Trend (Last 7 Days)")
        recent_data = df[df["date"] >= today - pd.Timedelta(days=7)]
        trend = recent_data.groupby("date")["salary"].sum().reset_index()
        st.line_chart(trend, x="date", y="salary", use_container_width=True)

# --------------------------
# Tab 2 - Add Record
# --------------------------
if role == "admin":
    with tab2:
        st.subheader("✍️ Add Salary Record")
        worker_list = workers_df["worker_name"].tolist()

        selected_worker = st.selectbox("Select Worker", ["--- Add New Worker ---"] + worker_list)
        if selected_worker == "--- Add New Worker ---":
            new_worker = st.text_input("Enter New Worker Name").strip()
            category = st.selectbox("Category", ["Mason", "Painter", "Helper", "Electrician", "Other"])
        else:
            new_worker = selected_worker
            category = workers_df.loc[workers_df["worker_name"] == new_worker, "category"].values[0]

        salary_date = st.date_input("Date", date.today())
        salary = st.number_input("Salary (₹)", min_value=0.0, step=100.0)
        notes = st.text_area("Notes (optional)")

        if st.button("💾 Save Record"):
            new_record = pd.DataFrame([{
                "date": str(salary_date),
                "worker_name": new_worker,
                "category": category,
                "salary": salary,
                "notes": notes
            }])
            df = pd.concat([df, new_record], ignore_index=True)
            save_data(df)

            # Register worker if new
            if new_worker not in worker_list:
                workers_df = pd.concat([workers_df, pd.DataFrame([{"worker_name": new_worker, "category": category}])], ignore_index=True)
                save_workers(workers_df)

            st.success(f"✅ Record added for {new_worker} on {salary_date}")

# --------------------------
# Tab 3 - Manage Workers
# --------------------------
if role == "admin":
    with tab3:
        st.subheader("👷 Worker Management")
        st.dataframe(workers_df, use_container_width=True)

        st.markdown("### ➕ Register New Worker")
        name = st.text_input("Worker Name").strip()
        cat = st.selectbox("Category", ["Mason", "Painter", "Helper", "Electrician", "Other"])
        if st.button("Register Worker"):
            if name in workers_df["worker_name"].values:
                st.warning("Worker already exists.")
            else:
                workers_df.loc[len(workers_df)] = [name, cat]
                save_workers(workers_df)
                st.success(f"✅ {name} registered as {cat}")

# --------------------------
# Tab 4 - View/Search Records
# --------------------------
with tab4:
    st.subheader("📋 Search and Filter Records")

    if df.empty:
        st.info("No records available.")
    else:
        df["date"] = pd.to_datetime(df["date"])
        start_date = st.date_input("Start Date", df["date"].min().date())
        end_date = st.date_input("End Date", df["date"].max().date())

        filtered = df[(df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)]

        worker_filter = st.selectbox("Filter by Worker", ["All"] + sorted(df["worker_name"].unique().tolist()))
        if worker_filter != "All":
            filtered = filtered[filtered["worker_name"] == worker_filter]

        search_text = st.text_input("Search Notes or Site")
        if search_text:
            filtered = filtered[filtered["notes"].str.contains(search_text, case=False, na=False)]

        st.dataframe(filtered, use_container_width=True)

        for i, row in filtered.iterrows():
            col1, col2 = st.columns([3, 1])
            col1.write(f"🧱 **{row['worker_name']}** — ₹{row['salary']} — {row['date'].date()}")
            pdf = generate_pdf(row)
            col2.download_button("📄 Download Slip", pdf, file_name=f"SalarySlip_{row['worker_name']}.pdf")

# --------------------------
# Logout
# --------------------------
st.markdown("---")
st.button("🔒 Logout", on_click=lambda: st.session_state.clear())
