import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import mysql.connector
import subprocess
import sys
import os
from PIL import Image, ImageTk
import shutil

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
selected_hotel = None
hotel_image_path = None

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

def go_to_manage_hotels():
    open_page("manage_hotels")

def logout():
    """Log out the current admin and return to login page"""
    global current_admin
    current_admin = None
    open_page("login")

# ------------------- Database Setup Functions -------------------
def setup_hotel_tables():
    """Create hotel-related tables if they don't exist"""
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Create Hotel table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Hotel (
                Hotel_ID INT AUTO_INCREMENT PRIMARY KEY,
                hotel_name VARCHAR(100) NOT NULL,
                location VARCHAR(100) NOT NULL,
                description TEXT,
                star_rating INT NOT NULL CHECK (star_rating BETWEEN 1 AND 5),
                image_path VARCHAR(255),
                created_by INT,
                FOREIGN KEY (created_by) REFERENCES Admin(Admin_ID) ON DELETE SET NULL
            )
        """)
        
        # Create RoomCategory table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS RoomCategory (
                Category_ID INT AUTO_INCREMENT PRIMARY KEY,
                Hotel_ID INT NOT NULL,
                category_name VARCHAR(50) NOT NULL,
                description TEXT,
                base_price DECIMAL(10, 2) NOT NULL,
                capacity INT NOT NULL,
                FOREIGN KEY (Hotel_ID) REFERENCES Hotel(Hotel_ID) ON DELETE CASCADE
            )
        """)
        
        # Create Amenities table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Amenities (
                Amenity_ID INT AUTO_INCREMENT PRIMARY KEY,
                amenity_name VARCHAR(50) NOT NULL,
                amenity_icon VARCHAR(20)
            )
        """)
        
        # Create Hotel_Amenities junction table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Hotel_Amenities (
                Hotel_ID INT NOT NULL,
                Amenity_ID INT NOT NULL,
                PRIMARY KEY (Hotel_ID, Amenity_ID),
                FOREIGN KEY (Hotel_ID) REFERENCES Hotel(Hotel_ID) ON DELETE CASCADE,
                FOREIGN KEY (Amenity_ID) REFERENCES Amenities(Amenity_ID) ON DELETE CASCADE
            )
        """)
        
        # Add some default amenities if Amenities table is empty
        cursor.execute("SELECT COUNT(*) FROM Amenities")
        amenities_count = cursor.fetchone()[0]
        
        if amenities_count == 0:
            amenities = [
                ("Free WiFi", "📶"),
                ("Swimming Pool", "🏊"),
                ("Free Parking", "🚗"),
                ("Restaurant", "🍽️"),
                ("Fitness Center", "💪"),
                ("Spa", "💆"),
                ("Room Service", "🛎️"),
                ("Air Conditioning", "❄️"),
                ("Bar", "🍹"),
                ("Conference Room", "👥"),
                ("Pet Friendly", "🐾"),
                ("Laundry", "👕"),
                ("Beach Access", "🏖️")
            ]
            
            cursor.executemany(
                "INSERT INTO Amenities (amenity_name, amenity_icon) VALUES (%s, %s)",
                amenities
            )
        
        # Ensure the image directory exists
        if not os.path.exists("hotel_images"):
            os.makedirs("hotel_images")
        
        connection.commit()
        return True
        
    except mysql.connector.Error as err:
        print(f"Database setup error: {err}")
        messagebox.showerror("Database Error", f"Error setting up hotel tables: {err}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Hotel Management Functions -------------------
def load_hotels():
    """Load all hotels from database"""
    hotels = []
    
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get hotels with room count and price range
        cursor.execute(
            """
            SELECT h.Hotel_ID, h.hotel_name, h.location, h.description, h.star_rating, h.image_path,
                   COUNT(rc.Category_ID) as room_categories,
                   MIN(rc.base_price) as min_price,
                   MAX(rc.base_price) as max_price
            FROM Hotel h
            LEFT JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
            GROUP BY h.Hotel_ID
            ORDER BY h.hotel_name
            """
        )
        
        hotels = cursor.fetchall()
        return hotels
        
    except mysql.connector.Error as err:
        print(f"Error loading hotels: {err}")
        messagebox.showerror("Database Error", f"Error loading hotels: {err}")
        return []
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def load_hotel_details(hotel_id):
    """Load details for a specific hotel"""
    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        
        # Query to get hotel details
        cursor.execute(
            """
            SELECT h.*
            FROM Hotel h
            WHERE h.Hotel_ID = %s
            """,
            (hotel_id,)
        )
        
        hotel = cursor.fetchone()
        
        if hotel:
            # Get room categories for this hotel
            cursor.execute(
                """
                SELECT rc.*
                FROM RoomCategory rc
                WHERE rc.Hotel_ID = %s
                ORDER BY rc.base_price
                """,
                (hotel_id,)
            )
            hotel['room_categories'] = cursor.fetchall()
            
            # Get amenities for this hotel
            cursor.execute(
                """
                SELECT a.*
                FROM Amenities a
                JOIN Hotel_Amenities ha ON a.Amenity_ID = ha.Amenity_ID
                WHERE ha.Hotel_ID = %s
                ORDER BY a.amenity_name
                """,
                (hotel_id,)
            )
            hotel['amenities'] = cursor.fetchall()
            
            # Get all available amenities (for editing)
            cursor.execute("SELECT * FROM Amenities ORDER BY amenity_name")
            hotel['all_amenities'] = cursor.fetchall()
        
        return hotel
        
    except mysql.connector.Error as err:
        print(f"Error loading hotel details: {err}")
        messagebox.showerror("Database Error", f"Error loading hotel details: {err}")
        return None
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def save_hotel_image(source_path):
    """Save hotel image to the hotel_images directory"""
    if not source_path:
        return None
        
    try:
        # Create hotel_images directory if it doesn't exist
        if not os.path.exists("hotel_images"):
            os.makedirs("hotel_images")
            
        # Generate a unique filename
        filename = os.path.basename(source_path)
        base_name, ext = os.path.splitext(filename)
        unique_name = f"{base_name}_{len(os.listdir('hotel_images'))}{ext}"
        destination = os.path.join("hotel_images", unique_name)
        
        # Copy the image file
        shutil.copy2(source_path, destination)
        
        return destination
    except Exception as e:
        print(f"Error saving image: {e}")
        messagebox.showerror("Image Error", f"Error saving hotel image: {e}")
        return None

def create_hotel():
    """Create a new hotel"""
    global hotel_image_path
    
    # Get data from entry fields
    hotel_name = hotel_name_entry.get()
    location = location_entry.get()
    description = description_text.get("1.0", "end-1c")
    
    try:
        star_rating = int(star_rating_var.get())
    except ValueError:
        messagebox.showwarning("Input Error", "Please select a valid star rating (1-5)")
        return
    
    # Validate input
    if not hotel_name or not location:
        messagebox.showwarning("Input Error", "Hotel name and location are required")
        return
    
    # Save the image if one was selected
    image_path = None
    if hotel_image_path:
        image_path = save_hotel_image(hotel_image_path)
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Insert new hotel
        cursor.execute(
            """
            INSERT INTO Hotel (hotel_name, location, description, star_rating, image_path, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (hotel_name, location, description, star_rating, image_path, current_admin['Admin_ID'])
        )
        
        # Get the new hotel ID
        hotel_id = cursor.lastrowid
        
        # Get selected amenities
        selected_amenities = []
        for amenity_id, var in amenity_vars.items():
            if var.get() == 1:
                selected_amenities.append(amenity_id)
        
        # Insert hotel-amenity relationships
        if selected_amenities:
            amenity_values = [(hotel_id, amenity_id) for amenity_id in selected_amenities]
            cursor.executemany(
                "INSERT INTO Hotel_Amenities (Hotel_ID, Amenity_ID) VALUES (%s, %s)",
                amenity_values
            )
        
        connection.commit()
        messagebox.showinfo("Success", "Hotel created successfully")
        
        # Clear form fields
        clear_hotel_form()
        
        # Refresh hotel table
        populate_hotel_table()
        
    except mysql.connector.Error as err:
        print(f"Error creating hotel: {err}")
        messagebox.showerror("Database Error", f"Error creating hotel: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def update_hotel():
    """Update an existing hotel"""
    global selected_hotel, hotel_image_path
    
    if not selected_hotel:
        messagebox.showwarning("Selection Error", "No hotel selected")
        return
    
    # Get data from entry fields
    hotel_name = hotel_name_entry.get()
    location = location_entry.get()
    description = description_text.get("1.0", "end-1c")
    
    try:
        star_rating = int(star_rating_var.get())
    except ValueError:
        messagebox.showwarning("Input Error", "Please select a valid star rating (1-5)")
        return
    
    # Validate input
    if not hotel_name or not location:
        messagebox.showwarning("Input Error", "Hotel name and location are required")
        return
    
    # Handle image update
    image_path = selected_hotel['image_path']
    if hotel_image_path:
        new_image_path = save_hotel_image(hotel_image_path)
        if new_image_path:
            image_path = new_image_path
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Update hotel data
        cursor.execute(
            """
            UPDATE Hotel
            SET hotel_name = %s, location = %s, description = %s, 
                star_rating = %s, image_path = %s
            WHERE Hotel_ID = %s
            """,
            (hotel_name, location, description, star_rating, 
             image_path, selected_hotel['Hotel_ID'])
        )
        
        # Update amenities
        # First remove all existing amenities for this hotel
        cursor.execute(
            "DELETE FROM Hotel_Amenities WHERE Hotel_ID = %s",
            (selected_hotel['Hotel_ID'],)
        )
        
        # Add selected amenities
        selected_amenities = []
        for amenity_id, var in amenity_vars.items():
            if var.get() == 1:
                selected_amenities.append(amenity_id)
        
        if selected_amenities:
            amenity_values = [(selected_hotel['Hotel_ID'], amenity_id) for amenity_id in selected_amenities]
            cursor.executemany(
                "INSERT INTO Hotel_Amenities (Hotel_ID, Amenity_ID) VALUES (%s, %s)",
                amenity_values
            )
        
        connection.commit()
        messagebox.showinfo("Success", "Hotel updated successfully")
        
        # Refresh hotel data
        selected_hotel = load_hotel_details(selected_hotel['Hotel_ID'])
        
        # Update hotel details display
        show_hotel_details()
        
        # Refresh hotel table
        populate_hotel_table()
        
    except mysql.connector.Error as err:
        print(f"Error updating hotel: {err}")
        messagebox.showerror("Database Error", f"Error updating hotel: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def delete_hotel():
    """Delete a hotel (with confirmation)"""
    #global selected_hotel
    
    if not selected_hotel:
        messagebox.showwarning("Selection Error", "No hotel selected")
        return
    
    # Confirm deletion
    confirmed = messagebox.askyesno(
        "Confirm Deletion",
        f"Are you sure you want to delete the hotel '{selected_hotel['hotel_name']}'?\n\n"
        f"This will also delete all room categories and amenity associations.\n"
        f"This action cannot be undone."
    )
    
    if not confirmed:
        return
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Delete the hotel (will cascade to room categories and amenity associations)
        cursor.execute("DELETE FROM Hotel WHERE Hotel_ID = %s", (selected_hotel['Hotel_ID'],))
        
        connection.commit()
        messagebox.showinfo("Success", "Hotel deleted successfully")
        
        # Clear form and details
        clear_hotel_form()
        hide_hotel_details()
        
        # Reset selected hotel
        selected_hotel = None
        
        # Refresh hotel table
        populate_hotel_table()
        
    except mysql.connector.Error as err:
        print(f"Error deleting hotel: {err}")
        messagebox.showerror("Database Error", f"Error deleting hotel: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def add_room_category():
    """Add a room category to the selected hotel"""
    #global selected_hotel
    
    if not selected_hotel:
        messagebox.showwarning("Selection Error", "No hotel selected")
        return
    
    # Create a new dialog window for room category details
    dialog = ctk.CTkToplevel(app)
    dialog.title("Add Room Category")
    dialog.geometry("400x400")
    dialog.resizable(False, False)
    dialog.transient(app)  # Set as transient to app window
    dialog.grab_set()  # Make dialog modal
    
    # Room category form
    form_frame = ctk.CTkFrame(dialog, fg_color="white")
    form_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Category name
    ctk.CTkLabel(form_frame, text="Category Name *", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
    category_name_entry = ctk.CTkEntry(form_frame, height=35)
    category_name_entry.pack(fill="x", pady=(0, 15))
    
    # Description
    ctk.CTkLabel(form_frame, text="Description", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
    description_text = ctk.CTkTextbox(form_frame, height=100)
    description_text.pack(fill="x", pady=(0, 15))
    
    # Base price
    ctk.CTkLabel(form_frame, text="Base Price ($) *", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
    price_entry = ctk.CTkEntry(form_frame, height=35)
    price_entry.pack(fill="x", pady=(0, 15))
    
    # Capacity
    ctk.CTkLabel(form_frame, text="Capacity (guests) *", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
    capacity_entry = ctk.CTkEntry(form_frame, height=35)
    capacity_entry.pack(fill="x", pady=(0, 15))
    
    # Submit button
    def save_category():
        # Get data from entry fields
        category_name = category_name_entry.get()
        description = description_text.get("1.0", "end-1c")
        
        try:
            base_price = float(price_entry.get())
            capacity = int(capacity_entry.get())
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter valid price and capacity values")
            return
        
        # Validate input
        if not category_name or base_price <= 0 or capacity <= 0:
            messagebox.showwarning("Input Error", "Category name, price, and capacity are required")
            return
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Insert new room category
            cursor.execute(
                """
                INSERT INTO RoomCategory (Hotel_ID, category_name, description, base_price, capacity)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (selected_hotel['Hotel_ID'], category_name, description, base_price, capacity)
            )
            
            connection.commit()
            messagebox.showinfo("Success", "Room category added successfully")
            
            # Close the dialog
            dialog.destroy()
            
            # Refresh hotel details
            #global selected_hotel
            selected_hotel = load_hotel_details(selected_hotel['Hotel_ID'])
            show_hotel_details()
            
        except mysql.connector.Error as err:
            print(f"Error adding room category: {err}")
            messagebox.showerror("Database Error", f"Error adding room category: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    submit_btn = ctk.CTkButton(form_frame, text="Save Category", font=("Arial", 12, "bold"), 
                              fg_color="#2C3E50", hover_color="#1E4D88",
                              command=save_category, height=40)
    submit_btn.pack(pady=(15, 0))

def edit_room_category(category_id):
    """Edit a room category"""
    #global selected_hotel
    
    if not selected_hotel or not category_id:
        messagebox.showwarning("Selection Error", "No category selected")
        return
    
    # Find the category in the selected hotel's room_categories
    category = None
    for cat in selected_hotel['room_categories']:
        if cat['Category_ID'] == category_id:
            category = cat
            break
    
    if not category:
        messagebox.showwarning("Selection Error", "Category not found")
        return
    
    # Create a new dialog window for room category details
    dialog = ctk.CTkToplevel(app)
    dialog.title("Edit Room Category")
    dialog.geometry("400x400")
    dialog.resizable(False, False)
    dialog.transient(app)  # Set as transient to app window
    dialog.grab_set()  # Make dialog modal
    
    # Room category form
    form_frame = ctk.CTkFrame(dialog, fg_color="white")
    form_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Category name
    ctk.CTkLabel(form_frame, text="Category Name *", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
    category_name_entry = ctk.CTkEntry(form_frame, height=35)
    category_name_entry.insert(0, category['category_name'])
    category_name_entry.pack(fill="x", pady=(0, 15))
    
    # Description
    ctk.CTkLabel(form_frame, text="Description", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
    description_text = ctk.CTkTextbox(form_frame, height=100)
    if category['description']:
        description_text.insert("1.0", category['description'])
    description_text.pack(fill="x", pady=(0, 15))
    
    # Base price
    ctk.CTkLabel(form_frame, text="Base Price ($) *", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
    price_entry = ctk.CTkEntry(form_frame, height=35)
    price_entry.insert(0, str(category['base_price']))
    price_entry.pack(fill="x", pady=(0, 15))
    
    # Capacity
    ctk.CTkLabel(form_frame, text="Capacity (guests) *", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
    capacity_entry = ctk.CTkEntry(form_frame, height=35)
    capacity_entry.insert(0, str(category['capacity']))
    capacity_entry.pack(fill="x", pady=(0, 15))
    
    # Submit button
    def update_category():
        # Get data from entry fields
        category_name = category_name_entry.get()
        description = description_text.get("1.0", "end-1c")
        
        try:
            base_price = float(price_entry.get())
            capacity = int(capacity_entry.get())
        except ValueError:
            messagebox.showwarning("Input Error", "Please enter valid price and capacity values")
            return
        
        # Validate input
        if not category_name or base_price <= 0 or capacity <= 0:
            messagebox.showwarning("Input Error", "Category name, price, and capacity are required")
            return
        
        try:
            connection = connect_db()
            cursor = connection.cursor()
            
            # Update room category
            cursor.execute(
                """
                UPDATE RoomCategory
                SET category_name = %s, description = %s, base_price = %s, capacity = %s
                WHERE Category_ID = %s
                """,
                (category_name, description, base_price, capacity, category_id)
            )
            
            connection.commit()
            messagebox.showinfo("Success", "Room category updated successfully")
            
            # Close the dialog
            dialog.destroy()
            
            # Refresh hotel details
            selected_hotel = load_hotel_details(selected_hotel['Hotel_ID'])
            show_hotel_details()
            
        except mysql.connector.Error as err:
            print(f"Error updating room category: {err}")
            messagebox.showerror("Database Error", f"Error updating room category: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    submit_btn = ctk.CTkButton(form_frame, text="Update Category", font=("Arial", 12, "bold"), 
                              fg_color="#2C3E50", hover_color="#1E4D88",
                              command=update_category, height=40)
    submit_btn.pack(pady=(15, 0))

def delete_room_category(category_id):
    """Delete a room category"""
    #global selected_hotel
    
    if not selected_hotel or not category_id:
        messagebox.showwarning("Selection Error", "No category selected")
        return
    
    # Find the category in the selected hotel's room_categories
    category_name = ""
    for cat in selected_hotel['room_categories']:
        if cat['Category_ID'] == category_id:
            category_name = cat['category_name']
            break
    
    if not category_name:
        messagebox.showwarning("Selection Error", "Category not found")
        return
    
    # Confirm deletion
    confirmed = messagebox.askyesno(
        "Confirm Deletion",
        f"Are you sure you want to delete the room category '{category_name}'?\n\n"
        f"This action cannot be undone."
    )
    
    if not confirmed:
        return
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Delete the room category
        cursor.execute("DELETE FROM RoomCategory WHERE Category_ID = %s", (category_id,))
        
        connection.commit()
        messagebox.showinfo("Success", "Room category deleted successfully")
        
        # Refresh hotel details
        selected_hotel = load_hotel_details(selected_hotel['Hotel_ID'])
        show_hotel_details()
        
    except mysql.connector.Error as err:
        print(f"Error deleting room category: {err}")
        messagebox.showerror("Database Error", f"Error deleting room category: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- UI Functions -------------------
def populate_hotel_table():
    """Populate the hotel table with data from database"""
    # Clear existing rows
    for row in hotel_table.get_children():
        hotel_table.delete(row)
    
    # Load hotels and add to table
    hotels = load_hotels()
    
    for hotel in hotels:
        # Format values
        room_count = hotel['room_categories'] if hotel['room_categories'] else 0
        
        price_range = "N/A"
        if hotel['min_price'] and hotel['max_price']:
            if hotel['min_price'] == hotel['max_price']:
                price_range = f"${hotel['min_price']:.2f}"
            else:
                price_range = f"${hotel['min_price']:.2f} - ${hotel['max_price']:.2f}"
        
        # Create star rating
        stars = '⭐' * hotel['star_rating']
        
        # Insert into table
        hotel_table.insert('', 'end', iid=hotel['Hotel_ID'], values=(
            hotel['Hotel_ID'],
            hotel['hotel_name'],
            hotel['location'],
            stars,
            room_count,
            price_range
        ))
    
    # Update hotel count
    hotel_count_label.configure(text=f"Total Hotels: {len(hotels)}")

def show_hotel_details(event=None):
    """Show details for the selected hotel"""
   # global selected_hotel, 
    global hotel_image_path
    
    # Reset image path
    hotel_image_path = None
    
    # If event is None, use the currently selected hotel
    if event is not None:
        selected_id = hotel_table.focus()
        if not selected_id:
            return
        
        # Convert to integer
        hotel_id = int(selected_id)
        
        # Load hotel details
        hotel = load_hotel_details(hotel_id)
        if not hotel:
            return
        
        selected_hotel = hotel
    
    # Fill in the form fields
    hotel_name_entry.delete(0, 'end')
    hotel_name_entry.insert(0, selected_hotel['hotel_name'])
    
    location_entry.delete(0, 'end')
    location_entry.insert(0, selected_hotel['location'])
    
    description_text.delete("1.0", "end")
    if selected_hotel['description']:
        description_text.insert("1.0", selected_hotel['description'])
    
    star_rating_var.set(str(selected_hotel['star_rating']))
    
    # Reset and update amenity checkboxes
    for amenity_id, var in amenity_vars.items():
        var.set(0)
    
    # Check the amenities that this hotel has
    if 'amenities' in selected_hotel:
        for amenity in selected_hotel['amenities']:
            if amenity['Amenity_ID'] in amenity_vars:
                amenity_vars[amenity['Amenity_ID']].set(1)
    
    # Update action buttons - show appropriate buttons for edit mode
    create_btn.grid_forget()  # Hide create button
    update_btn.grid(row=0, column=0, padx=(0, 10))
    delete_btn.grid(row=0, column=1, padx=(0, 10))
    clear_btn.grid(row=0, column=2)
    
    # Enable appropriate buttons
    update_btn.configure(state="normal")
    delete_btn.configure(state="normal")
    
    # Show hotel details section
    details_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
    
    # Update hotel details display
    details_hotel_id.configure(text=f"Hotel #{selected_hotel['Hotel_ID']}")
    details_name.configure(text=f"{selected_hotel['hotel_name']}")
    details_location.configure(text=f"Location: {selected_hotel['location']}")
    details_stars.configure(text='⭐' * selected_hotel['star_rating'])
    
    # Update hotel image
    if selected_hotel['image_path'] and os.path.exists(selected_hotel['image_path']):
        try:
            # Load and display the hotel image
            hotel_image = Image.open(selected_hotel['image_path'])
            
            # Resize for display
            hotel_image = hotel_image.resize((300, 200), Image.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(hotel_image)
            
            # Update the image label
            details_image_label.configure(image=photo)
            details_image_label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error loading hotel image: {e}")
            details_image_label.configure(image=None, text="Image not available")
    else:
        details_image_label.configure(image=None, text="No image available")
    
    # Clear the room categories list
    for widget in room_categories_container.winfo_children():
        widget.destroy()
    
    # Add room categories
    if 'room_categories' in selected_hotel and selected_hotel['room_categories']:
        for category in selected_hotel['room_categories']:
            create_room_category_card(category)
    else:
        no_rooms_label = ctk.CTkLabel(
            room_categories_container, 
            text="No room categories defined for this hotel",
            font=("Arial", 12),
            text_color="gray"
        )
        no_rooms_label.pack(pady=20)
    
    # Update amenities list
    amenities_text = "Amenities: "
    if 'amenities' in selected_hotel and selected_hotel['amenities']:
        amenities_list = [f"{a['amenity_icon']} {a['amenity_name']}" for a in selected_hotel['amenities']]
        amenities_text += " | ".join(amenities_list)
    else:
        amenities_text += "None"
    
    details_amenities.configure(text=amenities_text)

def clear_hotel_form():
    """Clear the hotel form fields"""
    hotel_name_entry.delete(0, 'end')
    location_entry.delete(0, 'end')
    description_text.delete("1.0", "end")
    star_rating_var.set("3")  # Default to 3 stars
    
    # Reset amenity checkboxes
    for var in amenity_vars.values():
        var.set(0)
    
    # Reset image
    global hotel_image_path
    hotel_image_path = None
    image_preview_label.configure(image=None, text="No image selected")
    
    # Reset selected hotel
    #global selected_hotel
    selected_hotel = None
    
    # Switch to create mode interface
    new_hotel_mode()

def hide_hotel_details():
    """Hide the hotel details section"""
    details_frame.pack_forget()

def new_hotel_mode():
    """Switch to new hotel mode"""
    # Hide hotel details section
    hide_hotel_details()
    
    # Update buttons for create mode
    update_btn.grid_forget()
    delete_btn.grid_forget()
    
    create_btn.grid(row=0, column=0, padx=(0, 10))
    clear_btn.grid(row=0, column=1)
    
    # Enable/disable appropriate buttons
    create_btn.configure(state="normal")
    
    # Set focus to hotel name field
    hotel_name_entry.focus_set()

def browse_image():
    """Open file dialog to select a hotel image"""
    global hotel_image_path
    
    file_path = filedialog.askopenfilename(
        title="Select Hotel Image",
        filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")]
    )
    
    if file_path:
        hotel_image_path = file_path
        
        try:
            # Load and preview the image
            image = Image.open(file_path)
            
            # Resize for preview
            image = image.resize((150, 100), Image.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)
            
            # Update the preview label
            image_preview_label.configure(image=photo, text="")
            image_preview_label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error loading image: {e}")
            messagebox.showerror("Image Error", f"Error loading image: {e}")
            hotel_image_path = None
            image_preview_label.configure(image=None, text="Error loading image")

def search_hotels():
    """Search hotels based on search term"""
    search_term = search_entry.get().lower()
    
    if not search_term:
        # If search term is empty, show all hotels
        populate_hotel_table()
        return
    
    # Clear existing rows
    for row in hotel_table.get_children():
        hotel_table.delete(row)
    
    # Load all hotels
    hotels = load_hotels()
    
    # Filter hotels
    filtered_hotels = []
    for hotel in hotels:
        # Check if search term is in name or location
        if (search_term in hotel['hotel_name'].lower() or 
            search_term in hotel['location'].lower()):
            filtered_hotels.append(hotel)
    
    # Add filtered hotels to table
    for hotel in filtered_hotels:
        # Format values
        room_count = hotel['room_categories'] if hotel['room_categories'] else 0
        
        price_range = "N/A"
        if hotel['min_price'] and hotel['max_price']:
            if hotel['min_price'] == hotel['max_price']:
                price_range = f"${hotel['min_price']:.2f}"
            else:
                price_range = f"${hotel['min_price']:.2f} - ${hotel['max_price']:.2f}"
        
        # Create star rating
        stars = '⭐' * hotel['star_rating']
        
        # Insert into table
        hotel_table.insert('', 'end', iid=hotel['Hotel_ID'], values=(
            hotel['Hotel_ID'],
            hotel['hotel_name'],
            hotel['location'],
            stars,
            room_count,
            price_range
        ))
    
    # Update hotel count
    hotel_count_label.configure(text=f"Filtered Hotels: {len(filtered_hotels)}")

def create_room_category_card(category):
    """Create a card widget for a room category"""
    card = ctk.CTkFrame(room_categories_container, fg_color="white", corner_radius=8,
                      border_width=1, border_color="#E5E5E5", height=80)
    card.pack(fill="x", pady=5)
    card.pack_propagate(False)  # Prevent shrinking
    
    # Category name and price
    header = ctk.CTkFrame(card, fg_color="white")
    header.pack(fill="x", padx=10, pady=(10, 5))
    
    ctk.CTkLabel(header, text=category['category_name'], 
               font=("Arial", 14, "bold"), text_color="#2C3E50").pack(side="left")
    
    price_label = ctk.CTkLabel(header, text=f"${category['base_price']:.2f} per night", 
                             font=("Arial", 12), text_color="#1E90FF")
    price_label.pack(side="right")
    
    # Description and capacity
    content = ctk.CTkFrame(card, fg_color="white")
    content.pack(fill="x", padx=10, pady=(0, 5))
    
    capacity_text = f"Capacity: {category['capacity']} guests"
    ctk.CTkLabel(content, text=capacity_text, 
               font=("Arial", 12), text_color="#6C757D").pack(side="left")
    
    # Action buttons
    action_frame = ctk.CTkFrame(content, fg_color="white")
    action_frame.pack(side="right")
    
    edit_btn = ctk.CTkButton(action_frame, text="Edit", font=("Arial", 11), 
                           fg_color="#6C757D", hover_color="#5A6268",
                           width=60, height=25, command=lambda: edit_room_category(category['Category_ID']))
    edit_btn.pack(side="left", padx=(0, 5))
    
    delete_btn = ctk.CTkButton(action_frame, text="Delete", font=("Arial", 11), 
                             fg_color="#DC3545", hover_color="#C82333",
                             width=60, height=25, command=lambda: delete_room_category(category['Category_ID']))
    delete_btn.pack(side="left")
    
    return card

# ----------------- Initialize App -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - Manage Hotels")
app.geometry("1200x750")
app.minsize(1000, 700)  # Set minimum window size for responsiveness

# Try to load admin session
if not load_admin_session():
    messagebox.showwarning("Login Required", "Admin login required to access this page")
    open_page("admin_login")

# Set up hotel tables in the database
setup_hotel_tables()

# ----------------- Main Frame -----------------
main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
main_frame.pack(expand=True, fill="both")

# ----------------- Sidebar (Navigation) -----------------
sidebar = ctk.CTkFrame(main_frame, fg_color="#2C3E50", width=220, corner_radius=0)
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
    fg_color="#3498DB",
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
    ("🏨 Manage Hotels", go_to_manage_hotels),
    ("🚪 Logout", logout)
]

for btn_text, btn_command in nav_buttons:
    is_active = "Manage Hotels" in btn_text
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

ctk.CTkLabel(header_frame, text="Manage Hotels", 
           font=("Arial", 28, "bold"), text_color="#2C3E50").pack(side="left")

# New Hotel and Search
action_frame = ctk.CTkFrame(header_frame, fg_color="white")
action_frame.pack(side="right")

# New hotel button
new_hotel_btn = ctk.CTkButton(action_frame, text="+ New Hotel", font=("Arial", 12, "bold"), 
                            fg_color="#28A745", hover_color="#218838",
                            command=new_hotel_mode, width=120, height=35, corner_radius=8)
new_hotel_btn.pack(side="left", padx=(0, 15))

# Search
search_frame = ctk.CTkFrame(action_frame, fg_color="#E9ECEF", corner_radius=8, height=35)
search_frame.pack(side="left", fill="y")

search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Search hotels...", 
                          border_width=0, fg_color="#E9ECEF", height=35)
search_entry.pack(side="left", padx=(10, 0))

search_btn = ctk.CTkButton(search_frame, text="🔍", font=("Arial", 12, "bold"), 
                         fg_color="#E9ECEF", text_color="#343A40", hover_color="#DEE2E6",
                         width=35, height=35, corner_radius=0, command=search_hotels)
search_btn.pack(side="right")

# ----------------- Hotel Form Section -----------------
form_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                        border_color="#DEE2E6", corner_radius=10)
form_frame.pack(fill="x", padx=30, pady=(0, 20))

# Form header
form_header = ctk.CTkFrame(form_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
form_header.pack(fill="x")

ctk.CTkLabel(form_header, text="Hotel Information", 
           font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)

# Form fields
form_fields = ctk.CTkFrame(form_frame, fg_color="white")
form_fields.pack(fill="x", padx=20, pady=(20, 20))

# Create two columns with grid layout for better responsiveness
form_fields.columnconfigure(0, weight=1)
form_fields.columnconfigure(1, weight=1)

# Left column
ctk.CTkLabel(form_fields, text="Hotel Name *", font=("Arial", 12), anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
hotel_name_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter hotel name")
hotel_name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

ctk.CTkLabel(form_fields, text="Location *", font=("Arial", 12), anchor="w").grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
location_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter location (city, country)")
location_entry.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

ctk.CTkLabel(form_fields, text="Description", font=("Arial", 12), anchor="w").grid(row=4, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
description_text = ctk.CTkTextbox(form_fields, height=100)
description_text.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))

# Right column - Star Rating, Image, Amenities
right_column = ctk.CTkFrame(form_fields, fg_color="white")
right_column.grid(row=0, column=1, rowspan=6, sticky="nsew", padx=(10, 0))

# Star Rating
ctk.CTkLabel(right_column, text="Star Rating *", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
star_frame = ctk.CTkFrame(right_column, fg_color="white")
star_frame.pack(fill="x", pady=(0, 15))

star_rating_var = ctk.StringVar(value="3")  # Default to 3 stars
for i in range(1, 6):
    star_rb = ctk.CTkRadioButton(star_frame, text=f"{i} ⭐", variable=star_rating_var, value=str(i))
    star_rb.pack(side="left", padx=(0, 10))

# Hotel Image
ctk.CTkLabel(right_column, text="Hotel Image", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
image_frame = ctk.CTkFrame(right_column, fg_color="white")
image_frame.pack(fill="x", pady=(0, 15))

image_preview_label = ctk.CTkLabel(image_frame, text="No image selected", width=150, height=100, 
                                 fg_color="#E9ECEF", corner_radius=5)
image_preview_label.pack(side="left", padx=(0, 10))

browse_btn = ctk.CTkButton(image_frame, text="Browse Image", font=("Arial", 12), 
                         fg_color="#6C757D", hover_color="#5A6268",
                         command=browse_image, width=100, height=35)
browse_btn.pack(side="left", pady=(30, 0))

# Amenities
ctk.CTkLabel(right_column, text="Amenities", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
amenities_frame = ctk.CTkScrollableFrame(right_column, fg_color="white", height=150)
amenities_frame.pack(fill="x", pady=(0, 15))

# Fetch all amenities
amenity_vars = {}  # Dictionary to store checkbox variables
try:
    connection = connect_db()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Amenities ORDER BY amenity_name")
    amenities = cursor.fetchall()
    
    # Create checkboxes for amenities in a grid layout (3 columns)
    for i, amenity in enumerate(amenities):
        row = i // 3
        col = i % 3
        
        # Create variable for this amenity
        var = ctk.IntVar(value=0)
        amenity_vars[amenity['Amenity_ID']] = var
        
        # Create checkbox
        cb = ctk.CTkCheckBox(amenities_frame, text=f"{amenity['amenity_icon']} {amenity['amenity_name']}", 
                          variable=var, font=("Arial", 11))
        cb.grid(row=row, column=col, sticky="w", padx=5, pady=2)
except mysql.connector.Error as err:
    print(f"Error loading amenities: {err}")
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()

# Form buttons
buttons_frame = ctk.CTkFrame(form_fields, fg_color="white")
buttons_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

# Button container
button_container = ctk.CTkFrame(buttons_frame, fg_color="white")
button_container.pack()

# Buttons
create_btn = ctk.CTkButton(button_container, text="Create Hotel", font=("Arial", 13, "bold"), 
                         fg_color="#28A745", hover_color="#218838",
                         command=create_hotel, width=140, height=40, corner_radius=8)

update_btn = ctk.CTkButton(button_container, text="Update Hotel", font=("Arial", 13, "bold"), 
                         fg_color="#2C3E50", hover_color="#1E4D88",
                         command=update_hotel, width=140, height=40, corner_radius=8, state="disabled")

delete_btn = ctk.CTkButton(button_container, text="Delete Hotel", font=("Arial", 13, "bold"), 
                         fg_color="#DC3545", hover_color="#C82333",
                         command=delete_hotel, width=140, height=40, corner_radius=8, state="disabled")

clear_btn = ctk.CTkButton(button_container, text="Clear Form", font=("Arial", 13, "bold"), 
                        fg_color="#6C757D", hover_color="#5A6268",
                        command=clear_hotel_form, width=140, height=40, corner_radius=8)

# Initially show only the create and clear buttons (new hotel mode)
create_btn.grid(row=0, column=0, padx=(0, 10))
clear_btn.grid(row=0, column=1)

# ----------------- Hotel Table Section -----------------
table_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                        border_color="#DEE2E6", corner_radius=10)
table_frame.pack(fill="x", padx=30, pady=(0, 20))

# Table header
table_header = ctk.CTkFrame(table_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
table_header.pack(fill="x")

ctk.CTkLabel(table_header, text="Hotel List", 
           font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)

# Hotel count
hotel_count_label = ctk.CTkLabel(table_header, text="Total Hotels: 0", font=("Arial", 12))
hotel_count_label.pack(side="right", padx=20, pady=10)

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

# Create treeview for hotels
columns = ('ID', 'Name', 'Location', 'Rating', 'Room Categories', 'Price Range')
hotel_table = ttk.Treeview(table_container, columns=columns, show='headings', height=6)

# Configure column headings
for col in columns:
    hotel_table.heading(col, text=col)
    if col == 'ID':
        hotel_table.column(col, width=50, anchor='center', minwidth=50)
    elif col == 'Rating':
        hotel_table.column(col, width=100, anchor='center', minwidth=100)
    elif col == 'Room Categories':
        hotel_table.column(col, width=120, anchor='center', minwidth=100)
    elif col == 'Price Range':
        hotel_table.column(col, width=120, anchor='center', minwidth=120)
    elif col == 'Location':
        hotel_table.column(col, width=200, anchor='w', minwidth=150)
    else:
        hotel_table.column(col, width=200, anchor='w', minwidth=150)

# Add scrollbar
table_scroll_y = ttk.Scrollbar(table_container, orient='vertical', command=hotel_table.yview)
table_scroll_x = ttk.Scrollbar(table_container, orient='horizontal', command=hotel_table.xview)
hotel_table.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)

# Pack the scrollbars and table
table_scroll_y.pack(side='right', fill='y')
table_scroll_x.pack(side='bottom', fill='x')
hotel_table.pack(expand=True, fill='both')

# Bind click event to show hotel details
hotel_table.bind('<<TreeviewSelect>>', show_hotel_details)

# ----------------- Hotel Details Section -----------------
details_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                          border_color="#DEE2E6", corner_radius=10)
# Initially hidden - will be shown when a hotel is selected

# Details header
details_header = ctk.CTkFrame(details_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
details_header.pack(fill="x")

details_hotel_id = ctk.CTkLabel(details_header, text="Hotel #", 
                             font=("Arial", 16, "bold"), text_color="#2C3E50")
details_hotel_id.pack(side="left", padx=20, pady=10)

# Add Room Category button
add_room_btn = ctk.CTkButton(details_header, text="+ Add Room Category", font=("Arial", 12), 
                           fg_color="#0F2D52", hover_color="#1E4D88",
                           command=add_room_category, width=150, height=30)
add_room_btn.pack(side="right", padx=20, pady=10)

# Details content
details_content = ctk.CTkFrame(details_frame, fg_color="white")
details_content.pack(fill="x", padx=20, pady=(15, 15))

# Hotel details with image
details_row = ctk.CTkFrame(details_content, fg_color="white")
details_row.pack(fill="x", pady=(0, 15))

# Left side - Hotel details
details_info = ctk.CTkFrame(details_row, fg_color="white", width=300)
details_info.pack(side="left", fill="y", padx=(0, 15))

details_name = ctk.CTkLabel(details_info, text="Hotel Name", 
                         font=("Arial", 18, "bold"), text_color="#2C3E50")
details_name.pack(anchor="w", pady=(0, 5))

details_location = ctk.CTkLabel(details_info, text="Location: ", 
                             font=("Arial", 14), text_color="#6C757D")
details_location.pack(anchor="w", pady=(0, 5))

details_stars = ctk.CTkLabel(details_info, text="⭐⭐⭐", 
                          font=("Arial", 14), text_color="#FFC107")
details_stars.pack(anchor="w", pady=(0, 10))

details_amenities = ctk.CTkLabel(details_info, text="Amenities: ", 
                               font=("Arial", 12), text_color="#6C757D", 
                               wraplength=300, justify="left")
details_amenities.pack(anchor="w", pady=(0, 5))

# Right side - Hotel image
details_image_frame = ctk.CTkFrame(details_row, fg_color="#F8F9FA", 
                                width=300, height=200, corner_radius=8)
details_image_frame.pack(side="left", fill="none", padx=(0, 0))
details_image_frame.pack_propagate(False)  # Prevent resizing

details_image_label = ctk.CTkLabel(details_image_frame, text="No image available", 
                                 font=("Arial", 12), text_color="#6C757D")
details_image_label.pack(expand=True)

# Room Categories
room_header = ctk.CTkFrame(details_content, fg_color="white")
room_header.pack(fill="x", pady=(15, 10))

ctk.CTkLabel(room_header, text="Room Categories", 
           font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left")

# Scrollable frame for room categories
room_categories_container = ctk.CTkScrollableFrame(details_content, fg_color="white", height=200)
room_categories_container.pack(fill="x", pady=(0, 10))

# Attach a keyboard shortcut to search (Enter key)
search_entry.bind("<Return>", lambda event: search_hotels())

# Populate the hotel table
populate_hotel_table()

# Initialize in "new hotel" mode
new_hotel_mode()

# Run the application
if __name__ == "__main__":
    app.mainloop()