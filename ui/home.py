import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import subprocess
import sys
from datetime import datetime, timedelta
import os
from tkcalendar import DateEntry
import re

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
def load_user_session(user_id=None):
    """Load user information from database"""
    global current_user
    
    # If no user_id is provided, check if any was passed as a command line argument
    if user_id is None and len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
        except (ValueError, IndexError):
            user_id = None
    
    if user_id:
        try:
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
            
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
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
    open_page("book")

def go_to_profile():
    open_page("user")

def go_to_feedback():
    open_page("feedback")

def logout():
    """Log out the current user and return to login page"""
    global current_user
    current_user = None
    open_page("login")

# ------------------- Hotel Search Function -------------------
def search_hotels():
    """Search for hotels based on criteria"""
    location = location_entry.get()
    check_in = checkin_entry.get_date() if hasattr(checkin_entry, 'get_date') else checkin_entry.get()
    check_out = checkout_entry.get_date() if hasattr(checkout_entry, 'get_date') else checkout_entry.get()
    guests = guests_entry.get()
    
    # Validate inputs
    if not location:
        messagebox.showwarning("Search Error", "Please enter a location.")
        return
    
    try:
        # Convert string dates to datetime objects if needed
        if isinstance(check_in, str) and check_in:
            check_in = datetime.strptime(check_in, "%m/%d/%Y")
        if isinstance(check_out, str) and check_out:
            check_out = datetime.strptime(check_out, "%m/%d/%Y")
            
        # Validate date range
        if check_in and check_out and check_in >= check_out:
            messagebox.showwarning("Date Error", "Check-out date must be after check-in date.")
            return
            
        # Validate guests
        if guests and not guests.isdigit():
            messagebox.showwarning("Input Error", "Number of guests must be a number.")
            return
            
        # Perform the search - for now just show a message
        messagebox.showinfo("Search Results", 
                          f"Searching for hotels in {location}\n"
                          f"Check-in: {check_in.strftime('%m/%d/%Y') if check_in else 'Not specified'}\n"
                          f"Check-out: {check_out.strftime('%m/%d/%Y') if check_out else 'Not specified'}\n"
                          f"Guests: {guests if guests else 'Not specified'}")
        
        # Here you would typically redirect to a search results page
        # open_page("search_results")  # Uncomment when you have this page
    
    except Exception as e:
        messagebox.showerror("Search Error", str(e))

# ------------------- View Hotel Details -------------------
def view_hotel_details(hotel_name):
    """Open the hotel details page for the selected hotel"""
    try:
        # Here you would typically pass the hotel ID to the hotel details page
        # For now, just show a message
        messagebox.showinfo("Hotel Details", f"Viewing details for {hotel_name}")
        
        # Example of how you might navigate to a hotel details page
        # subprocess.Popen([sys.executable, "hotel_details.py", str(hotel_id)])
        # app.destroy()
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Unable to view hotel details: {e}")

