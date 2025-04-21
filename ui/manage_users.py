import customtkinter as ctk
from tkinter import messagebox, ttk
import mysql.connector
import subprocess
import sys
import hashlib

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="new_password",
        database="hotel_book"
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
    
    # Update action buttons
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
    
    # Disable action buttons
    update_btn.configure(state="disabled")
    delete_btn.configure(state="disabled")
    
    # Reset selected user
    global selected_user
    selected_user = None

def hide_user_details():
    """Hide the user details section"""
    details_frame.pack_forget()

def new_user_mode():
    """Switch to new user mode"""
    clear_user_form()
    hide_user_details()
    
    # Update form buttons
    create_btn.configure(state="normal")
    update_btn.configure(state="disabled")
    delete_btn.configure(state="disabled")
    
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

# ----------------- Initialize App -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - Manage Users")
app.geometry("1200x700")
app.resizable(False, False)

# Try to load admin session
if not load_admin_session():
    messagebox.showwarning("Login Required", "Admin login required to access this page")
    open_page("admin_login")

# ----------------- Main Frame -----------------
main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
main_frame.pack(expand=True, fill="both")

# ----------------- Sidebar (Navigation) -----------------
sidebar = ctk.CTkFrame(main_frame, fg_color="#2C3E50", width=200, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)  # Prevent the frame from shrinking

# Header with logo
ctk.CTkLabel(sidebar, text="🏨 Hotel Booking", font=("Arial", 18, "bold"), text_color="white").pack(pady=(30, 20))

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
                      anchor="w", height=40, width=180, 
                      command=btn_command)
    btn.pack(pady=5, padx=10)

# Welcome message with admin name if available
if current_admin:
    admin_name = current_admin['AdminName']
    ctk.CTkLabel(sidebar, text=f"Welcome, {admin_name}", 
               font=("Arial", 12), text_color="white").pack(pady=(50, 10))

# ----------------- Content Area -----------------
content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
content_frame.pack(side="right", fill="both", expand=True)

# ----------------- Header -----------------
header_frame = ctk.CTkFrame(content_frame, fg_color="white", height=60)
header_frame.pack(fill="x", padx=30, pady=(30, 10))

ctk.CTkLabel(header_frame, text="Manage Users", 
           font=("Arial", 28, "bold"), text_color="#2C3E50").pack(side="left")

# New User and Search
action_frame = ctk.CTkFrame(header_frame, fg_color="white")
action_frame.pack(side="right")

# New user button
new_user_btn = ctk.CTkButton(action_frame, text="+ New User", font=("Arial", 12), 
                           fg_color="#28A745", hover_color="#218838",
                           command=new_user_mode, width=100, height=30)
new_user_btn.pack(side="left", padx=(0, 10))

# Search field
search_entry = ctk.CTkEntry(action_frame, width=200, placeholder_text="Search users...")
search_entry.pack(side="left", padx=(0, 5))

search_btn = ctk.CTkButton(action_frame, text="Search", font=("Arial", 12), 
                         fg_color="#0F2D52", hover_color="#1E4D88",
                         command=search_users, width=80, height=30)
search_btn.pack(side="left")

# ----------------- User Form Section -----------------
form_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                        border_color="#E5E5E5", corner_radius=10)
form_frame.pack(fill="x", padx=30, pady=(0, 20))

# Form header
form_header = ctk.CTkFrame(form_frame, fg_color="white", height=40)
form_header.pack(fill="x", padx=20, pady=10)

