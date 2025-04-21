import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import subprocess
import sys
from datetime import datetime, timedelta
import os
from tkcalendar import DateEntry  # You may need to install this: pip install tkcalendar

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="141.209.241.57",
        user="cheru4a",  # Replace with your MySQL username
        password="mypass",  # Replace with your MySQL password
        database="BIS698M1530_GRP1"  # Replace with your database name
    )

# ------------------- Global Variables -------------------
current_user = None
hotel_id = None
room_prices = {}  # To store room prices for calculation

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

# ------------------- Hotel & Room Functions -------------------
def load_hotel_details(hotel_id_param=None):
    """Load hotel details from database"""
    global hotel_id
    
    # Use parameter or check command line arguments
    if hotel_id_param:
        hotel_id = hotel_id_param
    elif len(sys.argv) > 2:
        try:
            hotel_id = int(sys.argv[2])
        except (ValueError, IndexError):
            # Default hotel ID if none provided
            hotel_id = 1
    else:
        # Default hotel ID if none provided
        hotel_id = 1
    
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # First check if we're dealing with data from the Hotel table or directly from Room table
        cursor.execute("SHOW TABLES LIKE 'Hotel'")
        hotel_table_exists = cursor.fetchone() is not None
        
        if hotel_table_exists:
            # Get hotel details from Hotel table
            cursor.execute(
                """
                SELECT h.Hotel_ID, h.hotel_name, h.location, h.description, h.star_rating, h.image_path
                FROM Hotel h
                WHERE h.Hotel_ID = %s
                """,
                (hotel_id,)
            )
            hotel_data = cursor.fetchone()
            
            if hotel_data:
                # Set hotel name and location
                hotel_name_label.configure(text=f"{hotel_data['hotel_name']}")
                hotel_location_label.configure(text=f"📍 {hotel_data['location']}")
                
                # Load available room types for this hotel from RoomCategory
                try:
                    cursor.execute(
                        """
                        SELECT rc.Category_ID as Room_ID, rc.category_name as Room_Type, 
                               rc.base_price as Price_per_Night, 'Available' as Availability_status
                        FROM RoomCategory rc
                        WHERE rc.Hotel_ID = %s
                        """,
                        (hotel_id,)
                    )
                    room_types = cursor.fetchall()
                except mysql.connector.Error:
                    # Fall back to Room table if RoomCategory table doesn't exist or query fails
                    cursor.execute(
                        """
                        SELECT Room_ID, Room_Type, Price_per_Night, Availability_status
                        FROM Room 
                        WHERE Room_Type LIKE %s AND Availability_status = 'Available'
                        """,
                        (f"%{hotel_data['hotel_name']}%",)
                    )
                    room_types = cursor.fetchall()
            else:
                # Try to get data directly from Room table
                # Assume hotel_id is actually a Room_ID in this case
                cursor.execute(
                    """
                    SELECT Room_ID, Room_Type, Price_per_Night, Availability_status
                    FROM Room 
                    WHERE Room_ID = %s AND Availability_status = 'Available'
                    """,
                    (hotel_id,)
                )
                room_types = cursor.fetchall()
                
                if room_types:
                    # Extract hotel name from room type
                    room_type_parts = room_types[0]['Room_Type'].split(' - ', 1)
                    hotel_name = room_type_parts[0] if len(room_type_parts) > 1 else room_types[0]['Room_Type']
                    hotel_name_label.configure(text=f"{hotel_name}")
                    hotel_location_label.configure(text=f"📍 Location information not available")
                else:
                    messagebox.showerror("Error", "Hotel/Room not found")
                    go_to_home()
                    return
        else:
            # No Hotel table, get room data directly
            cursor.execute(
                """
                SELECT Room_ID, Room_Type, Price_per_Night, Availability_status
                FROM Room 
                WHERE Room_ID = %s AND Availability_status = 'Available'
                """,
                (hotel_id,)
            )
            room_types = cursor.fetchall()
            
            if room_types:
                # Extract hotel name from room type
                room_type_parts = room_types[0]['Room_Type'].split(' - ', 1)
                hotel_name = room_type_parts[0] if len(room_type_parts) > 1 else room_types[0]['Room_Type']
                hotel_name_label.configure(text=f"{hotel_name}")
                hotel_location_label.configure(text=f"📍 Location information not available")
            else:
                messagebox.showerror("Error", "Room not found")
                go_to_home()
                return
                
        # Store room prices for calculation
        global room_prices
        room_prices = {room['Room_Type']: room['Price_per_Night'] for room in room_types}
        
        # Format room types for dropdown
        room_type_options = [f"{room['Room_Type']} - ${room['Price_per_Night']}/night" for room in room_types]
        
        if room_type_options:
            room_type_dropdown.configure(values=room_type_options)
            room_type_dropdown.set(room_type_options[0])
            
            # Set default values in summary
            update_booking_summary()
        else:
            room_type_dropdown.configure(values=["No rooms available"])
            room_type_dropdown.set("No rooms available")
            
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        print(f"Database Error in load_hotel_details: {err}")
        go_to_home()
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Booking Functions -------------------
def calculate_total_price():
    """Calculate the total price based on room type and nights"""
    try:
        # Get room price
        room_selection = room_type_dropdown.get()
        if "No rooms available" in room_selection:
            return 0, 0
            
        room_type = room_selection.split(" - $")[0]
        price_per_night = room_prices.get(room_type, 0)
        
        # Calculate number of nights
        check_in_str = checkin_entry.get_date() if hasattr(checkin_entry, 'get_date') else checkin_entry.get()
        check_out_str = checkout_entry.get_date() if hasattr(checkout_entry, 'get_date') else checkout_entry.get()
        
        if not check_in_str or not check_out_str:
            return 0, 0
            
        try:
            # Parse dates
            if isinstance(check_in_str, str):
                check_in = datetime.strptime(check_in_str, "%m/%d/%Y")
            else:
                check_in = check_in_str
                
            if isinstance(check_out_str, str):
                check_out = datetime.strptime(check_out_str, "%m/%d/%Y")
            else:
                check_out = check_out_str
                
            # Calculate night difference
            nights = (check_out - check_in).days
            if nights < 1:
                return 0, 0
                
            return price_per_night * nights, nights
            
        except ValueError:
            return 0, 0
            
    except Exception as e:
        print(f"Error calculating price: {e}")
        return 0, 0

