import streamlit as st
import pandas as pd
from datetime import date
import os

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")
DATA_FILE = "data.csv"
WORKERS_FILE = "workers.csv"

# --------------------------
# Secrets (Passwords)
# --------------------------
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
VIEW_PASSWORD = st.secrets["VIEW_PASSWORD"]

# --------------------------
# Load or Create Files
# --------------------------
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["date", "worker_name", "salary", "notes"]).to_csv(DATA_FILE, index=False)

if not os.path.exists(WORKERS_FILE):
    pd.DataFrame(columns=["worker_name"]).to_csv(WORKERS_FILE, index=False)

# --------------------------
# Utility Functions
# --------------------------
def load_data():
    return pd.read_csv(DATA_FILE)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def load_workers():
    return pd.read_csv(WORKERS_FILE)["worker_name"].tolist()

def save_workers(workers):
    pd.DataFrame({"worker_name": workers}).to_csv(WORKERS_FILE, index=False)

def add_record(date_val, worker_name, salary, notes):
    df = load_data()
    new_row = {"date": date_val, "worker_name": worker_name, "salary": salary, "notes": notes}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)

def delete_record(index):
    df = load_data()
    df = df.drop(index)
    df.reset_index(drop=True, inplace=True)
    save_data(df)

def register_worker(name):
    workers = load_workers()
    if name not in workers:
        workers.append(name)
        save_workers(workers)
        return True
    return False

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

    st.title("🏗 Contractor Salary Tracker")
    st.info(f"Data file: {os.path.abspath(DATA_FILE)}")

    # Load data and workers
    df = load_data()
    workers = load_workers()

    # --------------------------
    # Admin Features
    # --------------------------
    if role == "Admin":
        tab1, tab2, tab3 = st.tabs(["✍️ Add Record", "📋 View/Delete Records", "👷 Register Worker"])

        # --- Tab 1: Add Record ---
        with tab1:
            st.subheader("✍️ Add Worker Salary Record")

            selected_name = st.selectbox("Select Registered Worker", ["-- New Worker --"] + workers)
            if selected_name == "-- New Worker --":
                worker_name = st.text_input("Enter New Worker Name").strip()
            else:
                worker_name = selected_name

            date_val = st.date_input("Date", value=date.today())
            salary = st.number_input("Salary (₹)", min_value=0.0, step=100.0)
            notes = st.text_input("Notes (optional)")

            if st.button("💾 Save Record"):
                if worker_name:
                    add_record(date_val, worker_name, salary, notes)
                    st.success(f"Record saved for {worker_name}!")
                else:
                    st.warning("Please enter or select a worker name.")

        # --- Tab 2: View/Delete Records ---
        with tab2:
            st.subheader("📋 All Salary Records")
            if df.empty:
                st.info("No records found yet.")
            else:
                st.dataframe(df)
                del_index = st.number_input("Enter row number to delete (starting from 0)", 
                                            min_value=0, max_value=len(df)-1)
                if st.button("🗑️ Delete Record"):
                    delete_record(del_index)
                    st.success("Record deleted successfully!")
                    st.rerun()

        # --- Tab 3: Register Worker ---
        with tab3:
            st.subheader("👷 Register New Worker")
            new_worker = st.text_input("New Worker Name").strip()
            if st.button("✅ Register Worker"):
                if new_worker:
                    if register_worker(new_worker):
                        st.success(f"Worker '{new_worker}' registered successfully!")
                    else:
                        st.warning(f"'{new_worker}' is already registered.")
                else:
                    st.warning("Please enter a worker name.")

            if workers:
                st.markdown("### Registered Workers:")
                st.write(", ".join(workers))

    # --------------------------
    # Viewer Features
    # --------------------------
    elif role == "Viewer":
        st.subheader("📋 View Salary Records")
        if df.empty:
            st.info("No records found yet.")
        else:
            st.dataframe(df)
            st.download_button("⬇️ Download CSV", df.to_csv(index=False), "salary_data.csv")
