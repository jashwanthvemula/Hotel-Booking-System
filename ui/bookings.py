import customtkinter as ctk
from tkinter import messagebox, Canvas, Scrollbar
import mysql.connector
import subprocess
import sys
from datetime import datetime
import os

# Global variable to store the current user's information
current_user = None

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="new_password",  # Replace with your MySQL password
        database="hotel_book"  # Replace with your database name
    )

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
    open_page("user")  # Changed from profile.py to user.py

def go_to_feedback():
    open_page("feedback")

def logout():
    """Log out the current user and return to login page"""
    global current_user
    current_user = None
    open_page("login")

# ------------------- Booking Functions -------------------
def load_user_bookings():
    """Load the current user's bookings from the database"""
    bookings = []
    if not current_user:
        return bookings
    
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # First, try a simple query to get booking data
        try:
            cursor.execute(
                """
                SELECT b.Booking_ID, b.Check_IN_Date, b.Check_Out_Date, 
                       b.Total_Cost, b.Booking_Status,
                       r.Room_Type, r.Price_per_Night
                FROM Booking b
                JOIN Room r ON b.Room_ID = r.Room_ID
                WHERE b.User_ID = %s
                ORDER BY b.Check_IN_Date DESC
                """,
                (current_user['user_id'],)
            )
            bookings_data = cursor.fetchall()
            
            # Default values for additional fields
            for booking in bookings_data:
                booking['Guests'] = 2  # Default value
                room_parts = booking['Room_Type'].split(' - ', 1)
                booking['hotel_name'] = room_parts[0] if len(room_parts) > 1 else booking['Room_Type']
                booking['location'] = "Location information not available"
                booking['image_path'] = None
            
            return bookings_data
                
        except mysql.connector.Error as err:
            # If simple query fails, try more detailed approach
            print(f"Simple query failed: {err}")
            
            # Check if Booking table has a Guests column
            cursor.execute("SHOW COLUMNS FROM Booking LIKE 'Guests'")
            has_guests_column = cursor.fetchone() is not None
            
            # Check if Room is related to Hotel
            try:
                # Try to see if Room table has hotel_id column
                cursor.execute("SHOW COLUMNS FROM Room LIKE 'hotel_id'")
                has_hotel_id = cursor.fetchone() is not None
                
                # If so, build a query with hotel information
                if has_hotel_id:
                    base_query = """
                        SELECT b.Booking_ID, b.Check_IN_Date, b.Check_Out_Date, 
                               b.Total_Cost, b.Booking_Status,
                               r.Room_Type, r.Price_per_Night, 
                               h.hotel_name, h.location, h.image_path
                    """
                    
                    if has_guests_column:
                        base_query += ", b.Guests"
                        
                    query = f"""
                        {base_query}
                        FROM Booking b
                        JOIN Room r ON b.Room_ID = r.Room_ID
                        JOIN Hotel h ON r.hotel_id = h.Hotel_ID
                        WHERE b.User_ID = %s
                        ORDER BY b.Check_IN_Date DESC
                    """
                    
                    cursor.execute(query, (current_user['user_id'],))
                    bookings_data = cursor.fetchall()
                    
                    # Add default Guests if needed
                    if not has_guests_column:
                        for booking in bookings_data:
                            booking['Guests'] = 2  # Default value
                    
                    return bookings_data
                
            except mysql.connector.Error:
                # If that fails, fall back to basic booking information
                if has_guests_column:
                    cursor.execute(
                        """
                        SELECT b.Booking_ID, b.Check_IN_Date, b.Check_Out_Date, 
                               b.Total_Cost, b.Booking_Status, b.Guests,
                               r.Room_Type, r.Price_per_Night
                        FROM Booking b
                        JOIN Room r ON b.Room_ID = r.Room_ID
                        WHERE b.User_ID = %s
                        ORDER BY b.Check_IN_Date DESC
                        """,
                        (current_user['user_id'],)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT b.Booking_ID, b.Check_IN_Date, b.Check_Out_Date, 
                               b.Total_Cost, b.Booking_Status,
                               r.Room_Type, r.Price_per_Night
                        FROM Booking b
                        JOIN Room r ON b.Room_ID = r.Room_ID
                        WHERE b.User_ID = %s
                        ORDER BY b.Check_IN_Date DESC
                        """,
                        (current_user['user_id'],)
                    )
                
                bookings_data = cursor.fetchall()
                
                # Add missing fields with default values
                for booking in bookings_data:
                    if not has_guests_column:
                        booking['Guests'] = 2  # Default value
                    
                    # Extract hotel name from room type if possible
                    room_parts = booking['Room_Type'].split(' - ', 1)
                    booking['hotel_name'] = room_parts[0] if len(room_parts) > 1 else booking['Room_Type']
                    booking['location'] = "Location information not available"
                    booking['image_path'] = None
                
                return bookings_data
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Could not load bookings: {err}")
        print(f"Database Error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    
    return bookings

def cancel_booking(booking_id, booking_card):
    """Cancel a booking"""
    # Ask for confirmation
    confirm = messagebox.askyesno("Cancel Booking", 
                                 "Are you sure you want to cancel this booking?\nThis action cannot be undone.")
    if not confirm:
        return
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Get the Room_ID before cancelling
        cursor.execute(
            "SELECT Room_ID FROM Booking WHERE Booking_ID = %s",
            (booking_id,)
        )
        room_result = cursor.fetchone()
        
        if not room_result:
            messagebox.showerror("Error", "Booking not found")
            return
            
        room_id = room_result[0]
        
        # Update booking status
        cursor.execute(
            "UPDATE Booking SET Booking_Status = 'Cancelled' WHERE Booking_ID = %s",
            (booking_id,)
        )
        
        # Update room availability
        cursor.execute(
            "UPDATE Room SET Availability_status = 'Available' WHERE Room_ID = %s",
            (room_id,)
        )
        
        connection.commit()
        messagebox.showinfo("Success", "Booking cancelled successfully")
        
        # Update the booking card to show cancelled status
        update_booking_card_status(booking_card, "Cancelled")
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def update_booking_card_status(booking_card, new_status):
    """Update the status display on a booking card"""
    # Find the status label in the booking card
    for child in booking_card.winfo_children():
        if hasattr(child, 'status_label'):
            # Update the status
            child.status_label.configure(
                text=new_status,
                text_color="#E74C3C" if new_status == "Cancelled" else "#27AE60"
            )
            break

# ------------------- Create Booking Card -------------------
def create_booking_card(parent, booking_data):
    """Create a card widget for a booking"""
    card = ctk.CTkFrame(parent, fg_color="white", border_width=1, border_color="#D5D8DC", height=200)
    
    # Extract booking data with safe defaults for missing fields
    hotel_name = booking_data.get('hotel_name', "Hotel")
    room_type = booking_data.get('Room_Type', "Room")
    
    # Safely format dates
    try:
        check_in = datetime.strftime(booking_data['Check_IN_Date'], "%m/%d/%Y")
    except (TypeError, KeyError):
        check_in = str(booking_data.get('Check_IN_Date', "N/A"))
        
    try:
        check_out = datetime.strftime(booking_data['Check_Out_Date'], "%m/%d/%Y")
    except (TypeError, KeyError):
        check_out = str(booking_data.get('Check_Out_Date', "N/A"))
    
    total_cost = booking_data.get('Total_Cost', 0)
    booking_status = booking_data.get('Booking_Status', "Unknown")
    guests = booking_data.get('Guests', 1)
    location = booking_data.get('location', "Location not available")
    image_path = booking_data.get('image_path', None)
    booking_id = booking_data.get('Booking_ID', 0)
    
    # Grid layout for the card
    card.grid_columnconfigure(0, weight=0)
    card.grid_columnconfigure(1, weight=1)
    
    # Try to load and display the hotel image
    if image_path and os.path.exists(str(image_path)):
        try:
            from PIL import Image, ImageTk
            hotel_image = Image.open(image_path)
            hotel_image = hotel_image.resize((150, 120), Image.LANCZOS)
            photo = ImageTk.PhotoImage(hotel_image)
            
            image_label = ctk.CTkLabel(card, text="", image=photo, fg_color="white")
            image_label.image = photo  # Keep a reference
            image_label.grid(row=0, column=0, rowspan=4, padx=(10, 15), pady=10, sticky="nw")
        except Exception as e:
            print(f"Error loading hotel image: {e}")
            # If image fails, just show hotel name
            ctk.CTkLabel(card, text=hotel_name, font=("Arial", 16, "bold")).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nw")
    else:
        # No image, just show hotel name
        ctk.CTkLabel(card, text=hotel_name, font=("Arial", 16, "bold")).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nw")
    
    # Hotel Name and Location
    hotel_info = ctk.CTkFrame(card, fg_color="transparent")
    hotel_info.grid(row=0, column=1, sticky="nw", padx=10, pady=(10, 5))
    
    ctk.CTkLabel(hotel_info, text=hotel_name, font=("Arial", 16, "bold")).pack(anchor="w")
    ctk.CTkLabel(hotel_info, text=f"📍 {location}", font=("Arial", 12)).pack(anchor="w")
    
    # Booking Details
    booking_details = ctk.CTkFrame(card, fg_color="transparent")
    booking_details.grid(row=1, column=1, sticky="nw", padx=10, pady=5)
    
    ctk.CTkLabel(booking_details, text=f"Room Type: {room_type}", font=("Arial", 12)).pack(anchor="w", pady=2)
    ctk.CTkLabel(booking_details, text=f"Dates: {check_in} to {check_out}", font=("Arial", 12)).pack(anchor="w", pady=2)
    ctk.CTkLabel(booking_details, text=f"Guests: {guests}", font=("Arial", 12)).pack(anchor="w", pady=2)
    
    # Status and Total Cost
    status_frame = ctk.CTkFrame(card, fg_color="transparent")
    status_frame.grid(row=2, column=1, sticky="nw", padx=10, pady=5)
    
    # Status with color based on booking status
    status_color = "#27AE60" if booking_status == "Confirmed" else "#E74C3C"
    status_label = ctk.CTkLabel(status_frame, text=booking_status, 
                             font=("Arial", 14, "bold"), text_color=status_color)
    status_label.pack(anchor="w")
    
    # Store a reference to the status label for later updates
    status_frame.status_label = status_label
    
    # Format total cost with proper handling for different types
    try:
        total_cost_formatted = f"${float(total_cost):.2f}"
    except (ValueError, TypeError):
        total_cost_formatted = f"${total_cost}" if total_cost else "$0.00"
    
    ctk.CTkLabel(status_frame, text=f"Total Cost: {total_cost_formatted}", 
               font=("Arial", 14, "bold"), text_color="#1E90FF").pack(anchor="w")
    
    # Button Frame
    button_frame = ctk.CTkFrame(card, fg_color="transparent")
    button_frame.grid(row=3, column=1, sticky="se", padx=10, pady=10)
    
    # Only show cancel button for confirmed bookings
    if booking_status == "Confirmed":
        cancel_btn = ctk.CTkButton(button_frame, text="Cancel Booking", 
                                 font=("Arial", 12), 
                                 fg_color="#E74C3C", hover_color="#C0392B", 
                                 width=120, height=30, corner_radius=5,
                                 command=lambda: cancel_booking(booking_id, card))
        cancel_btn.pack(side="right", padx=5)
    
    return card

# ----------------- Setup -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - My Bookings")
app.geometry("1200x700")
app.resizable(False, False)

# Try to load user session
if not load_user_session():
    messagebox.showwarning("Login Required", "Please log in to view your bookings")
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
    is_active = "My Bookings" in btn_text
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

# ----------------- Header Section -----------------
header_frame = ctk.CTkFrame(content_frame, fg_color="white", height=50)
header_frame.pack(fill="x", padx=30, pady=(30, 10))

ctk.CTkLabel(header_frame, text="My Bookings", 
           font=("Arial", 24, "bold"), text_color="#2C3E50").pack(anchor="w")

# ----------------- Bookings Section (Scrollable) -----------------
bookings_section = ctk.CTkFrame(content_frame, fg_color="white")
bookings_section.pack(fill="both", expand=True, padx=30, pady=10)

# Create a canvas for scrolling
canvas = Canvas(bookings_section, bg="white", highlightthickness=0)
scrollbar = Scrollbar(bookings_section, orient="vertical", command=canvas.yview)
scrollable_frame = ctk.CTkFrame(canvas, fg_color="white")

# Configure the canvas
scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# Pack the canvas and scrollbar
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Load bookings from database
bookings = load_user_bookings()

# Create booking cards or show message if no bookings found
if bookings:
    for booking in bookings:
        card = create_booking_card(scrollable_frame, booking)
        card.pack(fill="x", padx=0, pady=10)
else:
    # Display a message when no bookings are found
    no_bookings_frame = ctk.CTkFrame(scrollable_frame, fg_color="white")
    no_bookings_frame.pack(fill="both", expand=True, padx=20, pady=50)
    
    ctk.CTkLabel(
        no_bookings_frame, 
        text="You don't have any bookings yet.", 
        font=("Arial", 16), 
        text_color="gray"
    ).pack(pady=10)
    
    ctk.CTkButton(
        no_bookings_frame,
        text="Browse Hotels",
        font=("Arial", 14),
        fg_color="#1E90FF",
        hover_color="#1872BB",
        width=150,
        height=40,
        command=go_to_home
    ).pack(pady=10)

# Enable mousewheel scrolling
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Run the application
if __name__ == "__main__":
    app.mainloop()