import customtkinter as ctk
from tkinter import messagebox
import sys
from datetime import datetime, timedelta
import re
from tkcalendar import DateEntry

import config
from custom.navigation_frame_user import UserNavigationFrame

# Global variable to store the current user's information
current_user = None

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
            connection = config.connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Users WHERE user_id = %s",
                (user_id,)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                current_user = user_data
                return True
            
        except Exception as err:
            print(f"Database Error: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    return False

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
            
        # For now, just display a message and open the booking page
        messagebox.showinfo("Search Results", 
                          f"Searching for hotels in {location}\n"
                          f"Check-in: {check_in.strftime('%m/%d/%Y') if check_in else 'Not specified'}\n"
                          f"Check-out: {check_out.strftime('%m/%d/%Y') if check_out else 'Not specified'}\n"
                          f"Guests: {guests if guests else 'Not specified'}")
        
        # Open booking page with current user
        if current_user:
            import subprocess
            subprocess.Popen([sys.executable, "custom/booking.py", str(current_user['user_id'])])
            app.destroy()
        
    except Exception as e:
        messagebox.showerror("Search Error", str(e))

# ------------------- View Hotel Details -------------------
def view_hotel_details(hotel_name):
    """Open the hotel details page for the selected hotel"""
    try:
        # For now, just show a message and open the booking page
        messagebox.showinfo("Hotel Details", f"Viewing details for {hotel_name}")
        
        # Open booking page with current user
        if current_user:
            import subprocess
            subprocess.Popen([sys.executable, "custom/booking.py", str(current_user['user_id'])])
            app.destroy()
            
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Unable to view hotel details: {e}")

# ------------------- Load Popular Hotels -------------------
def load_popular_hotels():
    """Load popular hotels from the database"""
    hotels = []
    try:
        connection = config.connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Since we don't have a Hotel table in the schema, we'll query rooms instead
        cursor.execute(
            """
            SELECT Room_ID, Room_Type, Price_per_Night, Availability_status
            FROM Room
            WHERE Availability_status = 'Available'
            LIMIT 3
            """
        )
        rooms = cursor.fetchall()
        
        # Format hotel data from rooms
        for room in rooms:
            # Extract hotel name from room type
            hotel_name = room['Room_Type'].split(" - ")[0] if " - " in room['Room_Type'] else room['Room_Type']
            
            # Create description
            description = f"Enjoy a comfortable stay in this {room['Room_Type'].lower()}. Perfect for business or leisure travelers."
            
            # Create fake amenities
            amenities = "📶 Free WiFi | 🏊 Pool | 🚗 Free Parking"
            
            # Add hotel to the list
            hotels.append((
                hotel_name,
                f"{description[:100]}...",
                amenities,
                f"${room['Price_per_Night']:.2f} per night"
            ))
            
    except Exception as err:
        messagebox.showerror("Database Error", f"Could not load hotels: {err}")
        print(f"Database Error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    
    return hotels

# ------------------- Create Hotel Card -------------------
def create_hotel_card(parent, hotel_data):
    """Create a hotel card widget"""
    name, description, amenities, price = hotel_data
    
    card = ctk.CTkFrame(parent, fg_color="white", border_width=1, border_color="#D5D8DC", width=280, height=150)
    card.pack_propagate(False)  # Prevent the frame from shrinking to fit its contents
    
    ctk.CTkLabel(card, text=name, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10,5))
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

# ----------------- Main Function -----------------
def main():
    global app, location_entry, checkin_entry, checkout_entry, guests_entry
    
    # Try to load user session
    load_user_session()
    
    # Initialize the app
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    app.title("Hotel Booking - Home")
    app.geometry("1200x700")
    app.resizable(False, False)
    
    # ----------------- Main Frame -----------------
    main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
    main_frame.pack(expand=True, fill="both")
    
    # ----------------- Navigation Sidebar -----------------
    nav_frame = UserNavigationFrame(main_frame, current_user)
    
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
        checkin_entry = DateEntry(search_grid, width=12, background='darkblue',
                                foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
        checkin_entry.grid(row=1, column=1, sticky="w", padx=(0, 20))
    except:
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
    except:
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
    
    app.mainloop()

if __name__ == "__main__":
    main()