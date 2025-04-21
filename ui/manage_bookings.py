import customtkinter as ctk
from tkinter import messagebox, ttk
import mysql.connector
import subprocess
import sys
from datetime import datetime
from tkcalendar import DateEntry  # You may need to install this: pip install tkcalendar

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
selected_booking = None

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

# ------------------- Booking Management Functions -------------------
def load_bookings():
    """Load all bookings from database"""
    bookings = []
    
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get bookings with user and room info
        cursor.execute(
            """
            SELECT b.Booking_ID, CONCAT(u.first_name, ' ', u.last_name) AS Customer,
                   r.Room_Type, b.Check_IN_Date, b.Check_Out_Date, 
                   b.Total_Cost, b.Booking_Status
            FROM Booking b
            JOIN Users u ON b.User_ID = u.user_id
            JOIN Room r ON b.Room_ID = r.Room_ID
            ORDER BY b.Check_IN_Date DESC
            """
        )
        
        bookings = cursor.fetchall()
        return bookings
        
    except mysql.connector.Error as err:
        print(f"Error loading bookings: {err}")
        messagebox.showerror("Database Error", f"Error loading bookings: {err}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def load_booking_details(booking_id):
    """Load details for a specific booking"""
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get detailed booking info
        cursor.execute(
            """
            SELECT b.*, u.first_name, u.last_name, u.email, u.phone, 
                   r.Room_Type, r.Price_per_Night
            FROM Booking b
            JOIN Users u ON b.User_ID = u.user_id
            JOIN Room r ON b.Room_ID = r.Room_ID
            WHERE b.Booking_ID = %s
            """,
            (booking_id,)
        )
        
        booking = cursor.fetchone()
        return booking
        
    except mysql.connector.Error as err:
        print(f"Error loading booking details: {err}")
        messagebox.showerror("Database Error", f"Error loading booking details: {err}")
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def update_booking_status(booking_id, status):
    """Update the status of a booking"""
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Update booking status
        cursor.execute(
            """
            UPDATE Booking 
            SET Booking_Status = %s
            WHERE Booking_ID = %s
            """,
            (status, booking_id)
        )
        
        # If cancelling, make the room available again
        if status == "Cancelled":
            cursor.execute(
                """
                UPDATE Room r
                JOIN Booking b ON r.Room_ID = b.Room_ID
                SET r.Availability_status = 'Available'
                WHERE b.Booking_ID = %s
                """,
                (booking_id,)
            )
        
        connection.commit()
        messagebox.showinfo("Success", f"Booking #{booking_id} status updated to {status}")
        return True
        
    except mysql.connector.Error as err:
        print(f"Error updating booking status: {err}")
        messagebox.showerror("Database Error", f"Error updating booking status: {err}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def delete_booking(booking_id):
    """Delete a booking and make the room available again"""
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Get the room ID before deleting the booking
        cursor.execute("SELECT Room_ID FROM Booking WHERE Booking_ID = %s", (booking_id,))
        room_id = cursor.fetchone()[0]
        
        # Delete the booking
        cursor.execute("DELETE FROM Booking WHERE Booking_ID = %s", (booking_id,))
        
        # Make the room available again
        cursor.execute(
            "UPDATE Room SET Availability_status = 'Available' WHERE Room_ID = %s",
            (room_id,)
        )
        
        connection.commit()
        messagebox.showinfo("Success", f"Booking #{booking_id} has been deleted")
        return True
        
    except mysql.connector.Error as err:
        print(f"Error deleting booking: {err}")
        messagebox.showerror("Database Error", f"Error deleting booking: {err}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- UI Functions -------------------
def populate_booking_table():
    """Populate the booking table with data from database"""
    # Clear existing rows
    for row in booking_table.get_children():
        booking_table.delete(row)
    
    # Load bookings and add to table
    bookings = load_bookings()
    
    for booking in bookings:
        # Format dates and values
        check_in = booking['Check_IN_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_IN_Date'], datetime) else booking['Check_IN_Date']
        check_out = booking['Check_Out_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_Out_Date'], datetime) else booking['Check_Out_Date']
        
        # Format amount
        amount = f"${booking['Total_Cost']}"
        
        # Status tag for color coding
        status = booking['Booking_Status']
        status_tag = status.lower()
        
        # Insert into table with status tag
        booking_table.insert('', 'end', iid=booking['Booking_ID'], values=(
            booking['Booking_ID'],
            booking['Customer'],
            booking['Room_Type'],
            check_in,
            check_out,
            amount,
            status
        ), tags=(status_tag,))
    
    # Update status counts
    update_status_counts()

def update_status_counts():
    """Update the status count labels"""
    # Count bookings by status
    bookings = booking_table.get_children()
    total = len(bookings)
    
    confirmed = 0
    pending = 0
    cancelled = 0
    
    for booking_id in bookings:
        status = booking_table.item(booking_id, 'values')[6]
        if status == "Confirmed":
            confirmed += 1
        elif status == "Pending":
            pending += 1
        elif status == "Cancelled":
            cancelled += 1
    
    # Update labels
    total_count_label.configure(text=f"Total: {total}")
    confirmed_count_label.configure(text=f"Confirmed: {confirmed}")
    pending_count_label.configure(text=f"Pending: {pending}")
    cancelled_count_label.configure(text=f"Cancelled: {cancelled}")

def show_booking_details(event):
    """Show details for the selected booking"""
    global selected_booking
    
    selected_id = booking_table.focus()
    if not selected_id:
        return
    
    # Convert to integer
    booking_id = int(selected_id)
    
    # Load booking details
    booking = load_booking_details(booking_id)
    if not booking:
        return
    
    selected_booking = booking
    
    # Update detail fields
    details_booking_id.configure(text=f"Booking #{booking['Booking_ID']}")
    details_customer.configure(text=f"{booking['first_name']} {booking['last_name']}")
    details_contact.configure(text=f"{booking['email']} | {booking['phone'] if booking['phone'] else 'No phone'}")
    details_room.configure(text=f"{booking['Room_Type']}")
    details_dates.configure(text=(
        f"Check-in: {booking['Check_IN_Date'].strftime('%Y-%m-%d')} | "
        f"Check-out: {booking['Check_Out_Date'].strftime('%Y-%m-%d')}"
    ))
    details_price.configure(text=(
        f"${booking['Price_per_Night']}/night | "
        f"Total: ${booking['Total_Cost']}"
    ))
    details_status.configure(text=f"Status: {booking['Booking_Status']}")
    
    # Update action buttons based on current status
    if booking['Booking_Status'] == "Pending":
        confirm_btn.configure(state="normal")
        cancel_btn.configure(state="normal")
    elif booking['Booking_Status'] == "Confirmed":
        confirm_btn.configure(state="disabled")
        cancel_btn.configure(state="normal")
    elif booking['Booking_Status'] == "Cancelled":
        confirm_btn.configure(state="normal")
        cancel_btn.configure(state="disabled")
    
    # Show detail panel
    details_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

def confirm_booking():
    """Confirm the selected booking"""
    if not selected_booking:
        return
    
    # Update booking status
    if update_booking_status(selected_booking['Booking_ID'], "Confirmed"):
        # Refresh booking table
        populate_booking_table()
        
        # Update details panel
        selected_booking['Booking_Status'] = "Confirmed"
        details_status.configure(text=f"Status: {selected_booking['Booking_Status']}")
        confirm_btn.configure(state="disabled")
        cancel_btn.configure(state="normal")

def cancel_booking():
    """Cancel the selected booking"""
    if not selected_booking:
        return
    
    # Confirm with user
    confirmed = messagebox.askyesno(
        "Confirm Cancellation", 
        f"Are you sure you want to cancel booking #{selected_booking['Booking_ID']}?"
    )
    
    if not confirmed:
        return
    
    # Update booking status
    if update_booking_status(selected_booking['Booking_ID'], "Cancelled"):
        # Refresh booking table
        populate_booking_table()
        
        # Update details panel
        selected_booking['Booking_Status'] = "Cancelled"
        details_status.configure(text=f"Status: {selected_booking['Booking_Status']}")
        confirm_btn.configure(state="normal")
        cancel_btn.configure(state="disabled")

def delete_booking_ui():
    """Delete the selected booking (with confirmation)"""
    if not selected_booking:
        return
    
    # Confirm with user
    confirmed = messagebox.askyesno(
        "Confirm Deletion", 
        f"Are you sure you want to DELETE booking #{selected_booking['Booking_ID']}?\n\n"
        f"This action cannot be undone."
    )
    
    if not confirmed:
        return
    
    # Delete the booking
    if delete_booking(selected_booking['Booking_ID']):
        # Refresh booking table
        populate_booking_table()
        
        # Hide details panel
        details_frame.pack_forget()
        
        # Reset selected booking
    
        selected_booking = None

def filter_bookings():
    """Filter bookings based on search term and date range"""
    search_term = search_entry.get().lower()
    try:
        start_date = start_date_entry.get_date() if hasattr(start_date_entry, 'get_date') else None
        end_date = end_date_entry.get_date() if hasattr(end_date_entry, 'get_date') else None
    except:
        start_date = None
        end_date = None
    
    status_filter = status_var.get()
    
    # Clear existing rows
    for row in booking_table.get_children():
        booking_table.delete(row)
    
    # Load all bookings
    bookings = load_bookings()
    
    # Apply filters
    filtered_bookings = []
    for booking in bookings:
        # Apply search term filter (customer name or room type)
        if search_term and search_term not in booking['Customer'].lower() and search_term not in booking['Room_Type'].lower():
            continue
        
        # Apply date range filter
        booking_date = booking['Check_IN_Date']
        if isinstance(booking_date, str):
            try:
                booking_date = datetime.strptime(booking_date, '%Y-%m-%d')
            except:
                booking_date = None
        
        if start_date and booking_date and booking_date < start_date:
            continue
        
        if end_date and booking_date and booking_date > end_date:
            continue
        
        # Apply status filter
        if status_filter != "All" and booking['Booking_Status'] != status_filter:
            continue
        
        filtered_bookings.append(booking)
    
    # Add filtered bookings to table
    for booking in filtered_bookings:
        # Format dates and values
        check_in = booking['Check_IN_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_IN_Date'], datetime) else booking['Check_IN_Date']
        check_out = booking['Check_Out_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_Out_Date'], datetime) else booking['Check_Out_Date']
        
        # Format amount
        amount = f"${booking['Total_Cost']}"
        
        # Status tag for color coding
        status = booking['Booking_Status']
        status_tag = status.lower()
        
        # Insert into table with status tag
        booking_table.insert('', 'end', iid=booking['Booking_ID'], values=(
            booking['Booking_ID'],
            booking['Customer'],
            booking['Room_Type'],
            check_in,
            check_out,
            amount,
            status
        ), tags=(status_tag,))
    
    # Update status counts
    update_status_counts()

