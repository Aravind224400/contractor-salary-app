import streamlit as st
import sqlite3

# Connect to database (or create it)
conn = sqlite3.connect("workers.db")
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS workers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    salary REAL
)
''')
conn.commit()

st.title("🏗 Contractor Salary Tracker")

# Input worker details
st.subheader("Add Worker")
name = st.text_input("Worker Name")
salary = st.text_input("Daily Salary (₹)")

if st.button("Add Worker"):
    if name and salary:
        try:
            salary_value = float(salary)
            c.execute("INSERT INTO workers (name, salary) VALUES (?, ?)", (name, salary_value))
            conn.commit()
            st.success(f"Added {name} with salary ₹{salary_value}")
        except ValueError:
            st.error("Please enter a valid number for salary")
    else:
        st.error("Please fill in both fields")

# Display all workers
st.subheader("Work
