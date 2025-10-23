import streamlit as st
import sqlite3
import os

# Database setup
DB_PATH = os.path.join(os.getcwd(), "workers.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS workers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    salary REAL
)
''')
conn.commit()

st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")

st.title("🏗 Contractor Salary Tracker")
st.markdown("Add, view, update, and delete workers' daily salary.")

# Sidebar for adding worker
st.sidebar.header("Add / Update Worker")
name = st.sidebar.text_input("Worker Name")
salary = st.sidebar.text_input("Daily Salary (₹)")
worker_id = st.sidebar.text_input("Worker ID (for update/delete)")

col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("Add Worker"):
        if name.strip() != "" and salary.strip() != "":
            try:
                salary_value = float(salary)
                c.execute("INSERT INTO workers (name, salary) VALUES (?, ?)", (name, salary_value))
                conn.commit()
                st.success(f"Added {name} with salary ₹{salary_value}")
            except ValueError:
                st.error("Enter a valid number for salary")
        else:
            st.error("Please enter name and salary")

with col2:
    if st.button("Update Worker"):
        if worker_id.strip().isdigit() and name.strip() != "" and salary.strip() != "":
            try:
                salary_value = float(salary)
                c.execute("UPDATE workers SET name=?, salary=? WHERE id=?", (name, salary_value, int(worker_id)))
                conn.commit()
                st.success(f"Updated worker ID {worker_id}")
            except ValueError:
                st.error("Enter valid details")
        else:
            st.error("Please provide valid ID, name, and salary")

with col3:
    if st.button("Delete Worker"):
        if worker_id.strip().isdigit():
            c.execute("DELETE FROM workers WHERE id=?", (int(worker_id),))
            conn.commit()
            st.success(f"Deleted worker ID {worker_id}")
        else:
            st.error("Enter a valid Worker ID")

# Display all workers
st.subheader("Workers List")
c.execute("SELECT * FROM workers ORDER BY id ASC")
workers = c.fetchall()

if len(workers) == 0:
    st.info("No workers added yet.")
else:
    # Beautiful table
    st.table([{"ID": w[0], "Name": w[1], "Salary (₹)": w[2]} for w in workers])
    total_salary = sum([w[2] for w in workers])
    st.markdown(f"### Total Daily Salary: ₹{total_salary}")