def reset_filters():
    """Reset all filters and show all bookings"""
    search_entry.delete(0, 'end')
    try:
        start_date_entry.set_date(None)
        end_date_entry.set_date(None)
    except:
        pass
    status_var.set("All")
    
    # Refresh booking table
    populate_booking_table()

# ----------------- Initialize App -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - Manage Bookings")
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
    is_active = "Manage Bookings" in btn_text
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

ctk.CTkLabel(header_frame, text="Manage Bookings", 
           font=("Arial", 28, "bold"), text_color="#2C3E50").pack(anchor="w")

# ----------------- Filter Section -----------------
filter_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                          border_color="#E5E5E5", corner_radius=10)
filter_frame.pack(fill="x", padx=30, pady=(0, 10))

# Filter header
filter_header = ctk.CTkFrame(filter_frame, fg_color="white", height=40)
filter_header.pack(fill="x", padx=20, pady=(10, 0))

ctk.CTkLabel(filter_header, text="Filter Bookings", 
           font=("Arial", 16, "bold"), text_color="#2C3E50").pack(anchor="w")

# Filter options
filter_options = ctk.CTkFrame(filter_frame, fg_color="white")
filter_options.pack(fill="x", padx=20, pady=(0, 10))

# Search field
search_frame = ctk.CTkFrame(filter_options, fg_color="white")
search_frame.pack(side="left", padx=(0, 10))

