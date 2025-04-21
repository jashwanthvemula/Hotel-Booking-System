import customtkinter as ctk
from tkinter import messagebox, ttk
import mysql.connector
import subprocess
import sys
from datetime import datetime

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
       host="141.209.241.57",
        user="cheru4a",  # Replace with your MySQL username
        password="mypass", 
            database="BIS698M1530_GRP1"
    )

# ------------------- Global Variables -------------------
current_user = None

# ------------------- User Session Management -------------------
def load_user_session():
    """Load user information from database"""
    global current_user
    
    # Check if any user_id was passed as a command line argument
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
            
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Users WHERE user_id = %s",
                (user_id,)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                current_user = user_data
                return True
                
        except (ValueError, IndexError, mysql.connector.Error) as err:
            print(f"Error loading user session: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    return False

# ------------------- Navigation Functions -------------------
def open_page(page_name):
    """Open another page and close the current one"""
    try:
        # Pass the current user ID to the next page if a user is logged in
        user_param = [str(current_user['user_id'])] if current_user else []
        
        # Construct the command to run the appropriate Python file
        command = [sys.executable, f"{page_name.lower()}.py"] + user_param
        
        subprocess.Popen(command)
        app.destroy()  # Close the current window
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Unable to open {page_name} page: {e}")

def go_to_home():
    open_page("home")

def go_to_bookings():
    open_page("bookings")

def go_to_profile():
    open_page("profile")

def go_to_feedback():
    open_page("feedback")

def logout():
    """Log out the current user and return to login page"""
    global current_user
    current_user = None
    open_page("login")

# ------------------- Profile Functions -------------------
def populate_profile_fields():
    """Populate profile fields with user data"""
    if current_user:
        # Set the full name
        full_name = f"{current_user['first_name']} {current_user['last_name']}"
        fullname_entry.delete(0, 'end')
        fullname_entry.insert(0, full_name)
        
        # Set email
        email_entry.delete(0, 'end')
        email_entry.insert(0, current_user['email'] if current_user['email'] else "")
        
        # Set phone
        phone_entry.delete(0, 'end')
        phone_entry.insert(0, current_user['phone'] if current_user.get('phone') else "")
        
        # Set address
        address_entry.delete(0, 'end')
        address_entry.insert(0, current_user['user_address'] if current_user.get('user_address') else "")

def update_profile():
    """Update user profile information"""
    if not current_user:
        messagebox.showwarning("Login Required", "Please log in to update your profile")
        return
    
    # Get form values
    full_name = fullname_entry.get()
    email = email_entry.get()
    phone = phone_entry.get()
    address = address_entry.get()
    
    # Validate inputs
    if not full_name or not email:
        messagebox.showwarning("Input Error", "Name and email are required")
        return
    
    # Split full name into first and last name
    name_parts = full_name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Update user data
        cursor.execute(
            """
            UPDATE Users 
            SET first_name = %s, 
                last_name = %s, 
                email = %s, 
                phone = %s, 
                user_address = %s
            WHERE user_id = %s
            """,
            (first_name, last_name, email, phone, address, current_user['user_id'])
        )
        
        connection.commit()
        
        # Update current_user data
        current_user['first_name'] = first_name
        current_user['last_name'] = last_name
        current_user['email'] = email
        current_user['phone'] = phone
        current_user['user_address'] = address
        
        messagebox.showinfo("Success", "Profile updated successfully!")
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Booking History Functions -------------------
def load_booking_history():
    """Load booking history from database"""
    if not current_user:
        return []
        
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query bookings with room and hotel info
        cursor.execute(
            """
            SELECT b.Booking_ID, r.Room_Type as Hotel, b.Check_IN_Date, 
                   b.Check_Out_Date, b.Total_Cost as Amount, b.Booking_Status as Status
            FROM Booking b
            JOIN Room r ON b.Room_ID = r.Room_ID
            WHERE b.User_ID = %s
            ORDER BY b.Check_IN_Date DESC
            """,
            (current_user['user_id'],)
        )
        
        bookings = cursor.fetchall()
        return bookings
        
    except mysql.connector.Error as err:
        print(f"Error loading booking history: {err}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def populate_booking_table():
    """Populate the booking history table"""
    # Clear existing rows
    for row in booking_table.get_children():
        booking_table.delete(row)
    
    bookings = load_booking_history()
    
    # Add bookings to the table
    for booking in bookings:
        # Format dates
        check_in = booking['Check_IN_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_IN_Date'], datetime) else booking['Check_IN_Date']
        check_out = booking['Check_Out_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_Out_Date'], datetime) else booking['Check_Out_Date']
        
        # Format amount
        amount = f"${booking['Amount']}"
        
        # Determine status display
        status = booking['Status']
        
        # Insert row into table
        booking_table.insert('', 'end', values=(
            f"#{booking['Booking_ID']}",
            booking['Hotel'],
            check_in,
            check_out,
            amount,
            status
        ))

# ----------------- Initialize App -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - User Profile")
app.geometry("1200x700")
app.resizable(False, False)

# Check if user is logged in
if not load_user_session():
    messagebox.showwarning("Login Required", "Please log in to view your profile")
    open_page("login")

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
    ("🏠 Home", go_to_home),
    ("📅 Bookings", go_to_bookings),
    ("👤 Profile", go_to_profile),
    ("💬 Feedback", go_to_feedback),
    ("🚪 Logout", logout)
]