def update_booking_summary(event=None):
    """Update the booking summary based on selected options"""
    # Get room selection
    room_selection = room_type_dropdown.get()
    if "No rooms available" in room_selection:
        room_type = "N/A"
        price_per_night = 0
    else:
        parts = room_selection.split(" - $")
        room_type = parts[0]
        price_per_night = float(parts[1].split("/")[0])
    
    # Calculate total price
    total_price, nights = calculate_total_price()
    
    # Update summary labels
    summary_hotel_label.configure(text=f"Hotel: {hotel_name_label.cget('text')}")
    summary_location_label.configure(text=f"Location: {hotel_location_label.cget('text').replace('📍 ', '')}")
    summary_room_label.configure(text=f"Room Type: {room_type}")
    summary_price_label.configure(text=f"Price per Night: ${price_per_night}")
    summary_nights_label.configure(text=f"Total Nights: {nights if nights else 0}")
    summary_total_label.configure(text=f"Total Price: ${total_price:.2f}" if total_price else "Total Price: $0.00")

def confirm_booking():
    """Process the booking confirmation"""
    # Check if user is logged in
    if not current_user:
        messagebox.showwarning("Login Required", "Please log in to book a room")
        open_page("login")
        return
    
    # Validate inputs
    check_in = checkin_entry.get_date() if hasattr(checkin_entry, 'get_date') else checkin_entry.get()
    check_out = checkout_entry.get_date() if hasattr(checkout_entry, 'get_date') else checkout_entry.get()
    guests = guests_entry.get()
    room_selection = room_type_dropdown.get()
    payment_method = payment_var.get()
    
    # Basic validation
    if not check_in or not check_out or not guests or "No rooms available" in room_selection:
        messagebox.showwarning("Input Error", "Please fill in all required fields")
        return
    
    # Parse dates if necessary
    if isinstance(check_in, str):
        try:
            check_in = datetime.strptime(check_in, "%m/%d/%Y")
        except ValueError:
            messagebox.showwarning("Date Error", "Invalid check-in date format")
            return
    
    if isinstance(check_out, str):
        try:
            check_out = datetime.strptime(check_out, "%m/%d/%Y")
        except ValueError:
            messagebox.showwarning("Date Error", "Invalid check-out date format")
            return
    
    # Check if check-out is after check-in
    if check_in >= check_out:
        messagebox.showwarning("Date Error", "Check-out date must be after check-in date")
        return
    
    # Validate guests
    try:
        guests_count = int(guests)
        if guests_count < 1:
            messagebox.showwarning("Input Error", "Invalid number of guests")
            return
    except ValueError:
        messagebox.showwarning("Input Error", "Number of guests must be a number")
        return
    
    # Get room ID from selection
    room_type = room_selection.split(" - $")[0]
    
    # Calculate total price
    total_price, nights = calculate_total_price()
    
    # Confirm with user
    confirm = messagebox.askyesno("Confirm Booking", 
                                f"Do you want to confirm this booking?\n\n"
                                f"Hotel: {hotel_name_label.cget('text')}\n"
                                f"Room Type: {room_type}\n"
                                f"Check-in: {check_in.strftime('%m/%d/%Y')}\n"
                                f"Check-out: {check_out.strftime('%m/%d/%Y')}\n"
                                f"Guests: {guests}\n"
                                f"Total Price: ${total_price:.2f}\n"
                                f"Payment Method: {payment_method}")
    
    if not confirm:
        return
    
    # Save booking to database
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if we're working with RoomCategory or Room table
        cursor.execute("SHOW TABLES LIKE 'RoomCategory'")
        roomcategory_exists = cursor.fetchone() is not None
        
        if roomcategory_exists:
            # Try to get the room from RoomCategory first
            cursor.execute(
                """
                SELECT Category_ID as Room_ID 
                FROM RoomCategory 
                WHERE category_name = %s AND Hotel_ID = %s LIMIT 1
                """,
                (room_type, hotel_id)
            )
            room_result = cursor.fetchone()
            
            # If not found, try the Room table
            if not room_result:
                cursor.execute(
                    """
                    SELECT Room_ID 
                    FROM Room 
                    WHERE Room_Type = %s AND Availability_status = 'Available' LIMIT 1
                    """,
                    (room_type,)
                )
                room_result = cursor.fetchone()
        else:
            # Get room ID from Room table
            cursor.execute(
                """
                SELECT Room_ID 
                FROM Room 
                WHERE Room_Type = %s AND Availability_status = 'Available' LIMIT 1
                """,
                (room_type,)
            )
            room_result = cursor.fetchone()
        
        if not room_result:
            messagebox.showerror("Booking Error", "Selected room is no longer available")
            return
            
        room_id = room_result[0]
        
        # Check if Booking table has a Guests column
        cursor.execute("SHOW COLUMNS FROM Booking LIKE 'Guests'")
        has_guests_column = cursor.fetchone() is not None
        
        # Insert booking record with appropriate column set
        if has_guests_column:
            cursor.execute(
                """
                INSERT INTO Booking (User_ID, Room_ID, Check_IN_Date, Check_Out_Date, 
                                  Total_Cost, Booking_Status, Guests)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (current_user['user_id'], room_id, check_in.strftime('%Y-%m-%d'), 
                check_out.strftime('%Y-%m-%d'), total_price, 'Confirmed', guests_count)
            )
        else:
            cursor.execute(
                """
                INSERT INTO Booking (User_ID, Room_ID, Check_IN_Date, Check_Out_Date, 
                                  Total_Cost, Booking_Status)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (current_user['user_id'], room_id, check_in.strftime('%Y-%m-%d'), 
                check_out.strftime('%Y-%m-%d'), total_price, 'Confirmed')
            )
        
        # Update room availability in Room table
        cursor.execute(
            "UPDATE Room SET Availability_status = 'Booked' WHERE Room_ID = %s",
            (room_id,)
        )
        
        connection.commit()
        messagebox.showinfo("Success", "Booking confirmed successfully!")
        
        # Go to bookings page
        go_to_bookings()
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
        print(f"Database Error in confirm_booking: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ----------------- Initialize App -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - Room Reservation")
