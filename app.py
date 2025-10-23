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

# --------------------------
# Sidebar Controls
# --------------------------
st.sidebar.header("Add / Update / Delete Worker")
name = st.sidebar.text_input("Worker Name")
salary = st.sidebar.text_input("Daily Salary (₹)")
worker_id = st.sidebar.text_input("Worker ID (for update/delete)")
today = date.today().strftime("%Y-%m-%d")

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
                st.success(f"Updated wor