for btn_text, btn_command in nav_buttons:
    is_active = "Profile" in btn_text
    btn = ctk.CTkButton(sidebar, text=btn_text, font=("Arial", 14), 
                      fg_color="#34495E" if is_active else "transparent", 
                      hover_color="#34495E",
                      anchor="w", height=40, width=180, 
                      command=btn_command)
    btn.pack(pady=5, padx=10)

# Welcome message with username if available
if current_user:
    username = f"{current_user['first_name']} {current_user['last_name']}"
    ctk.CTkLabel(sidebar, text=f"Welcome, {username}", 
               font=("Arial", 12), text_color="white").pack(pady=(50, 10))

# ----------------- Content Area -----------------
content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
content_frame.pack(side="right", fill="both", expand=True)

# ----------------- Header -----------------
header_frame = ctk.CTkFrame(content_frame, fg_color="white", height=60)
header_frame.pack(fill="x", padx=30, pady=(30, 20))

ctk.CTkLabel(header_frame, text="User Management", 
           font=("Arial", 30, "bold"), text_color="#2C3E50").pack(anchor="center")

# ----------------- Profile Section -----------------
profile_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                           border_color="#E5E5E5", corner_radius=10)
profile_frame.pack(fill="x", padx=30, pady=(0, 20))

# Profile Header
profile_header = ctk.CTkFrame(profile_frame, fg_color="white", height=50)
profile_header.pack(fill="x", padx=20, pady=10)

ctk.CTkLabel(profile_header, text="👤 Edit Profile", 
           font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")

# Profile Form
profile_form = ctk.CTkFrame(profile_frame, fg_color="white")
profile_form.pack(fill="x", padx=20, pady=(0, 20))

# Create two columns for the form
form_left = ctk.CTkFrame(profile_form, fg_color="white")
form_left.pack(side="left", fill="both", expand=True, padx=(0, 10))

form_right = ctk.CTkFrame(profile_form, fg_color="white")
form_right.pack(side="right", fill="both", expand=True, padx=(10, 0))

# Left Column - Full Name and Phone
ctk.CTkLabel(form_left, text="Full Name", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
fullname_entry = ctk.CTkEntry(form_left, width=300, height=35)
fullname_entry.pack(anchor="w", pady=(0, 15))

ctk.CTkLabel(form_left, text="Phone Number", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
phone_entry = ctk.CTkEntry(form_left, width=300, height=35)
phone_entry.pack(anchor="w", pady=(0, 15))

# Right Column - Email and Address
ctk.CTkLabel(form_right, text="Email Address", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
email_entry = ctk.CTkEntry(form_right, width=300, height=35)
email_entry.pack(anchor="w", pady=(0, 15))

ctk.CTkLabel(form_right, text="Address", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
address_entry = ctk.CTkEntry(form_right, width=300, height=35)
address_entry.pack(anchor="w", pady=(0, 15))

# Update Button
update_btn = ctk.CTkButton(profile_form, text="Update Profile", 
                          font=("Arial", 14, "bold"),
                          fg_color="#007BFF", hover_color="#0069D9",
                          height=35, width=150, command=update_profile)
update_btn.pack(anchor="w", pady=(10, 0))

# ----------------- Booking History Section -----------------
history_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                           border_color="#E5E5E5", corner_radius=10)
history_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

# History Header
history_header = ctk.CTkFrame(history_frame, fg_color="white", height=50)
history_header.pack(fill="x", padx=20, pady=10)

ctk.CTkLabel(history_header, text="🕒 Booking History", 
           font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")

# Booking Table
table_frame = ctk.CTkFrame(history_frame, fg_color="white")
table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

# Create Treeview widget for booking history
columns = ('Booking ID', 'Hotel', 'Check-in', 'Check-out', 'Amount', 'Status')
booking_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)

# Configure column headings
for col in columns:
    booking_table.heading(col, text=col)
    # Set column widths based on content
    if col == 'Booking ID':
        booking_table.column(col, width=100, anchor='w')
    elif col in ('Check-in', 'Check-out'):
        booking_table.column(col, width=120, anchor='center')
    elif col == 'Amount':
        booking_table.column(col, width=100, anchor='e')
    elif col == 'Status':
        booking_table.column(col, width=100, anchor='center')
    else:
        booking_table.column(col, width=200, anchor='w')

# Create scrollbar
scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=booking_table.yview)
booking_table.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side='right', fill='y')
booking_table.pack(fill="both", expand=True)

# Style the treeview
style = ttk.Style()
style.theme_use("default")
style.configure("Treeview", 
                background="#FFFFFF",
                foreground="#333333",
                rowheight=25,
                fieldbackground="#FFFFFF",
                borderwidth=0,
                font=('Arial', 10))
style.configure("Treeview.Heading", 
                font=('Arial', 12, 'bold'),
                background="#F0F0F0",
                foreground="#2C3E50")
style.map('Treeview', background=[('selected', '#C8E5FF')])

# Add some padding
style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

# Populate profile fields and booking table
populate_profile_fields()
populate_booking_table()

# Run the application
if __name__ == "__main__":
    app.mainloop()