ctk.CTkLabel(search_frame, text="Search", font=("Arial", 12)).pack(anchor="w")
search_entry = ctk.CTkEntry(search_frame, width=150, placeholder_text="Customer or Room")
search_entry.pack(pady=5)

# Date range fields
date_frame = ctk.CTkFrame(filter_options, fg_color="white")
date_frame.pack(side="left", padx=(10, 10))

ctk.CTkLabel(date_frame, text="Date Range", font=("Arial", 12)).pack(anchor="w")
date_fields = ctk.CTkFrame(date_frame, fg_color="white")
date_fields.pack(fill="x")

# Try to use DateEntry
try:
    start_date_entry = DateEntry(date_fields, width=10, background='darkblue', 
                                foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    start_date_entry.pack(side="left", padx=(0, 5))

    ctk.CTkLabel(date_fields, text="to", font=("Arial", 10)).pack(side="left", padx=5)

    end_date_entry = DateEntry(date_fields, width=10, background='darkblue', 
                            foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
    end_date_entry.pack(side="left", padx=(5, 0))
except:
    # Fallback to standard entries
    start_date_entry = ctk.CTkEntry(date_fields, width=100, placeholder_text="YYYY-MM-DD")
    start_date_entry.pack(side="left", padx=(0, 5))

    ctk.CTkLabel(date_fields, text="to", font=("Arial", 10)).pack(side="left", padx=5)

    end_date_entry = ctk.CTkEntry(date_fields, width=100, placeholder_text="YYYY-MM-DD")
    end_date_entry.pack(side="left", padx=(5, 0))

# Status filter
status_frame = ctk.CTkFrame(filter_options, fg_color="white")
status_frame.pack(side="left", padx=(10, 10))

ctk.CTkLabel(status_frame, text="Status", font=("Arial", 12)).pack(anchor="w")
status_var = ctk.StringVar(value="All")
status_options = ["All", "Pending", "Confirmed", "Cancelled"]
status_dropdown = ctk.CTkComboBox(status_frame, values=status_options, variable=status_var, width=120)
status_dropdown.pack(pady=5)

# Filter buttons
button_frame = ctk.CTkFrame(filter_options, fg_color="white")
button_frame.pack(side="left", padx=(10, 0))

ctk.CTkLabel(button_frame, text=" ", font=("Arial", 12)).pack(anchor="w")  # Spacer for alignment
filter_btn = ctk.CTkButton(button_frame, text="Apply Filters", font=("Arial", 12), 
                        fg_color="#0F2D52", hover_color="#1E4D88",
                        command=filter_bookings, width=100, height=30)
filter_btn.pack(side="left", pady=5, padx=(0, 5))

reset_btn = ctk.CTkButton(button_frame, text="Reset", font=("Arial", 12), 
                        fg_color="#6C757D", hover_color="#5A6268",
                        command=reset_filters, width=80, height=30)
reset_btn.pack(side="left", pady=5)

# ----------------- Booking Table Section -----------------
table_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                        border_color="#E5E5E5", corner_radius=10)
table_frame.pack(fill="x", padx=30, pady=(0, 10))

# Table header with status counts
table_header = ctk.CTkFrame(table_frame, fg_color="white", height=40)
table_header.pack(fill="x", padx=20, pady=10)

ctk.CTkLabel(table_header, text="Bookings", 
           font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left")

# Status counts
status_counts = ctk.CTkFrame(table_header, fg_color="white")
status_counts.pack(side="right")

total_count_label = ctk.CTkLabel(status_counts, text="Total: 0", font=("Arial", 12))
total_count_label.pack(side="left", padx=(0, 15))

confirmed_count_label = ctk.CTkLabel(status_counts, text="Confirmed: 0", font=("Arial", 12), text_color="#28A745")
confirmed_count_label.pack(side="left", padx=(0, 15))

pending_count_label = ctk.CTkLabel(status_counts, text="Pending: 0", font=("Arial", 12), text_color="#FFC107")
pending_count_label.pack(side="left", padx=(0, 15))

cancelled_count_label = ctk.CTkLabel(status_counts, text="Cancelled: 0", font=("Arial", 12), text_color="#DC3545")
cancelled_count_label.pack(side="left")

# Create treeview for bookings
columns = ('Booking ID', 'Customer', 'Room Type', 'Check-in', 'Check-out', 'Amount', 'Status')
booking_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)

# Configure column headings
for col in columns:
    booking_table.heading(col, text=col)
    if col == 'Booking ID':
        booking_table.column(col, width=80, anchor='center')
    elif col in ('Check-in', 'Check-out'):
        booking_table.column(col, width=100, anchor='center')
    elif col == 'Amount':
        booking_table.column(col, width=80, anchor='e')
    elif col == 'Status':
        booking_table.column(col, width=100, anchor='center')
    elif col == 'Customer':
        booking_table.column(col, width=150, anchor='w')
    else:
        booking_table.column(col, width=150, anchor='w')

# Configure tags for status colors
booking_table.tag_configure('confirmed', background='#d4edda')
booking_table.tag_configure('pending', background='#fff3cd')
booking_table.tag_configure('cancelled', background='#f8d7da')

# Add scrollbar
table_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=booking_table.yview)
booking_table.configure(yscrollcommand=table_scroll.set)
table_scroll.pack(side='right', fill='y')
booking_table.pack(expand=True, fill='both', padx=20, pady=(0, 20))