app.geometry("1200x700")
app.resizable(False, False)

# Try to load user session
if not load_user_session():
    messagebox.showwarning("Login Required", "Please log in to book a room")
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
    ("📅 My Bookings", go_to_bookings),
    ("👤 Profile", go_to_profile),
    ("💬 Feedback", go_to_feedback),
    ("🚪 Logout", logout)
]

for btn_text, btn_command in nav_buttons:
    btn = ctk.CTkButton(sidebar, text=btn_text, font=("Arial", 14), 
                      fg_color="transparent", hover_color="#34495E", 
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

# ----------------- Hotel Header -----------------
hotel_name_label = ctk.CTkLabel(content_frame, text="Luxury Grand Hotel", 
                              font=("Arial", 24, "bold"), text_color="#2C3E50")
hotel_name_label.pack(anchor="w", padx=30, pady=(30, 5))

hotel_location_label = ctk.CTkLabel(content_frame, text="📍 123 Main Street, Mt. Pleasant, Michigan", 
                                  font=("Arial", 14))
hotel_location_label.pack(anchor="w", padx=30, pady=(0, 20))

# ----------------- Booking Form and Summary -----------------
booking_container = ctk.CTkFrame(content_frame, fg_color="transparent")
booking_container.pack(fill="both", expand=True, padx=30)

# Left side - Booking Form
form_frame = ctk.CTkFrame(booking_container, fg_color="white", border_width=1, 
                        border_color="#E5E5E5", corner_radius=10)
form_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

# Form Header
form_header = ctk.CTkFrame(form_frame, fg_color="white", height=50)
form_header.pack(fill="x", padx=20, pady=(20, 10))

ctk.CTkLabel(form_header, text="📅 Select Your Stay", 
           font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")

# Form content
form_content = ctk.CTkFrame(form_frame, fg_color="white")
form_content.pack(fill="both", expand=True, padx=20, pady=10)

# Check-in Date
checkin_label = ctk.CTkLabel(form_content, text="Check-in Date", font=("Arial", 14, "bold"))
checkin_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

try:
    # Try to use DateEntry
    checkin_entry = DateEntry(form_content, width=12, background='darkblue',
                            foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
    checkin_entry.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 15))
    # Set today as default
    checkin_entry.set_date(datetime.today())
except:
    # Fallback to standard entry
    checkin_entry = ctk.CTkEntry(form_content, width=220, placeholder_text="mm/dd/yyyy")
    checkin_entry.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 15))
    # Set today as default
    checkin_entry.insert(0, datetime.today().strftime("%m/%d/%Y"))

