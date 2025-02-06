import streamlit as st
import mysql.connector
import bcrypt
from datetime import datetime, date
from admin import main
from customer import customer_app
import time
# Initialize session state

# MySQL Connection Setup
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="10Piggu10@",
        database="customer_management"
    )

# Hash the password
def hash_password(password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')  # Convert bytes to string

# Check password
def check_password(stored_hash, password):
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))  # Convert stored_hash to bytes



# Registration process
def register_user(username, cust_name, email, phone, address, gender, dob, city, country, password):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("""INSERT INTO customers (cust_name, email, phone, address, gender, dob, city, country)
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                   (cust_name, email, phone, address, gender, dob, city, country))
    db.commit()

    cursor.execute("SELECT LAST_INSERT_ID()")
    cust_id = cursor.fetchone()[0]

    password_hash = hash_password(password)
    cursor.execute("""INSERT INTO login_info (user_id, password_hash, user_type, cust_id)
                      VALUES (%s, %s, 1, %s)""", (username, password_hash, cust_id))
    db.commit()
    db.close()

# Forgot UserID
def forgot_userid(email):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM login_info WHERE cust_id = (SELECT cust_id FROM customers WHERE email = %s)", (email,))
    user = cursor.fetchone()
    db.close()

    if user:
        return user['user_id']
    else:
        return None



# Function to check if the username already exists in the database
def username_exists(username):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT user_id FROM login_info WHERE user_id = %s", (username,))
    user = cursor.fetchone()
    db.close()
    return user is not None


# Main pages
def login_page():
    st.markdown(f'<h1><span style="color:#4169e1">L</span>ogin Page</h1>', unsafe_allow_html=True)
    
    # Create a login form
    with st.form(key="login_form"):
        user_id = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        submit_button = st.form_submit_button("Login")
    
    if submit_button:
        if not user_id or not password:
            st.error("Please fill in both username and password.")
            return
        
        # Connect to the database to validate credentials
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM login_info WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        db.close()

        if user:
            # Check if the entered password matches the stored hash
            if check_password(user['password_hash'], password):
                # Set session state for logged-in user
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.user_type = user['user_type']  # 0 for Admin, 1 for Customer
                
                # Fetch additional user info for display purposes
                if user['user_type'] == 1:  # Customer
                    db = get_db_connection()
                    cursor = db.cursor(dictionary=True)
                    cursor.execute("SELECT cust_name FROM customers WHERE cust_id = %s", (user['cust_id'],))
                    customer = cursor.fetchone()
                    db.close()
                    
                    if customer:
                        st.session_state.full_name = customer['cust_name']
                    else:
                        st.session_state.full_name = "Customer"
                else:  # Admin
                    st.session_state.full_name = "Admin"

                st.success(f"Welcome, {st.session_state.full_name}!")
                with st.spinner("Will redirect to home 5 seconds..."):
                        time.sleep(5)
                st.rerun()  # Rerun the app to update navigation and pages
            else:
                st.error("Invalid password. Please try again.")
        else:
            st.error("Invalid username. Please try again.")


def registration_page():
    st.markdown(f'<h1>New Customer <span style="color:#4169e1">R</span>egistration</h1>', unsafe_allow_html=True)

    # Create the form for registration
    with st.form(key="registration_form"):
        username = st.text_input("Username", placeholder="Enter a unique username (alphanumeric, no spaces).")  # New field for username
        cust_name = st.text_input("Customer Name", placeholder="Enter your full name as per your ID.")
        email = st.text_input("Email", placeholder="Enter a valid email address (e.g., name@example.com).")
        phone = st.text_input("Phone", placeholder="Enter your phone number with country code (e.g., +1 123 456 7890).", max_chars=13)
        address = st.text_area("Address", placeholder="Enter your complete residential address.")
        gender = st.selectbox("Gender", ["Select", "Male", "Female", "Other"], index=0)  # Initial placeholder "Select"
        
        dob = st.date_input(
            "Date of Birth",
            value=None,  # Set default value to None
            min_value=datetime(1900, 1, 1),  # Minimum date allowed
            max_value=datetime.today(),  # Maximum date allowed
            key="dob_input"
        )

        if dob is None:
            st.warning("Please select a date of birth.")

        city = st.text_input("City", placeholder="Enter the city where you currently reside.")
        country = st.text_input("Country", placeholder="Enter the country where you currently reside.")
        password = st.text_input("Password", type="password")
        st.info("Password must be at least 8 characters long and include at least one special character, one uppercase letter, and one number.")
        # Submit button inside the form
        submit_button = st.form_submit_button("Register")
    
    # Check if the form is submitted
    if submit_button:
        if not all([username, cust_name, email, phone, address, gender, dob, city, country, password]):
            st.error("All fields are required.")
        elif len(phone) != 13:
            st.error("Phone number must be exactly 13 characters long, including the country code.")
        elif not validate_password(password):
            st.error("Password must meet the requirements: it must be at least 8 characters long, include at least one special character, one uppercase letter, and one number.")
        elif username_exists(username):  # Check if the username is already in use
            st.error("Username is already in use. Please choose a different one.")
        else:
            register_user(username, cust_name, email, phone, address, gender, dob, city, country, password)
            st.success("Registration successful, use your username for login.")
        reset_form()

def reset_form():
    """Refresh the page to reset the form."""
    time.sleep(2)  # Wait for 3 seconds before refreshing
    st.markdown('<meta http-equiv="refresh" content="0">', unsafe_allow_html=True)



# Define the function that will show the dialog with the UserID
@st.dialog("Your Username")
def show_userid():
    if 'user_id' in st.session_state:
        st.success(f"Found your username: {st.session_state.user_id}")
    else:
        st.write("UserID not found.")
    
    # Clear session state to reset the dialog and close it
    if st.button("OK"):
        # This will clear the session state and close the dialog
        st.session_state.user_id = None
        st.session_state.email_verified = False
        st.session_state.code_verified = False  # This will rerun the app and refresh the page
        reset_form()

def forgot_userid_page():
    st.markdown(f'<h1>Forgot <span style="color:#4169e1">U</span>sername</h1>', unsafe_allow_html=True)
    # Initialize session state for user_id if not already initialized
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None  # Default initialization

    # Create the form for forgot username page
    with st.form(key="forgot_userid_form"):
        # Step 1: Input for Email (Only shown initially)
        if 'email_verified' not in st.session_state:
            email = st.text_input("Enter your email")
            submit_button = st.form_submit_button("Send Code")

            # If submit button is clicked, send the code to the user's email
            if submit_button:
                if email:
                    user_id = forgot_userid(email)  # Pass email to the function to get the user_id
                    if user_id:
                        st.session_state.email_verified = True
                        st.session_state.user_id = user_id  # Set user_id in session state
                        st.session_state.code_verified = False  # Reset code_verified flag
                        st.info("Code sent to your email.")
                    else:
                        st.error("No username found for this email.")
                else:
                    st.error("Please enter a valid email.")

        # Step 2: Code Verification (Only shown after email is verified)
        if 'email_verified' in st.session_state and not st.session_state.code_verified:
            code = st.text_input("Enter Code")
            verify_button = st.form_submit_button("Verify Code")

            # Perform code verification when the button is clicked
            if verify_button:
                if code == "1010":  # Always mock code "1010"
                    st.session_state.code_verified = True
                    # Display the UserID dialog after successful code verification
                    show_userid()
                else:
                    st.error("Incorrect code entered.")

# Function to validate if the user_id exists in the database
def validate_user_id(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT ld.user_id, cd.email
        FROM login_info ld
        JOIN customers cd ON ld.cust_id = cd.cust_id
        WHERE ld.user_id = %s
    """, (user_id,))
    
    user = cursor.fetchone()
    db.close()
    
    if user:
        return user['email']  # Return the email associated with the user_id
    else:
        return None  # Return None if the user_id does not exist