# Bind click event to show details
booking_table.bind('<<TreeviewSelect>>', show_booking_details)

# ----------------- Booking Details Section -----------------
details_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                           border_color="#E5E5E5", corner_radius=10, height=200)
# Initially hidden - will be shown when a booking is selected

# Details header
details_header = ctk.CTkFrame(details_frame, fg_color="white", height=40)
details_header.pack(fill="x", padx=20, pady=10)

details_booking_id = ctk.CTkLabel(details_header, text="Booking #", 
                               font=("Arial", 16, "bold"), text_color="#2C3E50")
details_booking_id.pack(side="left")

# Action buttons
action_btns = ctk.CTkFrame(details_header, fg_color="white")
action_btns.pack(side="right")

confirm_btn = ctk.CTkButton(action_btns, text="Confirm", font=("Arial", 12), 
                          fg_color="#28A745", hover_color="#218838",
                          command=confirm_booking, width=100, height=30, state="disabled")
confirm_btn.pack(side="left", padx=(0, 5))

cancel_btn = ctk.CTkButton(action_btns, text="Cancel", font=("Arial", 12), 
                         fg_color="#DC3545", hover_color="#C82333",
                         command=cancel_booking, width=100, height=30, state="disabled")
cancel_btn.pack(side="left", padx=(0, 5))

