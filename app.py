import streamlit as st
from datetime import date
from supabase import create_client, Client
import pandas as pd

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

# --------------------------
# Secrets (Passwords & DB)
# --------------------------
ADMIN_PASSWORD = st.secrets["admin_password"]
VIEWER_PASSWORD = st.secrets["viewer_password"]
# app.py, line 16 (or similar)
SUPABASE_URL = st.secrets["SUPABASE_URL"] # ✅ CORRECT KEY

SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --------------------------
# Login
# --------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.mode = None

st.title("🏗 Contractor Salary Tracker")

if not st.session_state.logged_in:
    with st.form("login_form"):
        password = st.text_input("Enter Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if password == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.mode = "admin"
            st.success("Admin login successful ✅")
        elif password == VIEW_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.mode = "viewer"
            st.success("Viewer login successful 👀")
        else:
            st.error("Incorrect password. Try again.")

# --------------------------
# Main App (After Login)
# --------------------------
if st.session_state.logged_in:
    mode = st.session_state.mode

    # --------------------------
    # Add Salary Record (Admin)
    # --------------------------
    if mode == "admin":
        st.subheader("👷 Add Worker Salary Record")

        with st.form("salary_form"):
            name = st.text_input("Worker Name")
            work_date = st.date_input("Date", date.today())
            salary = st.number_input("Salary (₹)", min_value=0.0, step=100.0)
            note = st.text_area("Note (optional)")
            submitted = st.form_submit_button("Save Record")

        if submitted and name:
            data = {"date": str(work_date), "worker_name": name, "salary": salary, "notes": note}
            supabase.table("salaries").insert(data).execute()
            st.success("✅ Record saved permanently to Supabase!")
            st.experimental_rerun()

    # --------------------------
    # View Records (All Users)
    # --------------------------
    st.subheader("📋 View Records")

    # Fetch all records
    response = supabase.table("salaries").select("*").order("date", desc=True).execute()
    df = pd.DataFrame(response.data)

    if not df.empty:
        # Convert string date column to datetime
        df["date"] = pd.to_datetime(df["date"])

        # --------------------------
        # Date Filter
        # --------------------------
        st.markdown("### 📅 Filter by Date Range")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From", value=df["date"].min().date())
        with col2:
            end_date = st.date_input("To", value=df["date"].max().date())

        # Apply filter
        mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
        filtered_df = df.loc[mask]

        # --------------------------
        # Show filtered table
        # --------------------------
        st.dataframe(filtered_df)

        # --------------------------
        # Total Salary Summary
        # --------------------------
        st.markdown("### 💰 Total Salary per Worker")
        summary = filtered_df.groupby("worker_name")["salary"].sum().reset_index()
        summary = summary.rename(columns={"worker_name": "Worker", "salary": "Total Salary (₹)"})

        # Show grand total
        total_sum = summary["Total Salary (₹)"].sum()
        st.markdown(f"**🧾 Grand Total Paid: ₹{total_sum:,.2f}**")

        # Show table
        st.dataframe(summary)

        # --------------------------
        # Download Buttons
        # --------------------------
        st.download_button("💾 Download Filtered CSV", filtered_df.to_csv(index=False), "filtered_salaries.csv")
        st.download_button("💾 Download Summary CSV", summary.to_csv(index=False), "salary_summary.csv")
    else:
        st.info("No records found yet.")

    # --------------------------
    # Logout
    # --------------------------
    st.button("🔒 Logout", on_click=lambda: st.session_state.clear())

