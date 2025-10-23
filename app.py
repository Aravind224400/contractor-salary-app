import streamlit as st
import sqlite3
import os
from datetime import date

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker",
                   page_icon="🏗", layout="wide")

PASSWORD = "Dada"  # Change to your dad's secret

# --------------------------
# Login
# --------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Login")
    pwd = st.text_input("Enter password:", type="password")
    if st.button("Login"):
        if pwd == PASSWORD:
            st.session_state.logged_in = True
            st.success("Logged in successfully!")
        else:
            st.error("Incorrect password")
    st.stop()  # Stop app until logged in

# --------------------------
# Database Setup
# --------------------------
DB_PATH = os.path.join(os.getcwd(), "workers.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS workers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    salary REAL,
    entry_date TEXT
)
''')
conn.commit()

today_str = date.today().strftime("%Y-%m-%d")

# --------------------------
# Sidebar Controls
# --------------------------
st.sidebar.header("Add / Update / Delete Worker")
name = st.sidebar.text_input("Worker Name")
salary = st.sidebar.text_input("Daily Salary (₹)")
worker_id = st.sidebar.text_input("Worker ID (for update/delete)")
today = today_str

col1, col2, col3 = st.sidebar.columns(3)

# Add worker
with col1:
    if st.button("Add Worker"):
        if name.strip() != "" and salary.strip() != "":
            try:
                salary_value = float(salary)
                c.execute("INSERT INTO workers (name, salary, entry_date) VALUES (?, ?, ?)",
                          (name, salary_value, today))
                conn.commit()
                st.success(f"Added {name} with salary ₹{salary_value} on {today}")
            except ValueError:
                st.error("Enter a valid number for salary")
        else:
            st.error("Please enter name and salary")

# Update worker
with col2:
    if st.button("Update Worker"):
        if worker_id.strip().isdigit() and name.strip() != "" and salary.strip() != "":
            try:
                salary_value = float(salary)
                c.execute("UPDATE workers SET name=?, salary=?, entry_date=? WHERE id=?",
                          (name, salary_value, today, int(worker_id)))
                conn.commit()
                st.success(f"Updated worker ID {worker_id}")
            except ValueError:
                st.error("Enter valid details")
        else:
            st.error("Provide valid ID, name, and salary")

# Delete worker
with col3:
    if st.button("Delete Worker"):
        if worker_id.strip().isdigit():
            c.execute("DELETE FROM workers WHERE id=?", (int(worker_id),))
            conn.commit()
            st.success(f"Deleted worker ID {worker_id}")
        else:
            st.error("Enter a valid Worker ID")

# --------------------------
# Today's Workers
# --------------------------
st.header("📋 Today's Workers")
c.execute("SELECT * FROM workers WHERE entry_date=?", (today_str,))
todays_workers = c.fetchall()

total_today = 0
if len(todays_workers) == 0:
    st.info("No workers added today yet.")
else:
    for w in todays_workers:
        total_today += w[2]
        col1, col2, col3 = st.columns([1, 3, 2])
        col1.write(f"**ID:** {w[0]}")
        col2.write(f"**Name:** {w[1]}")
        col3.write(f"**Salary:** ₹{w[2]}")
    st.markdown(f"### 💰 Total Salary Today: ₹{total_today}")

# --------------------------
# Monthly Summary
# --------------------------
st.header("📅 Monthly Summary")
month_input = st.date_input("Select Month", value=date.today())
month_str = month_input.strftime("%Y-%m")

c.execute("SELECT * FROM workers WHERE entry_date LIKE ?", (f"{month_str}%",))
monthly_workers = c.fetchall()

if monthly_workers:
    monthly_total = sum([w[2] for w in monthly_workers])
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
        total_year += w[2]
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])
        col1.write(f"ID: {w[0]}")
        col2.write(f"Name: {w[1]}")
        col3.write(f"Salary: ₹{w[2]}")
        col4.write(f"Date: {w[3]}")
    st.markdown(f"### 💰 Total Salary Past 1 Year: ₹{total_year}")
