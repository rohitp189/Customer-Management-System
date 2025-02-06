import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import streamlit_shadcn_ui as ui
import plotly.express as px
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# Database connection setup
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="10Piggu10@",
        database="customer_management"
    )

# Main Streamlit App
def main():
    st.markdown(f'<h1><span style="color:#4169e1">C</span>ustomer Management System</h1>', unsafe_allow_html=True)
    st.write("")
    choice = ui.tabs(options=[
        "Dashboard",
        "Manage Customers",
        "Customer Analysis"
    ],
    default_value="Dashboard"
    )

    # Dashboard Overview
    if choice == "Dashboard":
        st.write("")    
        st.markdown('<h3>Customer <span style="color:#4169e1">A</span>nalaysis Report</h3>', unsafe_allow_html=True)
        st.divider()
        dashboard()

    # Manage Customers
    elif choice == "Manage Customers":
        st.write("")    
        st.markdown('<h3>Find <span style="color:#4169e1">C</span>ustomer Details</h3>', unsafe_allow_html=True)
        st.divider()
        manage_customers()

    # Customer Analysis
    elif choice == "Customer Analysis":
        st.write("")    
        st.markdown('<h3>Customer <span style="color:#4169e1">D</span>emographics</h3>', unsafe_allow_html=True)
        st.divider()
        customer_analysis()


