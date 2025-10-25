import streamlit as st
import pandas as pd
from datetime import date
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

# ----------------------------------------------------
# Streamlit Config
# ----------------------------------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# ----------------------------------------------------
# App Setup
# ----------------------------------------------------
DATA_FILE = "data.csv"
WORKER_FILE = "workers.csv"

# ----------------------------------------------------
# Utility Functions
# ----------------------------------------------------
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Date", "Worker", "Category", "Salary", "Notes"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_workers():
    if os.path.exists(WORKER_FILE):
        return pd.read_csv(WORKER_FILE)
    else:
        return pd.DataFrame(columns=["Worker", "Category"])

def save_workers(df):
    df.to_csv(WORKER_FILE, index=False)

def generate_pdf(worker, salary, note, pay_date):
    safe_worker = worker.replace(" ", "_")
    filename = f"SalarySlip_{safe_worker}_{pay_date}.pdf"
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

# ----------------------------------------------------
# Authentication
# ----------------------------------------------------
ADMIN_PASS = st.secrets.get("ADMIN_PASSWORD", "dada")
VIEW_PASS = st.secrets.get("VIEW_PASSWORD", "work")

# Session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.mode = None

# ------------------- Login Form -------------------
if not st.session_state.logged_in:
    st.title("🔐 Contractor Salary Tracker Login")

    with st.form("login_form"):
        mode = st.radio("Login as", ["Admin", "Viewer"])
        password = st.text_input("Enter Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        if (mode == "Admin" and password == ADMIN_PASS) or (mode == "Viewer" and password == VIEW_PASS):
            st.session_state.logged_in = True
            st.session_state.mode = mode
            st.success(f"Logged in as {mode}")
        else:
            st.error("❌ Incorrect password. Try again.")

# ------------------- Main App -------------------
if st.session_state.logged_in:
    mode = st.session_state.mode
    data = load_data()
    workers = load_workers()

    # Tabs based on role
    if mode == "Admin":
        tabs = st.tabs(["📅 Daily Dashboard", "➕ Add Record", "👷 Worker Management", "🔍 Search & Filter"])
    else:
        tabs = st.tabs(["📅 Daily Dashboard", "🔍 Search & Filter"])

    # ------------------- Tab 1: Daily Dashboard -------------------
    with tabs[0]:
        st.subheader("📊 Daily Summary")
        if not data.empty:
            today = date.today().strftime("%Y-%m-%d")
            today_data = data[data["Date"] == today]

            total_today = today_data["Salary"].sum() if not today_data.empty else 0
            worker_count = today_data["Worker"].nunique()
            high = today_data["Salary"].max() if not today_data.empty else 0
            low = today_data["Salary"].min() if not today_data.empty else 0

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Paid Today", f"₹{total_today}")
            col2.metric("Workers Paid", worker_count)
            col3.metric("Highest Salary", f"₹{high}")
            col4.metric("Lowest Salary", f"₹{low}")

            # Salary Trend
            st.subheader("📈 Weekly Salary Trend")
            trend = data.groupby("Date")["Salary"].sum().reset_index().sort_values("Date")
            fig, ax = plt.subplots()
            ax.plot(trend["Date"], trend["Salary"], marker="o")
            ax.set_xlabel("Date")
            ax.set_ylabel("Total Salary")
            ax.set_title("Salary Trend")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("No records found yet.")

    # ------------------- Tab 2: Add Record (Admin) -------------------
    if mode == "Admin":
        with tabs[1]:
            st.subheader("➕ Add New Record")

            if workers.empty:
                st.warning("No workers registered. Please add workers first.")
            else:
                with st.form("add_record_form"):
                    pay_date = st.date_input("Payment Date", value=date.today())
                    selected_worker = st.selectbox("Select Worker", workers["Worker"].tolist(), key="worker_select")
                    cat = workers.loc[workers["Worker"] == selected_worker, "Category"].values[0]
                    salary = st.number_input("Salary Amount (₹)", min_value=0)
                    note = st.text_area("Notes (Work done, site, etc.)")
                    submit = st.form_submit_button("💾 Add Record")

                    if submit:
                        new_row = pd.DataFrame([[pay_date.strftime("%Y-%m-%d"), selected_worker, cat, salary, note]],
                                               columns=["Date", "Worker", "Category", "Salary", "Notes"])
                        data = pd.concat([data, new_row], ignore_index=True)
                        save_data(data)
                        st.success("Record added successfully!")

                        pdf_file = generate_pdf(selected_worker, salary, note, pay_date.strftime("%Y-%m-%d"))
                        with open(pdf_file, "rb") as f:
                            st.download_button("⬇️ Download Salary Slip (PDF)", f, file_name=pdf_file)

    # ------------------- Tab 3: Worker Management (Admin) -------------------
    if mode == "Admin":
        with tabs[2]:
            st.subheader("👷 Worker Management")

            with st.form("worker_form"):
                name = st.text_input("Worker Name", key="add_worker_name")
                category = st.selectbox("Category", ["Mason", "Painter", "Helper", "Electrician", "Other"], key="add_worker_cat")
                add_btn = st.form_submit_button("Add Worker")

                if add_btn and name:
                    name = name.strip().title()
                    if name not in workers["Worker"].values:
                        new_w = pd.DataFrame([[name, category]], columns=["Worker", "Category"])
                        workers = pd.concat([workers, new_w], ignore_index=True)
                        save_workers(workers)
                        st.success(f"Worker '{name}' added.")
                    else:
                        st.warning("Worker already exists!")

            st.write("### 👷 Registered Workers")
            st.dataframe(workers)

    # ------------------- Tab 4: Search & Filter -------------------
    with tabs[-1]:
        st.subheader("🔍 Search and Filter Records")

        col1, col2 = st.columns(2)
        with col1:
            worker_filter = st.selectbox("Select Worker", ["All"] + workers["Worker"].tolist(), key="filter_worker")
        with col2:
            use_date_filter = st.checkbox("Filter by Date?")
            if use_date_filter:
                date_filter = st.date_input("Select Date", value=date.today())
            else:
                date_filter = None

        filtered_data = data.copy()
        if worker_filter != "All":
            filtered_data = filtered_data[filtered_data["Worker"] == worker_filter]
        if date_filter:
            filtered_data = filtered_data[filtered_data["Date"] == date_filter.strftime("%Y-%m-%d")]

        st.dataframe(filtered_data)
        st.write(f"Showing {len(filtered_data)} record(s).")