# Check-out Date
checkout_label = ctk.CTkLabel(form_content, text="Check-out Date", font=("Arial", 14, "bold"))
checkout_label.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 5))

try:
    # Try to use DateEntry
    checkout_entry = DateEntry(form_content, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
    checkout_entry.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 15))
    # Set tomorrow as default
    checkout_entry.set_date(datetime.today() + timedelta(days=1))
except:
    # Fallback to standard entry
    checkout_entry = ctk.CTkEntry(form_content, width=220, placeholder_text="mm/dd/yyyy")
    checkout_entry.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 15))
    # Set tomorrow as default
    checkout_entry.insert(0, (datetime.today() + timedelta(days=1)).strftime("%m/%d/%Y"))

# Guests
guests_label = ctk.CTkLabel(form_content, text="Guests", font=("Arial", 14, "bold"))
guests_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 5))

guests_entry = ctk.CTkEntry(form_content, width=220, placeholder_text="Number of guests")
guests_entry.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 15))
guests_entry.insert(0, "1")  # Default 1 guest

# Room Type
room_type_label = ctk.CTkLabel(form_content, text="Room Type", font=("Arial", 14, "bold"))
room_type_label.grid(row=2, column=1, sticky="w", padx=10, pady=(10, 5))

room_type_dropdown = ctk.CTkComboBox(form_content, width=220, 
                                   values=["Single Room - $150/night", "Double Room - $200/night"])