# ------------------- Load Popular Hotels -------------------
def load_popular_hotels():
    """Load popular hotels from the database"""
    hotels = []
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get popular hotels with their details
        cursor.execute(
            """
            SELECT h.Hotel_ID, h.hotel_name, h.location, 
                   h.description, h.star_rating, 
                   MIN(rc.base_price) as min_price
            FROM Hotel h
            JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
            GROUP BY h.Hotel_ID
            ORDER BY h.star_rating DESC, min_price
            LIMIT 3
            """
        )
        hotels_data = cursor.fetchall()
        
        # Format hotel data
        for hotel in hotels_data:
            # Fetch some amenities for the hotel
            cursor.execute(
                """
                SELECT GROUP_CONCAT(a.amenity_name SEPARATOR ' | ') as amenities
                FROM Hotel_Amenities ha
                JOIN Amenities a ON ha.Amenity_ID = a.Amenity_ID
                WHERE ha.Hotel_ID = %s
                LIMIT 3
                """, 
                (hotel['Hotel_ID'],)
            )
            amenities_result = cursor.fetchone()
            
            # Format amenities
            amenities = amenities_result['amenities'] if amenities_result and amenities_result['amenities'] else "📶 Free WiFi | 🏊 Pool | 🚗 Free Parking"
            
            # Add hotel to the list
            hotels.append((
                hotel['hotel_name'],
                f"{hotel['description'][:100]}...",
                amenities,
                f"${hotel['min_price']:.2f} per night"
            ))
            
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Could not load hotels: {err}")
        print(f"Database Error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    
    return hotels

# Replace the existing load_popular_hotels function in home.py with this updated version

def load_popular_hotels():
    """Load popular hotels from the database"""
    hotels = []
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get popular hotels with their details
        cursor.execute(
            """
            SELECT h.Hotel_ID, h.hotel_name, h.location, 
                   h.description, h.star_rating, h.image_path,
                   MIN(rc.base_price) as min_price
            FROM Hotel h
            LEFT JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
            GROUP BY h.Hotel_ID
            ORDER BY h.star_rating DESC, min_price
            LIMIT 3
            """
        )
        hotels_data = cursor.fetchall()
        
        # Format hotel data
        for hotel in hotels_data:
            # Fetch some amenities for the hotel
            cursor.execute(
                """
                SELECT GROUP_CONCAT(CONCAT(a.amenity_icon, ' ', a.amenity_name) SEPARATOR ' | ') as amenities
                FROM Hotel_Amenities ha
                JOIN Amenities a ON ha.Amenity_ID = a.Amenity_ID
                WHERE ha.Hotel_ID = %s
                LIMIT 3
                """, 
                (hotel['Hotel_ID'],)
            )
            amenities_result = cursor.fetchone()
            
            # Format amenities
            amenities = amenities_result['amenities'] if amenities_result and amenities_result['amenities'] else "📶 Free WiFi | 🏊 Pool | 🚗 Free Parking"
            
            # Format price
            price = f"${hotel['min_price']:.2f} per night" if hotel['min_price'] else "Price on request"
            
            # Format description
            description = f"{hotel['description'][:100]}..." if hotel['description'] else "Beautiful hotel in a prime location."
            
            # Add hotel to the list
            hotels.append((
                hotel['hotel_name'],
                description,
                amenities,
                price,
                hotel['image_path'] 
            ))
            
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Could not load hotels: {err}")
        print(f"Database Error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    
    return hotels

# And update the create_hotel_card function to handle the image:

def create_hotel_card(parent, hotel_data):
    """Create a hotel card widget"""
    name, description, amenities, price, image_path = hotel_data
    
    card = ctk.CTkFrame(parent, fg_color="white", border_width=1, border_color="#D5D8DC", width=280, height=250)
    card.pack_propagate(False)  # Prevent the frame from shrinking to fit its contents
    
    # Try to load and display the hotel image if available
    if image_path and os.path.exists(image_path):
        try:
            from PIL import Image, ImageTk
            hotel_image = Image.open(image_path)
            hotel_image = hotel_image.resize((260, 120), Image.LANCZOS)
            photo = ImageTk.PhotoImage(hotel_image)
            
            image_label = ctk.CTkLabel(card, text="", image=photo, fg_color="white")
            image_label.image = photo  # Keep a reference
            image_label.pack(anchor="center", padx=10, pady=(10, 5))
        except Exception as e:
            print(f"Error loading hotel image: {e}")
            # If image fails, just show the name with more padding
            ctk.CTkLabel(card, text=name, font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(20,5))
    else:
        # No image, just show the name with more padding
        ctk.CTkLabel(card, text=name, font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(20,5))
    
    # If we already showed the name because of missing image, don't show it again
    if image_path and os.path.exists(image_path):
        ctk.CTkLabel(card, text=name, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5,5))
        
    ctk.CTkLabel(card, text=description, font=("Arial", 10), wraplength=250).pack(anchor="w", padx=10)
    ctk.CTkLabel(card, text=amenities, font=("Arial", 9), wraplength=250).pack(anchor="w", padx=10, pady=(5,0))
    
    price_frame = ctk.CTkFrame(card, fg_color="white")
    price_frame.pack(anchor="w", fill="x", padx=10, pady=(5,10))
    
    ctk.CTkLabel(price_frame, text=price, font=("Arial", 10, "bold"), text_color="#1E90FF").pack(side="left")
    
    view_btn = ctk.CTkButton(price_frame, text="View", font=("Arial", 10), 
                           fg_color="#0F2D52", hover_color="#1E4D88", 
                           width=60, height=25, corner_radius=5,
                           command=lambda: view_hotel_details(name))
    view_btn.pack(side="right", padx=10)
    
    return card
# ------------------- Create Hotel Card -------------------
def create_hotel_card(parent, hotel_data):
    """Create a hotel card widget"""
    # Check if we have 5 elements (including image) or 4 elements (old format)
    if len(hotel_data) == 5:
        name, description, amenities, price, image_path = hotel_data
    else:
        name, description, amenities, price = hotel_data
        image_path = None
    
    card = ctk.CTkFrame(parent, fg_color="white", border_width=1, border_color="#D5D8DC", width=280, height=250)
    card.pack_propagate(False)  # Prevent the frame from shrinking to fit its contents
    
    # Try to load and display the hotel image if available
    if image_path and os.path.exists(image_path):
        try:
            from PIL import Image, ImageTk
            hotel_image = Image.open(image_path)
            hotel_image = hotel_image.resize((260, 120), Image.LANCZOS)
            photo = ImageTk.PhotoImage(hotel_image)
            
            image_label = ctk.CTkLabel(card, text="", image=photo, fg_color="white")
            image_label.image = photo  # Keep a reference
            image_label.pack(anchor="center", padx=10, pady=(10, 5))
        except Exception as e:
            print(f"Error loading hotel image: {e}")
            # If image fails, just show the name with more padding
            ctk.CTkLabel(card, text=name, font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(20,5))
    else:
        # No image, just show the name with more padding
        ctk.CTkLabel(card, text=name, font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(20,5))
    
    # If we already showed the name because of missing image, don't show it again
    if not (image_path and os.path.exists(image_path)):
        # No need to show name again
        pass
    else:
        ctk.CTkLabel(card, text=name, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5,5))
        
    ctk.CTkLabel(card, text=description, font=("Arial", 10), wraplength=250).pack(anchor="w", padx=10)
    ctk.CTkLabel(card, text=amenities, font=("Arial", 9), wraplength=250).pack(anchor="w", padx=10, pady=(5,0))
    
    price_frame = ctk.CTkFrame(card, fg_color="white")
    price_frame.pack(anchor="w", fill="x", padx=10, pady=(5,10))
    
    ctk.CTkLabel(price_frame, text=price, font=("Arial", 10, "bold"), text_color="#1E90FF").pack(side="left")
    
    view_btn = ctk.CTkButton(price_frame, text="View", font=("Arial", 10), 
                           fg_color="#0F2D52", hover_color="#1E4D88", 
                           width=60, height=25, corner_radius=5,
                           command=lambda: view_hotel_details(name))
    view_btn.pack(side="right", padx=10)
    
    return card

