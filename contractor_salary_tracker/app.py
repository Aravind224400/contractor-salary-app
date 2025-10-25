import streamlit as st
import pandas as pd
from datetime import date
import os

# --------------------------
# Config
# --------------------------
st.set_page_config(page_title="🏗 Contractor Salary Tracker", page_icon="🏗", layout="wide")
DATA_FILE = "data.csv"

# --------------------------
# Load or Create Data File
# --------------------------
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["date", "worker_name", "salary", "notes"])
    df.to_csv(DATA_FILE, index=False)
else:
    df = pd.read_csv(DATA_FILE)

# --------------------------
# Functions
# --------------------------
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def add_record(date_val, worker_name, salary, notes):
    global df
    new_row = {"date": date_val, "worker_name": worker_name, "salary": salary, "notes": notes}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_data(df)

def delete_record(index):
    global df
    df = df.drop(index)
    df.reset_index(drop=True, inplace=True)
    save_data(df)

# --------------------------
# UI
# --------------------------
st.title("🏗 Contractor Salary Tracker (No DB)")
st.write("Data is stored permanently in `data.csv` 📁")

with st.form("add_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        date_val = st.date_input("Date", value=date.today())
        worker_name = st.text_input("Worker Name")
    with col2:
        salary = st.number_input("Salary (₹)", min_value=0.0, step=100.0)
        notes = st.text_input("Notes")

    submitted = st.form_submit_button("➕ Add Record")
    if submitted:
        add_record(date_val, worker_name, salary, notes)
        st.success("Record added successfully!")

# --------------------------
# Show Records
# --------------------------
st.subheader("📋 Salary Records")
st.dataframe(df)

if not df.empty:
    del_index = st.number_input("Enter row number to delete (starting from 0)", min_value=0, max_value=len(df)-1)
    if st.button("🗑️ Delete Selected Record"):
        delete_record(del_index)
        st.success("Record deleted successfully!")