ctk.CTkLabel(form_header, text="User Information", 
           font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left")

# Form fields
form_fields = ctk.CTkFrame(form_frame, fg_color="white")
form_fields.pack(fill="x", padx=20, pady=(0, 20))

# Create two columns
form_left = ctk.CTkFrame(form_fields, fg_color="white")
form_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

form_right = ctk.CTkFrame(form_fields, fg_color="white")
form_right.pack(side="right", fill="both", expand=True, padx=(10, 0))

# Left column - First Name, Last Name, Email
ctk.CTkLabel(form_left, text="First Name *", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
first_name_entry = ctk.CTkEntry(form_left, width=300, height=35)
first_name_entry.pack(anchor="w", pady=(0, 10))

ctk.CTkLabel(form_left, text="Last Name *", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
last_name_entry = ctk.CTkEntry(form_left, width=300, height=35)
last_name_entry.pack(anchor="w", pady=(0, 10))

ctk.CTkLabel(form_left, text="Email *", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
email_entry = ctk.CTkEntry(form_left, width=300, height=35)
email_entry.pack(anchor="w", pady=(0, 10))

# Right column - Phone, Address, Password
ctk.CTkLabel(form_right, text="Phone", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
phone_entry = ctk.CTkEntry(form_right, width=300, height=35)
phone_entry.pack(anchor="w", pady=(0, 10))

ctk.CTkLabel(form_right, text="Address", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
address_entry = ctk.CTkEntry(form_right, width=300, height=35)
address_entry.pack(anchor="w", pady=(0, 10))

ctk.CTkLabel(form_right, text="Password" + " *" if not selected_user else "", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
password_entry = ctk.CTkEntry(form_right, width=300, height=35, show="•")
password_entry.pack(anchor="w", pady=(0, 10))

# Form buttons
buttons_frame = ctk.CTkFrame(form_fields, fg_color="white")
buttons_frame.pack(fill="x", pady=(10, 0))

create_btn = ctk.CTkButton(buttons_frame, text="Create User", font=("Arial", 12), 
                         fg_color="#28A745", hover_color="#218838",
                         command=create_user, width=120, height=35)
create_btn.pack(side="left", padx=(0, 5))

update_btn = ctk.CTkButton(buttons_frame, text="Update User", font=("Arial", 12), 
                         fg_color="#0F2D52", hover_color="#1E4D88",
                         command=update_user, width=120, height=35, state="disabled")
update_btn.pack(side="left", padx=(0, 5))

delete_btn = ctk.CTkButton(buttons_frame, text="Delete User", font=("Arial", 12), 
                         fg_color="#DC3545", hover_color="#C82333",
                         command=delete_user, width=120, height=35, state="disabled")
delete_btn.pack(side="left")

# Clear button (right aligned)
ctk.CTkButton(buttons_frame, text="Clear Form", font=("Arial", 12), 
            fg_color="#6C757D", hover_color="#5A6268",
            command=clear_user_form, width=120, height=35).pack(side="right")

# ----------------- User Table Section -----------------
table_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                        border_color="#E5E5E5", corner_radius=10)
table_frame.pack(fill="x", padx=30, pady=(0, 20))

# Table header
table_header = ctk.CTkFrame(table_frame, fg_color="white", height=40)
table_header.pack(fill="x", padx=20, pady=10)

ctk.CTkLabel(table_header, text="User List", 
           font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left")

# User count
user_count_label = ctk.CTkLabel(table_header, text="Total Users: 0", font=("Arial", 12))
user_count_label.pack(side="right")

# Create treeview for users
columns = ('ID', 'Name', 'Email', 'Phone', 'Address', 'Bookings')
user_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)

# Configure column headings
for col in columns:
    user_table.heading(col, text=col)
    if col == 'ID':
        user_table.column(col, width=50, anchor='center')
    elif col == 'Bookings':
        user_table.column(col, width=80, anchor='center')
    elif col == 'Phone':
        user_table.column(col, width=120, anchor='w')
    elif col == 'Email':
        user_table.column(col, width=200, anchor='w')
    elif col == 'Address':
        user_table.column(col, width=200, anchor='w')
    else:
        user_table.column(col, width=150, anchor='w')

# Add scrollbar
table_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=user_table.yview)
user_table.configure(yscrollcommand=table_scroll.set)
table_scroll.pack(side='right', fill='y')
user_table.pack(expand=True, fill='both', padx=20, pady=(0, 20))

# Bind click event to show user details
user_table.bind('<<TreeviewSelect>>', show_user_details)

# ----------------- User Details Section -----------------
details_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                          border_color="#E5E5E5", corner_radius=10, height=250)
# Initially hidden - will be shown when a user is selected

# Details header
details_header = ctk.CTkFrame(details_frame, fg_color="white", height=40)
details_header.pack(fill="x", padx=20, pady=10)

details_user_id = ctk.CTkLabel(details_header, text="User #", 
                            font=("Arial", 16, "bold"), text_color="#2C3E50")
details_user_id.pack(side="left")

# Details content
details_content = ctk.CTkFrame(details_frame, fg_color="white")
details_content.pack(fill="x", padx=20, pady=(0, 10))

# User details
details_name = ctk.CTkLabel(details_content, text="Full Name", 
                          font=("Arial", 14, "bold"), text_color="#2C3E50")
details_name.pack(anchor="w", pady=(0, 5))

details_email = ctk.CTkLabel(details_content, text="Email", 
                           font=("Arial", 12), text_color="#6C757D")
details_email.pack(anchor="w", pady=(0, 5))

details_phone = ctk.CTkLabel(details_content, text="Phone: ", 
                           font=("Arial", 12), text_color="#6C757D")
details_phone.pack(anchor="w", pady=(0, 5))

details_address = ctk.CTkLabel(details_content, text="Address: ", 
                             font=("Arial", 12), text_color="#6C757D")
details_address.pack(anchor="w", pady=(0, 10))

# User stats
stats_frame = ctk.CTkFrame(details_content, fg_color="white")
stats_frame.pack(fill="x")

details_bookings = ctk.CTkLabel(stats_frame, text="Total Bookings: 0", 
                              font=("Arial", 12, "bold"), text_color="#2C3E50")
details_bookings.pack(side="left", padx=(0, 20))

details_spent = ctk.CTkLabel(stats_frame, text="Total Spent: $0", 
                           font=("Arial", 12, "bold"), text_color="#2C3E50")
details_spent.pack(side="left")

# Recent bookings section
bookings_label = ctk.CTkLabel(details_content, text="Recent Bookings", 
                            font=("Arial", 12, "bold"), text_color="#2C3E50")
bookings_label.pack(anchor="w", pady=(20, 5))

# Create mini-treeview for recent bookings
booking_columns = ('Booking ID', 'Room Type', 'Check-in', 'Check-out', 'Amount', 'Status')
bookings_table = ttk.Treeview(details_content, columns=booking_columns, show='headings', height=3)

# Configure column headings
for col in booking_columns:
    bookings_table.heading(col, text=col)
    if col == 'Booking ID':
        bookings_table.column(col, width=80, anchor='center')
    elif col in ('Check-in', 'Check-out'):
        bookings_table.column(col, width=100, anchor='center')
    elif col == 'Amount':
        bookings_table.column(col, width=80, anchor='e')
    elif col == 'Status':
        bookings_table.column(col, width=100, anchor='center')
    else:
        bookings_table.column(col, width=150, anchor='w')

# Configure tags for status colors
bookings_table.tag_configure('confirmed', background='#d4edda')
bookings_table.tag_configure('pending', background='#fff3cd')
bookings_table.tag_configure('cancelled', background='#f8d7da')

bookings_table.pack(fill="x", pady=(0, 10))

# Populate the user table
populate_user_table()

# Run the application
if __name__ == "__main__":
    app.mainloop()