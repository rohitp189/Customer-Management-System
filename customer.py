import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import streamlit_shadcn_ui as ui
import time
import bcrypt
from datetime import timedelta, datetime
import plotly.graph_objects as go
# Database connection setup
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="10Piggu10@",
        database="customer_management"
    )

# Main Streamlit App for Customers
def customer_app():
    # Ensure user is logged in and of type Customer
    if not st.session_state.get("logged_in") or st.session_state.get("user_type") != 1:
        st.error("Unauthorized access. Please log in as a customer.")
        st.stop()
    # Get the full name from the session state
    full_name = st.session_state.get('full_name', 'Customer')

    # Get the first letter and rest of the name for styling
    first_letter = full_name[0]  # First letter
    rest_of_name = full_name[1:]  # Rest of the name

    # Connect to the database
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch the customer ID based on the full name
    cursor.execute("SELECT cust_id FROM customers WHERE cust_name = %s", (full_name,))
    customer_data = cursor.fetchone()

    # Check if the customer data exists
    if customer_data:
        cust_id = customer_data['cust_id']  # Fetch the customer ID
    else:
        st.error("Customer not found.")
        conn.close()
        exit()

    # Fetch membership type and expiry date using the customer ID
    cursor.execute("SELECT membership_type, expiry_date FROM memberships WHERE cust_id = %s", (cust_id,))
    membership_data = cursor.fetchone()

    # Handle case where membership data is not found or expired
    if membership_data:
        membership_type = membership_data['membership_type']
        expiry_date = membership_data['expiry_date']
    else:
        membership_type = "Basic"  # Default to Basic if no membership is found
        expiry_date = None

    # Check if membership is expired
    today = datetime.now().date()
    is_expired = expiry_date and expiry_date < today

    # Display welcome message with shimmer effect only if membership is active
    if not is_expired:
        if membership_type == "Gold":
            st.markdown(f"""
                <h1>
                    Welcome, <span style="color:#4169e1">{first_letter}</span>{rest_of_name}!
                    <span class="shimmer-gold">Gold</span>
                </h1>
            """, unsafe_allow_html=True)
        elif membership_type == "Premium":
            st.markdown(f"""
                <h1>
                    Welcome, <span style="color:#4169e1">{first_letter}</span>{rest_of_name}!
                    <span class="shimmer-premium">Premium</span>
                </h1>
            """, unsafe_allow_html=True)
        elif membership_type == "Basic":
            st.markdown(f"""
                <h1>
                    Welcome, <span style="color:#4169e1">{first_letter}</span>{rest_of_name}!
                    <span style="color: #6d8196;">Basic</span>
                </h1>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <h1>
                Welcome, <span style="color:#4169e1">{first_letter}</span>{rest_of_name}!
            </h1>
        """, unsafe_allow_html=True)

    # CSS code to apply the shimmer effect (make sure it's within a markdown or HTML block)
    st.markdown("""
        <style>
        /* General shimmer effect */
        .shimmer {
            display: inline-block;
            color: white;
            background: #acacac -webkit-gradient(linear, 100% 0, 0 0, from(#acacac), color-stop(0.5, #ffffff), to(#acacac));
            background-position: -4rem top;
            background-repeat: no-repeat;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            -webkit-animation-name: shimmer;
            -webkit-animation-duration: 2.2s;
            -webkit-animation-iteration-count: infinite;
            -webkit-background-size: 4rem 100%;
        }

        /* Gold shimmer effect */
        .shimmer-gold {
            display: inline-block;
            color: #ffd700;
            background: #ffd700 -webkit-gradient(linear, 100% 0, 0 0, from(#ffd700), color-stop(0.5, #ffffff), to(#ffd700));
            background-position: -4rem top;
            background-repeat: no-repeat;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            -webkit-animation-name: shimmer;
            -webkit-animation-duration: 2.2s;
            -webkit-animation-iteration-count: infinite;
            -webkit-background-size: 4rem 100%;
        }

        /* Premium shimmer effect */
        .shimmer-premium {
            display: inline-block;
            color: #551a8b;
            background: #551a8b -webkit-gradient(linear, 100% 0, 0 0, from(#551a8b), color-stop(0.5, #ffffff), to(#551a8b));
            background-position: -4rem top;
            background-repeat: no-repeat;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            -webkit-animation-name: shimmer;
            -webkit-animation-duration: 2.2s;
            -webkit-animation-iteration-count: infinite;
            -webkit-background-size: 4rem 100%;
        }

        @-webkit-keyframes shimmer {
            0% {
                background-position: -4rem top;
            }
            70% {
                background-position: 12.5rem top;
            }
            100% {
                background-position: 12.5rem top;
            }
        }
        </style>
    """, unsafe_allow_html=True)

    # Close the DB connection
    cursor.close()
    conn.close()
    choice = ui.tabs(
        options=[
            "Customer Analysis",
            "User Update",
            "Manage Membership"
        ],
        default_value="Customer Analysis"
    )

    if choice == "Customer Analysis":
        customer_analysis(st.session_state["user_id"])
    elif choice == "User Update":
        customer_update(st.session_state["user_id"])
    elif choice == "Manage Membership":
        manage_membership(st.session_state["user_id"])

