import streamlit as st
import pandas as pd
from datetime import date
from github import Github
import io

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# --------------------------
# Secrets
# --------------------------
ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
VIEW_PASSWORD = st.secrets["VIEW_PASSWORD"]

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
GITHUB_BRANCH = st.secrets["GITHUB_BRANCH"]

# --------------------------
# GitHub setup
# --------------------------
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

def read_csv_from_github(filename):
    try:
        file_content = repo.get_contents(filename, ref=GITHUB_BRANCH)
        return pd.read_csv(io.StringIO(file_content.decoded_content.decode()))
    except Exception:
        return pd.DataFrame(columns=["date", "worker_name", "salary", "notes"]) if "data" in filename else pd.DataFrame(columns=["worker_name"])

def save_csv_to_github(df, filename, message):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    try:
        file_content = repo.get_contents(filename, ref=GITHUB_BRANCH)
        repo.update_file(file_content.path, message, csv_buffer.getvalue(), file_content.sha, branch=GITHUB_BRANCH)
    except Exception:
        repo.create_file(filename, message, csv_buffer.getvalue(), branch=GITHUB_BRANCH)

# --------------------------
# Utility functions
# --------------------------
def load_data():
    return read_csv_from_github("data.csv")

def save_data(df):
    save_csv_to_github(df, "data.csv", "Update salary records")

def load_workers():
    df = read_csv_from_github("workers.csv")
    return df["worker_name"].tolist() if not df.empty else []

def save_workers(workers):
    pd.DataFrame({"worker_name": workers}).to_csv("workers.csv", index=False)
    save_csv_to_github(pd.DataFrame({"worker_name": workers}), "workers.csv", "Update worker list")

# --------------------------
# Login system
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

    df = load_data()
    workers = load_workers()

    st.title("🏗 Contractor Salary Tracker")
    st.info("All data is stored securely in your GitHub repository ✅")

    # Admin interface
    if role == "Admin":
        tab1, tab2, tab3 = st.tabs(["✍️ Add Record", "📅 View by Date", "👷 Register Worker"])

        # Add record
        with tab1:
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
                    new_row = pd.DataFrame([{
                        "date": str(date_val),
                        "worker_name": worker_name,
                        "salary": salary,
                        "notes": notes
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success(f"Record saved for {worker_name}!")
                    st.rerun()
                else:
                    st.warning("Please enter or select a worker name.")

        # View records
        with tab2:
            if df.empty:
                st.info("No records yet.")
            else:
                df["date"] = pd.to_datetime(df["date"])
                unique_dates = sorted(df["date"].dt.date.unique())
                selected_date = st.selectbox("Select Date", unique_dates[::-1])
                filtered = df[df["date"].dt.date == selected_date]
                st.dataframe(filtered)
                st.metric("Total Salary Paid", f"₹{filtered['salary'].sum():,.2f}")

        # Register worker
        with tab3:
            new_worker = st.text_input("New Worker Name").strip()
            if st.button("✅ Register Worker"):
                if new_worker:
                    if new_worker not in workers:
                        workers.append(new_worker)
                        save_workers(workers)
                        st.success(f"Worker '{new_worker}' registered!")
                    else:
                        st.warning("Already registered.")
                else:
                    st.warning("Enter worker name.")
            st.write(", ".join(workers))

    # Viewer interface
    else:
        if df.empty:
            st.info("No records yet.")
        else:
            df["date"] = pd.to_datetime(df["date"])
            col1, col2 = st.columns(2)
            with col1:
                start = st.date_input("From", value=df["date"].min().date())
            with col2:
                end = st.date_input("To", value=df["date"].max().date())

            mask = (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
            filtered = df[mask]
            st.dataframe(filtered)
            st.metric("Total Salary", f"₹{filtered['salary'].sum():,.2f}")
            st.download_button("⬇️ Download CSV", filtered.to_csv(index=False), "records.csv")
