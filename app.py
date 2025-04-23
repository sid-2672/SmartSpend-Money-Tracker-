import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import plotly.express as px
import plotly.graph_objects as go
import datetime
import time
from datetime import datetime, timedelta
import calendar
import uuid
from streamlit_option_menu import option_menu

# MUST BE THE VERY FIRST STREAMLIT COMMAND
st.set_page_config(page_title="SmartSpend - Personal Finance", page_icon="💰", layout="wide")

# Setup paths
base_dir = os.path.expanduser("/home/nhance-dev/Projects/SmartSpend")
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

# Initialize session state variables if they don't exist
def init_session_state():
    if 'theme' not in st.session_state:
        st.session_state.theme = 'light'
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    if 'expenses_history' not in st.session_state:
        st.session_state.expenses_history = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"

# Function to load/save user profile
def save_user_profile(profile, username):
    profile_path = os.path.join(base_dir, f'{username}_profile.json')
    with open(profile_path, 'w') as f:
        json.dump(profile, f)

def load_user_profile(username):
    profile_path = os.path.join(base_dir, f'{username}_profile.json')
    if os.path.exists(profile_path):
        try:
            with open(profile_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return None
    return None

# Function to save expenses
def save_expenses(expenses, username, month=None, year=None):
    if not month:
        month = datetime.now().month
    if not year:
        year = datetime.now().year
    
    expenses_path = os.path.join(base_dir, f'{username}_expenses.json')
    
    if os.path.exists(expenses_path):
        try:
            with open(expenses_path, 'r') as f:
                all_expenses = json.load(f)
        except json.JSONDecodeError:
            all_expenses = {}
    else:
        all_expenses = {}
    
    if str(year) not in all_expenses:
        all_expenses[str(year)] = {}
    if str(month) not in all_expenses[str(year)]:
        all_expenses[str(year)][str(month)] = {}
    
    expenses['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expense_id = str(uuid.uuid4())
    all_expenses[str(year)][str(month)][expense_id] = expenses
    
    with open(expenses_path, 'w') as f:
        json.dump(all_expenses, f)
    
    return expense_id

# Function to load expenses
def load_expenses(username, month=None, year=None):
    expenses_path = os.path.join(base_dir, f'{username}_expenses.json')
    
    if not os.path.exists(expenses_path):
        return {}
    
    try:
        with open(expenses_path, 'r') as f:
            all_expenses = json.load(f)
            
        if not month and not year:
            return all_expenses
        
        if str(year) in all_expenses and str(month) in all_expenses[str(year)]:
            return all_expenses[str(year)][str(month)]
        
        return {}
    except json.JSONDecodeError:
        return {}

# Function to load all expenses for a user
def get_all_user_expenses(username):
    expenses_path = os.path.join(base_dir, f'{username}_expenses.json')
    
    if not os.path.exists(expenses_path):
        return {}
    
    try:
        with open(expenses_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

# Function to add notification
def add_notification(message, type="info"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.notifications.append({
        "message": message,
        "type": type,
        "timestamp": timestamp,
        "read": False
    })

# Function to save budget goals
def save_budget_goals(username, budget_goals):
    budget_path = os.path.join(base_dir, f'{username}_budget.json')
    with open(budget_path, 'w') as f:
        json.dump(budget_goals, f)

# Function to load budget goals
def load_budget_goals(username):
    budget_path = os.path.join(base_dir, f'{username}_budget.json')
    if os.path.exists(budget_path):
        try:
            with open(budget_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

# Toggle theme function
def toggle_theme():
    if st.session_state.theme == 'light':
        st.session_state.theme = 'dark'
    else:
        st.session_state.theme = 'light'

# Calculate potential savings
def calculate_potential_savings(expenses, profile):
    potential_savings = {}
    savings_rates = {
        "Groceries": 0.15 if profile["City_Tier"] == "Tier_1" else 0.12,
        "Transport": 0.20 if profile["City_Tier"] == "Tier_1" else 0.15,
        "Eating_Out": 0.25,
        "Entertainment": 0.20,
        "Utilities": 0.10,
        "Healthcare": 0.05,
        "Education": 0.08,
        "Miscellaneous": 0.15
    }
    
    for category, amount in expenses.items():
        if category in savings_rates:
            potential_savings[category] = round(amount * savings_rates[category], 2)
    
    return potential_savings

# Apply theme CSS
def apply_theme():
    if st.session_state.theme == 'dark':
        st.markdown("""
        <style>
        .main {
            background-color: #1E1E1E;
            color: #FFFFFF;
        }
        .stButton button {
            background-color: #4CAF50;
            color: white;
        }
        .sidebar .sidebar-content {
            background-color: #2D2D2D;
            color: #FFFFFF;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
        }
        .css-145kmo2 {
            color: #FFFFFF !important;
        }
        .stProgress > div > div {
            background-color: #4CAF50 !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        .stButton button {
            background-color: #4CAF50;
            color: white;
        }
        .stProgress > div > div {
            background-color: #4CAF50 !important;
        }
        </style>
        """, unsafe_allow_html=True)

# Function to create sample expenses history
def generate_sample_data(months=6):
    data = {}
    categories = ["Groceries", "Transport", "Eating_Out", "Entertainment", "Utilities", "Healthcare", "Education", "Miscellaneous"]
    
    today = datetime.now()
    
    for i in range(months):
        target_date = today - timedelta(days=30*i)
        year = target_date.year
        month = target_date.month
        
        if str(year) not in data:
            data[str(year)] = {}
        
        if str(month) not in data[str(year)]:
            data[str(year)][str(month)] = {}
        
        for j in range(np.random.randint(3, 6)):
            expense_data = {}
            for category in categories:
                base_amount = np.random.randint(500, 5000)
                variation = np.random.uniform(0.8, 1.2)
                expense_data[category] = round(base_amount * variation)
            
            expense_id = str(uuid.uuid4())
            expense_data['timestamp'] = (target_date - timedelta(days=np.random.randint(1, 28))).strftime("%Y-%m-%d %H:%M:%S")
            data[str(year)][str(month)][expense_id] = expense_data
    
    return data

# Main app function
def main():
    init_session_state()
    apply_theme()

    # Sidebar Setup
    with st.sidebar:
        st.image("https://via.placeholder.com/150x80?text=SmartSpend", width=150)
        st.title("SmartSpend")
        
        # Theme toggle
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Theme:")
        with col2:
            theme_icon = "🌙" if st.session_state.theme == 'light' else "☀️"
            if st.button(theme_icon):
                toggle_theme()
                st.rerun()
        
        st.divider()
        
        # Sidebar Navigation Menu
        selected = option_menu(
            menu_title=None,
            options=["Dashboard", "Profile", "Expenses", "Budget", "Analytics", "Notifications"],
            icons=["house", "person", "cash-coin", "piggy-bank", "graph-up", "bell"],
            menu_icon="cast",
            default_index=0,
        )
        
        st.session_state.current_page = selected
        
        # Profile Selection
        st.divider()
        st.header("User Profile Setup")
        
        profiles = [f.split('_profile.json')[0] for f in os.listdir(base_dir) if f.endswith('_profile.json')]
        username = st.selectbox("Select or Create a Profile", options=["-- Create New Profile --"] + profiles)

        # Load profile if selected
        profile = None
        if username != "-- Create New Profile --":
            profile = load_user_profile(username)
            if profile:
                st.write(f"Hello, {profile['Name']}!")
                st.write(f"Age: {profile['Age']}, Occupation: {profile['Occupation']}")
                st.write(f"Income: ₹{profile['Income']}, City Tier: {profile['City_Tier']}")
                st.write(f"Dependents: {profile['Dependents']}, Desired Savings: {profile['Desired_Savings_Percentage']}%")
            else:
                st.warning("No valid profile found. Please create a new one.")

    # Display different pages based on selected menu
    if st.session_state.current_page == "Dashboard":
        st.title("💸 SmartSpend - Dashboard")
        
        if profile:
            # Display quick stats
            st.subheader("Financial Overview")
            
            col1, col2, col3 = st.columns(3)
            
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            current_expenses = load_expenses(username, current_month, current_year)
            
            monthly_total = 0
            category_totals = {"Groceries": 0, "Transport": 0, "Eating_Out": 0, "Entertainment": 0, 
                              "Utilities": 0, "Healthcare": 0, "Education": 0, "Miscellaneous": 0}
            
            for expense_id, expense_data in current_expenses.items():
                for category, amount in expense_data.items():
                    if category in category_totals:
                        category_totals[category] += amount
                        monthly_total += amount
            
            if monthly_total == 0:
                st.info("No expenses recorded for this month. Showing sample data for demonstration.")
                if 'sample_data' not in st.session_state:
                    st.session_state.sample_data = generate_sample_data()
                
                if str(current_year) in st.session_state.sample_data and str(current_month) in st.session_state.sample_data[str(current_year)]:
                    sample_month_data = st.session_state.sample_data[str(current_year)][str(current_month)]
                    
                    for expense_id, expense_data in sample_month_data.items():
                        for category, amount in expense_data.items():
                            if category in category_totals:
                                category_totals[category] += amount
                                monthly_total += amount
            
            with col1:
                st.metric("Monthly Income", f"₹{profile['Income']:,}")
            
            with col2:
                st.metric("Total Expenses", f"₹{monthly_total:,}")
            
            with col3:
                savings = profile['Income'] - monthly_total
                savings_percentage = (savings / profile['Income']) * 100 if profile['Income'] > 0 else 0
                diff = savings_percentage - profile['Desired_Savings_Percentage']
                
                st.metric("Savings", f"₹{savings:,} ({savings_percentage:.1f}%)", 
                         delta=f"{diff:.1f}%" if diff != 0 else None,
                         delta_color="normal" if diff >= 0 else "inverse")
            
            # Budget tracking progress bars
            st.subheader("Budget Tracking")
            
            budget_goals = load_budget_goals(username)
            
            if not budget_goals:
                budget_goals = {
                    "Groceries": profile['Income'] * 0.2,
                    "Transport": profile['Income'] * 0.1,
                    "Eating_Out": profile['Income'] * 0.1,
                    "Entertainment": profile['Income'] * 0.05,
                    "Utilities": profile['Income'] * 0.15,
                    "Healthcare": profile['Income'] * 0.05,
                    "Education": profile['Income'] * 0.1,
                    "Miscellaneous": profile['Income'] * 0.05
                }
            
            for category, budget in budget_goals.items():
                spent = category_totals[category]
                percentage = (spent / budget) * 100 if budget > 0 else 0
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.progress(min(percentage/100, 1.0))
                with col2:
                    st.write(f"{category}: ₹{spent:,} / ₹{budget:,}")
                
                if percentage > 90:
                    if percentage > 100:
                        st.warning(f"⚠️ Overspent on {category} by ₹{spent - budget:,}")
                    else:
                        st.info(f"ℹ️ Close to {category} budget limit ({percentage:.1f}%)")
            
            # Recent activity
            st.subheader("Recent Activity")
            
            all_expenses = get_all_user_expenses(username)
            
            if not all_expenses:
                all_expenses = st.session_state.sample_data if 'sample_data' in st.session_state else generate_sample_data()
            
            recent_activities = []
            for year in all_expenses:
                for month in all_expenses[year]:
                    for expense_id, expense_data in all_expenses[year][month].items():
                        if 'timestamp' in expense_data:
                            timestamp = expense_data['timestamp']
                            total = sum([expense_data[cat] for cat in category_totals.keys() if cat in expense_data])
                            recent_activities.append({
                                "Date": timestamp,
                                "Total": total,
                                "Details": expense_data
                            })
            
            recent_activities.sort(key=lambda x: x["Date"], reverse=True)
            recent_activities = recent_activities[:5]
            
            for idx, activity in enumerate(recent_activities):
                with st.expander(f"Expense on {activity['Date']} - ₹{activity['Total']:,}"):
                    for category, amount in activity['Details'].items():
                        if category in category_totals:
                            st.write(f"{category}: ₹{amount:,}")
            
            # Quick insights
            st.subheader("Quick Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                expense_data = pd.DataFrame(list(category_totals.items()), columns=["Category", "Amount"])
                expense_data = expense_data[expense_data["Amount"] > 0]
                
                if not expense_data.empty:
                    fig = px.pie(expense_data, names="Category", values="Amount", title="Expense Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No expense data to show")
            
            with col2:
                sorted_expenses = expense_data.sort_values("Amount", ascending=False)
                
                if not sorted_expenses.empty:
                    fig2 = px.bar(sorted_expenses.head(3), x="Category", y="Amount", title="Top Spending Categories")
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No expense data to show")
        else:
            st.info("Please select or create a user profile to view the dashboard")

    elif st.session_state.current_page == "Profile":
        st.title("User Profile")
        
        if username == "-- Create New Profile --":
            st.subheader("Create a New Profile")
            
            col1, col2 = st.columns(2)
            with col1:
                user_name = st.text_input("Name")
                age = st.number_input("Age", min_value=18, max_value=120)
                occupation = st.selectbox("Occupation", ["Professional", "Self_Employed", "Student", "Retired"])
            
            with col2:
                city_tier = st.selectbox("City Tier", ["Tier_1", "Tier_2", "Tier_3"])
                income = st.number_input("Monthly Income (₹)", min_value=1000)
                dependents = st.number_input("Dependents", min_value=0)
            
            st.subheader("Financial Goals")
            desired_savings_percentage = st.slider("Desired Savings Percentage", min_value=0, max_value=50, value=20, step=1)
            
            with st.expander("Advanced Profile Settings"):
                financial_goals = st.text_area("Financial Goals (Optional)", 
                                            placeholder="Example: Save for a house down payment in 2 years")
                risk_profile = st.select_slider("Investment Risk Profile", 
                                            options=["Conservative", "Moderate", "Aggressive"], value="Moderate")
                has_investments = st.checkbox("I have existing investments")
                has_loans = st.checkbox("I have existing loans")
            
            if st.button("Save Profile"):
                profile = {
                    "Name": user_name,
                    "Age": age,
                    "Occupation": occupation,
                    "City_Tier": city_tier,
                    "Income": income,
                    "Dependents": dependents,
                    "Desired_Savings_Percentage": desired_savings_percentage,
                    "Financial_Goals": financial_goals if 'financial_goals' in locals() else "",
                    "Risk_Profile": risk_profile if 'risk_profile' in locals() else "Moderate",
                    "Has_Investments": has_investments if 'has_investments' in locals() else False,
                    "Has_Loans": has_loans if 'has_loans' in locals() else False
                }
                save_user_profile(profile, user_name)
                st.success(f"Profile for {user_name} saved successfully!")
                add_notification(f"New profile created for {user_name}", "success")
                st.session_state.current_page = "Dashboard"
                st.rerun()

        
        elif profile:
            st.subheader(f"Edit Profile for {profile['Name']}")
            
            col1, col2 = st.columns(2)
            with col1:
                age = st.number_input("Age", min_value=18, max_value=120, value=profile.get('Age', 30))
                occupation = st.selectbox("Occupation", 
                                     options=["Professional", "Self_Employed", "Student", "Retired"],
                                     index=["Professional", "Self_Employed", "Student", "Retired"].index(profile.get('Occupation', 'Professional')))
            
            with col2:
                city_tier = st.selectbox("City Tier", 
                                    options=["Tier_1", "Tier_2", "Tier_3"],
                                    index=["Tier_1", "Tier_2", "Tier_3"].index(profile.get('City_Tier', 'Tier_1')))
                income = st.number_input("Monthly Income (₹)", min_value=1000, value=profile.get('Income', 50000))
                dependents = st.number_input("Dependents", min_value=0, value=profile.get('Dependents', 0))
            
            st.subheader("Financial Goals")
            desired_savings_percentage = st.slider("Desired Savings Percentage", 
                                              min_value=0, max_value=50, 
                                              value=profile.get('Desired_Savings_Percentage', 20), 
                                              step=1)
            
            with st.expander("Advanced Profile Settings"):
                financial_goals = st.text_area("Financial Goals", 
                                            value=profile.get('Financial_Goals', ""))
                risk_profile = st.select_slider("Investment Risk Profile", 
                                            options=["Conservative", "Moderate", "Aggressive"], 
                                            value=profile.get('Risk_Profile', "Moderate"))
                has_investments = st.checkbox("I have existing investments", value=profile.get('Has_Investments', False))
                has_loans = st.checkbox("I have existing loans", value=profile.get('Has_Loans', False))
            
            if st.button("Update Profile"):
                updated_profile = {
                    "Name": profile["Name"],
                    "Age": age,
                    "Occupation": occupation,
                    "City_Tier": city_tier,
                    "Income": income,
                    "Dependents": dependents,
                    "Desired_Savings_Percentage": desired_savings_percentage,
                    "Financial_Goals": financial_goals,
                    "Risk_Profile": risk_profile,
                    "Has_Investments": has_investments,
                    "Has_Loans": has_loans
                }
                save_user_profile(updated_profile, profile["Name"])
                st.success(f"Profile for {profile['Name']} updated successfully!")
                add_notification(f"Profile updated for {profile['Name']}", "success")
                st.rerun()

        else:
            st.info("Please select a user profile to edit or create a new one")

    elif st.session_state.current_page == "Expenses":
        st.title("Expense Tracker")
        
        if profile:
            tab1, tab2 = st.tabs(["Enter Expenses", "Expense History"])
            
            with tab1:
                st.subheader("Enter Your Monthly Expenses")
                
                col1, col2 = st.columns(2)
                with col1:
                    current_month = datetime.now().month
                    current_year = datetime.now().year
                    
                    month = st.selectbox("Month", 
                                     options=list(range(1, 13)),
                                     index=current_month - 1,
                                     format_func=lambda x: calendar.month_name[x])
                
                with col2:
                    year = st.selectbox("Year", 
                                   options=list(range(current_year - 2, current_year + 1)),
                                   index=2)
                
                categories = {
                    "Groceries": "Food items, household supplies, etc.",
                    "Transport": "Fuel, public transport, ride-sharing, etc.",
                    "Eating_Out": "Restaurants, cafes, food delivery, etc.",
                    "Entertainment": "Movies, events, subscriptions, etc.",
                    "Utilities": "Electricity, water, internet, mobile, etc.",
                    "Healthcare": "Medicines, doctor visits, insurance, etc.",
                    "Education": "Courses, books, tuition, etc.",
                    "Miscellaneous": "Other expenses not fitting above categories"
                }
                
                expenses = {}
                st.write("Fill in your expenses for each category:")
                
                col1, col2 = st.columns(2)
                cat_list = list(categories.items())
                mid_point = len(cat_list) // 2
                
                with col1:
                    for category, description in cat_list[:mid_point]:
                        expenses[category] = st.number_input(
                            f"{category} (₹)", 
                            min_value=0,
                            help=description,
                            key=f"expense_{category}"
                        )
                
                with col2:
                    for category, description in cat_list[mid_point:]:
                        expenses[category] = st.number_input(
                            f"{category} (₹)", 
                            min_value=0,
                            help=description,
                            key=f"expense_{category}"
                        )
                
                notes = st.text_area("Notes (Optional)", placeholder="Any additional information about this month's expenses")
                
                if st.button("Save Expenses"):
                    expenses["notes"] = notes
                    expense_id = save_expenses(expenses, username, month, year)
                    st.success("Expenses saved successfully!")
                    total_expense = sum([
    float(amount) for category, amount in expenses.items()
    if category != "notes" and str(amount).replace('.', '', 1).isdigit()
])
                    add_notification(f"New expense entry of ₹{total_expense:,} added", "success")
                    
                    budget_goals = load_budget_goals(username)
                    if budget_goals:
                        warnings = []
                        for category, amount in expenses.items():
                            if category in budget_goals and category != "notes":
                                if amount > budget_goals[category]:
                                    warnings.append(f"Overspent on {category} by ₹{amount - budget_goals[category]:,}")
                        
                        if warnings:
                            warning_msg = "\n".join(warnings)
                            st.warning(warning_msg)
                            add_notification("Budget alert: " + ", ".join(warnings), "warning")
            
            with tab2:
                st.subheader("Expense History")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    history_month = st.selectbox("Filter by Month", 
                                            options=[0] + list(range(1, 13)),
                                            index=0,
                                            format_func=lambda x: "All Months" if x == 0 else calendar.month_name[x],
                                            key="history_month")
                
                with col2:
                    history_year = st.selectbox("Filter by Year", 
                                           options=[0] + list(range(datetime.now().year - 2, datetime.now().year + 1)),
                                           index=0,
                                           format_func=lambda x: "All Years" if x == 0 else str(x),
                                           key="history_year")
                
                all_expenses = get_all_user_expenses(username)
                
                if not all_expenses:
                    if 'sample_data' not in st.session_state:
                        st.session_state.sample_data = generate_sample_data()
                    all_expenses = st.session_state.sample_data
                
                filtered_expenses = []
                
                for year_key, year_data in all_expenses.items():
                    if history_year != 0 and str(history_year) != year_key:
                        continue
                        
                    for month_key, month_data in year_data.items():
                        if history_month != 0 and str(history_month) != month_key:
                            continue
                            
                        for expense_id, expense_data in month_data.items():
                            expense_total = sum([
                                expense_data[cat] for cat in categories.keys() 
                                if cat in expense_data and isinstance(expense_data[cat], (int, float))
                            ])
                            
                            timestamp = expense_data.get('timestamp', f"{year_key}-{month_key}-01 00:00:00")
                            try:
                                date_obj = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                                formatted_date = date_obj.strftime("%b %d, %Y")
                            except:
                                formatted_date = f"{calendar.month_name[int(month_key)]} {year_key}"
                            
                            filtered_expenses.append({
                                "id": expense_id,
                                "date": formatted_date,
                                "timestamp": timestamp,
                                "total": expense_total,
                                "details": expense_data
                            })
                
                filtered_expenses.sort(key=lambda x: x["timestamp"], reverse=True)
                
                if filtered_expenses:
                    for expense in filtered_expenses:
                        with st.expander(f"{expense['date']} - ₹{expense['total']:,}"):
                            col1, col2 = st.columns(2)
                            items = [(cat, expense['details'].get(cat, 0)) for cat in categories.keys()]
                            mid_point = len(items) // 2
                            
                            with col1:
                                for category, amount in items[:mid_point]:
                                    st.write(f"**{category}:** ₹{amount:,}")
                            
                            with col2:
                                for category, amount in items[mid_point:]:
                                    st.write(f"**{category}:** ₹{amount:,}")
                            
                            if 'notes' in expense['details'] and expense['details']['notes']:
                                st.write("**Notes:**")
                                st.write(expense['details']['notes'])
                else:
                    st.info("No expense records found for the selected filters.")
        else:
            st.info("Please select or create a user profile to track expenses")

    elif st.session_state.current_page == "Budget":
        st.title("Budget Planning & Tracking")
        
        if profile:
            budget_goals = load_budget_goals(username)
            
            if not budget_goals:
                budget_goals = {
                    "Groceries": profile['Income'] * 0.2,
                    "Transport": profile['Income'] * 0.1,
                    "Eating_Out": profile['Income'] * 0.1,
                    "Entertainment": profile['Income'] * 0.05,
                    "Utilities": profile['Income'] * 0.15,
                    "Healthcare": profile['Income'] * 0.05,
                    "Education": profile['Income'] * 0.1,
                    "Miscellaneous": profile['Income'] * 0.05
                }
            
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            current_expenses = load_expenses(username, current_month, current_year)
            
            monthly_total = 0
            category_totals = {"Groceries": 0, "Transport": 0, "Eating_Out": 0, "Entertainment": 0, 
                              "Utilities": 0, "Healthcare": 0, "Education": 0, "Miscellaneous": 0}
            
            for expense_id, expense_data in current_expenses.items():
                for category, amount in expense_data.items():
                    if category in category_totals:
                        category_totals[category] += amount
                        monthly_total += amount
            
            if monthly_total == 0:
                if 'sample_data' not in st.session_state:
                    st.session_state.sample_data = generate_sample_data()
                
                if str(current_year) in st.session_state.sample_data and str(current_month) in st.session_state.sample_data[str(current_year)]:
                    sample_month_data = st.session_state.sample_data[str(current_year)][str(current_month)]
                    
                    for expense_id, expense_data in sample_month_data.items():
                        for category, amount in expense_data.items():
                            if category in category_totals:
                                category_totals[category] += amount
                                monthly_total += amount
            
            st.subheader("Set Your Budget Goals")
            
            col1, col2 = st.columns(2)
            updated_budget = {}
            
            with col1:
                for i, category in enumerate(list(category_totals.keys())[:4]):
                    updated_budget[category] = st.number_input(
                        f"{category} Budget (₹)",
                        min_value=0,
                        value=int(budget_goals.get(category, 0)),
                        key=f"budget_{category}"
                    )
            
            with col2:
                for i, category in enumerate(list(category_totals.keys())[4:]):
                    updated_budget[category] = st.number_input(
                        f"{category} Budget (₹)",
                        min_value=0,
                        value=int(budget_goals.get(category, 0)),
                        key=f"budget_{category}"
                    )
            
            if st.button("Save Budget Goals"):
                save_budget_goals(username, updated_budget)
                st.success("Budget goals saved successfully!")
                add_notification("Budget goals updated", "success")
                st.rerun()
            
            st.subheader("Budget Progress for Current Month")
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write("**Category**")
            with col2:
                st.write("**Budget**")
            with col3:
                st.write("**Spent**")
            with col4:
                st.write("**Remaining**")
            
            st.markdown("---")
            
            for category in category_totals.keys():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                budget = budget_goals.get(category, 0)
                spent = category_totals.get(category, 0)
                remaining = budget - spent
                percentage = (spent / budget) * 100 if budget > 0 else 0
                
                with col1:
                    st.write(category)
                    st.progress(min(percentage/100, 1.0))
                
                with col2:
                    st.write(f"₹{budget:,}")
                
                with col3:
                    st.write(f"₹{spent:,}")
                
                with col4:
                    if remaining >= 0:
                        st.write(f"₹{remaining:,}")
                    else:
                        st.write(f"**-₹{abs(remaining):,}**")
            
            st.markdown("---")
            total_budget = sum(budget_goals.values())
            
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.write("**TOTAL**")
                overall_percentage = (monthly_total / total_budget) * 100 if total_budget > 0 else 0
                st.progress(min(overall_percentage/100, 1.0))
            
            with col2:
                st.write(f"**₹{total_budget:,}**")
            
            with col3:
                st.write(f"**₹{monthly_total:,}**")
            
            with col4:
                remaining = total_budget - monthly_total
                if remaining >= 0:
                    st.write(f"**₹{remaining:,}**")
                else:
                    st.write(f"**-₹{abs(remaining):,}**")
            
            st.subheader("Smart Budget Suggestions")
            
            savings = profile['Income'] - monthly_total
            savings_percentage = (savings / profile['Income']) * 100 if profile['Income'] > 0 else 0
            
            if savings_percentage < profile['Desired_Savings_Percentage']:
                st.warning(f"You're currently saving {savings_percentage:.1f}% of your income, which is below your goal of {profile['Desired_Savings_Percentage']}%.")
                
                overspent_categories = []
                for category, spent in category_totals.items():
                    budget = budget_goals.get(category, 0)
                    if spent > budget:
                        overspent_categories.append((category, spent - budget))
                
                if overspent_categories:
                    st.write("Consider reducing spending in these categories:")
                    for category, amount in sorted(overspent_categories, key=lambda x: x[1], reverse=True):
                        st.write(f"- {category}: Over budget by ₹{amount:,}")
            else:
                st.success(f"Great job! You're saving {savings_percentage:.1f}% of your income, which meets or exceeds your goal of {profile['Desired_Savings_Percentage']}%.")
                
                if savings > 10000:
                    st.write("Consider putting some of your savings into investments:")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("- Emergency fund (3-6 months of expenses)")
                        st.write("- Fixed deposits for short-term goals")
                    with col2:
                        st.write("- Mutual funds for long-term growth")
                        st.write("- Tax-saving investments")
        else:
            st.info("Please select or create a user profile to plan your budget")

    elif st.session_state.current_page == "Analytics":
        st.title("Financial Analytics")
        
        if profile:
            all_expenses = get_all_user_expenses(username)
            
            if not all_expenses:
                if 'sample_data' not in st.session_state:
                    st.session_state.sample_data = generate_sample_data()
                all_expenses = st.session_state.sample_data
            
            monthly_totals = []
            category_trends = {category: [] for category in ["Groceries", "Transport", "Eating_Out", "Entertainment", 
                                                          "Utilities", "Healthcare", "Education", "Miscellaneous"]}
            
            for year in sorted(all_expenses.keys()):
                for month in sorted(all_expenses[year].keys()):
                    month_data = all_expenses[year][month]
                    
                    month_categories = {category: 0 for category in category_trends.keys()}
                    
                    for expense_id, expense_data in month_data.items():
                        for category in category_trends.keys():
                            if category in expense_data:
                                month_categories[category] += expense_data[category]
                    
                    month_total = sum(month_categories.values())
                    month_name = f"{calendar.month_abbr[int(month)]} {year}"
                    monthly_totals.append({"Month": month_name, "Total": month_total, "Sort_Key": f"{year}-{month:02d}"})
                    
                    for category, amount in month_categories.items():
                        category_trends[category].append({"Month": month_name, "Amount": amount, "Category": category, "Sort_Key": f"{year}-{month:02d}"})
            
            monthly_totals.sort(key=lambda x: x["Sort_Key"])
            flat_category_trends = []
            for category, data in category_trends.items():
                sorted_data = sorted(data, key=lambda x: x["Sort_Key"])
                for item in sorted_data:
                    flat_category_trends.append(item)
            
            tab1, tab2, tab3 = st.tabs(["Spending Trends", "Category Analysis", "Savings Analysis"])
            
            with tab1:
                st.subheader("Monthly Spending Trends")
                
                if monthly_totals:
                    fig = px.line(monthly_totals, x="Month", y="Total", 
                              title="Total Monthly Expenses",
                              labels={"Total": "Expense (₹)", "Month": ""},
                              markers=True)
                    
                    fig.update_layout(xaxis={'categoryorder':'array', 'categoryarray':[d["Month"] for d in monthly_totals]})
                    st.plotly_chart(fig, use_container_width=True)
                    
                    avg_spending = sum(item["Total"] for item in monthly_totals) / len(monthly_totals)
                    max_month = max(monthly_totals, key=lambda x: x["Total"])
                    min_month = min(monthly_totals, key=lambda x: x["Total"])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Monthly Spending", f"₹{avg_spending:,.2f}")
                    with col2:
                        st.metric("Highest Spending Month", f"{max_month['Month']}: ₹{max_month['Total']:,}")
                    with col3:
                        st.metric("Lowest Spending Month", f"{min_month['Month']}: ₹{min_month['Total']:,}")
                    
                    if len(monthly_totals) > 1:
                        recent_months = monthly_totals[-3:] if len(monthly_totals) >= 3 else monthly_totals
                        recent_avg = sum(item["Total"] for item in recent_months) / len(recent_months)
                        
                        if recent_avg > avg_spending * 1.1:
                            st.warning("⚠️ Your recent spending is higher than your historical average.")
                        elif recent_avg < avg_spending * 0.9:
                            st.success("👍 Your recent spending is lower than your historical average.")
                else:
                    st.info("Not enough data to show spending trends")
            
            with tab2:
                st.subheader("Category Spending Analysis")
                
                if flat_category_trends:
                    fig = px.bar(flat_category_trends, x="Month", y="Amount", color="Category",
                             title="Monthly Spending by Category",
                             labels={"Amount": "Expense (₹)", "Month": ""},
                             barmode="stack")
                    
                    unique_months = list(set(item["Month"] for item in flat_category_trends))
                    unique_months.sort(key=lambda m: next(item["Sort_Key"] for item in flat_category_trends if item["Month"] == m))
                    fig.update_layout(xaxis={'categoryorder':'array', 'categoryarray': unique_months})
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    if len(monthly_totals) > 0:
                        st.subheader("Category Comparison")
                        
                        category_avgs = {}
                        for category in category_trends:
                            if category_trends[category]:
                                category_avgs[category] = sum(item["Amount"] for item in category_trends[category]) / len(category_trends[category])
                        
                        sorted_categories = sorted(category_avgs.items(), key=lambda x: x[1], reverse=True)
                        
                        category_avg_data = [{"Category": cat, "Average": avg} for cat, avg in sorted_categories]
                        fig2 = px.bar(category_avg_data, y="Category", x="Average", 
                                 title="Average Monthly Spending by Category",
                                 labels={"Average": "Average Expense (₹)"},
                                 orientation="h")
                        
                        st.plotly_chart(fig2, use_container_width=True)
                        
                        if sorted_categories:
                            top_category = sorted_categories[0]
                            st.write(f"Your highest spending category is **{top_category[0]}** with an average of ₹{top_category[1]:,.2f} per month.")
                            
                            category_percent = (top_category[1] / avg_spending) * 100
                            st.write(f"This represents **{category_percent:.1f}%** of your monthly expenses.")
                            
                            if category_percent > 30:
                                st.warning("This category consumes a significant portion of your budget. Consider finding ways to reduce spending here.")
                else:
                    st.info("Not enough data to show category analysis")
            
            with tab3:
                st.subheader("Savings Analysis")
                
                if monthly_totals:
                    savings_data = []
                    
                    for item in monthly_totals:
                        savings = profile["Income"] - item["Total"]
                        savings_percent = (savings / profile["Income"]) * 100 if profile["Income"] > 0 else 0
                        savings_data.append({
                            "Month": item["Month"],
                            "Savings": savings,
                            "SavingsPercent": savings_percent,
                            "Sort_Key": item["Sort_Key"]
                        })
                    
                    savings_data.sort(key=lambda x: x["Sort_Key"])
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Scatter(
                        x=[item["Month"] for item in savings_data],
                        y=[item["Savings"] for item in savings_data],
                        name="Savings (₹)",
                        line=dict(color="green", width=3),
                        mode="lines+markers"
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=[item["Month"] for item in savings_data],
                        y=[item["SavingsPercent"] for item in savings_data],
                        name="Savings %",
                        line=dict(color="blue", width=3, dash="dot"),
                        mode="lines+markers",
                        yaxis="y2"
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=[item["Month"] for item in savings_data],
                        y=[profile["Desired_Savings_Percentage"]] * len(savings_data),
                        name="Target Savings %",
                        line=dict(color="red", width=2, dash="dash"),
                        yaxis="y2"
                    ))
                    
                    fig.update_layout(
                        title="Monthly Savings Analysis",
                        yaxis=dict(title="Savings (₹)", side="left"),
                        yaxis2=dict(
                            title="Savings %",
                            side="right",
                            overlaying="y",
                            tickmode="auto",
                            range=[0, max(max(item["SavingsPercent"] for item in savings_data) * 1.1, profile["Desired_Savings_Percentage"] * 1.2)]
                        ),
                        legend=dict(x=0.05, y=1, traceorder="normal"),
                        hovermode="x unified"
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    avg_savings_percent = sum(item["SavingsPercent"] for item in savings_data) / len(savings_data)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Average Monthly Savings", 
                              f"₹{sum(item['Savings'] for item in savings_data) / len(savings_data):,.2f}")
                    
                    with col2:
                        st.metric("Average Savings Percentage", 
                              f"{avg_savings_percent:.1f}%", 
                              delta=f"{avg_savings_percent - profile['Desired_Savings_Percentage']:.1f}%",
                              delta_color="normal" if avg_savings_percent >= profile['Desired_Savings_Percentage'] else "inverse")
                    
                    if profile.get("Financial_Goals"):
                        st.subheader("Progress Towards Financial Goals")
                        st.write(profile["Financial_Goals"])
                        
                        total_saved = sum(item["Savings"] for item in savings_data)
                        st.write(f"Total saved so far: ₹{total_saved:,}")
                        
                        if len(savings_data) > 0:
                            avg_monthly_savings = sum(item["Savings"] for item in savings_data) / len(savings_data)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Projected 1-Year Savings", f"₹{avg_monthly_savings * 12:,.2f}")
                            with col2:
                                st.metric("Projected 3-Year Savings", f"₹{avg_monthly_savings * 36:,.2f}")
                            with col3:
                                st.metric("Projected 5-Year Savings", f"₹{avg_monthly_savings * 60:,.2f}")
                else:
                    st.info("Not enough data to show savings analysis")
        else:
            st.info("Please select or create a user profile to view analytics")

    elif st.session_state.current_page == "Notifications":
        st.title("Notifications & Alerts")
        
        notifications = sorted(st.session_state.notifications, key=lambda x: x["timestamp"], reverse=True)
        
        if notifications:
            col1, col2 = st.columns(2)
            with col1:
                filter_type = st.selectbox("Filter by Type", 
                                       options=["All", "info", "success", "warning", "error"], 
                                       index=0)
            
            with col2:
                mark_all_read = st.button("Mark All As Read")
                if mark_all_read:
                    for notif in st.session_state.notifications:
                        notif["read"] = True
                    st.success("All notifications marked as read")
                    time.sleep(1)
                    st.rerun()
            
            if filter_type != "All":
                filtered_notifications = [n for n in notifications if n["type"] == filter_type]
            else:
                filtered_notifications = notifications
            
            for idx, notification in enumerate(filtered_notifications):
                if notification["type"] == "success":
                    icon = "✅"
                    bg_color = "#d4edda"
                    text_color = "#155724"
                elif notification["type"] == "warning":
                    icon = "⚠️"
                    bg_color = "#fff3cd"
                    text_color = "#856404"
                elif notification["type"] == "error":
                    icon = "❌"
                    bg_color = "#f8d7da"
                    text_color = "#721c24"
                else:
                    icon = "ℹ️"
                    bg_color = "#d1ecf1"
                    text_color = "#0c5460"
                
                with st.expander(f"{icon} {notification['message']} ({notification['timestamp']})"):
                    st.write(f"**Type:** {notification['type'].capitalize()}")
                    st.write(f"**Time:** {notification['timestamp']}")
                    
                    if not notification["read"]:
                        mark_read = st.button("Mark as Read", key=f"mark_read_{idx}")
                        if mark_read:
                            notification["read"] = True
                            st.success("Notification marked as read")
                            time.sleep(1)
                            st.rerun()

                    else:
                        st.write("**Status:** Read")
        else:
            st.info("No notifications to display")
            
            if st.button("Generate Sample Notifications"):
                add_notification("Welcome to SmartSpend!", "info")
                add_notification("Profile created successfully", "success")
                add_notification("You're close to your budget limit for Groceries", "warning")
                add_notification("Failed to save expenses", "error")
                st.rerun()

    # Add footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: gray;">
            <p>SmartSpend - Personal Finance Management App</p>
            <p>© 2023 All rights reserved</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