# Feature: Customer Analysis
def customer_analysis(user_id):
    st.write("")    
    st.markdown('<h3>Your Spending <span style="color:#4169e1">A</span>nalysis</h3>', unsafe_allow_html=True)
    st.divider()
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Get cust_id from login_info table using user_id
    cursor.execute("SELECT cust_id FROM login_info WHERE user_id = %s", (user_id,))
    login_info = cursor.fetchone()

    if not login_info:
        st.warning("User not linked to a customer account.")
        return

    cust_id = login_info["cust_id"]

    # Total Spendings and Total Savings for logged-in user
    cursor.execute("""
        SELECT SUM(amount_spent) AS total_spendings, SUM(amount_saved) AS total_savings
        FROM purchases WHERE cust_id = %s
    """, (cust_id,))
    totals = cursor.fetchone()
    total_spendings = totals['total_spendings'] or 0
    total_savings = totals['total_savings'] or 0

    # Spending and Savings Trend
    cursor.execute("""
        SELECT DATE(purchase_date) AS date, 
               SUM(amount_spent) AS spendings, 
               SUM(amount_saved) AS savings 
        FROM purchases WHERE cust_id = %s GROUP BY DATE(purchase_date)
    """, (cust_id,))
    trends = cursor.fetchall()
    trend_data = pd.DataFrame(trends)

    # Purchases Table
    cursor.execute("""
                    SELECT 
                        item AS "Item Purchased", 
                        amount_spent AS "Amount Spent ($)", 
                        amount_saved AS "Amount Saved ($)", 
                        purchase_date AS "Purchase Date"
                    FROM purchases
                    WHERE cust_id = %s
                """, (cust_id,))
    purchases = pd.DataFrame(cursor.fetchall())

    conn.close()

    # Display metrics
    with st.container():
        cols = st.columns(2)
        with cols[0]:
            ui.metric_card(title="Total Spendings", content=f"${total_spendings:,.2f}", description="Overall Spendings")
        with cols[1]:
            ui.metric_card(title="Total Savings", content=f"${total_savings:,.2f}", description="Overall Savings")

    # Display Spending and Savings Trend
    with st.container():
        st.subheader("Spending and Savings Trend")
    
        # Assuming `trend_data` is the variable you are using
        if not trend_data.empty:
            fig = go.Figure()

            # Add Spendings line (in #4169e1 color)
            fig.add_trace(go.Scatter(
                x=trend_data['date'], 
                y=trend_data['spendings'], 
                mode='lines+markers', 
                name='Spendings', 
                line=dict(color='#4169e1'),  # Spendings in #4169e1 color
                marker=dict(size=4)
            ))

            # Add Savings line (in a lighter shade of #4169e1)
            fig.add_trace(go.Scatter(
                x=trend_data['date'], 
                y=trend_data['savings'], 
                mode='lines+markers', 
                name='Savings', 
                line=dict(color='#6495ed'),  # Savings in a lighter shade of #4169e1
                marker=dict(size=4, symbol='cross')
            ))

            # Customize layout
            fig.update_layout(
                title="Spending and Savings Over Time",
                xaxis_title="Date",
                yaxis_title="Amount",
                template="plotly_white",
                showlegend=True,
                height=500
            )

            # Show the figure in Streamlit
            st.plotly_chart(fig)
        else:
            st.write("No trend data available.")

    # Display Purchases Table
    with st.container():
        st.subheader("Purchases Table")
        if not purchases.empty:
            st.dataframe(purchases)
        else:
            st.write("No purchases available.")

