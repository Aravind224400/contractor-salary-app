import streamlit as st
import sqlite3
import os
from datetime import date, timedelta

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker",
                   page_icon="🏗", layout="wide")

ADMIN_PASSWORD = "Dada"   # full access
VIEW_PASSWORD = "work"     # read-only access

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
                    c.execute("
