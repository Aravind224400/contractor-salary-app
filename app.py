import streamlit as st
import sqlite3
import os
from datetime import date, timedelta

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker",
                   page_icon="🏗", layout="wide")

ADMIN_PASSWORD = "DadSecret123"   # full access
VIEW_PASSWORD = "ViewOnly123"     # read-only access

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
            st.success("Logged in as Admin (full access)")
        elif pwd == VIEW_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.role = 'viewer'
            st.success("Logged in as Viewer (read-only)")
        else:
            st.error("Incorrect password")
    st.stop()

# --------------------------
# Database Setup
# --------------------------
DB_PATH = os.path.join(os.getcwd(), "workers.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Workers table
c.execute('''
CREATE TABLE IF NOT EXISTS workers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    salary REAL NOT NULL,
    entry_date TEXT NOT NULL
)
''')

# Notes table
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

    # Add Worker
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
                    st.error("Enter a valid number for salary")
            else:
                st.error("Enter name and salary")

    # Update Worker
    with col2:
        if st.button("Update Worker"):
            if worker_id.strip().isdigit() and (name.strip() != "" or salary.strip() != ""):
                try:
                    c.execute("SELECT name, salary FROM workers WHERE id=?", (int(worker_id),))
                    row = c.fetchone()
                    if row:
                        new_name = name.strip() if name.strip() != "" else row[0]
                        new_salary = float(salary) if salary.strip() != "" else row[1]
                        c.execute("UPDATE workers SET name=?, salary=?, entry_date=? WHERE id=?",
                                  (new_name, new_salary, today_str, int(worker_id)))
                        conn.commit()
                        st.success(f"Updated worker ID {worker_id} for today {today_str}")
                    else:
                        st.error("Worker ID not found")
                except:
                    st.error("Invalid data for update")
            else:
                st.error("Provide Worker ID and at least a new name or salary")

    # Daily Notes / Holiday
    st.sidebar.header("Daily Notes / Holiday Info")
    daily_note = st.sidebar.text_area("Note for Today", "")
    if st.sidebar.button("Save Note"):
        if daily_note.strip() != "":
            c.execute("INSERT INTO day_notes (entry_date, note) VALUES (?, ?)",
                      (today_str, daily_note.strip()))
            conn.commit()
            st.success("Note saved for today!")
        else:
            st.warning("Enter something before saving.")

# --------------------------
# Daily Dashboard (Past 30 Days)
# --------------------------
st.header("📋 Daily Work Status (Past 30 Days)")
today = date.today()
start_date = today - timedelta(days=30)

for i in range(31):
    day = start_date + timedelta(days=i)
    day_str = day.strftime("%Y-%m-%d")
    
    # Workers
    c.execute("SELECT * FROM workers WHERE entry_date=?", (day_str,))
    workers = c.fetchall()
    
    # Notes
    c.execute("SELECT * FROM day_notes WHERE entry_date=?", (day_str,))
    notes = c.fetchall()
    
    st.markdown(f"### Date: {day_str}")
    
    if workers:
        for w in workers:
            try:
                salary_value = float(w[2])
            except:
                salary_value = 0
            st.success(f"Worker: {w[1]} | Salary: ₹{salary_value}")
    if notes:
        for n in notes:
            st.info(f"Note: {n[2]}")
    
    if not workers and not notes:
        st.warning("⚠️ No work recorded")

# --------------------------
# Monthly Summary
# --------------------------
st.header("📅 Monthly Summary")
month_input = st.date_input("Select Month", value=date.today())
month_str = month_input.strftime("%Y-%m")

c.execute("SELECT * FROM workers WHERE entry_date LIKE ?", (f"{month_str}%",))
monthly_workers = c.fetchall()

if monthly_workers:
    monthly_total = sum([float(w[2]) for w in monthly_workers])
    st.write(f"Total salary for {month_str}: ₹{monthly_total}")
else:
    st.write(f"No entries for {month_str}")

# --------------------------
# Past 1 Year Data
# --------------------------
st.header("📅 Past 1 Year Data")
c.execute("SELECT * FROM workers WHERE entry_date >= date('now', '-1 year') ORDER BY entry_date DESC")
year_data = c.fetchall()

total_year = 0
if len(year_data) == 0:
    st.info("No entries in the past 1 year.")
else:
    for w in year_data:
        try:
            total_year += float(w[2])
        except:
            continue
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        col1.write(f"ID: {w[0]}")
        col2.write(f"Name: {w[1]}")
        col3.write(f"Salary: ₹{w[2]}")
        col4.write(f"Date: {w[3]}")
    st.markdown(f"### 💰 Total Salary Past 1 Year: ₹{total_year}")

# --------------------------
# Viewer Info
# --------------------------
if st.session_state.role == 'viewer':
    st.info("You have read-only access. You cannot add or modify data.")