room_type_dropdown.grid(row=3, column=1, sticky="w", padx=10, pady=(0, 15))
room_type_dropdown.bind("<<ComboboxSelected>>", update_booking_summary)

# Payment Method
payment_label = ctk.CTkLabel(form_content, text="💳 Payment Method", font=("Arial", 18, "bold"))
payment_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 10))

payment_var = ctk.StringVar(value="Credit/Debit Card")
card_radio = ctk.CTkRadioButton(form_content, text="Credit/Debit Card", 
                              variable=payment_var, value="Credit/Debit Card",
                              font=("Arial", 14))
card_radio.grid(row=5, column=0, sticky="w", padx=10, pady=5)

paypal_radio = ctk.CTkRadioButton(form_content, text="PayPal", 
                                variable=payment_var, value="PayPal",
                                font=("Arial", 14))
paypal_radio.grid(row=5, column=1, sticky="w", padx=10, pady=5)

# Confirm Button
confirm_btn = ctk.CTkButton(form_content, text="Confirm Booking", 
                          font=("Arial", 14, "bold"),
                          fg_color="#FFC107", text_color="black", 
                          hover_color="#FFD54F",
                          height=45, width=280, command=confirm_booking)
confirm_btn.grid(row=6, column=0, columnspan=2, pady=30)

# Right side - Booking Summary
summary_frame = ctk.CTkFrame(booking_container, fg_color="white", border_width=1, 
                           border_color="#E5E5E5", corner_radius=10, width=300)
summary_frame.pack(side="right", fill="y", padx=(10, 0), pady=10)
summary_frame.pack_propagate(False)  # Prevent the frame from shrinking

# Summary Header
summary_header = ctk.CTkFrame(summary_frame, fg_color="white", height=50)
summary_header.pack(fill="x", padx=20, pady=(20, 10))

ctk.CTkLabel(summary_header, text="📝 Booking Summary", 
           font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")

# Summary Content
summary_content = ctk.CTkFrame(summary_frame, fg_color="white")
summary_content.pack(fill="both", expand=True, padx=20, pady=10)

# Summary Details
summary_hotel_label = ctk.CTkLabel(summary_content, text="Hotel: Luxury Grand Hotel", 
                                 font=("Arial", 14), anchor="w")
summary_hotel_label.pack(anchor="w", pady=3)

summary_location_label = ctk.CTkLabel(summary_content, text="Location: New York, USA", 
                                    font=("Arial", 14), anchor="w")
summary_location_label.pack(anchor="w", pady=3)

summary_room_label = ctk.CTkLabel(summary_content, text="Room Type: Single Room", 
                                font=("Arial", 14), anchor="w")
summary_room_label.pack(anchor="w", pady=3)

summary_price_label = ctk.CTkLabel(summary_content, text="Price per Night: $150", 
                                 font=("Arial", 14), anchor="w")
summary_price_label.pack(anchor="w", pady=3)

summary_nights_label = ctk.CTkLabel(summary_content, text="Total Nights: 1", 
                                  font=("Arial", 14), anchor="w")
summary_nights_label.pack(anchor="w", pady=3)

# Total Price (highlighted)
total_price_frame = ctk.CTkFrame(summary_content, fg_color="white", height=50)
total_price_frame.pack(fill="x", pady=(20, 10))

summary_total_label = ctk.CTkLabel(total_price_frame, text="Total Price: $150.00", 
                                 font=("Arial", 16, "bold"), text_color="#2C3E50")
summary_total_label.pack(anchor="w")

# Initialize hotel details and update summary
load_hotel_details()

# Run the application
if __name__ == "__main__":
    app.mainloop()