import streamlit as st
import sqlite3
from datetime import date

# ========================
# Database Setup
# ========================
conn = sqlite3.connect("contractor.db", check_same_thread=False)
c = conn.cursor()

# Worker master table
c.execute("""
CREATE TABLE IF NOT EXISTS workers_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    role TEXT,
    contact TEXT
)
""")

# Daily work entries
c.execute("""
CREATE TABLE IF NOT EXISTS work_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER,
    salary REAL,
    entry_date TEXT,
    note TEXT,
    FOREIGN KEY(worker_id) REFERENCES workers_master(id)
)
""")

# Admin password storage
c.execute("""
CREATE TABLE IF NOT EXISTS admin_pass (
    id INTEGER PRIMARY KEY,
    password TEXT
)
""")
conn.commit()

# ========================
# Page Setup
# ========================
st.set_page_config(page_title="Contractor Salary Tracker", page_icon="🧱", layout="wide")
st.markdown("<h1 style='text-align:center;color:#0d47a1;'>🧱 Contractor Salary Tracker</h1>", unsafe_allow_html=True)

# ========================
# Admin Login
# ========================
def get_admin_password():
    row = c.execute("SELECT password FROM admin_pass WHERE id=1").fetchone()
    return row[0] if row else None

st.sidebar.header("🔐 Login / Role Selection")
role = st.sidebar.radio("Select Role:", ["Viewer", "Admin"])

if role == "Admin":
    saved_password = get_admin_password()
    if saved_password is None:
        st.sidebar.info("Set your Admin password for the first time")
        new_pass = st.sidebar.text_input("Enter New Admin Password", type="password")
        if st.sidebar.button("Set Password"):
            if new_pass.strip():
                c.execute("INSERT INTO admin_pass (id, password) VALUES (1, ?)", (new_pass.strip(),))
                conn.commit()
                st.sidebar.success("✅ Admin password set! Please restart the app.")
                st.stop()
            else:
                st.sidebar.error("Password cannot be empty")
    else:
        entered_pass = st.sidebar.text_input("Enter Admin Password", type="password")
        if st.sidebar.button("Login"):
            if entered_pass == saved_password:
                st.session_state.admin_logged = True
                st.sidebar.success("Logged in as Admin")
            else:
                st.sidebar.error("Incorrect password")
                st.stop()
        if not st.session_state.get("admin_logged", False):
            st.stop()
else:
    st.session_state.admin_logged = False

# ========================
# Tabs
# ========================
tab1, tab2, tab3, tab4 = st.tabs(["👷 Register Worker", "💰 Daily Entry", "📅 View Records", "📝 Notes & Holidays"])

# ========================
# 1️⃣ Register Worker
# ========================
with tab1:
    st.header("👷 Register New Worker")
    with st.form("add_worker_form"):
        name = st.text_input("Worker Name")
        role_input = st.text_input("Role (e.g. Mason, Painter, Labourer)")
        contact = st.text_input("Contact Number")
        submit_worker = st.form_submit_button("Add Worker")

        if submit_worker:
            if not name.strip():
                st.error("Worker name cannot be empty.")
            else:
                try:
                    c.execute("INSERT INTO workers_master (name, role, contact) VALUES (?, ?, ?)",
                              (name.strip(), role_input.strip(), contact.strip()))
                    conn.commit()
                    st.success(f"✅ Worker '{name}' added successfully")
                except sqlite3.IntegrityError:
                    st.warning("⚠️ Worker already exists!")

    st.subheader("Registered Workers")
    workers = c.execute("SELECT * FROM workers_master ORDER BY name").fetchall()
    for w in workers:
        col1, col2, col3, col4 = st.columns([2,2,2,1])
        col1.write(f"**{w[1]}**")
        col2.write(w[2] or "")
        col3.write(w[3] or "")
        if st.session_state.admin_logged:
            if col4.button("❌ Delete", key=f"del_worker_{w[0]}"):
                c.execute("DELETE FROM workers_master WHERE id=?", (w[0],))
                conn.commit()
                st.warning(f"Deleted worker '{w[1]}'")
                st.experimental_rerun()

# ========================
# 2️⃣ Daily Entry
# ========================
with tab2:
    st.header("💰 Daily Salary Entry")
    entry_date = st.date_input("Select Date", date.today())
    
    # Worker selection
    worker_list = c.execute("SELECT id, name FROM workers_master ORDER BY name").fetchall()
    worker_dict = {w[1]: w[0] for w in worker_list}
    worker_choice = st.selectbox("Select Worker", ["-- Select Worker --"] + list(worker_dict.keys()))

    salary = st.number_input("Enter Salary (₹)", min_value=0.0, step=100.0)
    note = st.text_input("Work / Note (optional)")

    if st.session_state.admin_logged:
        if st.button("Add Daily Entry"):
            if worker_choice == "-- Select Worker --":
                st.error("Please select a worker")
            elif salary <= 0:
                st.error("Enter a valid salary")
            else:
                c.execute("INSERT INTO work_entries (worker_id, salary, entry_date, note) VALUES (?, ?, ?, ?)",
                          (worker_dict[worker_choice], salary, entry_date.strftime("%Y-%m-%d"), note))
                conn.commit()
                st.success(f"💰 Added salary for {worker_choice} on {entry_date}")

# ========================
# 3️⃣ View Records
# ========================
with tab3:
    st.header("📅 View Records")
    view_date = st.date_input("Select Date", date.today(), key="view_date")
    view_str = view_date.strftime("%Y-%m-%d")

    c.execute("""
        SELECT we.id, wm.name, wm.role, we.salary, we.note
        FROM work_entries we
        JOIN workers_master wm ON we.worker_id = wm.id
        WHERE we.entry_date=?
        ORDER BY wm.name
    """, (view_str,))
    records = c.fetchall()

    if records:
        total_salary = sum([r[3] for r in records])
        st.success(f"Total Salary on {view_str}: ₹{total_salary}")
        for r in records:
            col1, col2, col3, col4, col5 = st.columns([2,2,2,2,1])
            col1.write(f"👷 {r[1]}")
            col2.write(r[2])
            col3.write(f"₹{r[3]}")
            col4.write(r[4] or "")
            if st.session_state.admin_logged:
                if col5.button("🗑️ Delete", key=f"del_entry_{r[0]}"):
                    c.execute("DELETE FROM work_entries WHERE id=?", (r[0],))
                    conn.commit()
                    st.warning(f"Deleted entry for {r[1]}")
                    st.experimental_rerun()
    else:
        st.info("No entries for this date. (No Work)")

# ========================
# 4️⃣ Notes / Holidays
# ========================
with tab4:
    st.header("📝 Notes / Holidays")
    note_date = st.date_input("Select Date", date.today(), key="note_date")
    existing_note = c.execute("SELECT note FROM work_entries WHERE entry_date=? LIMIT 1", (note_date.strftime("%Y-%m-%d"),)).fetchone()
    note_text = st.text_area("Add Note / Holiday Info", existing_note[0] if existing_note else "")

    if st.session_state.admin_logged:
        if st.button("Save Note"):
            if existing_note:
                c.execute("UPDATE work_entries SET note=? WHERE entry_date=?", (note_text, note_date.strftime("%Y-%m-%d")))
            else:
                c.execute("INSERT INTO work_entries (worker_id, salary, entry_date, note) VALUES (?, ?, ?, ?)",
                          (0, 0, note_date.strftime("%Y-%m-%d"), note_text))
            conn.commit()
            st.success("Note saved successfully!")

conn.close()
