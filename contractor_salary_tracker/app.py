import streamlit as st
import pandas as pd
from datetime import date
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

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
        tabs = st.tabs(["📅 Daily Dashboard", "➕ Add Record", "👷 Worker Management", "✏️ Edit Records", "🔍 Search & Filter"])
    else:  # Viewer
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

            col1, col2, col3, col4
