import streamlit as st
import pandas as pd
from datetime import date
import os

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")
DATA_FILE = "data.csv"

# --------------------------
# Secrets (Passwords)
# --------------------------
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
VIEW_PASSWORD = st.secrets["VIEW_PASSWORD"]

# --------------------------
# Load or Create Data File
# --------------------------
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["date", "worker_name", "salary", "notes"])
    df.to_csv(DATA_FILE, index=False)
else:
    df = pd.read_csv(DATA_FILE)

# --------------------------
# Functions
# --------------------------
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def add_record(date_val, worker_name, salary, notes):
    global df
    new_row = {"date": date_val, "worker_name": worker_name, "salary": salary, "notes": notes}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)

def delete_record(index):
    global df
    df = df.drop(index)
    df.reset_index(drop=True, inplace=True)
    save_data(df)

# --------------------------
# Login System
# --------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔐 Contractor Salary Tracker Login")
    password = st.text_input("Enter Password", type="password")

    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.role = "Admin"
            st.success("✅ Logged in as Admin!")
        elif password == VIEW_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.role = "Viewer"
            st.success("👀 Logged in as Viewer!")
        else:
            st.error("❌ Incorrect password")

else:
    role = st.session_state.role
    st.sidebar.success(f"Logged in as {role}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🏗 Contractor Salary Tracker (CSV Version)")
    st.info(f"Data file path: {os.path.abspath(DATA_FILE)}")

    # --------------- Admin Features ---------------
    if role == "Admin":
        with st.form("add_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date_val = st.date_input("Date", value=date.today())
                worker_name = st.text_input("Worker Name")
            with col2:
                salary = st.number_input("Salary (₹)", min_value=0.0, step=100.0)
                notes = st.text_input("Notes")

            submitted = st.form_submit_button("➕ Add Record")
            if submitted:
                add_record(date_val, worker_name, salary, notes)
                st.success("Record added successfully!")

        st.subheader("📋 Salary Records")
        st.dataframe(df)

        if not df.empty:
            del_index = st.number_input("Enter row number to delete (starting from 0)", min_value=0, max_value=len(df)-1)
            if st.button("🗑️ Delete Selected Record"):
                delete_record(del_index)
                st.success("Record deleted successfully!")

    # --------------- Viewer Features ---------------
    elif role == "Viewer":
        st.subheader("📋 Salary Records (Read-Only)")
        st.dataframe(df)
        st.download_button("⬇️ Download CSV", df.to_csv(index=False), file_name="salary_data.csv")