# No default hotels - all hotels are fetched from database

# ----------------- Setup -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - Home")
app.geometry("1200x700")
app.resizable(False, False)

# Try to load user session
load_user_session()

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

# ----------------- Header Section -----------------
header_frame = ctk.CTkFrame(content_frame, fg_color="white", height=50)
header_frame.pack(fill="x", padx=30, pady=(30, 10))

ctk.CTkLabel(header_frame, text="Find Your Perfect Stay", 
           font=("Arial", 24, "bold"), text_color="#2C3E50").pack(anchor="w")

# ----------------- Search Section -----------------
search_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E5E5")
search_frame.pack(fill="x", padx=30, pady=(10, 20))

# Create the search form layout
search_grid = ctk.CTkFrame(search_frame, fg_color="transparent")
search_grid.pack(padx=20, pady=20, fill="x")

# Location Field
location_label = ctk.CTkLabel(search_grid, text="📍 Location", font=("Arial", 12, "bold"))
location_label.grid(row=0, column=0, sticky="w", padx=(0, 20))
location_entry = ctk.CTkEntry(search_grid, width=200, placeholder_text="Enter Location")
location_entry.grid(row=1, column=0, sticky="w", padx=(0, 20))

# Check-in Date Field
checkin_label = ctk.CTkLabel(search_grid, text="📅 Check-in Date", font=("Arial", 12, "bold"))
checkin_label.grid(row=0, column=1, sticky="w", padx=(0, 20))