def dashboard():
    # Create a connection and a cursor
    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Total Customers
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]

        # New Customers Trend
        cursor.execute("SELECT created_at, COUNT(*) AS count FROM customers GROUP BY created_at")
        new_customers = cursor.fetchall()

        # Customer Spendings
        cursor.execute("SELECT MONTH(purchase_date) AS month, SUM(amount_spent) AS total FROM purchases GROUP BY month")
        spending_data = cursor.fetchall()

        # Gender Distribution
        cursor.execute("SELECT gender, COUNT(*) FROM customers GROUP BY gender")
        gender_data = cursor.fetchall()

        # Membership Trend
        cursor.execute("SELECT bought_at, membership_type FROM memberships")
        membership_data = cursor.fetchall()
        
        # Additional Metrics
                # 1. Fetch Overall Total Customers (All-Time)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customers
        """)
        total_customers = cursor.fetchone()[0] or 0  # Handle cases with no customers

        # 2. Fetch Total Customers in the Current Month
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customers 
            WHERE DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(CURRENT_DATE, '%Y-%m')
        """)
        current_month_customers = int(cursor.fetchone()[0] or 0)  # Convert to int

        # 3. Fetch Total Customers in the Previous Month
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customers 
            WHERE DATE_FORMAT(created_at, '%Y-%m') = DATE_FORMAT(CURRENT_DATE - INTERVAL 1 MONTH, '%Y-%m')
        """)
        previous_month_customers = int(cursor.fetchone()[0] or 0)  # Convert to int

        # 4. Calculate Customers Delta (Current Month - Previous Month)
        customers_delta = current_month_customers - previous_month_customers

        # 6. Fetch Total Spendings for the Current Month
        cursor.execute("""
            SELECT SUM(amount_spent) 
            FROM purchases 
            WHERE DATE_FORMAT(purchase_date, '%Y-%m') = DATE_FORMAT(CURRENT_DATE, '%Y-%m')
        """)
        current_month_spending = cursor.fetchone()[0] or 0  # Total spending this month

        # 7. Fetch Total Spendings for the Previous Month
        cursor.execute("""
            SELECT SUM(amount_spent) 
            FROM purchases 
            WHERE DATE_FORMAT(purchase_date, '%Y-%m') = DATE_FORMAT(CURRENT_DATE - INTERVAL 1 MONTH, '%Y-%m')
        """)
        previous_month_spending = cursor.fetchone()[0] or 0 
        
        cursor.execute("""
            SELECT SUM(amount_spent) 
            FROM purchases
            """)
        overall_spending = cursor.fetchone()[0] or 0  # Total overall spending # Total spending last month


        # 9. Calculate Percentage Change for Spendings
        spending_percentage_change = ((previous_month_spending - current_month_spending) / previous_month_spending) * 100


        # 10. Display metrics for customers and spending
        with st.container():
            cols = st.columns(2)
            with cols[0]:
                if customers_delta ==0:
                    st.metric(label="Total Customers", value=total_customers, 
                        delta=f"{abs(customers_delta)}", 
                        delta_color= "off", border=True)
                else:
                    st.metric(label="Total Customers", value=total_customers, 
                        delta=f"{abs(customers_delta)}", 
                        delta_color= "normal", border=True)
            with cols[1]:
                if spending_percentage_change == 0:
                    st.metric(
                    label="Total Spendings",
                    value=f"${overall_spending:,.2f}",
                    delta=f"{(spending_percentage_change):.2f}%",  # Show percentage change
                    delta_color="off", border=True)
                
                else:    
                    st.metric(
                        label="Total Spendings",
                        value=f"${overall_spending:,.2f}",
                        delta=f"{(spending_percentage_change):.2f}%",  # Show percentage change
                        delta_color="normal", border=True)


        
        # Display new container with Gender and Membership Type charts
        with st.container(border=True):

            cols = st.columns(2)
            
            # Gender Distribution Pie Chart
            with cols[0]:
                gender_df = pd.DataFrame(gender_data, columns=["gender", "count"])
                fig = px.pie(gender_df, names="gender", values="count", title="Gender Distribution",
                             color="gender", color_discrete_map={"Male": "blue", "Female": "pink", "Other": "gray"})
                st.plotly_chart(fig, use_container_width=True)

            # Membership Type Distribution Pie Chart
            with cols[1]:
                membership_df = pd.DataFrame(membership_data, columns=["bought_at", "membership_type"])
                membership_counts = membership_df["membership_type"].value_counts().reset_index()
                membership_counts.columns = ["membership_type", "count"]
                fig = px.pie(membership_counts, names="membership_type", values="count", title="Membership Type Distribution",
                             color="membership_type", color_discrete_map={"Basic": "#6d8196", "Premium": "#551a8b", "Gold": "#ffd700"})
                st.plotly_chart(fig, use_container_width=True)


        cursor.execute("SELECT created_at FROM customers")
        new_customers = cursor.fetchall()

        # Convert the fetched data into a pandas DataFrame
        new_customer_df = pd.DataFrame(new_customers, columns=["created_at"])

        # Convert 'created_at' to datetime format if not already in datetime
        new_customer_df["created_at"] = pd.to_datetime(new_customer_df["created_at"])

        # Extract Date and Time separately
        new_customer_df['date'] = new_customer_df['created_at'].dt.date
        new_customer_df['time'] = new_customer_df['created_at'].dt.time

        # Convert time to hours for the y-axis (without minutes and seconds)
        new_customer_df['time_in_hours'] = new_customer_df['created_at'].dt.hour

        # Color Mapping Based on Hour of the Day
        def get_time_of_day(hour):
            if 6 <= hour < 12:
                return "Morning"
            elif 12 <= hour < 18:
                return "Afternoon"
            elif 18 <= hour < 24:
                return "Evening"
            else:
                return "Night"

        new_customer_df['time_of_day'] = new_customer_df['time_in_hours'].apply(get_time_of_day)

        # Now the DataFrame has both 'date', 'time_in_hours', and 'time_of_day' columns
        with st.container(border=True):

            # Create scatter plot with 'date' as x (date) and 'time_in_hours' as y (time in hours)
            fig = px.scatter(new_customer_df, x="date", y="time_in_hours", title="New Customers Over Time",
                             color="time_of_day", color_discrete_map={
                                 "Morning": "lightblue", 
                                 "Afternoon": "yellow", 
                                 "Evening": "orange", 
                                 "Night": "darkblue"
                             },
                             labels={"date": "Date", "time_in_hours": "Hour of the Day"})

            # Display Plotly chart
            st.plotly_chart(fig, use_container_width=True)


        # 2. Customer Total Spendings by Month (Line Chart)
        with st.container(border=True):

            # Toggle between Gender and Membership visualization
            on = st.toggle("Toggle to switch between Gender and Membership")
            if on:
                # Fetch total spendings by Gender over time (e.g., by month)
                cursor.execute("""
                    SELECT MONTH(purchase_date) AS month, gender, SUM(amount_spent) AS total_spent 
                    FROM customers 
                    JOIN purchases ON customers.cust_id = purchases.cust_id 
                    GROUP BY month, gender
                    ORDER BY month
                """)
                gender_spending_data = cursor.fetchall()
                gender_spending_df = pd.DataFrame(gender_spending_data, columns=["month", "gender", "total_spent"])
                
                # Ensure proper sorting by month
                gender_spending_df["month"] = gender_spending_df["month"].astype(int)
                gender_spending_df = gender_spending_df.sort_values(by="month")
                
                # Generate Line chart for total spendings by gender over time (month)
                fig = px.line(gender_spending_df, x="month", y="total_spent", color="gender", 
                              title="Total Spendings by Gender Over Time", 
                              color_discrete_map={"Male": "blue", "Female": "pink", "Transgender": "purple", "Other": "gray"})
                fig.update_layout(
                    xaxis_title='Month',  # Renaming x-axis
                    yaxis_title='Total Spendings ($)',
                    legend_title='Gender'  # Renaming y-axis
                    )
                st.plotly_chart(fig, use_container_width=True)

            else:
                # Fetch total spendings by Membership over time (e.g., by month)
                cursor.execute("""
                    SELECT MONTH(purchase_date) AS month, membership_type, SUM(amount_spent) AS total_spent 
                    FROM memberships 
                    JOIN purchases ON memberships.cust_id = purchases.cust_id 
                    GROUP BY month, membership_type
                    ORDER BY month
                """)
                membership_spending_data = cursor.fetchall()
                membership_spending_df = pd.DataFrame(membership_spending_data, columns=["month", "membership_type", "total_spent"])
                
                # Ensure proper sorting by month
                membership_spending_df["month"] = membership_spending_df["month"].astype(int)
                membership_spending_df = membership_spending_df.sort_values(by="month")
                
                # Generate Line chart for total spendings by membership over time (month)
                fig = px.line(membership_spending_df, x="month", y="total_spent", color="membership_type", 
                              title="Total Spendings by Membership Over Time", 
                              color_discrete_map={"Basic": "#6d8196", "Premium": "#551a8b", "Gold": "#ffd700"})
                fig.update_layout(
                    xaxis_title='Month',  # Renaming x-axis
                    yaxis_title='Total Spendings ($)',
                    legend_title='Membership Type'  # Renaming y-axis
                    )
                st.plotly_chart(fig, use_container_width=True)


        # 4. Membership Type by Time (Scatter Plot)
        with st.container(border=True):
            membership_df["bought_at"] = pd.to_datetime(membership_df["bought_at"])

            # Ensure the 'membership_type' is a categorical column with defined order
            membership_df["membership_type"] = pd.Categorical(membership_df["membership_type"], 
                                                            categories=["Gold", "Premium", "Basic"], 
                                                            ordered=True)

            # Create the scatter plot with colors based on 'membership_type'
            fig = px.scatter(membership_df, 
                            x="bought_at", 
                            y="membership_type", 
                            title="Membership Types Over Time",
                            color="membership_type", 
                            color_discrete_map={
                                "Gold": "#ffd700", 
                                "Premium": "#551a8b", 
                                "Basic": "#6d8196"
                            },
                            labels={"bought_at": "Date", "membership_type": "Membership Type"},
                            category_orders={"membership_type": ["Gold", "Premium", "Basic"]})  # Enforce order here

            # Display the plot
            st.plotly_chart(fig, use_container_width=True)
        
        # 5. Numbers of Item Types (Bar Chart)
        # Categorize items into their respective categories
        categories = {
            "Electronics": [
                "Laptop", "Smartphone", "Headphones", "Tablet", "Smartwatch", "Gaming Console", 
                "TV", "Camera", "Speaker", "Microwave", "Blender", "Vacuum Cleaner", "Dishwasher", 
                "Refrigerator", "Oven", "Toaster", "Air Purifier", "Fan", "Heater", "Smart Light", 
                "Thermostat", "Electric Kettle", "Toaster Oven", "Mixer", "Juicer", "Air Fryer", 
                "Deep Fryer", "Grill", "BBQ Set", "Router", "Printer", "Scanner", "External Drive", 
                "Projector", "Tripod", "Battery Pack", "Power Bank", "Adapter", "HDMI Cable"
            ],
            "Furniture": [
                "Mattress", "Bed Frame", "Sofa", "Coffee Table", "Dining Set", "Chair", "Wardrobe", 
                "Bookshelf", "Desk", "Office Chair", "Monitor", "Keyboard", "Mouse"
            ],
            "Sports & Fitness": [
                "Bike", "Helmet", "Treadmill", "Weights", "Yoga Mat", "Tennis Racket", "Golf Clubs", 
                "Fishing Rod", "Camping Tent", "Sleeping Bag"
            ],
            "Fashion & Accessories": [
                "Backpack", "Sunglasses", "Hat", "Shoes", "Boots", "Jacket", "Sweater", "Pants"
            ]
        }

        # Flatten the data into a format suitable for plotting
        category_data = []
        for category, items in categories.items():
            for item in items:
                category_data.append({"category": category, "item": item})

        # Create a DataFrame from the data
        category_df = pd.DataFrame(category_data)

        # Count the number of items in each category
        item_counts = category_df.groupby("category").size().reset_index(name="count")

        # Inside a container
        with st.container(border=True):
            st.subheader("Number of Items by Category")

            # Plot the bar chart using Plotly with good color palette and rounded bars
            fig = px.bar(item_counts, 
                        x="category", 
                        y="count", 
                        title="Number of Items by Category",
                        color="category",
                        color_discrete_sequence=["#8AB8E6", "#E6CFFE", "#CBB391", "#86C7A5"])  # Custom colors

            # Update layout for rounded bars
            #fig.update_traces(marker=dict(line=dict(width=1, color="black")))
   

            # Display the chart
            st.plotly_chart(fig, use_container_width=True)

    
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
    
    finally:
        # Close cursor and connection if they exist
        if cursor:
            cursor.close()
        if conn:
            conn.close()



# Feature: Manage Customers
# Function to create dynamic metric cards
def dynamic_metric_card(title, value, description, key):
    return ui.metric_card(title=title, content=value, description=description, key=key)

# Feature: Manage Customers with Dynamic Metric Cards
def manage_customers():
    # Initialize session state for customer ID
    if "customer_id" not in st.session_state:
        st.session_state["customer_id"] = None

    # Form to enter customer ID
    with st.form("manage_customer_form"):
        customer_id = st.text_input("Enter Customer ID", value=st.session_state["customer_id"])
        submit = st.form_submit_button("Get Customer Details")

    if submit:
        st.session_state["customer_id"] = customer_id  # Save to session state

    customer_id = st.session_state["customer_id"]
    cols = st.columns(2)  # Columns for metric cards

    if customer_id:
        conn = create_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch customer details
        cursor.execute("SELECT cust_name, gender, dob, phone, email, address, country, city FROM customers WHERE cust_id = %s", (customer_id,))
        customer_details = cursor.fetchone()

        if customer_details:
            # Display metric cards with customer details
            with cols[0]:
                dynamic_metric_card("Customer Name", customer_details['cust_name'], "", "card21")
                dynamic_metric_card("Phone Number", customer_details['phone'], "", "card25")
                dob = customer_details["dob"]
                age = (datetime.now().year - dob.year - ((datetime.now().month, datetime.now().day) < (dob.month, dob.day))) if dob else "N/A"
                dynamic_metric_card("Date of Birth", str(dob), f"Age {age}", "card23")
            with cols[1]:
                dynamic_metric_card("Gender", customer_details['gender'], "", "card22")
                dynamic_metric_card("Email", customer_details['email'], "", "card26")
                cursor.execute("SELECT membership_type, expiry_date FROM memberships WHERE cust_id = %s", (customer_id,))
                membership = cursor.fetchone()
                membership_type = membership["membership_type"] if membership else "No membership"
                expiry_date = membership["expiry_date"] if membership else "N/A"
                dynamic_metric_card("Membership Type", membership_type, f"Expires on {expiry_date}", "card28")
                dynamic_metric_card("Address", customer_details['address'], f"{customer_details['city']}, {customer_details['country']}", "card24")

            # Fetch and display savings and membership details
            cursor.execute("SELECT SUM(amount_saved) AS total_savings FROM purchases WHERE cust_id = %s", (customer_id,))
            total_savings = cursor.fetchone()["total_savings"] or 0.0


            with cols[0]:
                dynamic_metric_card("Total Savings", f"${total_savings:.2f}", "Savings accumulated", "card27")

            # Modify customer details
            st.write("")
            st.markdown("<h5>Modify Customer Details</h5>", unsafe_allow_html=True)
            with st.form("modify_customer_form"):
                updated_name = st.text_input("Customer Name", customer_details["cust_name"])
                updated_gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=["Male", "Female", "Other"].index(customer_details["gender"]))
                updated_phone = st.text_input("Phone Number", customer_details["phone"])
                updated_email = st.text_input("Email", customer_details["email"])
                updated_address = st.text_area("Address", customer_details["address"])
                updated_city = st.text_input("City", customer_details["city"])
                updated_country = st.text_input("Country", customer_details["country"])
                updated_dob = st.date_input("Date of Birth", customer_details["dob"], min_value=datetime(1900, 1, 1), max_value=datetime.today())

                update_submit = st.form_submit_button("Update Customer Details")

                if update_submit:
                    cursor.execute(
                        """
                        UPDATE customers
                        SET cust_name = %s, gender = %s, phone = %s, email = %s, address = %s, city = %s, country = %s, dob = %s
                        WHERE cust_id = %s
                        """,
                        (updated_name, updated_gender, updated_phone, updated_email, updated_address, updated_city, updated_country, updated_dob, customer_id))
                    conn.commit()
                    st.success("Customer details updated successfully!")

            # Modify membership details
            st.markdown("<h5>Modify Membership Details</h5>", unsafe_allow_html=True)
            if membership:
                with st.form("modify_membership_form"):
                    updated_membership_type = st.selectbox("Membership Type", ["Basic", "Premium", "Gold"], index=["Basic", "Premium", "Gold"].index(membership["membership_type"]))
                    updated_expiry_date = st.date_input("Expiry Date", membership["expiry_date"])

                    membership_submit = st.form_submit_button("Update Membership")

                    if membership_submit:
                        cursor.execute(
                            """
                            UPDATE memberships
                            SET membership_type = %s, expiry_date = %s
                            WHERE cust_id = %s
                            """,
                            (updated_membership_type, updated_expiry_date, customer_id))
                        conn.commit()
                        st.success("Membership details updated successfully!")

            # Delete Customer
            st.write("")
            st.markdown("<h5>Delete Customer Account</h5>", unsafe_allow_html=True)
            delete_customer = st.button("Delete Customer Account")

            if delete_customer:
                confirm_delete = st.radio("Are you sure you want to delete this account?", ["No", "Yes"], index=0)
                if confirm_delete == "Yes":
                    cursor.execute("DELETE FROM customers WHERE cust_id = %s", (customer_id,))
                    cursor.execute("DELETE FROM purchases WHERE cust_id = %s", (customer_id,))
                    cursor.execute("DELETE FROM memberships WHERE cust_id = %s", (customer_id,))
                    conn.commit()
                    st.success("Customer account and all related data deleted successfully!")

        else:
            st.warning(f"No customer found with ID: {customer_id}")

        conn.close()
    else:
        # Display empty cards for undefined customer
        with cols[0]:
            dynamic_metric_card("Customer Name", "N/A", "", "card41")
            dynamic_metric_card("Phone Number", "N/A", "", "card45")
            dynamic_metric_card("Date of Birth", "N/A", "", "card43")
            dynamic_metric_card("Total Savings", "N/A", "", "card47")
        with cols[1]:
            dynamic_metric_card("Gender", "N/A", "", "card42")
            dynamic_metric_card("Email", "N/A", "", "card46")
            dynamic_metric_card("Address", "N/A", "", "card44")
            dynamic_metric_card("Membership Type", "N/A", "", "card48")




# Feature: Customer Analysis
def customer_analysis():
    # Establish database connection
    conn = create_connection()
    df = pd.read_sql("SELECT * FROM customers", conn)
    
    # Filters for gender, city, and country
    gender_filter = st.multiselect("Filter by Gender", options=df["gender"].unique())
    if gender_filter:
        df = df[df["gender"].isin(gender_filter)]

    # Filter by city
    city_filter = st.multiselect("Filter by City", options=df["city"].unique())
    if city_filter:
        df = df[df["city"].isin(city_filter)]

    # Filter by country
    country_filter = st.multiselect("Filter by Country", options=df["country"].unique())
    if country_filter:
        df = df[df["country"].isin(country_filter)]
    
    st.dataframe(df)  # Show filtered data

    # Geocode addresses if latitude and longitude are not available
    if 'latitude' not in df.columns or 'longitude' not in df.columns:
        geolocator = Nominatim(user_agent="customer_analysis", timeout=10)
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1) 
        # Create latitude and longitude if missing
        def geocode_address(row):
            location = geocode(row["address"] + ", " + row["city"] + ", " + row["country"])
            if location:
                return location.latitude, location.longitude
            else:
                return None, None

        # Apply geocoding for each customer
        df["latitude"], df["longitude"] = zip(*df.apply(geocode_address, axis=1))
    
    # Create a map centered on the average location
    avg_lat = df["latitude"].mean()
    avg_lon = df["longitude"].mean()

    map_center = [avg_lat, avg_lon]
    customer_map = folium.Map(location=map_center, zoom_start=10)

    # Plot each customer on the map
    for _, row in df.iterrows():
        if pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['cust_name']} ({row['gender']})",
            ).add_to(customer_map)

    # Display the map in Streamlit
    st.write("### Customer Locations")
    st.components.v1.html(customer_map._repr_html_(), height=500)

    # Close the connection
    conn.close()

if __name__ == "__main__":
    main()
