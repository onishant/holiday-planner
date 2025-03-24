import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import plotly.express as px
import json
import os
from datetime import date
import hashlib

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to load user credentials
def load_users(filename='users.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

# Function to save user credentials
def save_users(users, filename='users.json'):
    with open(filename, 'w') as f:
        json.dump(users, f)

# Function to serialize datetime objects for JSON
def serialize_dates(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError("Type not serializable")

# Function to deserialize datetime objects from JSON
def deserialize_dates(plan):
    plan['start_date'] = datetime.strptime(plan['start_date'], '%Y-%m-%d').date()
    plan['end_date'] = datetime.strptime(plan['end_date'], '%Y-%m-%d').date()
    return plan

def save_to_json(holiday_plans, username, filename='holiday_plans.json'):
    """Save holiday plans to a JSON file"""
    try:
        # Load existing data
        all_plans = {}
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                all_plans = json.load(f)
        
        # Update with current user's plans
        all_plans[username] = holiday_plans
        
        # Save back to file
        with open(filename, 'w') as f:
            json.dump(all_plans, f, default=serialize_dates, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def load_from_json(username, filename='holiday_plans.json'):
    """Load holiday plans from a JSON file"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                data = json.load(f)
                if username in data:
                    # Convert string dates back to datetime objects
                    return {k: deserialize_dates(v) for k, v in data[username].items()}
        return {}
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return {}

def login_page():
    st.title("🌴 Holiday Planner Login")
    
    # Initialize users if not exists
    if 'users' not in st.session_state:
        st.session_state.users = load_users()
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if username in st.session_state.users:
                    if st.session_state.users[username] == hash_password(password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.rerun()
                    else:
                        st.error("Incorrect password")
                else:
                    st.error("Username not found")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register = st.form_submit_button("Register")
            
            if register:
                if new_username in st.session_state.users:
                    st.error("Username already exists")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    st.session_state.users[new_username] = hash_password(new_password)
                    save_users(st.session_state.users)
                    st.success("Registration successful! Please login.")

def add_holiday_plan(name, start_date, end_date, travel_cost, accommodation_cost, 
                    experiences_cost, misc_cost):
    plan_id = str(uuid.uuid4())
    total_cost = travel_cost + accommodation_cost + experiences_cost + misc_cost
    
    st.session_state.holiday_plans[plan_id] = {
        'name': name,
        'start_date': start_date,
        'end_date': end_date,
        'travel_cost': travel_cost,
        'accommodation_cost': accommodation_cost,
        'experiences_cost': experiences_cost,
        'misc_cost': misc_cost,
        'total_cost': total_cost
    }
    # Save to JSON file after adding new plan
    save_to_json(st.session_state.holiday_plans, st.session_state.username)

def remove_holiday_plan(plan_id):
    if plan_id in st.session_state.holiday_plans:
        del st.session_state.holiday_plans[plan_id]
        # Save to JSON file after removing plan
        save_to_json(st.session_state.holiday_plans, st.session_state.username)

def main():
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    # Show login page if not logged in
    if not st.session_state.logged_in:
        login_page()
        return
    
    # Initialize holiday plans for logged-in user
    if 'holiday_plans' not in st.session_state:
        st.session_state.holiday_plans = load_from_json(st.session_state.username)
    
    # Add logout button
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title("🌴 Holiday Planning & Budget Tracker")
    with col2:
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
    
    st.write(f"Welcome, {st.session_state.username}!")
    
    # Add new holiday plan section
    st.header("Add New Holiday Plan")
    with st.form("holiday_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Holiday Destination")
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
        
        with col2:
            travel_cost = st.number_input("Travel Cost", min_value=0.0, value=0.0)
            accommodation_cost = st.number_input("Accommodation Cost", min_value=0.0, value=0.0)
            experiences_cost = st.number_input("Experiences Cost", min_value=0.0, value=0.0)
            misc_cost = st.number_input("Miscellaneous Cost", min_value=0.0, value=0.0)
        
        submit_button = st.form_submit_button("Add Holiday Plan")
        
        if submit_button:
            if name and start_date <= end_date:
                add_holiday_plan(name, start_date, end_date, travel_cost, 
                               accommodation_cost, experiences_cost, misc_cost)
                st.success("Holiday plan added successfully!")
            else:
                st.error("Please check your inputs and try again.")

    # Display existing holiday plans
    st.header("Your Holiday Plans")
    if st.session_state.holiday_plans:
        for plan_id, plan in st.session_state.holiday_plans.items():
            with st.expander(f"🏖️ {plan['name']} ({plan['start_date']} to {plan['end_date']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Duration:**", (plan['end_date'] - plan['start_date']).days + 1, "days")
                    st.write("**Travel Cost:** $", plan['travel_cost'])
                    st.write("**Accommodation Cost:** $", plan['accommodation_cost'])
                
                with col2:
                    st.write("**Experiences Cost:** $", plan['experiences_cost'])
                    st.write("**Miscellaneous Cost:** $", plan['misc_cost'])
                    st.write("**Total Cost:** $", plan['total_cost'])
                
                if st.button("Remove Plan", key=f"remove_{plan_id}"):
                    remove_holiday_plan(plan_id)
                    st.rerun()

        # Display summary statistics
        st.header("Summary Statistics")
        total_budget = sum(plan['total_cost'] for plan in st.session_state.holiday_plans.values())
        total_trips = len(st.session_state.holiday_plans)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Trips Planned", total_trips)
        col2.metric("Total Budget", f"${total_budget:,.2f}")
        if total_trips > 0:
            col3.metric("Average Cost per Trip", f"${total_budget/total_trips:,.2f}")

        # Display budget breakdown pie chart
        if st.session_state.holiday_plans:
            st.subheader("Budget Breakdown")
            budget_data = {
                'Travel': sum(plan['travel_cost'] for plan in st.session_state.holiday_plans.values()),
                'Accommodation': sum(plan['accommodation_cost'] for plan in st.session_state.holiday_plans.values()),
                'Experiences': sum(plan['experiences_cost'] for plan in st.session_state.holiday_plans.values()),
                'Miscellaneous': sum(plan['misc_cost'] for plan in st.session_state.holiday_plans.values())
            }
            
            fig_data = pd.DataFrame(list(budget_data.items()), columns=['Category', 'Amount'])
            
            # Create pie chart using plotly express
            fig = px.pie(fig_data, 
                        values='Amount', 
                        names='Category',
                        title='Budget Distribution')
            
            # Display the chart in Streamlit
            st.plotly_chart(fig)

                    # Display treemap visualization
        if st.session_state.holiday_plans:
            st.subheader("Holiday Plans Treemap")
            
            # Prepare data for treemap
            treemap_data = []
            for plan_id, plan in st.session_state.holiday_plans.items():
                # Add travel cost
                if plan['travel_cost'] > 0:
                    treemap_data.append({
                        'Holiday': plan['name'],
                        'Category': 'Travel',
                        'Cost': plan['travel_cost']
                    })
                # Add accommodation cost
                if plan['accommodation_cost'] > 0:
                    treemap_data.append({
                        'Holiday': plan['name'],
                        'Category': 'Accommodation',
                        'Cost': plan['accommodation_cost']
                    })
                # Add experiences cost
                if plan['experiences_cost'] > 0:
                    treemap_data.append({
                        'Holiday': plan['name'],
                        'Category': 'Experiences',
                        'Cost': plan['experiences_cost']
                    })
                # Add miscellaneous cost
                if plan['misc_cost'] > 0:
                    treemap_data.append({
                        'Holiday': plan['name'],
                        'Category': 'Miscellaneous',
                        'Cost': plan['misc_cost']
                    })
            
            # Create DataFrame for treemap
            df_treemap = pd.DataFrame(treemap_data)
            
            # Create treemap
            fig_treemap = px.treemap(
                df_treemap,
                path=[px.Constant("All Holidays"), 'Holiday', 'Category'],
                values='Cost',
                title='Holiday Expenses Breakdown',
                color='Cost',
                color_continuous_scale='Viridis',
                custom_data=['Cost']
            )
            
            # Update layout and hover template
            fig_treemap.update_traces(
                hovertemplate='<b>%{label}</b><br>Cost: $%{customdata[0]:,.2f}<extra></extra>'
            )
            
            fig_treemap.update_layout(
                height=600,
                width=800
            )
            
            # Display the treemap
            st.plotly_chart(fig_treemap, use_container_width=True)

            # Add a table view of the data
            st.subheader("Detailed Holiday Plans")
            
            # Prepare data for the table
            table_data = []
            for plan in st.session_state.holiday_plans.values():
                table_data.append({
                    'Destination': plan['name'],
                    'Duration': f"{(plan['end_date'] - plan['start_date']).days + 1} days",
                    'Start Date': plan['start_date'].strftime('%Y-%m-%d'),
                    'End Date': plan['end_date'].strftime('%Y-%m-%d'),
                    'Travel': f"${plan['travel_cost']:,.2f}",
                    'Accommodation': f"${plan['accommodation_cost']:,.2f}",
                    'Experiences': f"${plan['experiences_cost']:,.2f}",
                    'Miscellaneous': f"${plan['misc_cost']:,.2f}",
                    'Total': f"${plan['total_cost']:,.2f}"
                })
            
            # Create and display the table
            df_table = pd.DataFrame(table_data)
            st.dataframe(
                df_table,
                column_config={
                    "Destination": st.column_config.TextColumn(
                        "Destination",
                        width="medium",
                    ),
                    "Duration": st.column_config.TextColumn(
                        "Duration",
                        width="small",
                    ),
                },
                hide_index=True,
            )

    else:
        st.info("No holiday plans added yet. Start by adding your first holiday plan!")

if __name__ == "__main__":
    main()