# Try to use DateEntry if available, otherwise use normal entry
try:
    # For date picker, you need: pip install tkcalendar
    import tkcalendar
    checkin_entry = DateEntry(search_grid, width=12, background='darkblue',
                            foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
    checkin_entry.grid(row=1, column=1, sticky="w", padx=(0, 20))
except ImportError:
    checkin_entry = ctk.CTkEntry(search_grid, width=200, placeholder_text="mm/dd/yyyy")
    checkin_entry.grid(row=1, column=1, sticky="w", padx=(0, 20))

# Check-out Date Field
checkout_label = ctk.CTkLabel(search_grid, text="📅 Check-out Date", font=("Arial", 12, "bold"))
checkout_label.grid(row=0, column=2, sticky="w", padx=(0, 20))

try:
    # For date picker
    checkout_entry = DateEntry(search_grid, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
    checkout_entry.grid(row=1, column=2, sticky="w", padx=(0, 20))
except ImportError:
    checkout_entry = ctk.CTkEntry(search_grid, width=200, placeholder_text="mm/dd/yyyy")
    checkout_entry.grid(row=1, column=2, sticky="w", padx=(0, 20))

# Guests Field
guests_label = ctk.CTkLabel(search_grid, text="👥 Guests", font=("Arial", 12, "bold"))
guests_label.grid(row=0, column=3, sticky="w")
guests_entry = ctk.CTkEntry(search_grid, width=100, placeholder_text="Number of guests")
guests_entry.grid(row=1, column=3, sticky="w")

# Search Button
search_btn = ctk.CTkButton(search_grid, text="Search Rooms", font=("Arial", 12, "bold"),
                         fg_color="#FFC107", text_color="black", hover_color="#FFD54F",
                         height=35, width=150, command=search_hotels)
search_btn.grid(row=1, column=4, padx=(20, 0))

# ----------------- Popular Hotels Section -----------------
hotels_section = ctk.CTkFrame(content_frame, fg_color="white")
hotels_section.pack(fill="both", expand=True, padx=30, pady=10)

ctk.CTkLabel(hotels_section, text="Popular Hotels", 
           font=("Arial", 20, "bold"), text_color="#2C3E50").pack(anchor="w", pady=(0, 15))

# Hotel Cards Container
hotel_cards = ctk.CTkFrame(hotels_section, fg_color="transparent")
hotel_cards.pack(fill="both", expand=True)

# Load hotels from database
hotels = load_popular_hotels()

# Create hotel cards or show message if no hotels found
if hotels:
    for i, hotel_data in enumerate(hotels):
        card = create_hotel_card(hotel_cards, hotel_data)
        card.pack(side="left", padx=10, pady=10)
else:
    # Display a message when no hotels are found
    no_hotels_label = ctk.CTkLabel(
        hotel_cards, 
        text="No hotels found in the database.\nPlease add hotels through the admin interface.", 
        font=("Arial", 14), 
        text_color="gray"
    )
    no_hotels_label.pack(pady=50)

# Run the application
if __name__ == "__main__":
    app.mainloop()