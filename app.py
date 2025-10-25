import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

# ========================
# Config
# ========================
st.set_page_config(page_title="🏗 Contractor Salary Tracker",
                   page_icon="🧱", layout="wide")
st.markdown("<h1 style='text-align:center;color:#0d47a1;'>🧱 Contractor Salary Tracker</h1>", unsafe_allow_html=True)

# ========================
# Supabase Setup
# ========================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Hardcoded Login
# ========================
ADMIN_PASSWORD = st.secrets["admin_password"]
VIEW_PASSWORD = st.secrets["viewer_password"]

st.sidebar.header("🔐 Login")
role = st.sidebar.radio("Select Role:", ["Admin", "Viewer"])
entered_pass = st.sidebar.text_input("Enter Password", type="password")

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.admin_logged = False

# Login check
if st.sidebar.button("Login"):
    if role == "Admin" and entered_pass == ADMIN_PASSWORD:
        st.session_state.logged_in = True
        st.session_state.admin_logged = True
        st.sidebar.success("✅ Logged in as Admin")
        st.experimental_rerun()
    elif role == "Viewer" and entered_pass == VIEW_PASSWORD:
        st.session_state.logged_in = True
        st.session_state.admin_logged = False
        st.sidebar.info("Logged in as Viewer")
        st.experimental_rerun()
    else:
        st.session_state.logged_in = False
        st.session_state.admin_logged = False
        st.sidebar.error("❌ Incorrect password")

# Stop the app if not logged in
if not st.session_state.logged_in:
    st.stop()

# ========================
# Tabs
# ========================
if st.session_state.admin_logged:
    tab1, tab2, tab3, tab4 = st.tabs(["👷 Register Worker", "💰 Daily Entry", "📅 View Records", "📝 Notes / Holidays"])
else:
    tab3, = st.tabs(["📅 View Records"])

# ========================
# 1️⃣ Register Worker (Admin Only)
# ========================
if st.session_state.admin_logged:
    with tab1:
        st.header("👷 Register New Worker")
        with st.form("add_worker_form"):
            worker_name = st.text_input("Worker Name")
            worker_role = st.text_input("Role (e.g. Mason, Painter, Labourer)")
            worker_contact = st.text_input("Contact Number")
            submit_worker = st.form_submit_button("Add Worker")

            if submit_worker:
                if not worker_name.strip():
                    st.error("Worker name cannot be empty.")
                else:
                    try:
                        supabase.table("workers").insert({
                            "name": worker_name.strip(),
                            "role": worker_role.strip(),
                            "contact": worker_contact.strip()
                        }).execute()
                        st.success(f"✅ Worker '{worker_name}' added successfully")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"⚠️ Error adding worker: {e}")

        st.subheader("Registered Workers")
        workers_data = supabase.table("workers").select("*").order("name").execute().data
        for w in workers_data:
            col1, col2, col3, col4 = st.columns([2,2,2,1])
            col1.write(f"**{w['name']}**")
            col2.write(w.get('role', ''))
            col3.write(w.get('contact', ''))
            if st.session_state.admin_logged:
                if col4.button("❌ Delete", key=f"del_worker_{w['id']}"):
                    supabase.table("workers").delete().eq("id", w['id']).execute()
                    st.warning(f"Deleted worker '{w['name']}'")
                    st.experimental_rerun()

# ========================
# 2️⃣ Daily Entry (Admin Only)
# ========================
if st.session_state.admin_logged:
    with tab2:
        st.header("💰 Daily Salary Entry")
        entry_date = st.date_input("Select Date", date.today())
        
        workers_list = supabase.table("workers").select("*").order("name").execute().data
        worker_dict = {w['name']: w['id'] for w in workers_list}
        worker_choice = st.selectbox("Select Worker", ["-- Select Worker --"] + list(worker_dict.keys()))

        salary = st.number_input("Enter Salary (₹)", min_value=0.0, step=100.0)
        note = st.text_input("Work / Note (optional)")

        if st.button("Add Daily Entry"):
            if worker_choice == "-- Select Worker --":
                st.error("Please select a worker")
            elif salary <= 0:
                st.error("Enter a valid salary")
            else:
                supabase.table("salaries").insert({
                    "worker_id": worker_dict[worker_choice],
                    "salary": salary,
                    "entry_date": str(entry_date),
                    "note": note
                }).execute()
                st.success(f"💰 Added salary for {worker_choice} on {entry_date}")
                st.experimental_rerun()

# ========================
# 3️⃣ View Records (All Users)
# ========================
with (tab3 if st.session_state.admin_logged else tab3):
    st.header("📅 View Records")
    start_date = st.date_input("From Date", date.today(), key="view_start")
    end_date = st.date_input("To Date", date.today(), key="view_end")

    # Fetch salaries joined with workers
    salaries_data = supabase.table("salaries").select("*, worker_id(*)").order("entry_date", desc=True).execute().data
    if salaries_data:
        # Flatten nested worker data
        records = []
        for r in salaries_data:
            worker = r['worker_id']
            records.append({
                "id": r["id"],
                "name": worker.get("name", ""),
                "role": worker.get("role", ""),
                "salary": r["salary"],
                "note": r.get("note", ""),
                "date": r["entry_date"]
            })
        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        mask = (df["date"].dt.date >= start_date) & (df["date"].dt.date <= end_date)
        filtered_df = df.loc[mask]

        if not filtered_df.empty:
            total_salary = filtered_df["salary"].sum()
            st.success(f"Total Salary in range: ₹{total_salary}")

            for r in filtered_df.itertuples():
                col1, col2, col3, col4, col5 = st.columns([2,2,2,2,1])
                col1.write(f"👷 {r.name}")
                col2.write(r.role)
                col3.write(f"₹{r.salary}")
                col4.write(r.note or "")
                if st.session_state.admin_logged:
                    if col5.button("🗑️ Delete", key=f"del_entry_{r.id}"):
                        supabase.table("salaries").delete().eq("id", r.id).execute()
                        st.warning(f"Deleted entry for {r.name}")
                        st.experimental_rerun()

            # Summary per worker
            st.markdown("### 💰 Summary per Worker")
            summary = filtered_df.groupby("name")["salary"].sum().reset_index().rename(columns={"salary":"Total Salary"})
            st.dataframe(summary)
            st.download_button("💾 Download CSV", filtered_df.to_csv(index=False), "filtered_salaries.csv")
        else:
            st.info("No entries found in this date range.")
    else:
        st.info("No salary records yet.")

# ========================
# 4️⃣ Notes / Holidays (Admin Only)
# ========================
if st.session_state.admin_logged:
    with tab4:
        st.header("📝 Notes / Holidays")
        note_date = st.date_input("Select Date", date.today(), key="note_date")
        existing_note = supabase.table("notes").select("*").eq("note_date", str(note_date)).execute().data
        note_text = st.text_area("Add Note / Holiday Info", existing_note[0]["note"] if existing_note else "")

        if st.button("Save Note"):
            if existing_note:
                supabase.table("notes").update({"note": note_text}).eq("note_date", str(note_date)).execute()
            else:
                supabase.table("notes").insert({"note_date": str(note_date), "note": note_text}).execute()
            st.success("Note saved successfully!")
            st.experimental_rerun()
