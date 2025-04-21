import customtkinter as ctk
from tkinter import messagebox, ttk
import mysql.connector
import subprocess
import sys
import hashlib

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="141.209.241.57",
        user="cheru4a",  # Replace with your MySQL username
        password="mypass",  # Replace with your MySQL password
        database="BIS698M1530_GRP1" 
    )

# ------------------- Global Variables -------------------
current_admin = None
selected_user = None

# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Admin Session Management -------------------
def load_admin_session():
    """Load admin information from database"""
    global current_admin
    
    # Check if any admin_id was passed as a command line argument
    if len(sys.argv) > 1:
        try:
            admin_id = int(sys.argv[1])
            
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Admin WHERE Admin_ID = %s",
                (admin_id,)
            )
            admin_data = cursor.fetchone()
            
            if admin_data:
                current_admin = admin_data
                return True
                
        except (ValueError, IndexError, mysql.connector.Error) as err:
            print(f"Error loading admin session: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    return False

# ------------------- Navigation Functions -------------------
def open_page(page_name):
    """Open another page and close the current one"""
    try:
        # Pass the current admin ID to the next page if an admin is logged in
        admin_param = [str(current_admin['Admin_ID'])] if current_admin else []
        
        # Construct the command to run the appropriate Python file
        command = [sys.executable, f"{page_name.lower()}.py"] + admin_param
        
        subprocess.Popen(command)
        app.destroy()  # Close the current window
    except Exception as e:
        print(f"Navigation Error: {e}")
        messagebox.showerror("Navigation Error", f"Unable to open {page_name} page: {e}")

def go_to_dashboard():
    open_page("admin")

def go_to_manage_bookings():
    open_page("manage_bookings")

def go_to_manage_users():
    open_page("manage_users")

def logout():
    """Log out the current admin and return to login page"""
    global current_admin
    current_admin = None
    open_page("login")

# ------------------- User Management Functions -------------------
def load_users():
    """Load all users from database"""
    users = []
    
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get users with booking count
        cursor.execute(
            """
            SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone, 
                   u.user_address, COUNT(b.Booking_ID) as bookings
            FROM Users u
            LEFT JOIN Booking b ON u.user_id = b.User_ID
            GROUP BY u.user_id
            ORDER BY u.user_id
            """
        )
        
        users = cursor.fetchall()
        return users
        
    except mysql.connector.Error as err:
        print(f"Error loading users: {err}")
        messagebox.showerror("Database Error", f"Error loading users: {err}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def load_user_details(user_id):
    """Load details for a specific user"""
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get user details
        cursor.execute(
            """
            SELECT u.*, COUNT(b.Booking_ID) as bookings,
                  SUM(b.Total_Cost) as total_spent
            FROM Users u
            LEFT JOIN Booking b ON u.user_id = b.User_ID
            WHERE u.user_id = %s
            GROUP BY u.user_id
            """,
            (user_id,)
        )
        
        user = cursor.fetchone()
        
        # Get user's bookings
        if user:
            cursor.execute(
                """
                SELECT b.Booking_ID, r.Room_Type, b.Check_IN_Date, 
                       b.Check_Out_Date, b.Total_Cost, b.Booking_Status
                FROM Booking b
                JOIN Room r ON b.Room_ID = r.Room_ID
                WHERE b.User_ID = %s
                ORDER BY b.Check_IN_Date DESC
                LIMIT 5
                """,
                (user_id,)
            )
            user['recent_bookings'] = cursor.fetchall()
        
        return user
        
    except mysql.connector.Error as err:
        print(f"Error loading user details: {err}")
        messagebox.showerror("Database Error", f"Error loading user details: {err}")
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def create_user():
    """Create a new user"""
    # Get data from entry fields
    first_name = first_name_entry.get()
    last_name = last_name_entry.get()
    email = email_entry.get()
    phone = phone_entry.get()
    address = address_entry.get()
    password = password_entry.get()
    
    # Validate input
    if not first_name or not last_name or not email or not password:
        messagebox.showwarning("Input Error", "First name, last name, email, and password are required")
        return
    
    # Hash the password
    hashed_password = hash_password(password)
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        if cursor.fetchone():
            messagebox.showwarning("Input Error", "A user with this email already exists")
            return
        
        # Insert new user
        cursor.execute(
            """
            INSERT INTO Users (first_name, last_name, email, phone, password, user_address)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (first_name, last_name, email, phone, hashed_password, address)
        )
        
        connection.commit()
        messagebox.showinfo("Success", "User created successfully")
        
        # Clear form fields
        clear_user_form()
        
        # Refresh user table
        populate_user_table()
        
    except mysql.connector.Error as err:
        print(f"Error creating user: {err}")
        messagebox.showerror("Database Error", f"Error creating user: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def update_user():
    """Update an existing user"""
    global selected_user
    
    if not selected_user:
        messagebox.showwarning("Selection Error", "No user selected")
        return
    
    # Get data from entry fields
    first_name = first_name_entry.get()
    last_name = last_name_entry.get()
    email = email_entry.get()
    phone = phone_entry.get()
    address = address_entry.get()
    password = password_entry.get()
    
    # Validate input
    if not first_name or not last_name or not email:
        messagebox.showwarning("Input Error", "First name, last name, and email are required")
        return
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if email already exists for a different user
        cursor.execute("SELECT user_id FROM Users WHERE email = %s AND user_id != %s", 
                    (email, selected_user['user_id']))
        if cursor.fetchone():
            messagebox.showwarning("Input Error", "Another user with this email already exists")
            return
        
        # Update user data
        if password:
            # Update with new password
            hashed_password = hash_password(password)
            cursor.execute(
                """
                UPDATE Users
                SET first_name = %s, last_name = %s, email = %s, 
                    phone = %s, user_address = %s, password = %s
                WHERE user_id = %s
                """,
                (first_name, last_name, email, phone, address, 
                 hashed_password, selected_user['user_id'])
            )
        else:
            # Update without changing password
            cursor.execute(
                """
                UPDATE Users
                SET first_name = %s, last_name = %s, email = %s, 
                    phone = %s, user_address = %s
                WHERE user_id = %s
                """,
                (first_name, last_name, email, phone, address, 
                 selected_user['user_id'])
            )
        
        connection.commit()
        messagebox.showinfo("Success", "User updated successfully")
        
        # Refresh user data
        selected_user = load_user_details(selected_user['user_id'])
        
        # Update user details display
        show_user_details()
        
        # Refresh user table
        populate_user_table()
        
    except mysql.connector.Error as err:
        print(f"Error updating user: {err}")
        messagebox.showerror("Database Error", f"Error updating user: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def delete_user():
    """Delete a user (with confirmation)"""
    global selected_user
    
    if not selected_user:
        messagebox.showwarning("Selection Error", "No user selected")
        return
    
    # Confirm deletion
    confirmed = messagebox.askyesno(
        "Confirm Deletion",
        f"Are you sure you want to delete the user {selected_user['first_name']} {selected_user['last_name']}?\n\n"
        f"This will also delete all their bookings and reviews.\n"
        f"This action cannot be undone."
    )
    
    if not confirmed:
        return
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Delete the user
        cursor.execute("DELETE FROM Users WHERE user_id = %s", (selected_user['user_id'],))
        
        connection.commit()
        messagebox.showinfo("Success", "User deleted successfully")
        
        # Clear form and details
        clear_user_form()
        hide_user_details()
        
        # Reset selected user
        selected_user = None
        
        # Refresh user table
        populate_user_table()
        
    except mysql.connector.Error as err:
        print(f"Error deleting user: {err}")
        messagebox.showerror("Database Error", f"Error deleting user: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- UI Functions -------------------
def populate_user_table():
    """Populate the user table with data from database"""
    # Clear existing rows
    for row in user_table.get_children():
        user_table.delete(row)
    
    # Load users and add to table
    users = load_users()
    
    for user in users:
        # Format values
        full_name = f"{user['first_name']} {user['last_name']}"
        phone = user['phone'] if user['phone'] else "N/A"
        address = user['user_address'] if user['user_address'] else "N/A"
        bookings = str(user['bookings'])
        
        # Insert into table
        user_table.insert('', 'end', iid=user['user_id'], values=(
            user['user_id'],
            full_name,
            user['email'],
            phone,
            address,
            bookings
        ))
    
    # Update user count
    user_count_label.configure(text=f"Total Users: {len(users)}")

def show_user_details(event=None):
    """Show details for the selected user"""
    global selected_user
    
    # If event is None, use the currently selected user
    if event is not None:
        selected_id = user_table.focus()
        if not selected_id:
            return
        
        # Convert to integer
        user_id = int(selected_id)
        
        # Load user details
        user = load_user_details(user_id)
        if not user:
            return
        
        selected_user = user
    
    # Fill in the form fields
    first_name_entry.delete(0, 'end')
    first_name_entry.insert(0, selected_user['first_name'])
    
    last_name_entry.delete(0, 'end')
    last_name_entry.insert(0, selected_user['last_name'])
    
    email_entry.delete(0, 'end')
    email_entry.insert(0, selected_user['email'])
    
    phone_entry.delete(0, 'end')
    if selected_user['phone']:
        phone_entry.insert(0, selected_user['phone'])
    
    address_entry.delete(0, 'end')
    if selected_user['user_address']:
        address_entry.insert(0, selected_user['user_address'])
    
    password_entry.delete(0, 'end')
    
    # Update action buttons - show appropriate buttons for edit mode
    create_btn.grid_forget()  # Hide create button
    update_btn.grid(row=0, column=0, padx=(0, 10))
    delete_btn.grid(row=0, column=1, padx=(0, 10))
    clear_btn.grid(row=0, column=2)
    
    # Enable appropriate buttons
    update_btn.configure(state="normal")
    delete_btn.configure(state="normal")
    
    # Show user details section
    details_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
    
    # Update user details display
    details_user_id.configure(text=f"User #{selected_user['user_id']}")
    details_name.configure(text=f"{selected_user['first_name']} {selected_user['last_name']}")
    details_email.configure(text=f"{selected_user['email']}")
    details_phone.configure(text=f"Phone: {selected_user['phone'] if selected_user['phone'] else 'N/A'}")
    details_address.configure(text=f"Address: {selected_user['user_address'] if selected_user['user_address'] else 'N/A'}")
    
    # Update booking stats
    total_bookings = selected_user['bookings'] if selected_user['bookings'] else 0
    total_spent = selected_user['total_spent'] if selected_user['total_spent'] else 0
    
    details_bookings.configure(text=f"Total Bookings: {total_bookings}")
    details_spent.configure(text=f"Total Spent: ${total_spent}")
    
    # Clear the bookings table
    for row in bookings_table.get_children():
        bookings_table.delete(row)
    
    # Add recent bookings
    if 'recent_bookings' in selected_user and selected_user['recent_bookings']:
        for booking in selected_user['recent_bookings']:
            bookings_table.insert('', 'end', values=(
                booking['Booking_ID'],
                booking['Room_Type'],
                booking['Check_IN_Date'].strftime('%Y-%m-%d') if hasattr(booking['Check_IN_Date'], 'strftime') else booking['Check_IN_Date'],
                booking['Check_Out_Date'].strftime('%Y-%m-%d') if hasattr(booking['Check_OUT_Date'], 'strftime') else booking['Check_Out_Date'],
                f"${booking['Total_Cost']}",
                booking['Booking_Status']
            ))

def clear_user_form():
    """Clear the user form fields"""
    first_name_entry.delete(0, 'end')
    last_name_entry.delete(0, 'end')
    email_entry.delete(0, 'end')
    phone_entry.delete(0, 'end')
    address_entry.delete(0, 'end')
    password_entry.delete(0, 'end')
    
    # Reset selected user
    global selected_user
    selected_user = None
    
    # Switch to create mode interface
    new_user_mode()

def hide_user_details():
    """Hide the user details section"""
    details_frame.pack_forget()

def new_user_mode():
    """Switch to new user mode"""
    # Hide user details section
    hide_user_details()
    
    # Update buttons for create mode
    update_btn.grid_forget()
    delete_btn.grid_forget()
    
    create_btn.grid(row=0, column=0, padx=(0, 10))
    clear_btn.grid(row=0, column=1)
    
    # Enable/disable appropriate buttons
    create_btn.configure(state="normal")
    
    # Set focus to first name field
    first_name_entry.focus_set()

def search_users():
    """Search users based on search term"""
    search_term = search_entry.get().lower()
    
    if not search_term:
        # If search term is empty, show all users
        populate_user_table()
        return
    
    # Clear existing rows
    for row in user_table.get_children():
        user_table.delete(row)
    
    # Load all users
    users = load_users()
    
    # Filter users
    filtered_users = []
    for user in users:
        # Check if search term is in name, email, or address
        full_name = f"{user['first_name']} {user['last_name']}".lower()
        email = user['email'].lower()
        address = user['user_address'].lower() if user['user_address'] else ""
        
        if (search_term in full_name or search_term in email or 
            search_term in address):
            filtered_users.append(user)
    
    # Add filtered users to table
    for user in filtered_users:
        # Format values
        full_name = f"{user['first_name']} {user['last_name']}"
        phone = user['phone'] if user['phone'] else "N/A"
        address = user['user_address'] if user['user_address'] else "N/A"
        bookings = str(user['bookings'])
        
        # Insert into table
        user_table.insert('', 'end', iid=user['user_id'], values=(
            user['user_id'],
            full_name,
            user['email'],
            phone,
            address,
            bookings
        ))
    
    # Update user count
    user_count_label.configure(text=f"Filtered Users: {len(filtered_users)}")

# ----------------- Color Constants -----------------
PRIMARY_COLOR = "#2C3E50"       # Dark blue for main elements
SECONDARY_COLOR = "#3498DB"     # Lighter blue for accents
SUCCESS_COLOR = "#28A745"       # Green for success actions
SUCCESS_HOVER = "#218838"       # Darker green for hover
DANGER_COLOR = "#DC3545"        # Red for dangerous actions
DANGER_HOVER = "#C82333"        # Darker red for hover
WARNING_COLOR = "#FFC107"       # Yellow for warnings
INFO_COLOR = "#17A2B8"          # Teal for info
LIGHT_COLOR = "#E9ECEF"         # Light gray for backgrounds
DARK_COLOR = "#343A40"          # Dark for text
GRAY_COLOR = "#6C757D"          # Medium gray for secondary text
BORDER_COLOR = "#DEE2E6"        # Border color

# ----------------- Initialize App -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - Manage Users")
app.geometry("1200x750")
app.minsize(1000, 700)  # Set minimum window size for responsiveness

# Try to load admin session
if not load_admin_session():
    messagebox.showwarning("Login Required", "Admin login required to access this page")
    open_page("admin_login")

# ----------------- Main Frame -----------------
main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
main_frame.pack(expand=True, fill="both")

# ----------------- Sidebar (Navigation) -----------------
sidebar = ctk.CTkFrame(main_frame, fg_color=PRIMARY_COLOR, width=220, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)  # Prevent the frame from shrinking

# Header with logo
logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=100)
logo_frame.pack(fill="x", pady=(20, 10))

logo_label = ctk.CTkLabel(
    logo_frame, 
    text="H", 
    font=("Arial", 32, "bold"), 
    text_color="white",
    fg_color=SECONDARY_COLOR,
    corner_radius=12,
    width=60,
    height=60
)
logo_label.place(relx=0.5, rely=0.5, anchor="center")

ctk.CTkLabel(sidebar, text="Hotel Booking", font=("Arial", 18, "bold"), text_color="white").pack(pady=(0, 20))

# Navigation buttons with icons
nav_buttons = [
    ("📊 Dashboard", go_to_dashboard),
    ("📅 Manage Bookings", go_to_manage_bookings),
    ("👤 Manage Users", go_to_manage_users),
    ("🚪 Logout", logout)
]

for btn_text, btn_command in nav_buttons:
    is_active = "Manage Users" in btn_text
    btn = ctk.CTkButton(sidebar, text=btn_text, font=("Arial", 14), 
                      fg_color="#34495E" if is_active else "transparent", 
                      hover_color="#34495E",
                      anchor="w", height=45, width=200, 
                      command=btn_command)
    btn.pack(pady=5, padx=10)

# Welcome message with admin name if available
if current_admin:
    admin_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=80)
    admin_frame.pack(side="bottom", fill="x", pady=20, padx=10)
    
    admin_name = current_admin['AdminName']
    ctk.CTkLabel(admin_frame, text=f"Welcome,", 
               font=("Arial", 12), text_color="#8395a7").pack(anchor="w")
    ctk.CTkLabel(admin_frame, text=f"{admin_name}", 
               font=("Arial", 14, "bold"), text_color="white").pack(anchor="w")

# ----------------- Content Area -----------------
content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
content_frame.pack(side="right", fill="both", expand=True)

# ----------------- Header -----------------
header_frame = ctk.CTkFrame(content_frame, fg_color="white", height=60)
header_frame.pack(fill="x", padx=30, pady=(30, 10))

ctk.CTkLabel(header_frame, text="Manage Users", 
           font=("Arial", 28, "bold"), text_color=PRIMARY_COLOR).pack(side="left")

# New User and Search
action_frame = ctk.CTkFrame(header_frame, fg_color="white")
action_frame.pack(side="right")

# New user button
new_user_btn = ctk.CTkButton(action_frame, text="+ New User", font=("Arial", 12, "bold"), 
                           fg_color=SUCCESS_COLOR, hover_color=SUCCESS_HOVER,
                           command=new_user_mode, width=120, height=35, corner_radius=8)
new_user_btn.pack(side="left", padx=(0, 15))

# Search with improved styling
search_frame = ctk.CTkFrame(action_frame, fg_color=LIGHT_COLOR, corner_radius=8, height=35)
search_frame.pack(side="left", fill="y")

search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Search users...", 
                          border_width=0, fg_color=LIGHT_COLOR, height=35)
search_entry.pack(side="left", padx=(10, 0))

search_btn = ctk.CTkButton(search_frame, text="🔍", font=("Arial", 12, "bold"), 
                         fg_color=LIGHT_COLOR, text_color=DARK_COLOR, hover_color=BORDER_COLOR,
                         width=35, height=35, corner_radius=0, command=search_users)
search_btn.pack(side="right")

# ----------------- User Form Section -----------------
form_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                        border_color=BORDER_COLOR, corner_radius=10)
form_frame.pack(fill="x", padx=30, pady=(0, 20))

# Form header
form_header = ctk.CTkFrame(form_frame, fg_color=LIGHT_COLOR, height=50, corner_radius=0)
form_header.pack(fill="x")

ctk.CTkLabel(form_header, text="User Information", 
           font=("Arial", 16, "bold"), text_color=PRIMARY_COLOR).pack(side="left", padx=20, pady=10)

# Form fields
form_fields = ctk.CTkFrame(form_frame, fg_color="white")
form_fields.pack(fill="x", padx=20, pady=(20, 20))

# Create two columns with grid layout for better responsiveness
form_fields.columnconfigure(0, weight=1)
form_fields.columnconfigure(1, weight=1)

# Left column - First Name, Last Name, Email
left_label_frame = ctk.CTkFrame(form_fields, fg_color="transparent")
left_label_frame.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

ctk.CTkLabel(left_label_frame, text="First Name *", font=("Arial", 12), anchor="w").pack(fill="x")
first_name_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter first name")
first_name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

ctk.CTkLabel(form_fields, text="Last Name *", font=("Arial", 12), anchor="w").grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
last_name_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter last name")
last_name_entry.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

ctk.CTkLabel(form_fields, text="Email *", font=("Arial", 12), anchor="w").grid(row=4, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
email_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter email address")
email_entry.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

# Right column - Phone, Address, Password
ctk.CTkLabel(form_fields, text="Phone", font=("Arial", 12), anchor="w").grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
phone_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter phone number")
phone_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))

ctk.CTkLabel(form_fields, text="Address", font=("Arial", 12), anchor="w").grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
address_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter address")
address_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))

ctk.CTkLabel(form_fields, text="Password *", font=("Arial", 12), anchor="w").grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
password_entry = ctk.CTkEntry(form_fields, height=35, show="•", placeholder_text="Enter password")
password_entry.grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))

# Form buttons
buttons_frame = ctk.CTkFrame(form_fields, fg_color="transparent")
buttons_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

# Center-align the button container
buttons_frame.columnconfigure(0, weight=1)
buttons_frame.columnconfigure(1, weight=1)
buttons_frame.columnconfigure(2, weight=1)
buttons_frame.columnconfigure(3, weight=1)

# Button container
button_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
button_container.grid(row=0, column=1, columnspan=2)

# Use grid instead of pack for better control
create_btn = ctk.CTkButton(button_container, text="Create User", font=("Arial", 13, "bold"), 
                         fg_color=SUCCESS_COLOR, hover_color=SUCCESS_HOVER,
                         command=create_user, width=140, height=40, corner_radius=8)

update_btn = ctk.CTkButton(button_container, text="Update User", font=("Arial", 13, "bold"), 
                         fg_color=PRIMARY_COLOR, hover_color="#1E4D88",
                         command=update_user, width=140, height=40, corner_radius=8, state="disabled")

delete_btn = ctk.CTkButton(button_container, text="Delete User", font=("Arial", 13, "bold"), 
                         fg_color=DANGER_COLOR, hover_color=DANGER_HOVER,
                         command=delete_user, width=140, height=40, corner_radius=8, state="disabled")

clear_btn = ctk.CTkButton(button_container, text="Clear Form", font=("Arial", 13, "bold"), 
                        fg_color=GRAY_COLOR, hover_color="#5A6268",
                        command=clear_user_form, width=140, height=40, corner_radius=8)

# Initially show only the create and clear buttons (new user mode)
create_btn.grid(row=0, column=0, padx=(0, 10))
clear_btn.grid(row=0, column=1)

# ----------------- User Table Section -----------------
table_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                        border_color=BORDER_COLOR, corner_radius=10)
table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

# Table header
table_header = ctk.CTkFrame(table_frame, fg_color=LIGHT_COLOR, height=50, corner_radius=0)
table_header.pack(fill="x")

ctk.CTkLabel(table_header, text="User List", 
           font=("Arial", 16, "bold"), text_color=PRIMARY_COLOR).pack(side="left", padx=20, pady=10)

# User count
user_count_label = ctk.CTkLabel(table_header, text="Total Users: 0", font=("Arial", 12))
user_count_label.pack(side="right", padx=20, pady=10)

# Create table container with fixed height
table_container = ctk.CTkFrame(table_frame, fg_color="white")
table_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))

# Style configuration for the treeview
style = ttk.Style()
style.configure("Treeview", 
                background="#ffffff", 
                foreground="#333333", 
                rowheight=40, 
                fieldbackground="#ffffff")
style.configure("Treeview.Heading", 
                background="#f8f9fa", 
                foreground="#2C3E50", 
                font=('Arial', 11, 'bold'))
style.map('Treeview', background=[('selected', '#3498DB')])

# Create treeview for users
columns = ('ID', 'Name', 'Email', 'Phone', 'Address', 'Bookings')
user_table = ttk.Treeview(table_container, columns=columns, show='headings', height=8)

# Configure column headings
for col in columns:
    user_table.heading(col, text=col)
    if col == 'ID':
        user_table.column(col, width=50, anchor='center', minwidth=50)
    elif col == 'Bookings':
        user_table.column(col, width=80, anchor='center', minwidth=80)
    elif col == 'Phone':
        user_table.column(col, width=120, anchor='w', minwidth=120)
    elif col == 'Email':
        user_table.column(col, width=200, anchor='w', minwidth=150)
    elif col == 'Address':
        user_table.column(col, width=200, anchor='w', minwidth=150)
    else:
        user_table.column(col, width=150, anchor='w', minwidth=100)

# Add scrollbar
table_scroll_y = ttk.Scrollbar(table_container, orient='vertical', command=user_table.yview)
table_scroll_x = ttk.Scrollbar(table_container, orient='horizontal', command=user_table.xview)
user_table.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)

# Pack the scrollbars and table
table_scroll_y.pack(side='right', fill='y')
table_scroll_x.pack(side='bottom', fill='x')
user_table.pack(expand=True, fill='both')

# Bind click event to show user details
user_table.bind('<<TreeviewSelect>>', show_user_details)

# ----------------- User Details Section -----------------
details_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                          border_color=BORDER_COLOR, corner_radius=10)
# Initially hidden - will be shown when a user is selected

# Details header
details_header = ctk.CTkFrame(details_frame, fg_color=LIGHT_COLOR, height=50, corner_radius=0)
details_header.pack(fill="x")

details_user_id = ctk.CTkLabel(details_header, text="User #", 
                            font=("Arial", 16, "bold"), text_color=PRIMARY_COLOR)
details_user_id.pack(side="left", padx=20, pady=10)

# Details content
details_content = ctk.CTkFrame(details_frame, fg_color="white")
details_content.pack(fill="x", padx=20, pady=(15, 15))

# User details
details_name = ctk.CTkLabel(details_content, text=" Full Name", 
                          font=("Arial", 16, "bold"), text_color=PRIMARY_COLOR)
details_name.pack(anchor="w", pady=(0, 5))

details_email = ctk.CTkLabel(details_content, text="Email", 
                           font=("Arial", 13), text_color=GRAY_COLOR)
details_email.pack(anchor="w", pady=(0, 10))

details_info_frame = ctk.CTkFrame(details_content, fg_color="white")
details_info_frame.pack(fill="x", pady=(0, 15))
details_info_frame.columnconfigure(0, weight=1)
details_info_frame.columnconfigure(1, weight=1)

details_phone = ctk.CTkLabel(details_info_frame, text="Phone: ", 
                           font=("Arial", 13), text_color=GRAY_COLOR)
details_phone.grid(row=0, column=0, sticky="w", pady=(0, 5))

details_address = ctk.CTkLabel(details_info_frame, text="Address: ", 
                             font=("Arial", 13), text_color=GRAY_COLOR)
details_address.grid(row=1, column=0, sticky="w", pady=(0, 5))

# User stats in a visually appealing card format
stats_frame = ctk.CTkFrame(details_content, fg_color=LIGHT_COLOR, corner_radius=8)
stats_frame.pack(fill="x", pady=(0, 15))

stats_frame.columnconfigure(0, weight=1)
stats_frame.columnconfigure(1, weight=1)

# Booking stats
stats_icon1 = ctk.CTkLabel(stats_frame, text="🗓️", font=("Arial", 20))
stats_icon1.grid(row=0, column=0, padx=(15, 5), pady=15, sticky="e")

details_bookings = ctk.CTkLabel(stats_frame, text="Total Bookings: 0", 
                              font=("Arial", 13, "bold"), text_color=PRIMARY_COLOR)
details_bookings.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="w")

# Total spent stats 
stats_icon2 = ctk.CTkLabel(stats_frame, text="💰", font=("Arial", 20))
stats_icon2.grid(row=0, column=2, padx=(15, 5), pady=15, sticky="e")

details_spent = ctk.CTkLabel(stats_frame, text="Total Spent: $0", 
                           font=("Arial", 13, "bold"), text_color=PRIMARY_COLOR)
details_spent.grid(row=0, column=3, padx=(0, 15), pady=15, sticky="w")

# Recent bookings section with better styling
bookings_header = ctk.CTkFrame(details_content, fg_color="white")
bookings_header.pack(fill="x", pady=(5, 10))

bookings_label = ctk.CTkLabel(bookings_header, text="Recent Bookings", 
                            font=("Arial", 14, "bold"), text_color=PRIMARY_COLOR)
bookings_label.pack(side="left")

bookings_container = ctk.CTkFrame(details_content, fg_color="white")
bookings_container.pack(fill="x", pady=(0, 10))

# Create mini-treeview for recent bookings with better styling
booking_columns = ('Booking ID', 'Room Type', 'Check-in', 'Check-out', 'Amount', 'Status')
bookings_table = ttk.Treeview(bookings_container, columns=booking_columns, show='headings', height=4)

# Configure column headings for bookings table
for col in booking_columns:
    bookings_table.heading(col, text=col)
    if col == 'Booking ID':
        bookings_table.column(col, width=80, anchor='center', minwidth=80)
    elif col in ('Check-in', 'Check-out'):
        bookings_table.column(col, width=100, anchor='center', minwidth=100)
    elif col == 'Amount':
        bookings_table.column(col, width=80, anchor='e', minwidth=80)
    elif col == 'Status':
        bookings_table.column(col, width=100, anchor='center', minwidth=100)
    else:
        bookings_table.column(col, width=150, anchor='w', minwidth=150)

# Configure tags for status colors
bookings_table.tag_configure('confirmed', background='#d4edda')
bookings_table.tag_configure('pending', background='#fff3cd')
bookings_table.tag_configure('cancelled', background='#f8d7da')

# Add scrollbars for bookings table
bookings_scroll_y = ttk.Scrollbar(bookings_container, orient='vertical', command=bookings_table.yview)
bookings_scroll_x = ttk.Scrollbar(bookings_container, orient='horizontal', command=bookings_table.xview)
bookings_table.configure(yscrollcommand=bookings_scroll_y.set, xscrollcommand=bookings_scroll_x.set)

# Pack the scrollbars and table
bookings_scroll_y.pack(side='right', fill='y')
bookings_scroll_x.pack(side='bottom', fill='x')
bookings_table.pack(fill="x")

# Attach a keyboard shortcut to search (Enter key)
search_entry.bind("<Return>", lambda event: search_users())

# Populate the user table
populate_user_table()

# Initialize in "new user" mode
new_user_mode()

# Run the application
if __name__ == "__main__":
    app.mainloop()