delete_btn = ctk.CTkButton(action_btns, text="Delete", font=("Arial", 12), 
                         fg_color="#6C757D", hover_color="#5A6268",
                         command=delete_booking_ui, width=100, height=30)
delete_btn.pack(side="left")

# Details content
details_content = ctk.CTkFrame(details_frame, fg_color="white")
details_content.pack(fill="x", padx=20, pady=(0, 20))

# Customer info
details_customer = ctk.CTkLabel(details_content, text="Customer Name", 
                             font=("Arial", 14, "bold"), text_color="#2C3E50")
details_customer.pack(anchor="w", pady=(0, 5))

details_contact = ctk.CTkLabel(details_content, text="Email | Phone", 
                            font=("Arial", 12), text_color="#6C757D")
details_contact.pack(anchor="w", pady=(0, 10))

# Booking info
info_columns = ctk.CTkFrame(details_content, fg_color="white")
info_columns.pack(fill="x")

# Left column (Room)
info_left = ctk.CTkFrame(info_columns, fg_color="white")
info_left.pack(side="left", fill="both", expand=True)

details_room = ctk.CTkLabel(info_left, text="Room Type", 
                         font=("Arial", 12), text_color="#2C3E50")
details_room.pack(anchor="w", pady=2)

details_dates = ctk.CTkLabel(info_left, text="Check-in: | Check-out:", 
                          font=("Arial", 12), text_color="#2C3E50")
details_dates.pack(anchor="w", pady=2)

# Right column (Price)
info_right = ctk.CTkFrame(info_columns, fg_color="white")
info_right.pack(side="right", fill="both", expand=True)

details_price = ctk.CTkLabel(info_right, text="Price/night | Total", 
                           font=("Arial", 12), text_color="#2C3E50")
details_price.pack(anchor="w", pady=2)

details_status = ctk.CTkLabel(info_right, text="Status: ", 
                            font=("Arial", 12, "bold"), text_color="#2C3E50")
details_status.pack(anchor="w", pady=2)

# Populate the booking table
populate_booking_table()

# Run the application
if __name__ == "__main__":
    app.mainloop()