import streamlit as st
import sqlite3
import os

# Make sure database is in the current working directory
DB_PATH = os.path.join(os.getcwd(), "workers.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

# Create table if it doesn't exist
c.execute('''
CREATE TABLE IF NOT EXISTS workers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    salary REAL
)
''')
conn.commit()

st.title("🏗 Contractor Salary Tracker")

# Add Worker Section
st.subheader("Add Worker")
name = st.text_input("Worker Name")
salary = st.text_input("Daily Salary (₹)")

if st.button("Add Worker"):
    if name.strip() != "" and salary.strip() != "":
        try:
            salary_value = float(salary)
            c.execute("INSERT INTO workers (name, salary) VALUES (?, ?)", (name, salary_value))
            conn.commit()
            st.success(f"Added {name} with salary ₹{salary_value}"_