# Function to get the current password hash from the database
def get_current_password(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT password_hash FROM login_info WHERE user_id = %s", (user_id,))
    result = cursor.fetchone()
    db.close()
    
    if result:
        return result[0]  # Return the current password hash
    else:
        return None  # Return None if no user found

# Function to update the password in the database
def forgot_password(user_id, new_password):
    db = get_db_connection()
    cursor = db.cursor()
    new_password_hash = hash_password(new_password)
    cursor.execute("UPDATE login_info SET password_hash = %s WHERE user_id = %s", (new_password_hash, user_id))
    db.commit()
    db.close()

# Function to validate password based on given requirements
def validate_password(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    if not any(char in "!@#$%^&*()" for char in password):
        return False
    return True

# Reset Password Dialog
@st.dialog("Reset Password")
def reset_password_dialog():
    if "code_verified" in st.session_state and st.session_state.code_verified:
        with st.form(key="reset_password_form"):
            new_password = st.text_input("New Password", type="password", placeholder="Enter a strong password")
            confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Re-enter the new password")
            submit_button = st.form_submit_button("Submit")

            if submit_button:
                if new_password == confirm_password:
                    if validate_password(new_password):
                        forgot_password(st.session_state.user_id, new_password)
                        st.success("Password reset successful.")
                        time.sleep(3)
                        st.session_state.clear()
                        st.rerun()
                    else:
                        st.error("Password does not meet the required criteria. Ensure it is at least 8 characters long, contains an uppercase letter, a digit, and a special character.")
                else:
                    st.error("Passwords do not match. Please try again.")
    else:
        st.error("Please verify the code first.")

# Forgot Password Page
def forgot_password_page():
    st.markdown(f'<h1>Forgot <span style="color:#4169e1">P</span>assword</h1>', unsafe_allow_html=True)
    
    # Initialize session state for user_id, email, and verification flags
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None  # Initialize user_id to None if not set
    if 'email_verified' not in st.session_state:
        st.session_state.email_verified = False  # Initialize email_verified flag
    if 'code_verified' not in st.session_state:
        st.session_state.code_verified = False  # Initialize code_verified flag
    if 'show_code_input' not in st.session_state:
        st.session_state.show_code_input = False  # Initialize flag for showing code input

    # Step 1: User ID input and verification
    with st.container():  # Use container for both user_id and code input sections
        if not st.session_state.email_verified:
            with st.form(key="forgot_password_form"):
                user_id = st.text_input("Enter your Customer ID")
                submit_button = st.form_submit_button("Send Code")

                if submit_button:
                    if user_id:
                        # Retrieve the email associated with the user_id from the database
                        email = validate_user_id(user_id)  # Ensure this function is implemented

                        if email:
                            # Store email and user_id in session state
                            st.session_state.user_id = user_id
                            st.session_state.email = email
                            st.session_state.code_verified = False  # Reset code_verified flag
                            st.session_state.email_verified = True  # Mark email as verified
                            st.info(f"Code has been sent to your registered email: {email}")
                            st.session_state.show_code_input = True  # Show code input section
                        else:
                            st.error("No Customer found with this user ID.")
                    else:
                        st.error("Please enter a valid user ID.")

        # Step 2: Code Verification input (Only shown after user_id is verified)
        if st.session_state.show_code_input:
            with st.form(key="code_verification_form"):
                code = st.text_input("Enter Verification Code")
                verify_button = st.form_submit_button("Verify Code")

                if verify_button:
                    if code == "1010":  # Replace with actual verification logic
                        st.session_state.code_verified = True
                        # Show the Reset Password dialog after successful code verification
                        reset_password_dialog()  # Show the reset password form
                    else:
                        st.error("Incorrect code entered.")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.full_name = None

# Define Home Page
import streamlit as st

def home_page():
    # Title with custom color
    st.markdown('<h1>Welcome to the <span style="color:#4169e1;">C</span>ustomer <span style="color:#4169e1;">M</span>anagement App</h1>', unsafe_allow_html=True)
    st.write("")

    # Introduction Section
    st.markdown("""
    <div style="background-color:#f7f7f7; padding: 20px; border-radius: 8px;">
    Why Choose Our Customer Management App?
    Our app is designed to help businesses like yours grow and succeed by offering powerful tools and insights into your customer base. With a user-friendly interface and advanced analytics, you can:
    <ul>
        <li><b>Gain valuable insights:</b> Analyze customer behaviors and trends to make informed decisions.</li>
        <li><b>Build stronger relationships:</b> Manage customer interactions and deliver personalized experiences.</li>
        <li><b>Save time and resources:</b> Automate routine tasks and focus on what matters most—your customers.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    # Key Features Section with Icons
    st.markdown("<h3 style='color:#4169e1;'>Key Features:</h3>", unsafe_allow_html=True)
    features = [
        ("Customer Profiles", "Manage customer details with ease."),
        ("Purchase Tracking", "Track spending patterns and opportunities."),
        ("Membership Management", "Seamlessly manage memberships and subscriptions."),
        ("Data Security", "Your data is encrypted and securely stored."),
        ("Customizable Dashboards", "Tailor the app to meet your business needs."),
    ]
    
    cols = st.columns(3)
    for i, feature in enumerate(features):
        with cols[i % 3]:
            st.markdown(f"<h4><b> {feature[0]}</b></h4>", unsafe_allow_html=True)
            st.write(feature[1])
    
    # How It Works Section
    st.markdown("<h3 style='color:#4169e1;'>How It Works:</h3>", unsafe_allow_html=True)
    st.markdown("""
    <ol>
        <li><b>Register your business:</b> Create an account and set up your company profile.</li>
        <li><b>Add customers:</b> Input customer details manually or import them from existing databases.</li>
        <li><b>Track and analyze:</b> Access detailed reports on customer activity, purchases, and trends.</li>
        <li><b>Grow your business:</b> Use insights to create targeted marketing campaigns and enhance customer satisfaction.</li>
    </ol>
    """, unsafe_allow_html=True)

    # Benefits Section
    st.markdown("<h3 style='color:#4169e1;'>Benefits:</h3>", unsafe_allow_html=True)
    st.markdown("""
    <ul>
        <li>Increased customer loyalty</li>
        <li>Improved operational efficiency</li>
        <li>Higher sales and revenue growth</li>
    </ul>
    """, unsafe_allow_html=True)

    # Call to Action Section
    st.markdown(""" 
    <div style="text-align:center; background-color:#4169e1; color:white; padding: 20px; border-radius: 8px;">
        <h2>Get Started Today!</h2>
        <p>Whether you're a small business owner or an enterprise-level manager, our app is here to help you succeed.</p>
        <a href="#get-started" style="background-color:#f8f8f8; color:#4169e1; padding: 10px 20px; border-radius: 5px; text-decoration:none; font-weight:bold;">Get Started</a>
    </div>
    """, unsafe_allow_html=True)
    st.write("")

    # Testimonials Section
    st.markdown("<h3 style='color:#4169e1;'>Testimonials:</h3>", unsafe_allow_html=True)
    st.markdown("""
    <blockquote>
        <p><i>"This app transformed the way I interact with my customers. Highly recommend it!"</i> – <b>John D.</b> (Small Business Owner)</p>
        <p><i>"The analytics features are a game-changer for our campaigns."</i> – <b>Sarah P.</b> (Marketing Manager)</p>
    </blockquote>
    """, unsafe_allow_html=True)

    # Contact Us Section with Icons
    st.markdown("<h3 style='color:#4169e1;'>Contact Us:</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background-color:#f7f7f7; padding: 20px; border-radius: 8px;">
        Have questions or need support? Reach out to our team:
        <ul>
            <li><b>Email:</b> <a href="mailto:support@customerapp.com">rohitpawra189@gmail.com</a></li>
            <li><b>github:</b> rohitp189</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Footer Section with custom credits
    st.markdown("""
    <footer style="display: flex; justify-content: space-between; padding: 10px; background-color: #f7f7f7;">
        <span style="color:#4169e1;">© Rohit Pawra 2024</span>
        <span style="color:#4169e1;">v1.2</span>
    </footer>
    """, unsafe_allow_html=True)


# Define Logout Page
def logout_page():
    st.markdown(f"## Account: {st.session_state.get('full_name', 'User')}")
    if st.session_state.logged_in:
        if st.button("Log out"):
            # Clear the session state for login
            st.session_state.logged_in = False
            st.session_state.full_name = None
            st.session_state.user_type = None
            st.session_state.user_id = None
            st.success("Logged out successfully.")
            st.rerun()

# Main function for logged-in users
def loggedin():
    if st.session_state.user_type == 0:  # Admin
        main()  # Run Admin's main page
    else:  # Customer
        customer_app()  # Run Customer's main page

# Placeholder for "Manage" tab when not logged in
def loggedout():
    st.markdown(f'<h1>Please <span style="color:#4169e1">L</span>ogin to access this page!</h1>', unsafe_allow_html=True)
# Pages Configuration
home = st.Page(home_page, title="Home", icon=":material/home:")
login = st.Page(login_page, title="Login", icon=":material/login:")
logout = st.Page(logout_page, title=f"Account: {st.session_state.get('full_name', 'User')}", icon=":material/account_circle:")
mlogout = st.Page(loggedout, title="Manage", icon=":material/manage_accounts:")
mlogin = st.Page(loggedin, title="Manage", icon=":material/manage_accounts:")
regist = st.Page(registration_page, title="New Registration", icon=":material/person_add:")
forgotp = st.Page(forgot_password_page, title="Forgot Password", icon=":material/password:")
forgotid = st.Page(forgot_userid_page, title="Forgot Username", icon=":material/question_mark:")

# Navigation Setup
if st.session_state.get("logged_in", False):
    if st.session_state.user_type == 0:  # Admin
        pg = st.navigation(
            {
                "Home": [home],
                "Account": [logout],
                "Manage Customers": [mlogin],  # Admin can manage customers
            }
        )
    else:  # Customer
        pg = st.navigation(
            {
                "Home": [home],
                "Account": [logout],
                "Manage Account": [mlogin],  # Customer manages their own account
            }
        )
else:
    pg = st.navigation(
        {
            "Home": [home],
            "Account": [login, regist, forgotp, forgotid],
            "Manage": [mlogout],
        }
    )

# Run Selected Page
pg.run()
