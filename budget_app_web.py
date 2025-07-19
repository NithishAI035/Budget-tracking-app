import streamlit as st
import json
import os
import plotly.express as px
import pandas as pd

# ------------------ Configurations ------------------
st.set_page_config(page_title="Budget Tracker", page_icon="💸", layout="centered")

# Centered title using HTML
st.markdown("""
    <h1 style='
        text-align: center;
        font-size: 40px;
        font-weight: 700;
        background: linear-gradient(to right, #3a6073, #16222a);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: none;
        margin-bottom: 30px;
    '>
        Personal Budget Tracker
    </h1>
""", unsafe_allow_html=True)

# ------------------ File Paths ------------------
CREDENTIALS_FILE = "user_credentials.json"

# ------------------ Helper Functions ------------------
def load_credentials():
    if os.path.exists(CREDENTIALS_FILE):
        with open(CREDENTIALS_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_credentials(credentials):
    with open(CREDENTIALS_FILE, 'w') as file:
        json.dump(credentials, file, indent=4)

def register(username, password):
    credentials = load_credentials()
    if username in credentials:
        return False
    credentials[username] = password
    save_credentials(credentials)
    return True

def login(username, password):
    credentials = load_credentials()
    return credentials.get(username) == password

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def get_user_filepath(username):
    return f'budget_data_{username}.json'

def add_expense(expenses, description, amount):
    expenses.append({"description": description, "amount": amount})

def get_total_expenses(expenses):
    return sum(expense['amount'] for expense in expenses)

def get_balance(budget, expenses):
    return budget - get_total_expenses(expenses)

def load_budget_data(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as file:
                data = json.load(file)
                return data.get('initial_budget', 0), data.get('expenses', [])
        except json.JSONDecodeError:
            return 0, []
    return 0, []

def save_budget_data(filepath, initial_budget, expenses):
    data = {'initial_budget': initial_budget, 'expenses': expenses}
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

# ------------------ Authentication ------------------
if "users" not in st.session_state:
    st.session_state.users = {"admin": "admin"}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "Login"

def login(username, password):
    return username in st.session_state.users and st.session_state.users[username] == password

def register(username, password):
    if username in st.session_state.users:
        return False
    st.session_state.users[username] = password
    return True

# ---------- MAIN UI ----------
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.auth_mode == "Login":
            st.markdown("<h3 style='text-align: center;'>🔐 Login</h3>", unsafe_allow_html=True)
            username = st.text_input("👤 Username", key="login_username")
            password = st.text_input("🔑 Password", type="password", key="login_password")
            if st.button("Login"):
                if login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")
        elif st.session_state.auth_mode == "Register":
            st.markdown("<h3 style='text-align: center;'>🆕 Register</h3>", unsafe_allow_html=True)
            new_username = st.text_input("🆕 New Username")
            new_password = st.text_input("🔑 New Password", type="password")
            if st.button("Register"):
                if register(new_username, new_password):
                    st.success("✅ Registered successfully! You can now log in.")
                else:
                    st.error("❌ Username already exists. Try another.")

        st.markdown("---")
        if st.session_state.auth_mode == "Login":
            if st.button("🆕 New here? Register"):
                st.session_state.auth_mode = "Register"
                st.rerun()
        else:
            if st.button("🔐 Already have an account? Login"):
                st.session_state.auth_mode = "Login"
                st.rerun()

# ------------------ Main App ------------------
if st.session_state.get("logged_in"):
    username = st.session_state.username
    filepath = get_user_filepath(username)

    st.sidebar.header(f"👋 Welcome, {username}")
    if st.sidebar.button("🚪 Logout"):
        logout()
        st.rerun()

    # Load data
    initial_budget, expenses = load_budget_data(filepath)

    if 'expenses' not in st.session_state:
        st.session_state.expenses = expenses
    if 'budget' not in st.session_state:
        st.session_state.budget = initial_budget
    if 'edit_index' not in st.session_state:
        st.session_state.edit_index = None

    # Sidebar Budget Input
    st.sidebar.header("📌 Setup Your Budget")
    budget_input = st.sidebar.number_input(
        "💼 Enter Initial Budget",
        min_value=0.0,
        value=float(st.session_state.budget),
        step=100.0,
        format="%.2f"
    )
    st.session_state.budget = budget_input

    # ----------- Handle edit values BEFORE form ----------- #
    description_default = ""
    amount_default = 0.0

    if st.session_state.edit_index is not None:
        try:
            selected_expense = st.session_state.expenses[st.session_state.edit_index]
            description_default = selected_expense["description"]
            amount_default = selected_expense["amount"]
        except IndexError:
            st.session_state.edit_index = None

    # Expense Input Form
    st.subheader("➕ Add / Edit Expense")
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            description = st.text_input("📝 Description", value=description_default)
        with col2:
            amount = st.number_input("💵 Amount", min_value=0.0, format="%.2f", value=amount_default)

        button_label = "✅ Update" if st.session_state.edit_index is not None else "✅ Add"
        submitted = st.form_submit_button(button_label)

        if submitted:
            if description and amount > 0:
                if st.session_state.edit_index is not None:
                    st.session_state.expenses[st.session_state.edit_index] = {
                        "description": description,
                        "amount": amount
                    }
                    st.session_state.edit_index = None
                else:
                    add_expense(st.session_state.expenses, description, amount)
                save_budget_data(filepath, st.session_state.budget, st.session_state.expenses)
                st.rerun()
            else:
                st.warning("⚠️ Please enter valid values.")

    # Budget Summary
    st.subheader("📊 Budget Summary")
    total_spent = get_total_expenses(st.session_state.expenses)
    balance = get_balance(st.session_state.budget, st.session_state.expenses)

    col1, col2, col3 = st.columns(3)
    col1.metric("💼 Budget", f"₹{st.session_state.budget:.2f}")
    col2.metric("💸 Spent", f"₹{total_spent:.2f}")
    col3.metric("💰 Remaining", f"₹{balance:.2f}", delta=f"{balance:.2f}")

    # Expense List with Edit/Delete
    st.subheader("📋 Expense List")
    if st.session_state.expenses:
        for idx, exp in enumerate(st.session_state.expenses):
            col1, col2, col3 = st.columns([4, 2, 2])
            col1.markdown(f"**{exp['description']}** - ₹{exp['amount']:.2f}")
            edit_key = f"edit_{idx}_{exp['description']}_{exp['amount']}"
            delete_key = f"del_{idx}_{exp['description']}_{exp['amount']}"

            if col2.button("✏️ Edit", key=edit_key):
                st.session_state.edit_index = idx
                st.rerun()

            if col3.button("🗑️ Delete", key=delete_key):
                st.session_state.expenses.pop(idx)
                save_budget_data(filepath, st.session_state.budget, st.session_state.expenses)
                st.rerun()
    else:
        st.info("No expenses added yet.")

    # Charts Section
    st.subheader("📈 Visual Insights")
    if st.session_state.expenses:
        df = pd.DataFrame(st.session_state.expenses)
        pie_chart = px.pie(df, names='description', values='amount', title='🔵 Expense Distribution')
        st.plotly_chart(pie_chart, use_container_width=True)

        bar_chart = px.bar(df, x='description', y='amount', title='🟦 Expense by Category', color='description')
        st.plotly_chart(bar_chart, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown("[GitHub](https://github.com/SaiNehaa/Budget_tracker_app)")