def hash_password(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8') 

# Function to handle password reset dialog
@st.dialog("Reset Password")
def reset_password_dialog():
    # Create a form inside the dialog for password reset
    with st.form(key="reset_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        submit_button = st.form_submit_button("Submit")

        if submit_button:
            # Retrieve the current (old) password from the database
            db = create_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT password_hash FROM login_info WHERE user_id = %s", (st.session_state.user_id,))
            old_password = cursor.fetchone()

            if old_password:
                old_password = old_password['password_hash']

                # Check if the new password is the same as the old one
                if new_password == old_password:
                    st.error("New password cannot be the same as the old password.")
                elif new_password == confirm_password:
                    # Hash the new password and update it in the database
                    hashed_password = hash_password(new_password)
                    cursor.execute("UPDATE login_info SET password_hash = %s WHERE user_id = %s", (hashed_password, st.session_state.user_id))
                    db.commit()
                    db.close()
                    st.success("Password reset successful.")
                    with st.spinner("Will close in 10 seconds..."):
                        time.sleep(10)
                    # Clear session and rerun the page
                    st.session_state.clear()
                    st.rerun()  # Refresh the page after password reset
                else:
                    st.error("Passwords do not match.")
            else:
                st.error("Failed to retrieve the old password.")

# Function to handle account deletion dialog
@st.dialog("Delete Account")
def delete_account_dialog():
    st.write("**Are you sure you want to delete your account?**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Yes"):
            # Delete the user account
            db = create_connection()
            cursor = db.cursor()
            cursor.execute("DELETE FROM customers WHERE cust_id = %s", (st.session_state.cust_id,))
            cursor.execute("DELETE FROM login_info WHERE user_id = %s", (st.session_state.user_id,))
            db.commit()
            db.close()
            st.success("Your account has been deleted successfully.")
            st.session_state.clear()  # Clear session
            st.experimental_rerun()  # Refresh page to reflect account deletion
    with col2:
        if st.button("No"):
            st.write("Account deletion cancelled.")

# Main function to update customer details
def customer_update(user_id):
    st.write("")    
    st.markdown('<h3>Update your <span style="color:#4169e1">D</span>etails</h3>', unsafe_allow_html=True)
    st.divider()
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Get cust_id from login_info table using the user_id
    cursor.execute("SELECT cust_id FROM login_info WHERE user_id = %s", (user_id,))
    login_info = cursor.fetchone()

    if login_info:
        cust_id = login_info["cust_id"]

        # Fetch user data from the customers table using cust_id
        cursor.execute("SELECT * FROM customers WHERE cust_id = %s", (cust_id,))
        user_data = cursor.fetchone()

        if user_data:
            # Display existing customer details
            st.write(f"**Username:** {user_id}")
            st.write(f"**Name:** {user_data['cust_name']}")
            st.write(f"**Gender:** {user_data['gender']}")
            st.write(f"**DOB:** {user_data['dob']}")

            # Form to update user details
            with st.form("update_user_form"):
                updated_email = st.text_input("Email", user_data['email'])
                updated_phone = st.text_input("Phone", user_data['phone'])
                updated_address = st.text_area("Address", user_data['address'])
                updated_city = st.text_input("City", user_data['city'])
                updated_country = st.text_input("Country", user_data['country'])

                submit = st.form_submit_button("Update Details")
                if submit:
                    # Update details in the customers table
                    cursor.execute("""
                        UPDATE customers 
                        SET email = %s, phone = %s, address = %s, city = %s, country = %s 
                        WHERE cust_id = %s
                    """, (updated_email, updated_phone, updated_address, updated_city, updated_country, cust_id))
                    conn.commit()
                    st.success("Your details have been updated successfully!")
        else:
            st.warning("Customer data not found.")
    else:
        st.warning("User not linked to a customer account.")

    conn.close()

    # Add a button to change the password
    if st.button("Change Password"):
        reset_password_dialog()  # Open the password reset dialog

    # Add a button to delete the account
    if st.button("Delete Account"):
        delete_account_dialog()  # Open the account deletion dialog

# Define durations for membership plans
durations = {
    "1 Month": 30, "3 Months": 90, "6 Months": 180, 
    "1 Year": 365, "2 Years": 730, "5 Years": 1825
}

# Membership prices for each plan and duration
membership_prices = {
    "Basic": {
        "1 Month": 30, "3 Months": 70, "6 Months": 120, 
        "1 Year": 200, "2 Years": 380, "5 Years": 900
    },
    "Premium": {
        "1 Month": 50, "3 Months": 120, "6 Months": 220, 
        "1 Year": 400, "2 Years": 750, "5 Years": 1800
    },
    "Gold": {
        "1 Month": 100, "3 Months": 230, "6 Months": 450, 
        "1 Year": 800, "2 Years": 1500, "5 Years": 3500
    }
}

# Tax rate (for example, 15%)
TAX_RATE = 0.15

# Function to handle the payment dialog
@st.dialog("Buy Membership")
def membership_buy_dialog(cust_id, membership_type, duration_label, today):
    conn = create_connection()  # Re-establish DB connection inside the dialog
    cursor = conn.cursor(dictionary=True)

    # Get the price for the selected membership type and duration
    price = membership_prices[membership_type][duration_label]
    duration_days = durations[duration_label]
    months = duration_days // 30  # Approximate number of months
    total_price = price

    # Apply tax and calculate final amount
    tax_amount = total_price * TAX_RATE
    total_amount = total_price + tax_amount

    with st.form(key="payment_form"):
        st.write(f"**Invoice:**")
        st.write(f"Membership Type: {membership_type}")
        st.write(f"Duration: {duration_label}")
        st.write(f"Price: ${price}")
        st.write(f"Tax Rate: {int(TAX_RATE * 100)}%")
        st.write(f"Tax Amount: ${tax_amount}")
        st.write(f"**Total Amount Due: ${total_amount}**")

        card_number = st.text_input("Enter Card Number (16 digits)", max_chars=16)
        expiry_date_card = st.text_input("Enter Card Expiry Date (MM/YY)")
        cvv = st.text_input("Enter CVV", type="password", max_chars=3)
        confirm = st.form_submit_button("Confirm Payment")

        if confirm:
            if len(card_number) != 16 or not card_number.isdigit():
                st.error("Card number must be a valid 16-digit number.")
            elif not expiry_date_card or len(expiry_date_card) != 5 or expiry_date_card[2] != '/':
                st.error("Please enter a valid card expiry date in MM/YY format.")
            elif len(cvv) != 3 or not cvv.isdigit():
                st.error("CVV must be a valid 3-digit number.")
            else:
                # Payment successful
                with st.spinner("Processing your transaction..."):
                    time.sleep(3)  # Simulate processing time

                # Remove existing membership if present
                cursor.execute("DELETE FROM memberships WHERE cust_id = %s", (cust_id,))

                # Calculate expiry date
                expiry_date = today + timedelta(days=duration_days)

                # Insert new membership
                cursor.execute("""
                    INSERT INTO memberships (cust_id, membership_type, bought_at, expiry_date) 
                    VALUES (%s, %s, %s, %s)
                """, (cust_id, membership_type, today, expiry_date))
                conn.commit()

                st.success("Your transaction was successful!")
                with st.spinner("Will close in 10 seconds..."):
                    time.sleep(10)

                # Refresh page to show updated membership
                st.rerun()

    cursor.close()
    conn.close()  # Close the connection after completing the transaction

# Feature: Manage Membership
def manage_membership(user_id):
    st.write("")    
    st.markdown('<h3>Manage your <span style="color:#4169e1">M</span>embership</h3>', unsafe_allow_html=True)
    st.divider()
    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Retrieve cust_id and cust_name using user_id from login_info and customers tables
    cursor.execute("""
        SELECT login_info.cust_id, customers.cust_name 
        FROM login_info 
        JOIN customers ON login_info.cust_id = customers.cust_id 
        WHERE login_info.user_id = %s
    """, (user_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        st.warning("User not linked to a customer account.")
        return

    cust_id = user_data['cust_id']
    cust_name = user_data['cust_name']

    # Check existing membership
    cursor.execute("SELECT * FROM memberships WHERE cust_id = %s", (cust_id,))
    membership_data = cursor.fetchone()

    today = datetime.now().date()

    if membership_data:
        expiry_date = membership_data["expiry_date"]
        membership_type = membership_data['membership_type']
        remaining_days = (expiry_date - today).days
        
        # Display membership details and expiry
        if expiry_date < today:
            st.warning(f"Your membership '{membership_type}' expired on {expiry_date}.")
            st.subheader(f"Available Membership Plans for {cust_name}")
            show_membership_plans(cust_id,today)
        else:
            # Display membership type with color coding and additional info
            display_membership_details(membership_type, remaining_days, expiry_date)
            
            if remaining_days > 30:
                st.info(f"✅ Your membership will expire in **{remaining_days} days**.")
            elif 10 < remaining_days <= 30:
                st.warning(f"⚠️ Your membership will expire in **{remaining_days} days**.")
            else:
                st.error(f"❌ Your membership will expire in **{remaining_days} days**. Renew soon!")
                st.subheader(f"Available Membership Plans for {cust_name}")
                show_membership_plans()
    else:
        st.warning("You do not have any membership. Please select a plan below to buy.")
        st.subheader(f"Available Membership Plans for {cust_name}")
        show_membership_plans()

    cursor.close()
    conn.close()

def display_membership_details(membership_type, remaining_days, expiry_date):
    st.markdown("""<style>
                    .detail-box {
                    background-color: #f7f7f7;
                    padding: 20px;
                    border-radius: 10px;
                    max-width: 90%;
                    min-width: 350px;
                    margin: auto;
                    text-align: left;
                    word-wrap: break-word;
                    overflow-wrap: break-word;
                    display: flex;
                    flex-direction: column;
                    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                    margin-bottom: 20px;
                }
                
                 </style>""", unsafe_allow_html=True)
    # Display membership details based on type
    if membership_type == "Basic":
        st.markdown(f"""
            <div class='detail-box' style='border-left: 6px solid #6d8196;'>
                <h6>
                    <span style='background-color:#6d8196; padding: 6px 12px; border-radius: 6px; color: white; font-size: 18px; display: inline-block;'>
                        Basic Membership
                    </span>
                    <br><br>
                    <span style='font-size: 16px; color: #333;'><strong>Expiry Date:</strong> {expiry_date}</span>
                    <br><br>
                    <span style='font-size: 16px; color: #333;'><strong>Benefits:</strong></span>
                    <ul style='font-size: 14px; color: #555; padding-left: 20px; margin-top: 5px;'>
                        <li>🛒 <strong>5% Discount</strong> on all in-store items.</li>
                        <li>🎟️ <strong>Access to Basic Promotions</strong> & special deals.</li>
                        <li>💳 <strong>Loyalty Points</strong> for every purchase.</li>
                        <li>📩 Invitations to <strong>Store Events</strong> & product launches.</li>
                        <li>🕒 <strong>Standard Customer Service</strong> response time.</li>
                    </ul>
                </h6>
            </div>
        """, unsafe_allow_html=True)

    elif membership_type == "Premium":
        st.markdown(f"""
            <div class='detail-box' style='border-left: 6px solid #551a8b;'>
                <h6>
                    <span style='background-color:#551a8b; padding: 6px 12px; border-radius: 6px; color: white; font-size: 18px; display: inline-block;'>
                        Premium Membership
                    </span>
                    <br><br>
                    <span style='font-size: 16px; color: #333;'><strong>Expiry Date:</strong> {expiry_date}</span>
                    <br><br>
                    <span style='font-size: 16px; color: #333;'><strong>Benefits:</strong></span>
                    <ul style='font-size: 14px; color: #555; padding-left: 20px; margin-top: 5px;'>
                        <li>💰 <strong>15% Discount</strong> on all in-store items.</li>
                        <li>🛍️ <strong>Early Access</strong> to seasonal sales & exclusive discounts.</li>
                        <li>💎 <strong>Double Reward Points</strong> for every purchase.</li>
                        <li>🎁 <strong>Exclusive Birthday Gifts</strong> every year.</li>
                        <li>📞 <strong>Priority Customer Support</strong> for faster resolution.</li>
                    </ul>
                </h6>
            </div>
        """, unsafe_allow_html=True)
    elif membership_type == "Gold":
        st.markdown(f"""
                    <div class='detail-box' style='border-left: 6px solid #ffd700;'>
                        <h6>
                            <span style='background-color:#ffd700; padding: 6px 12px; border-radius: 6px; color: white; font-size: 18px; display: inline-block;'>
                                Gold Membership
                            </span>
                            <br><br>
                            <span style='font-size: 16px; color: #333;'><strong>Expiry Date:</strong> {expiry_date}</span>
                            <br><br>
                            <span style='font-size: 16px; color: #333;'><strong>Benefits:</strong></span>
                            <ul style='font-size: 14px; color: #555; padding-left: 20px; margin-top: 5px;'>
                                <li>🛍️ <strong>30% Discount</strong> on all in-store items.</li>
                                <li>🚚 <strong>Free Delivery</strong> on all purchases (online & in-store).</li>
                                <li>💰 <strong>Triple Reward Points</strong> for every purchase.</li>
                                <li>🎁 <strong>Exclusive Offers</strong> and a personal shopping experience.</li>
                                <li>🎟️ Invitations to <strong>exclusive events</strong> & designer meet-and-greets.</li>
                                <li>🔑 <strong>Priority Access</strong> to new launches & limited editions.</li>
                                <li>🎀 <strong>Free Gift Wrapping</strong> service for all purchases.</li>
                            </ul>
                        </h6>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.write(f"Membership Type: {membership_type}")  # Default case if not one of the above

def show_membership_plans(cust_id,today):
    plan_data = []
    for plan, durations_prices in membership_prices.items():
        row = {"Membership Type": plan}
        for duration, price in durations_prices.items():
            row[duration] = f"${price}"
        plan_data.append(row)

    plan_table = pd.DataFrame(plan_data)
    st.table(plan_table)

    with st.form("buy_membership_form"):
        membership_type = st.selectbox("Select Membership Type", list(membership_prices.keys()))
        duration_label = st.selectbox("Select Duration", list(durations.keys()))
        submit = st.form_submit_button("Buy Membership")

        if submit:
            # Open the payment dialog for card details
            membership_buy_dialog(cust_id, membership_type, duration_label, today)

if __name__ == "__main__":
    customer_app()
