import streamlit as st
import sqlite3
from datetime import date

# ========================
# Database Setup
# ========================
conn = sqlite3.connect("contractor.db", check_same_thread=False)
c = conn.cursor()

# Workers table
c.execute("""
CREATE TABLE IF NOT EXISTS workers_master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    role TEXT,
    contact TEXT
)
""")

# Daily entries table
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

conn.commit()

# ========================
# Page Setup
# ========================
st.set_page_config(page_title="Contractor Salary Tracker", page_icon="🧱", layout="wide")
st.markdown("<h1 style='text-align:center;color:#0d47a1;'>🧱 Contractor Salary Tracker</h1>", unsafe_allow_html=True)

# ========================
# Hardcoded Login
# ========================
ADMIN_PASSWORD = "dada"
VIEW_PASSWORD = "work"

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
    elif role == "Viewer" and entered_pass == VIEW_PASSWORD:
        st.session_state.logged_in = True
        st.session_state.admin_logged = False
        st.sidebar.info("Logged in as Viewer")
    else:
        st.session_state.logged_in = False
        st.session_state.admin_logged = False
        st.sidebar.error("❌ Incorrect password")

# Stop the app from loading any content until login
if not st.session_state.logged_in:
    st.stop()

# ========================
# Tabs
# ========================
if st.session_state.admin_logged:
    # Admin sees all tabs
    tab1, tab2, tab3, tab4 = st.tabs(["👷 Register Worker", "💰 Daily Entry", "📅 View Records", "📝 Notes & Holidays"])
else:
    # Viewer sees only "View Records"
    tab3, = st.tabs(["📅 View Records"])

# ========================
# 1️⃣ Register Worker (Admin Only)
# ========================
if st.session_state.admin_logged:
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
# 2️⃣ Daily Entry (Admin Only)
# ========================
if st.session_state.admin_logged:
    with tab2:
        st.header("💰 Daily Salary Entry")
        entry_date = st.date_input("Select Date", date.today())
        
        worker_list = c.execute("SELECT id, name FROM workers_master ORDER BY name").fetchall()
        worker_dict = {w[1]: w[0] for w in worker_list}
        worker_choice = st.selectbox("Select Worker", ["-- Select Worker --"] + list(worker_dict.keys()))

        salary = st.number_input("Enter Salary (₹)", min_value=0.0, step=100.0)
        note = st.text_input("Work / Note (optional)")

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
# 3️⃣ View Records (All Users)
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
# 4️⃣ Notes / Holidays (Admin Only)
# ========================
if st.session_state.admin_logged:
    with tab4:
        st.header("📝 Notes / Holidays")
        note_date = st.date_input("Select Date", date.today(), key="note_date")
        existing_note = c.execute("SELECT note FROM work_entries WHERE entry_date=? LIMIT 1", (note_date.strftime("%Y-%m-%d"),)).fetchone()
        note_text = st.text_area("Add Note / Holiday Info", existing_note[0] if existing_note else "")

        if st.button("Save Note"):
            if existing_note:
                c.execute("UPDATE work_entries SET note=? WHERE entry_date=?", (note_text, note_date.strftime("%Y-%m-%d")))
            else:
                c.execute("INSERT INTO work_entries (worker_id, salary, entry_date, note) VALUES (?, ?, ?, ?)",
                          (0, 0, note_date.strftime("%Y-%m-%d"), note_text))
            conn.commit()
            st.success("Note saved successfully!")

conn.close()
