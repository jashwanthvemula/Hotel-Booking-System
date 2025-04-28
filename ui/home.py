import customtkinter as ctk
from tkinter import messagebox, Canvas, Scrollbar, ttk
import mysql.connector
from datetime import datetime, timedelta
import os
from PIL import Image, ImageTk
from tkcalendar import DateEntry
import re
import sys
import logging
from db_config import connect_db

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ------------------- Main Application Class -------------------
class HotelBookingUserApp:
    def __init__(self, root, user_id=None):
        self.root = root
        self.root.title("Hotel Booking")
        self.root.geometry("1200x700")
        self.root.resizable(True, True)
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        
        # Initialize user session
        self.current_user = None
        self.user_id = user_id if user_id else (int(sys.argv[1]) if len(sys.argv) > 1 else None)
        if not self.load_user_session():
            messagebox.showwarning("Login Required", "Please log in to continue")
            self.root.destroy()
            return
        
        # Variables
        self.selected_hotel_id = None
        self.room_prices = {}
        self.selected_rating = 0
        self.star_buttons = []
        self.selected_booking = None
        
        # Frames dictionary to store all section frames
        self.frames = {}
        
        # Setup main frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=0)
        self.main_frame.pack(expand=True, fill="both")
        
        # Setup sidebar
        self.setup_sidebar()
        
        # Setup content area
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # Initialize all frames
        self.frames['home'] = self.create_home_frame()
        self.frames['book'] = self.create_book_frame()
        self.frames['bookings'] = self.create_bookings_frame()
        self.frames['user'] = self.create_user_frame()
        self.frames['feedback'] = self.create_feedback_frame()
        
        # Show home frame by default
        self.show_frame('home')

    def setup_sidebar(self):
        """Setup the sidebar with navigation buttons"""
        self.sidebar = ctk.CTkFrame(self.main_frame, fg_color="#2C3E50", width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        ctk.CTkLabel(self.sidebar, text="🏨 Hotel Booking", font=("Arial", 18, "bold"), text_color="white").pack(pady=(30, 20))
        
        nav_buttons = [
            ("🏠 Home", lambda: self.show_frame('home')),
            ("📅 Bookings", lambda: self.show_frame('bookings')),
            ("👤 Profile", lambda: self.show_frame('user')),
            ("💬 Feedback", lambda: self.show_frame('feedback')),
            ("🚪 Logout", self.logout)
        ]
        
        for btn_text, btn_command in nav_buttons:
            btn = ctk.CTkButton(self.sidebar, text=btn_text, font=("Arial", 14),
                               fg_color="transparent", hover_color="#34495E",
                               anchor="w", height=40, width=180,
                               command=btn_command)
            btn.pack(pady=5, padx=10)
        
        if self.current_user:
            username = f"{self.current_user['first_name']} {self.current_user['last_name']}"
            ctk.CTkLabel(self.sidebar, text=f"Welcome, {username}",
                        font=("Arial", 12), text_color="white").pack(pady=(50, 10))

    def show_frame(self, frame_name):
        """Show the specified frame and hide others"""
        for frame in self.frames.values():
            frame.pack_forget()
        
        self.frames[frame_name].pack(side="right", fill="both", expand=True)
        
        # Refresh data for specific frames
        logging.debug(f"Showing frame: {frame_name}, current_user: {self.current_user}")
        if frame_name == 'home':
            self.load_popular_hotels()
        elif frame_name == 'bookings':
            self.populate_bookings()
        elif frame_name == 'user':
            self.populate_profile_fields()
            self.populate_booking_table()
        elif frame_name == 'feedback':
            pass  # No refresh needed for feedback frame

    def load_user_session(self):
        """Load user information from database"""
        if self.user_id:
            try:
                connection = connect_db()
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM Users WHERE user_id = %s", (self.user_id,))
                user_data = cursor.fetchone()
                if user_data:
                    self.current_user = user_data
                    logging.debug(f"User session loaded: {self.current_user}")
                    return True
            except mysql.connector.Error as err:
                logging.error(f"Error loading user session: {err}")
            finally:
                if 'connection' in locals() and connection.is_connected():
                    cursor.close()
                    connection.close()
        logging.warning("Failed to load user session")
        return False

    def logout(self):
        """Log out and return to login page"""
        self.current_user = None
        self.root.destroy()

    # ------------------- Home Frame -------------------
    def create_home_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=0)
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=50)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header_frame, text="Find Your Perfect Stay",
                    font=("Arial", 24, "bold"), text_color="#2C3E50").pack(anchor="w")
        
        # Search Section
        search_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E5E5")
        search_frame.pack(fill="x", padx=30, pady=(10, 20))
        search_grid = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_grid.pack(padx=20, pady=20, fill="x")
        
        # Location
        self.home_location_label = ctk.CTkLabel(search_grid, text="📍 Location", font=("Arial", 12, "bold"))
        self.home_location_label.grid(row=0, column=0, sticky="w", padx=(0, 20))
        self.home_location_entry = ctk.CTkEntry(search_grid, width=200, placeholder_text="Enter Location")
        self.home_location_entry.grid(row=1, column=0, sticky="w", padx=(0, 20))
        
        # Check-in
        self.home_checkin_label = ctk.CTkLabel(search_grid, text="📅 Check-in Date", font=("Arial", 12, "bold"))
        self.home_checkin_label.grid(row=0, column=1, sticky="w", padx=(0, 20))
        try:
            self.home_checkin_entry = DateEntry(search_grid, width=12, background='darkblue',
                                              foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
            self.home_checkin_entry.grid(row=1, column=1, sticky="w", padx=(0, 20))
        except:
            self.home_checkin_entry = ctk.CTkEntry(search_grid, width=200, placeholder_text="mm/dd/yyyy")
            self.home_checkin_entry.grid(row=1, column=1, sticky="w", padx=(0, 20))
        
        # Check-out
        self.home_checkout_label = ctk.CTkLabel(search_grid, text="📅 Check-out Date", font=("Arial", 12, "bold"))
        self.home_checkout_label.grid(row=0, column=2, sticky="w", padx=(0, 20))
        try:
            self.home_checkout_entry = DateEntry(search_grid, width=12, background='darkblue',
                                               foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
            self.home_checkout_entry.grid(row=1, column=2, sticky="w", padx=(0, 20))
        except:
            self.home_checkout_entry = ctk.CTkEntry(search_grid, width=200, placeholder_text="mm/dd/yyyy")
            self.home_checkout_entry.grid(row=1, column=2, sticky="w", padx=(0, 20))
        
        # Guests
        self.home_guests_label = ctk.CTkLabel(search_grid, text="👥 Guests", font=("Arial", 12, "bold"))
        self.home_guests_label.grid(row=0, column=3, sticky="w")
        self.home_guests_entry = ctk.CTkEntry(search_grid, width=100, placeholder_text="Number of guests")
        self.home_guests_entry.grid(row=1, column=3, sticky="w")
        
        # Search Button
        self.home_search_btn = ctk.CTkButton(search_grid, text="Search Rooms", font=("Arial", 12, "bold"),
                                           fg_color="#FFC107", text_color="black", hover_color="#FFD54F",
                                           height=35, width=150, command=self.search_hotels)
        self.home_search_btn.grid(row=1, column=4, padx=(20, 0))
        
        # Popular Hotels Section
        self.home_hotels_section = ctk.CTkFrame(frame, fg_color="white")
        self.home_hotels_section.pack(fill="both", expand=True, padx=30, pady=10)
        ctk.CTkLabel(self.home_hotels_section, text="Popular Hotels",
                    font=("Arial", 20, "bold"), text_color="#2C3E50").pack(anchor="w", pady=(0, 15))
        
        self.home_canvas = Canvas(self.home_hotels_section, bg="white", highlightthickness=0)
        self.home_scrollbar = Scrollbar(self.home_hotels_section, orient="vertical", command=self.home_canvas.yview)
        self.home_scrollable_frame = ctk.CTkFrame(self.home_canvas, fg_color="white")
        
        self.home_scrollable_frame.bind("<Configure>", lambda e: self.home_canvas.configure(scrollregion=self.home_canvas.bbox("all")))
        self.home_canvas.create_window((0, 0), window=self.home_scrollable_frame, anchor="nw")
        self.home_canvas.configure(yscrollcommand=self.home_scrollbar.set)
        
        self.home_canvas.pack(side="left", fill="both", expand=True)
        self.home_scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            self.home_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.home_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        return frame

    def search_hotels(self):
        """Search for hotels based on criteria"""
        location = self.home_location_entry.get()
        check_in = self.home_checkin_entry.get_date() if hasattr(self.home_checkin_entry, 'get_date') else self.home_checkin_entry.get()
        check_out = self.home_checkout_entry.get_date() if hasattr(self.home_checkout_entry, 'get_date') else self.home_checkout_entry.get()
        guests = self.home_guests_entry.get()
        
        if not location:
            messagebox.showwarning("Search Error", "Please enter a location.")
            return
        
        try:
            if isinstance(check_in, str) and check_in:
                check_in = datetime.strptime(check_in, "%m/%d/%Y")
            if isinstance(check_out, str) and check_out:
                check_out = datetime.strptime(check_out, "%m/%d/%Y")
                
            if check_in and check_out and check_in >= check_out:
                messagebox.showwarning("Date Error", "Check-out date must be after check-in date.")
                return
                
            if guests and not guests.isdigit():
                messagebox.showwarning("Input Error", "Number of guests must be a number.")
                return
            
            for widget in self.home_scrollable_frame.winfo_children():
                widget.destroy()
            
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT h.Hotel_ID, h.hotel_name, h.location, h.description, h.star_rating, h.image_path,
                       MIN(rc.base_price) as min_price
                FROM Hotel h
                LEFT JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
                WHERE h.location LIKE %s
            """
            params = [f"%{location}%"]
            
            if check_in and check_out:
                query += """
                    AND EXISTS (
                        SELECT 1 FROM Room r
                        WHERE r.Room_ID = rc.Category_ID
                        AND r.Availability_status = 'Available'
                    )
                """
            
            query += " GROUP BY h.Hotel_ID ORDER BY h.star_rating DESC, min_price"
            
            cursor.execute(query, params)
            hotels_data = cursor.fetchall()
            
            if hotels_data:
                for hotel in hotels_data:
                    cursor.execute(
                        """
                        SELECT GROUP_CONCAT(CONCAT(a.amenity_icon, ' ', a.amenity_name) SEPARATOR ' | ') as amenities
                        FROM Hotel_Amenities ha
                        JOIN Amenities a ON ha.Amenity_ID = a.Amenity_ID
                        WHERE ha.Hotel_ID = %s
                        LIMIT 3
                        """, (hotel['Hotel_ID'],)
                    )
                    amenities_result = cursor.fetchone()
                    amenities = amenities_result['amenities'] if amenities_result and amenities_result['amenities'] else "📶 Free WiFi | 🏊 Pool | 🚗 Free Parking"
                    
                    price = f"${hotel['min_price']:.2f} per night" if hotel['min_price'] else "Price on request"
                    description = f"{hotel['description'][:100]}..." if hotel['description'] else "Beautiful hotel in a prime location."
                    
                    hotel_data = (hotel['hotel_name'], description, amenities, price, hotel['image_path'], hotel['Hotel_ID'])
                    card = self.create_hotel_card(self.home_scrollable_frame, hotel_data)
                    card.pack(anchor="w", padx=10, pady=10, fill="x")
            else:
                ctk.CTkLabel(self.home_scrollable_frame, text="No hotels found matching your criteria.",
                            font=("Arial", 14), text_color="gray").pack(pady=50)
                
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Search failed: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def load_popular_hotels(self):
        """Load popular hotels from the database"""
        for widget in self.home_scrollable_frame.winfo_children():
            widget.destroy()
        
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT h.Hotel_ID, h.hotel_name, h.location, h.description, h.star_rating, h.image_path,
                       MIN(rc.base_price) as min_price
                FROM Hotel h
                LEFT JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
                GROUP BY h.Hotel_ID
                ORDER BY h.star_rating DESC, min_price
                LIMIT 6
                """
            )
            hotels_data = cursor.fetchall()
            
            for hotel in hotels_data:
                cursor.execute(
                    """
                    SELECT GROUP_CONCAT(CONCAT(a.amenity_icon, ' ', a.amenity_name) SEPARATOR ' | ') as amenities
                    FROM Hotel_Amenities ha
                    JOIN Amenities a ON ha.Amenity_ID = a.Amenity_ID
                    WHERE ha.Hotel_ID = %s
                    LIMIT 3
                    """, (hotel['Hotel_ID'],)
                )
                amenities_result = cursor.fetchone()
                amenities = amenities_result['amenities'] if amenities_result and amenities_result['amenities'] else "📶 Free WiFi | 🏊 Pool | 🚗 Free Parking"
                
                price = f"${hotel['min_price']:.2f} per night" if hotel['min_price'] else "Price on request"
                description = f"{hotel['description'][:100]}..." if hotel['description'] else "Beautiful hotel in a prime location."
                
                hotel_data = (hotel['hotel_name'], description, amenities, price, hotel['image_path'], hotel['Hotel_ID'])
                card = self.create_hotel_card(self.home_scrollable_frame, hotel_data)
                card.pack(anchor="w", padx=10, pady=10, fill="x")
                
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Could not load hotels: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def create_hotel_card(self, parent, hotel_data):
        """Create a hotel card widget"""
        name, description, amenities, price, image_path, hotel_id = hotel_data
        card = ctk.CTkFrame(parent, fg_color="white", border_width=1, border_color="#D5D8DC", height=250)
        
        if image_path and os.path.exists(image_path):
            try:
                hotel_image = Image.open(image_path)
                hotel_image = hotel_image.resize((260, 120), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(hotel_image)
                image_label = ctk.CTkLabel(card, text="", image=photo, fg_color="white")
                image_label.image = photo
                image_label.pack(anchor="center", padx=10, pady=(10, 5))
            except Exception as e:
                print(f"Error loading hotel image: {e}")
                ctk.CTkLabel(card, text=name, font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(20,5))
        else:
            ctk.CTkLabel(card, text=name, font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(20,5))
        
        if image_path and os.path.exists(image_path):
            ctk.CTkLabel(card, text=name, font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(5,5))
            
        ctk.CTkLabel(card, text=description, font=("Arial", 10), wraplength=650).pack(anchor="w", padx=10)
        ctk.CTkLabel(card, text=amenities, font=("Arial", 9), wraplength=650).pack(anchor="w", padx=10, pady=(5,0))
        
        price_frame = ctk.CTkFrame(card, fg_color="white")
        price_frame.pack(anchor="w", fill="x", padx=10, pady=(5,10))
        ctk.CTkLabel(price_frame, text=price, font=("Arial", 10, "bold"), text_color="#1E90FF").pack(side="left")
        
        view_btn = ctk.CTkButton(price_frame, text="Book Now", font=("Arial", 10),
                               fg_color="#0F2D52", hover_color="#1E4D88",
                               width=80, height=25, corner_radius=5,
                               command=lambda: self.view_hotel_details(hotel_id))
        view_btn.pack(side="right", padx=10)
        
        return card

    def view_hotel_details(self, hotel_id):
        """Navigate to the book frame with selected hotel"""
        self.selected_hotel_id = hotel_id
        self.load_hotel_details(hotel_id)
        self.show_frame('book')

    # ------------------- Book Frame -------------------
    def create_book_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=0)
        
        # Hotel Header
        self.book_hotel_name_label = ctk.CTkLabel(frame, text="Luxury Grand Hotel",
                                                font=("Arial", 24, "bold"), text_color="#2C3E50")
        self.book_hotel_name_label.pack(anchor="w", padx=30, pady=(30, 5))
        
        self.book_hotel_location_label = ctk.CTkLabel(frame, text="📍 123 Main Street, Mt. Pleasant, Michigan",
                                                    font=("Arial", 14))
        self.book_hotel_location_label.pack(anchor="w", padx=30, pady=(0, 20))
        
        # Booking Form and Summary
        booking_container = ctk.CTkFrame(frame, fg_color="transparent")
        booking_container.pack(fill="both", expand=True, padx=30)
        
        # Form Frame
        self.book_form_frame = ctk.CTkFrame(booking_container, fg_color="white", border_width=1,
                                          border_color="#E5E5E5", corner_radius=10)
        self.book_form_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)
        
        form_header = ctk.CTkFrame(self.book_form_frame, fg_color="white", height=50)
        form_header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(form_header, text="📅 Select Your Stay",
                    font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")
        
        form_content = ctk.CTkFrame(self.book_form_frame, fg_color="white")
        form_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Check-in
        self.book_checkin_label = ctk.CTkLabel(form_content, text="Check-in Date", font=("Arial", 14, "bold"))
        self.book_checkin_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        try:
            self.book_checkin_entry = DateEntry(form_content, width=12, background='darkblue',
                                              foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
            self.book_checkin_entry.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 15))
            self.book_checkin_entry.set_date(datetime.today())
        except:
            self.book_checkin_entry = ctk.CTkEntry(form_content, width=220, placeholder_text="mm/dd/yyyy")
            self.book_checkin_entry.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 15))
            self.book_checkin_entry.insert(0, datetime.today().strftime("%m/%d/%Y"))
        
        # Check-out
        self.book_checkout_label = ctk.CTkLabel(form_content, text="Check-out Date", font=("Arial", 14, "bold"))
        self.book_checkout_label.grid(row=0, column=1, sticky="w", padx=10, pady=(10, 5))
        try:
            self.book_checkout_entry = DateEntry(form_content, width=12, background='darkblue',
                                               foreground='white', borderwidth=2, date_pattern='mm/dd/yyyy')
            self.book_checkout_entry.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 15))
            self.book_checkout_entry.set_date(datetime.today() + timedelta(days=1))
        except:
            self.book_checkout_entry = ctk.CTkEntry(form_content, width=220, placeholder_text="mm/dd/yyyy")
            self.book_checkout_entry.grid(row=1, column=1, sticky="w", padx=10, pady=(0, 15))
            self.book_checkout_entry.insert(0, (datetime.today() + timedelta(days=1)).strftime("%m/%d/%Y"))
        
        # Guests
        self.book_guests_label = ctk.CTkLabel(form_content, text="Guests", font=("Arial", 14, "bold"))
        self.book_guests_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 5))
        self.book_guests_entry = ctk.CTkEntry(form_content, width=220, placeholder_text="Number of guests")
        self.book_guests_entry.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 15))
        self.book_guests_entry.insert(0, "1")
        
        # Room Type
        self.book_room_type_label = ctk.CTkLabel(form_content, text="Room Type", font=("Arial", 14, "bold"))
        self.book_room_type_label.grid(row=2, column=1, sticky="w", padx=10, pady=(10, 5))
        self.book_room_type_dropdown = ctk.CTkComboBox(form_content, width=220,
                                                    values=["Select a room"])
        self.book_room_type_dropdown.grid(row=3, column=1, sticky="w", padx=10, pady=(0, 15))
        self.book_room_type_dropdown.bind("<<ComboboxSelected>>", self.update_booking_summary)
        
        # Payment Method
        self.book_payment_label = ctk.CTkLabel(form_content, text="💳 Payment Method", font=("Arial", 18, "bold"))
        self.book_payment_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=(20, 10))
        self.book_payment_var = ctk.StringVar(value="Credit/Debit Card")
        self.book_card_radio = ctk.CTkRadioButton(form_content, text="Credit/Debit Card",
                                               variable=self.book_payment_var, value="Credit/Debit Card",
                                               font=("Arial", 14))
        self.book_card_radio.grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.book_paypal_radio = ctk.CTkRadioButton(form_content, text="PayPal",
                                                  variable=self.book_payment_var, value="PayPal",
                                                  font=("Arial", 14))
        self.book_paypal_radio.grid(row=5, column=1, sticky="w", padx=10, pady=5)
        
        # Confirm Button
        self.book_confirm_btn = ctk.CTkButton(form_content, text="Confirm Booking",
                                            font=("Arial", 14, "bold"),
                                            fg_color="#FFC107", text_color="black",
                                            hover_color="#FFD54F", height=45, width=280,
                                            command=self.confirm_booking)
        self.book_confirm_btn.grid(row=6, column=0, columnspan=2, pady=30)
        
        # Summary Frame
        self.book_summary_frame = ctk.CTkFrame(booking_container, fg_color="white", border_width=1,
                                            border_color="#E5E5E5", corner_radius=10, width=300)
        self.book_summary_frame.pack(side="right", fill="y", padx=(10, 0), pady=10)
        self.book_summary_frame.pack_propagate(False)
        
        summary_header = ctk.CTkFrame(self.book_summary_frame, fg_color="white", height=50)
        summary_header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(summary_header, text="📝 Booking Summary",
                    font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")
        
        self.book_summary_content = ctk.CTkFrame(self.book_summary_frame, fg_color="white")
        self.book_summary_content.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.book_summary_hotel_label = ctk.CTkLabel(self.book_summary_content, text="Hotel: Luxury Grand Hotel",
                                                   font=("Arial", 14), anchor="w")
        self.book_summary_hotel_label.pack(anchor="w", pady=3)
        self.book_summary_location_label = ctk.CTkLabel(self.book_summary_content, text="Location: New York, USA",
                                                      font=("Arial", 14), anchor="w")
        self.book_summary_location_label.pack(anchor="w", pady=3)
        self.book_summary_room_label = ctk.CTkLabel(self.book_summary_content, text="Room Type: Single Room",
                                                  font=("Arial", 14), anchor="w")
        self.book_summary_room_label.pack(anchor="w", pady=3)
        self.book_summary_price_label = ctk.CTkLabel(self.book_summary_content, text="Price per Night: $150",
                                                   font=("Arial", 14), anchor="w")
        self.book_summary_price_label.pack(anchor="w", pady=3)
        self.book_summary_nights_label = ctk.CTkLabel(self.book_summary_content, text="Total Nights: 1",
                                                    font=("Arial", 14), anchor="w")
        self.book_summary_nights_label.pack(anchor="w", pady=3)
        
        total_price_frame = ctk.CTkFrame(self.book_summary_content, fg_color="white", height=50)
        total_price_frame.pack(fill="x", pady=(20, 10))
        self.book_summary_total_label = ctk.CTkLabel(total_price_frame, text="Total Price: $150.00",
                                                   font=("Arial", 16, "bold"), text_color="#2C3E50")
        self.book_summary_total_label.pack(anchor="w")
        
        return frame

    def load_hotel_details(self, hotel_id):
        """Load hotel details from database"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT h.Hotel_ID, h.hotel_name, h.location, h.description, h.star_rating, h.image_path
                FROM Hotel h
                WHERE h.Hotel_ID = %s
                """, (hotel_id,)
            )
            hotel_data = cursor.fetchone()
            
            if hotel_data:
                self.book_hotel_name_label.configure(text=hotel_data['hotel_name'])
                self.book_hotel_location_label.configure(text=f"📍 {hotel_data['location']}")
                
                cursor.execute(
                    """
                    SELECT Category_ID as Room_ID, category_name as Room_Type,
                           base_price as Price_per_Night, 'Available' as Availability_status
                    FROM RoomCategory rc
                    WHERE rc.Hotel_ID = %s
                    """, (hotel_id,)
                )
                room_types = cursor.fetchall()
                
                self.room_prices = {room['Room_Type']: room['Price_per_Night'] for room in room_types}
                room_type_options = [f"{room['Room_Type']} - ${room['Price_per_Night']}/night" for room in room_types]
                
                if room_type_options:
                    self.book_room_type_dropdown.configure(values=room_type_options)
                    self.book_room_type_dropdown.set(room_type_options[0])
                    self.update_booking_summary()
                else:
                    self.book_room_type_dropdown.configure(values=["No rooms available"])
                    self.book_room_type_dropdown.set("No rooms available")
                    
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def calculate_total_price(self):
        """Calculate the total price based on room type and nights"""
        try:
            room_selection = self.book_room_type_dropdown.get()
            if "No rooms available" in room_selection:
                return 0, 0
                
            room_type = room_selection.split(" - $")[0]
            price_per_night = self.room_prices.get(room_type, 0)
            
            check_in = self.book_checkin_entry.get_date() if hasattr(self.book_checkin_entry, 'get_date') else self.book_checkin_entry.get()
            check_out = self.book_checkout_entry.get_date() if hasattr(self.book_checkout_entry, 'get_date') else self.book_checkout_entry.get()
            
            if not check_in or not check_out:
                return 0, 0
                
            if isinstance(check_in, str):
                check_in = datetime.strptime(check_in, "%m/%d/%Y")
            if isinstance(check_out, str):
                check_out = datetime.strptime(check_out, "%m/%d/%Y")
                
            nights = (check_out - check_in).days
            if nights < 1:
                return 0, 0
                
            return price_per_night * nights, nights
            
        except Exception as e:
            print(f"Error calculating price: {e}")
            return 0, 0

    def update_booking_summary(self, event=None):
        """Update the booking summary based on selected options"""
        room_selection = self.book_room_type_dropdown.get()
        if "No rooms available" in room_selection:
            room_type = "N/A"
            price_per_night = 0
        else:
            parts = room_selection.split(" - $")
            room_type = parts[0]
            price_per_night = float(parts[1].split("/")[0])
        
        total_price, nights = self.calculate_total_price()
        
        self.book_summary_hotel_label.configure(text=f"Hotel: {self.book_hotel_name_label.cget('text')}")
        self.book_summary_location_label.configure(text=f"Location: {self.book_hotel_location_label.cget('text').replace('📍 ', '')}")
        self.book_summary_room_label.configure(text=f"Room Type: {room_type}")
        self.book_summary_price_label.configure(text=f"Price per Night: ${price_per_night}")
        self.book_summary_nights_label.configure(text=f"Total Nights: {nights if nights else 0}")
        self.book_summary_total_label.configure(text=f"Total Price: ${total_price:.2f}" if total_price else "Total Price: $0.00")

    def confirm_booking(self):
        """Process the booking confirmation"""
        if not self.current_user:
            messagebox.showwarning("Login Required", "Please log in to book a room")
            self.show_frame('home')
            return
            
        check_in = self.book_checkin_entry.get_date() if hasattr(self.book_checkin_entry, 'get_date') else self.book_checkin_entry.get()
        check_out = self.book_checkout_entry.get_date() if hasattr(self.book_checkout_entry, 'get_date') else self.book_checkout_entry.get()
        guests = self.book_guests_entry.get()
        room_selection = self.book_room_type_dropdown.get()
        payment_method = self.book_payment_var.get()
        
        if not check_in or not check_out or not guests or "No rooms available" in room_selection:
            messagebox.showwarning("Input Error", "Please fill in all required fields")
            return
            
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
                
        if check_in >= check_out:
            messagebox.showwarning("Date Error", "Check-out date must be after check-in date")
            return
            
        try:
            guests_count = int(guests)
            if guests_count < 1:
                messagebox.showwarning("Input Error", "Invalid number of guests")
                return
        except ValueError:
            messagebox.showwarning("Input Error", "Number of guests must be a number")
            return
            
        room_type = room_selection.split(" - $")[0]
        total_price, nights = self.calculate_total_price()
        
        confirm = messagebox.askyesno("Confirm Booking",
                                    f"Do you want to confirm this booking?\n\n"
                                    f"Hotel: {self.book_hotel_name_label.cget('text')}\n"
                                    f"Room Type: {room_type}\n"
                                    f"Check-in: {check_in.strftime('%m/%d/%Y')}\n"
                                    f"Check-out: {check_out.strftime('%m/%d/%Y')}\n"
                                    f"Guests: {guests}\n"
                                    f"Total Price: ${total_price:.2f}\n"
                                    f"Payment Method: {payment_method}")
        
        if not confirm:
            return
            
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT Category_ID as Room_ID
                FROM RoomCategory
                WHERE category_name = %s AND Hotel_ID = %s LIMIT 1
                """, (room_type, self.selected_hotel_id)
            )
            room_result = cursor.fetchone()
            
            if not room_result:
                messagebox.showerror("Booking Error", "Selected room is no longer available")
                return
                
            room_id = room_result[0]
            
            cursor.execute("SHOW COLUMNS FROM Booking LIKE 'Guests'")
            has_guests_column = cursor.fetchone() is not None
            
            if has_guests_column:
                cursor.execute(
                    """
                    INSERT INTO Booking (User_ID, Room_ID, Check_IN_Date, Check_Out_Date,
                                      Total_Cost, Booking_Status, Guests)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (self.current_user['user_id'], room_id, check_in.strftime('%Y-%m-%d'),
                         check_out.strftime('%Y-%m-%d'), total_price, 'Confirmed', guests_count)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO Booking (User_ID, Room_ID, Check_IN_Date, Check_Out_Date,
                                      Total_Cost, Booking_Status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """, (self.current_user['user_id'], room_id, check_in.strftime('%Y-%m-%d'),
                         check_out.strftime('%Y-%m-%d'), total_price, 'Confirmed')
                )
                
            cursor.execute(
                "UPDATE Room SET Availability_status = 'Booked' WHERE Room_ID = %s", (room_id,)
            )
            
            connection.commit()
            messagebox.showinfo("Success", "Booking confirmed successfully!")
            self.show_frame('bookings')
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    # ------------------- Bookings Frame -------------------
    def create_bookings_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=0)
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=50)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header_frame, text="My Bookings",
                    font=("Arial", 24, "bold"), text_color="#2C3E50").pack(anchor="w")
        
        # Bookings Section
        self.bookings_section = ctk.CTkFrame(frame, fg_color="white")
        self.bookings_section.pack(fill="both", expand=True, padx=30, pady=10)
        
        self.bookings_canvas = Canvas(self.bookings_section, bg="white", highlightthickness=0)
        self.bookings_scrollbar = Scrollbar(self.bookings_section, orient="vertical", command=self.bookings_canvas.yview)
        self.bookings_scrollable_frame = ctk.CTkFrame(self.bookings_canvas, fg_color="white")
        
        self.bookings_scrollable_frame.bind("<Configure>", lambda e: self.bookings_canvas.configure(scrollregion=self.bookings_canvas.bbox("all")))
        self.bookings_canvas.create_window((0, 0), window=self.bookings_scrollable_frame, anchor="nw")
        self.bookings_canvas.configure(yscrollcommand=self.bookings_scrollbar.set)
        
        self.bookings_canvas.pack(side="left", fill="both", expand=True)
        self.bookings_scrollbar.pack(side="right", fill="y")
        
        def on_mousewheel(event):
            self.bookings_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.bookings_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        return frame

    def load_user_bookings(self):
        """Load the current user's bookings from the database"""
        if not self.current_user:
            logging.warning("No current user in load_user_bookings")
            return []
            
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT b.Booking_ID, b.Check_IN_Date, b.Check_Out_Date,
                       b.Total_Cost, b.Booking_Status, b.Guests,
                       r.Room_Type, r.Price_per_Night, h.hotel_name, h.location, h.image_path
                FROM Booking b
                JOIN Room r ON b.Room_ID = r.Room_ID
                JOIN RoomCategory rc ON r.Room_ID = rc.Category_ID
                JOIN Hotel h ON rc.Hotel_ID = h.Hotel_ID
                WHERE b.User_ID = %s
                ORDER BY b.Check_IN_Date DESC
                """, (self.current_user['user_id'],)
            )
            bookings = cursor.fetchall()
            logging.debug(f"Loaded user bookings: {bookings}")
            return bookings
        except mysql.connector.Error as err:
            logging.error(f"Could not load bookings: {err}")
            messagebox.showerror("Database Error", f"Could not load bookings: {err}")
            return []
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def populate_bookings(self):
        """Populate the bookings section with booking cards"""
        for widget in self.bookings_scrollable_frame.winfo_children():
            widget.destroy()
            
        bookings = self.load_user_bookings()
        if bookings:
            for booking in bookings:
                card = self.create_booking_card(self.bookings_scrollable_frame, booking)
                card.pack(fill="x", padx=0, pady=10)
        else:
            no_bookings_frame = ctk.CTkFrame(self.bookings_scrollable_frame, fg_color="white")
            no_bookings_frame.pack(fill="both", expand=True, padx=20, pady=50)
            ctk.CTkLabel(no_bookings_frame, text="You don't have any bookings yet.",
                        font=("Arial", 16), text_color="gray").pack(pady=10)
            ctk.CTkButton(no_bookings_frame, text="Browse Hotels", font=("Arial", 14),
                         fg_color="#1E90FF", hover_color="#1872BB", width=150, height=40,
                         command=lambda: self.show_frame('home')).pack(pady=10)

    def create_booking_card(self, parent, booking_data):
        """Create a card widget for a booking"""
        card = ctk.CTkFrame(parent, fg_color="white", border_width=1, border_color="#D5D8DC", height=200)
        
        hotel_name = booking_data.get('hotel_name', "Hotel")
        room_type = booking_data.get('Room_Type', "Room")
        check_in = booking_data['Check_IN_Date'].strftime("%m/%d/%Y") if isinstance(booking_data['Check_IN_Date'], datetime) else str(booking_data.get('Check_IN_Date', "N/A"))
        check_out = booking_data['Check_Out_Date'].strftime("%m/%d/%Y") if isinstance(booking_data['Check_Out_Date'], datetime) else str(booking_data.get('Check_Out_Date', "N/A"))
        total_cost = booking_data.get('Total_Cost', 0)
        booking_status = booking_data.get('Booking_Status', "Unknown")
        guests = booking_data.get('Guests', 1)
        location = booking_data.get('location', "Location not available")
        image_path = booking_data.get('image_path', None)
        booking_id = booking_data.get('Booking_ID', 0)
        
        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)
        
        if image_path and os.path.exists(str(image_path)):
            try:
                hotel_image = Image.open(image_path)
                hotel_image = hotel_image.resize((150, 120), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(hotel_image)
                image_label = ctk.CTkLabel(card, text="", image=photo, fg_color="white")
                image_label.image = photo
                image_label.grid(row=0, column=0, rowspan=4, padx=(10, 15), pady=10, sticky="nw")
            except Exception as e:
                print(f"Error loading hotel image: {e}")
                ctk.CTkLabel(card, text=hotel_name, font=("Arial", 16, "bold")).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nw")
        else:
            ctk.CTkLabel(card, text=hotel_name, font=("Arial", 16, "bold")).grid(row=0, column=0, padx=10, pady=(10, 5), sticky="nw")
        
        hotel_info = ctk.CTkFrame(card, fg_color="transparent")
        hotel_info.grid(row=0, column=1, sticky="nw", padx=10, pady=(10, 5))
        ctk.CTkLabel(hotel_info, text=hotel_name, font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(hotel_info, text=f"📍 {location}", font=("Arial", 12)).pack(anchor="w")
        
        booking_details = ctk.CTkFrame(card, fg_color="transparent")
        booking_details.grid(row=1, column=1, sticky="nw", padx=10, pady=5)
        ctk.CTkLabel(booking_details, text=f"Room Type: {room_type}", font=("Arial", 12)).pack(anchor="w", pady=2)
        ctk.CTkLabel(booking_details, text=f"Dates: {check_in} to {check_out}", font=("Arial", 12)).pack(anchor="w", pady=2)
        ctk.CTkLabel(booking_details, text=f"Guests: {guests}", font=("Arial", 12)).pack(anchor="w", pady=2)
        
        status_frame = ctk.CTkFrame(card, fg_color="transparent")
        status_frame.grid(row=2, column=1, sticky="nw", padx=10, pady=5)
        status_color = "#27AE60" if booking_status == "Confirmed" else "#E74C3C"
        status_label = ctk.CTkLabel(status_frame, text=booking_status,
                                   font=("Arial", 14, "bold"), text_color=status_color)
        status_label.pack(anchor="w")
        status_frame.status_label = status_label
        
        try:
            total_cost_formatted = f"${float(total_cost):.2f}"
        except (ValueError, TypeError):
            total_cost_formatted = f"${total_cost}" if total_cost else "$0.00"
        ctk.CTkLabel(status_frame, text=f"Total Cost: {total_cost_formatted}",
                    font=("Arial", 14, "bold"), text_color="#1E90FF").pack(anchor="w")
        
        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.grid(row=3, column=1, sticky="se", padx=10, pady=10)
        if booking_status == "Confirmed":
            cancel_btn = ctk.CTkButton(button_frame, text="Cancel Booking",
                                     font=("Arial", 12), fg_color="#E74C3C", hover_color="#C0392B",
                                     width=120, height=30, corner_radius=5,
                                     command=lambda: self.cancel_booking(booking_id, card))
            cancel_btn.pack(side="right", padx=5)
        
        return card

    def cancel_booking(self, booking_id, booking_card):
        """Cancel a booking"""
        confirm = messagebox.askyesno("Cancel Booking",
                                     "Are you sure you want to cancel this booking?\nThis action cannot be undone.")
        if not confirm:
            return
            
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("SELECT Room_ID FROM Booking WHERE Booking_ID = %s", (booking_id,))
            room_result = cursor.fetchone()
            
            if not room_result:
                messagebox.showerror("Error", "Booking not found")
                return
                
            room_id = room_result[0]
            cursor.execute("UPDATE Booking SET Booking_Status = 'Cancelled' WHERE Booking_ID = %s", (booking_id,))
            cursor.execute("UPDATE Room SET Availability_status = 'Available' WHERE Room_ID = %s", (room_id,))
            
            connection.commit()
            messagebox.showinfo("Success", "Booking cancelled successfully")
            self.update_booking_card_status(booking_card, "Cancelled")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def update_booking_card_status(self, booking_card, new_status):
        """Update the status display on a booking card"""
        for child in booking_card.winfo_children():
            if hasattr(child, 'status_label'):
                child.status_label.configure(
                    text=new_status,
                    text_color="#E74C3C" if new_status == "Cancelled" else "#27AE60"
                )
                break

    # ------------------- User Frame -------------------
    def create_user_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=0)
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        ctk.CTkLabel(header_frame, text="User Management",
                    font=("Arial", 30, "bold"), text_color="#2C3E50").pack(anchor="center")
        
        # Profile Section
        self.user_profile_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1,
                                             border_color="#E5E5E5", corner_radius=10)
        self.user_profile_frame.pack(fill="x", padx=30, pady=(0, 20))
        
        profile_header = ctk.CTkFrame(self.user_profile_frame, fg_color="white", height=50)
        profile_header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(profile_header, text="👤 Edit Profile",
                    font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")
        
        self.user_profile_form = ctk.CTkFrame(self.user_profile_frame, fg_color="white")
        self.user_profile_form.pack(fill="x", padx=20, pady=(0, 20))
        
        form_left = ctk.CTkFrame(self.user_profile_form, fg_color="white")
        form_left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        form_right = ctk.CTkFrame(self.user_profile_form, fg_color="white")
        form_right.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(form_left, text="Full Name", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
        self.user_fullname_entry = ctk.CTkEntry(form_left, width=300, height=35)
        self.user_fullname_entry.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(form_left, text="Phone Number", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
        self.user_phone_entry = ctk.CTkEntry(form_left, width=300, height=35)
        self.user_phone_entry.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(form_right, text="Email Address", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
        self.user_email_entry = ctk.CTkEntry(form_right, width=300, height=35)
        self.user_email_entry.pack(anchor="w", pady=(0, 15))
        
        ctk.CTkLabel(form_right, text="Address", font=("Arial", 14)).pack(anchor="w", pady=(0, 5))
        self.user_address_entry = ctk.CTkEntry(form_right, width=300, height=35)
        self.user_address_entry.pack(anchor="w", pady=(0, 15))
        
        self.user_update_btn = ctk.CTkButton(self.user_profile_form, text="Update Profile",
                                           font=("Arial", 14, "bold"), fg_color="#007BFF", hover_color="#0069D9",
                                           height=35, width=150, command=self.update_profile)
        self.user_update_btn.pack(anchor="w", pady=(10, 0))
        
        # Booking History Section
        self.user_history_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1,
                                             border_color="#E5E5E5", corner_radius=10)
        self.user_history_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        history_header = ctk.CTkFrame(self.user_history_frame, fg_color="white", height=50)
        history_header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(history_header, text="🕒 Booking History",
                    font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")
        
        table_frame = ctk.CTkFrame(self.user_history_frame, fg_color="white")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = ('Booking ID', 'Hotel', 'Check-in', 'Check-out', 'Amount', 'Status')
        self.user_booking_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.user_booking_table.heading(col, text=col)
            if col == 'Booking ID':
                self.user_booking_table.column(col, width=100, anchor='w')
            elif col in ('Check-in', 'Check-out'):
                self.user_booking_table.column(col, width=120, anchor='center')
            elif col == 'Amount':
                self.user_booking_table.column(col, width=100, anchor='e')
            elif col == 'Status':
                self.user_booking_table.column(col, width=100, anchor='center')
            else:
                self.user_booking_table.column(col, width=200, anchor='w')
        
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.user_booking_table.yview)
        self.user_booking_table.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.user_booking_table.pack(fill="both", expand=True)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#FFFFFF", foreground="#333333", rowheight=25,
                       fieldbackground="#FFFFFF", borderwidth=0, font=('Arial', 10))
        style.configure("Treeview.Heading", font=('Arial', 12, 'bold'), background="#F0F0F0", foreground="#2C3E50")
        style.map('Treeview', background=[('selected', '#C8E5FF')])
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        
        return frame

    def populate_profile_fields(self):
        """Populate profile fields with user data"""
        if self.current_user:
            full_name = f"{self.current_user['first_name']} {self.current_user['last_name']}"
            self.user_fullname_entry.delete(0, 'end')
            self.user_fullname_entry.insert(0, full_name)
            self.user_email_entry.delete(0, 'end')
            self.user_email_entry.insert(0, self.current_user['email'] if self.current_user['email'] else "")
            self.user_phone_entry.delete(0, 'end')
            self.user_phone_entry.insert(0, self.current_user['phone'] if self.current_user.get('phone') else "")
            self.user_address_entry.delete(0, 'end')
            self.user_address_entry.insert(0, self.current_user['user_address'] if self.current_user.get('user_address') else "")

    def update_profile(self):
        """Update user profile information"""
        if not self.current_user:
            messagebox.showwarning("Login Required", "Please log in to update your profile")
            return
            
        full_name = self.user_fullname_entry.get()
        email = self.user_email_entry.get()
        phone = self.user_phone_entry.get()
        address = self.user_address_entry.get()
        
        if not full_name or not email:
            messagebox.showwarning("Input Error", "Name and email are required")
            return
            
        name_parts = full_name.split(maxsplit=1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE Users
                SET first_name = %s, last_name = %s, email = %s, phone = %s, user_address = %s
                WHERE user_id = %s
                """, (first_name, last_name, email, phone, address, self.current_user['user_id'])
            )
            connection.commit()
            
            self.current_user['first_name'] = first_name
            self.current_user['last_name'] = last_name
            self.current_user['email'] = email
            self.current_user['phone'] = phone
            self.current_user['user_address'] = address
            
            messagebox.showinfo("Success", "Profile updated successfully!")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def load_booking_history(self):
        """Load booking history from database"""
        logging.debug(f"Loading booking history for user: {self.current_user}")
        if not self.current_user:
            logging.warning("No current user in load_booking_history")
            return []
            
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT b.Booking_ID,
                       CONCAT(h.hotel_name, ' - ', r.Room_Type) as Room_Type,
                       b.Check_IN_Date, b.Check_Out_Date,
                       b.Total_Cost as Amount, b.Booking_Status as Status
                FROM Booking b
                JOIN Room r ON b.Room_ID = r.Room_ID
                JOIN RoomCategory rc ON r.Room_ID = rc.Category_ID
                JOIN Hotel h ON rc.Hotel_ID = h.Hotel_ID
                WHERE b.User_ID = %s
                ORDER BY b.Check_IN_Date DESC
                """, (self.current_user['user_id'],)
            )
            bookings = cursor.fetchall()
            logging.debug(f"Booking history loaded: {bookings}")
            return bookings
        except mysql.connector.Error as err:
            logging.error(f"Error loading booking history: {err}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error in load_booking_history: {e}")
            return []
        finally:
            if 'connection' in locals() and connection.is_connected():
                try:
                    cursor.close()
                    connection.close()
                except Exception as e:
                    logging.error(f"Error closing database connection: {e}")

    def populate_booking_table(self):
        """Populate the booking history table"""
        for row in self.user_booking_table.get_children():
            self.user_booking_table.delete(row)
            
        bookings = self.load_booking_history()
        if bookings:
            for booking in bookings:
                check_in = booking['Check_IN_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_IN_Date'], datetime) else booking['Check_IN_Date']
                check_out = booking['Check_Out_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_Out_Date'], datetime) else booking['Check_Out_Date']
                amount = f"${booking['Amount']}"
                self.user_booking_table.insert('', 'end', values=(
                    f"#{booking['Booking_ID']}",
                    booking['Room_Type'],
                    check_in,
                    check_out,
                    amount,
                    booking['Status']
                ))
        else:
            # Display a message if no bookings are found
            self.user_booking_table.insert('', 'end', values=(
                "", "No bookings found", "", "", "", ""
            ))

    # ------------------- Feedback Frame -------------------
    def create_feedback_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white", corner_radius=0)
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=100)
        header_frame.pack(fill="x", padx=30, pady=(30, 0))
        ctk.CTkLabel(header_frame, text="Give Your",
                    font=("Arial", 30, "bold"), text_color="#2C3E50").pack(anchor="center")
        ctk.CTkLabel(header_frame, text="Feedback",
                    font=("Arial", 30, "bold"), text_color="#2C3E50").pack(anchor="center")
        
        # Feedback Form
        self.feedback_form_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1,
                                              border_color="#E5E5E5", corner_radius=10)
        self.feedback_form_frame.pack(fill="both", expand=True, padx=100, pady=30)
        
        form_content = ctk.CTkFrame(self.feedback_form_frame, fg_color="white")
        form_content.pack(fill="both", expand=True, padx=30, pady=30)
        
        title_frame = ctk.CTkFrame(form_content, fg_color="white")
        title_frame.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(title_frame, text="💬 We Value Your Feedback",
                    font=("Arial", 20, "bold"), text_color="#2C3E50").pack(anchor="center")
        
        self.feedback_name_label = ctk.CTkLabel(form_content, text="👤 Full Name", font=("Arial", 14))
        self.feedback_name_label.pack(anchor="center", pady=(0, 5))
        self.feedback_name_entry = ctk.CTkEntry(form_content, width=400, height=40, placeholder_text="Enter your full name")
        self.feedback_name_entry.pack(anchor="center", pady=(0, 20))
        
        self.feedback_rating_label = ctk.CTkLabel(form_content, text="⭐ Rate Your Experience", font=("Arial", 14))
        self.feedback_rating_label.pack(anchor="center", pady=(0, 5))
        
        stars_frame = ctk.CTkFrame(form_content, fg_color="white", height=50)
        stars_frame.pack(fill="x", pady=(0, 20))
        self.star_buttons = []
        for i in range(1, 6):
            star_btn = ctk.CTkButton(stars_frame, text="☆", width=30, height=30,
                                    font=("Arial", 24), text_color="#B0B0B0",
                                    command=lambda i=i: self.set_rating(i))
            star_btn.pack(side="left", padx=5, expand=True)
            self.star_buttons.append(star_btn)
        
        self.feedback_text_label = ctk.CTkLabel(form_content, text="💭 Your Feedback", font=("Arial", 14))
        self.feedback_text_label.pack(anchor="center", pady=(0, 5))
        self.feedback_text = ctk.CTkTextbox(form_content, width=600, height=150,
                                          corner_radius=5, border_width=1, border_color="#E5E5E5")
        self.feedback_text.pack(anchor="center", pady=(0, 20))
        self.feedback_text.insert("1.0", "Write your feedback here...")
        self.feedback_text.bind("<FocusIn>", lambda e: self.feedback_text.delete("1.0", "end") if
                               self.feedback_text.get("1.0", "end-1c") == "Write your feedback here..." else None)
        
        self.feedback_submit_btn = ctk.CTkButton(form_content, text="Submit Feedback",
                                               font=("Arial", 14, "bold"), fg_color="#0F2D52", hover_color="#1E4D88",
                                               height=45, width=400, command=self.submit_feedback)
        self.feedback_submit_btn.pack(anchor="center", pady=(10, 0))
        
        if self.current_user:
            full_name = f"{self.current_user['first_name']} {self.current_user['last_name']}"
            self.feedback_name_entry.delete(0, 'end')
            self.feedback_name_entry.insert(0, full_name)
        
        return frame

    def set_rating(self, rating):
        """Set the selected rating value and update star appearance"""
        self.selected_rating = rating
        for i in range(1, 6):
            if i <= rating:
                self.star_buttons[i-1].configure(text="★", text_color="#FFD700", font=("Arial", 24))
            else:
                self.star_buttons[i-1].configure(text="☆", text_color="#B0B0B0", font=("Arial", 24))

    def submit_feedback(self):
        """Submit the feedback to the database"""
        name = self.feedback_name_entry.get()
        comment = self.feedback_text.get("1.0", "end-1c")
        
        if not name:
            messagebox.showwarning("Input Error", "Please enter your name.")
            return
            
        if self.selected_rating == 0:
            messagebox.showwarning("Input Error", "Please select a rating.")
            return
            
        if not comment or len(comment.strip()) < 5:
            messagebox.showwarning("Input Error", "Please provide feedback comments (minimum 5 characters).")
            return
            
        user_id = self.current_user['user_id'] if self.current_user else None
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO Review (User_ID, Rating, Comments, Review_Date)
                VALUES (%s, %s, %s, %s)
                """, (user_id, self.selected_rating, comment, datetime.now().strftime('%Y-%m-%d'))
            )
            connection.commit()
            messagebox.showinfo("Success", "Thank you for your feedback!")
            
            self.feedback_name_entry.delete(0, 'end')
            self.feedback_text.delete("1.0", "end")
            self.set_rating(0)
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", str(err))
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

# ------------------- Main Application Entry Point -------------------
if __name__ == "__main__":
    root = ctk.CTk()
    app = HotelBookingUserApp(root)
    root.mainloop()