import streamlit as st
import sqlite3
from datetime import date

# --- Database setup ---
conn = sqlite3.connect("contractor_app.db", check_same_thread=False)
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

# Daily work table
c.execute("""
CREATE TABLE IF NOT EXISTS work_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id INTEGER,
    salary REAL,
    entry_date TEXT,
    FOREIGN KEY(worker_id) REFERENCES workers_master(id)
)
""")

# Notes / holidays
c.execute("""
CREATE TABLE IF NOT EXISTS day_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT,
    note TEXT
)
""")
conn.commit()

# --- Page setup ---
st.set_page_config(page_title="Contractor Salary Tracker", page_icon="🧱", layout="wide")
st.title("🧱 Contractor Daily Salary Tracker")

# --- Authentication ---
st.sidebar.header("🔐 Login")
role = st.sidebar.radio("Select Role", ["Viewer", "Admin"])

if role == "Admin":
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    if password != "1234":
        st.warning("Wrong password! Only Admin can edit or delete.")
        st.stop()

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "👷 Register Worker",
    "💰 Daily Entry",
    "📅 View Records",
    "📝 Notes & Holidays"
])

# ========== 1️⃣ REGISTER WORKER ==========
with tab1:
    st.header("👷 Register New Worker")
    with st.form("add_worker_form"):
        name = st.text_input("Worker Name")
        role_input = st.text_input("Role (e.g. Mason, Painter, Labourer)")
        contact = st.text_input("Contact Number")
        submit_worker = st.form_submit_button("Add Worker")

        if submit_worker:
            if not name:
                st.error("Please enter the worker's name.")
            else:
                try:
                    c.execute("INSERT INTO workers_master (name, role, contact) VALUES (?, ?, ?)",
                              (name.strip(), role_input.strip(), contact.strip()))
                    conn.commit()
                    st.success(f"✅ Worker '{name}' added successfully!")
                except sqlite3.IntegrityError:
                    st.warning("⚠️ Worker already exists!")

    st.subheader("Registered Workers")
    workers = c.execute("SELECT * FROM workers_master ORDER BY name").fetchall()
    if workers:
        for w in workers:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            col1.write(f"**{w[1]}**")
            col2.write(w[2] or "")
            col3.write(w[3] or "")
            if role == "Admin":
                if col4.button("❌ Delete", key=f"del_worker_{w[0]}"):
                    c.execute("DELETE FROM workers_master WHERE id=?", (w[0],))
                    conn.commit()
                    st.warning(f"Deleted worker '{w[1]}'")
                    st.experimental_rerun()
    else:
        st.info("No workers registered yet.")

# ========== 2️⃣ DAILY ENTRY ==========
with tab2:
    st.header("💰 Daily Salary Entry")
    entry_date = st.date_input("Select Date", date.today())

    # Fetch all worker names
    c.execute("SELECT id, name FROM workers_master ORDER BY name")
    worker_data = c.fetchall()
    worker_dict = {w[1]: w[0] for w in worker_data}

    # Selectbox (searchable) for worker name
    worker_choice = st.selectbox("Select Worker (searchable)", ["-- Select Worker --"] + list(worker_dict.keys()))

    st.markdown("Or register a new worker below 👇")
    new_name = st.text_input("New Worker Name (optional)")
    new_role = st.text_input("New Worker Role (optional)")
    new_contact = st.text_input("New Worker Contact (optional)")

    salary = st.number_input("Enter Salary (₹)", min_value=0.0, step=100.0)

    if role == "Admin":
        if st.button("✅ Save Entry"):
            if worker_choice == "-- Select Worker --" and not new_name:
                st.error("Please select or add a worker.")
            elif salary <= 0:
                st.error("Please enter a valid salary.")
            else:
                # If new worker entered, register automatically
                if new_name:
                    try:
                        c.execute("INSERT INTO workers_master (name, role, contact) VALUES (?, ?, ?)",
                                  (new_name.strip(), new_role.strip(), new_contact.strip()))
                        conn.commit()
                        worker_id = c.execute("SELECT id FROM workers_master WHERE name=?", (new_name.strip(),)).fetchone()[0]
                        worker_name = new_name
                    except sqlite3.IntegrityError:
                        worker_id = c.execute("SELECT id FROM workers_master WHERE name=?", (new_name.strip(),)).fetchone()[0]
                        worker_name = new_name
                else:
                    worker_id = worker_dict[worker_choice]
                    worker_name = worker_choice

                c.execute("INSERT INTO work_entries (worker_id, salary, entry_date) VALUES (?, ?, ?)",
                          (worker_id, salary, entry_date.strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"💰 Added {worker_name} - ₹{salary} on {entry_date}")

# ========== 3️⃣ VIEW RECORDS ==========
with tab3:
    st.header("📅 View Daily Records")
    view_date = st.date_input("Select Date", date.today(), key="view_date")
    view_date_str = view_date.strftime("%Y-%m-%d")

    c.execute("""
        SELECT wm.name, wm.role, we.salary, we.id
        FROM work_entries we
        JOIN workers_master wm ON we.worker_id = wm.id
        WHERE we.entry_date=?
        ORDER BY wm.name
    """, (view_date_str,))
    entries = c.fetchall()

    if entries:
        total_salary = sum([e[2] for e in entries])
        st.success(f"💰 Total Salary Paid on {view_date_str}: ₹{total_salary}")
        for e in entries:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            col1.write(f"👷 {e[0]}")
            col2.write(f"🪜 {e[1]}")
            col3.write(f"₹{e[2]}")
            if role == "Admin":
                if col4.button("✏️ Edit", key=f"edit_{e[3]}"):
                    new_salary = st.number_input(f"New salary for {e[0]}", min_value=0.0, step=100.0, key=f"new_sal_{e[3]}")
                    if st.button("✅ Save", key=f"save_{e[3]}"):
                        c.execute("UPDATE work_entries SET salary=? WHERE id=?", (new_salary, e[3]))
                        conn.commit()
                        st.success("Updated successfully!")
                        st.experimental_rerun()
                if col5.button("🗑️ Delete", key=f"del_{e[3]}"):
                    c.execute("DELETE FROM work_entries WHERE id=?", (e[3],))
                    conn.commit()
                    st.warning(f"Deleted {e[0]}")
                    st.experimental_rerun()
    else:
        st.info("No entries found for this date.")

# ========== 4️⃣ NOTES ==========
with tab4:
    st.header("📝 Notes / Holidays")
    note_date = st.date_input("Note Date", date.today(), key="note_date")
    c.execute("SELECT note FROM day_notes WHERE entry_date=?", (note_date.strftime("%Y-%m-%d"),))
    existing_note = c.fetchone()
    note_text = st.text_area("Add Note or Holiday Description", existing_note[0] if existing_note else "")

    if role == "Admin":
        if st.button("💾 Save Note"):
            if existing_note:
                c.execute("UPDATE day_notes SET note=? WHERE entry_date=?", (note_text, note_date.strftime("%Y-%m-%d")))
            else:
                c.execute("INSERT INTO day_notes (entry_date, note) VALUES (?, ?)", (note_date.strftime("%Y-%m-%d"), note_text))
            conn.commit()
            st.success("Note saved successfully!")

    st.divider()
    st.subheader("📅 All Notes")
    for n in c.execute("SELECT * FROM day_notes ORDER BY entry_date DESC").fetchall():
        st.write(f"📌 {n[1]} — {n[2]}")

conn.close()
