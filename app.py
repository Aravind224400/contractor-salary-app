import streamlit as st
import sqlite3
import os
from datetime import date, timedelta

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker",
                   page_icon="🏗", layout="wide")

ADMIN_PASSWORD = "DadSecret123"
VIEW_PASSWORD = "ViewOnly123"

# --------------------------
# Login
# --------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None

if not st.session_state.logged_in:
    st.title("🔒 Login")
    pwd = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.role = 'admin'
            st.success("Logged in as Admin")
        elif pwd == VIEW_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.role = 'viewer'
            st.success("Logged in as Viewer")
        else:
            st.error("Incorrect password")
    st.stop()

# --------------------------
# Database Setup
# --------------------------
DB_PATH = os.path.join(os.getcwd(), "workers.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Tables
c.execute('''
CREATE TABLE IF NOT EXISTS workers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    salary REAL NOT NULL,
    entry_date TEXT NOT NULL
)
''')
c.execute('''
CREATE TABLE IF NOT EXISTS day_notes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT NOT NULL,
    note TEXT
)
''')
conn.commit()

today_str = date.today().strftime("%Y-%m-%d")

# --------------------------
# Admin Sidebar
# --------------------------
if st.session_state.role == 'admin':
    st.sidebar.header("Add / Update Worker")
    name = st.sidebar.text_input("Worker Name")
    salary = st.sidebar.text_input("Daily Salary (₹)")
    worker_id = st.sidebar.text_input("Worker ID (for update only)")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("Add Worker"):
            if name.strip() != "" and salary.strip() != "":
                try:
                    salary_value = float(salary)
                    c.execute("INSERT INTO workers (name, salary, entry_date) VALUES (?, ?, ?)",
                              (name.strip(), salary_value, today_str))
                    conn.commit()
                    st.success(f"Added {name} with salary ₹{salary_value} on {today_str}")
                except:
                    st.error("Enter valid salary")
            else:
                st.error("Enter name and salary")
    with col2:
        if st.button("Update Worker"):
            if worker_id.strip().isdigit() and (name.strip() != "" or salary.strip() != ""):
                c.execute("SELECT name, salary FROM workers WHERE id=?", (int(worker_id),))
                row = c.fetchone()
                if row:
                    new_name = name.strip() if name.strip() != "" else row[0]
                    new_salary = float(salary) if salary.strip() != "" else row[1]
                    c.execute("UPDATE workers SET name=?, salary=?, entry_date=? WHERE id=?",
                              (new_name, new_salary, today_str, int(worker_id)))
                    conn.commit()
                    st.success(f"Updated worker ID {worker_id}")
                else:
                    st.error("Worker ID not found")
            else:
                st.error("Provide Worker ID and new data")

    # Daily notes / holidays
    st.sidebar.header("Daily Notes / Holiday Info")
    daily_note = st.sidebar.text_area("Note for Today", "")
    if st.sidebar.button("Save Note"):
        if daily_note.strip() != "":
            c.execute("INSERT INTO day_notes (entry_date, note) VALUES (?, ?)",
                      (today_str, daily_note.strip()))
            conn.commit()
            st.success("Note saved for today!")
        else:
            st.warning("Enter something before saving")

# --------------------------
# Search / Edit Section
# --------------------------
st.header("🔍 Search and Edit Entries")

# Date search
search_type = st.radio("Search Type:", ["Exact Date", "Month"])
if search_type == "Exact Date":
    search_date = st.date_input("Select Date")
    search_str = search_date.strftime("%Y-%m-%d")
    c.execute("SELECT * FROM workers WHERE entry_date=?", (search_str,))
    workers = c.fetchall()
    c.execute("SELECT * FROM day_notes WHERE entry_date=?", (search_str,))
    notes = c.fetchall()
else:
    month_input = st.date_input("Select Month")
    month_str = month_input.strftime("%Y-%m")
    c.execute("SELECT * FROM workers WHERE entry_date LIKE ?", (f"{month_str}%",))
    workers = c.fetchall()
    c.execute("SELECT * FROM day_notes WHERE entry_date LIKE ?", (f"{month_str}%",))
    notes = c.fetchall()

# --------------------------
# Display Worker Entries
# --------------------------
st.subheader("👷 Worker Entries")
if workers:
    for w in workers:
        col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])
        col1.write(f"ID: {w[0]}")
        col2.write(f"Name: {w[1]}")
        col3.write(f"Salary: ₹{w[2]}")
        col4.write(f"Date: {w[3]}")
        if st.session_state.role == 'admin':
            if col5.button(f"Edit ID {w[0]}"):
                # Editable modal
                new_name = st.text_input(f"New Name for ID {w[0]}", w[1])
                new_salary = st.text_input(f"New Salary for ID {w[0]}", str(w[2]))
                new_date = st.date_input(f"New Date for ID {w[0]}", date.fromisoformat(w[3]))
                if st.button(f"Save Changes ID {w[0]}"):
                    c.execute("UPDATE workers SET name=?, salary=?, entry_date=? WHERE id=?",
                              (new_name, float(new_salary), new_date.isoformat(), w[0]))
                    conn.commit()
                    st.success(f"Updated worker ID {w[0]}")
else:
    st.warning("No worker entries found")

# --------------------------
# Display Notes
# --------------------------
st.subheader("📝 Notes / Holidays")
if notes:
    for n in notes:
        col1, col2, col3 = st.columns([2, 4, 2])
        col1.write(f"ID: {n[0]}")
        col2.write(f"Date: {n[1]}")
        col3.write(f"Note: {n[2]}")
        if st.session_state.role == 'admin':
            if st.button(f"Edit Note ID {n[0]}"):
                new_note = st.text_area(f"Edit Note ID {n[0]}", n[2])
                if st.button(f"Save Note ID {n[0]}"):
                    c.execute("UPDATE day_notes SET note=? WHERE id=?", (new_note, n[0]))
                    conn.commit()
                    st.success(f"Updated note ID {n[0]}")
else:
    st.warning("No notes found")

# --------------------------
# Past 1 Year Summary
# --------------------------
st.header("📅 Past 1 Year Worker Data")
c.execute("SELECT * FROM workers WHERE entry_date >= date('now','-1 year') ORDER BY entry_date DESC")
year_data = c.fetchall()
total_year = sum([float(w[2]) for w in year_data]) if year_data else 0

if year_data:
    for w in year_data:
        st.info(f"Date: {w[3]} | Worker: {w[1]} | Salary: ₹{w[2]}")
st.markdown(f"### 💰 Total Salary Past 1 Year: ₹{total_year}")

# --------------------------
# Viewer Info
# --------------------------
if st.session_state.role == 'viewer':
    st.info("You have read-only access. You cannot edit or add data.")
