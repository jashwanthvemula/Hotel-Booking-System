import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import subprocess
import sys
import os
import hashlib
from PIL import Image, ImageTk
from db_config import connect_mysql, connect_db,database_name

# ------------------- Database Setup Functions -------------------
def setup_database():
    """Create database and tables if they don't exist"""
    connection = None
    try:
        # Connect to MySQL (without specifying a database)
        connection = connect_mysql()
        if connection is None:
            return False
            
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        database_name = "hotel_book"
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        cursor.execute(f"USE {database_name}")

#         cursor.execute("""
# ALTER TABLE Users
# ADD COLUMN is_active TINYINT(1) DEFAULT 1 NOT NULL;""")

# UPDATE Users SET is_active = 1 WHERE is_active IS NULL;""") 
        
        # Create Users table with security question fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                password VARCHAR(255) NOT NULL,
                user_address VARCHAR(255),
                user_role VARCHAR(20) DEFAULT 'customer',
                security_question VARCHAR(255),
                security_answer VARCHAR(255)
            )
        """)
        
        # Create Admin table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Admin (
                Admin_ID INT AUTO_INCREMENT PRIMARY KEY,
                AdminName VARCHAR(100) NOT NULL,
                AdminEmail VARCHAR(100) UNIQUE NOT NULL,
                AdminPassword VARCHAR(255) NOT NULL
            )
        """)
        
        # Create Room table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Room (
                Room_ID INT AUTO_INCREMENT PRIMARY KEY,
                Room_Type VARCHAR(50) NOT NULL,
                Price_per_Night DECIMAL(10, 2) NOT NULL,
                Availability_status VARCHAR(20) DEFAULT 'Available',
                Updated_By INT,
                FOREIGN KEY (Updated_By) REFERENCES Admin(Admin_ID) ON DELETE SET NULL
            )
        """)
        
        # Create Booking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Booking (
                Booking_ID INT AUTO_INCREMENT PRIMARY KEY,
                User_ID INT NOT NULL,
                Room_ID INT NOT NULL,
                Check_IN_Date DATE NOT NULL,
                Check_Out_Date DATE NOT NULL,
                Total_Cost DECIMAL(10, 2) NOT NULL,
                Booking_Status VARCHAR(20) DEFAULT 'Pending',
                FOREIGN KEY (User_ID) REFERENCES Users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (Room_ID) REFERENCES Room(Room_ID) ON DELETE CASCADE
            )
        """)
        
        # Create Review table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Review (
                Review_ID INT AUTO_INCREMENT PRIMARY KEY,
                User_ID INT,
                Rating INT NOT NULL CHECK (Rating BETWEEN 1 AND 5),
                Comments TEXT,
                Review_Date DATE,
                FOREIGN KEY (User_ID) REFERENCES Users(user_id) ON DELETE SET NULL
            )
        """)
        
        # Create Report table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Report (
                Report_ID INT AUTO_INCREMENT PRIMARY KEY,
                Generated_By INT,
                Generate_Time DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (Generated_By) REFERENCES Admin(Admin_ID) ON DELETE SET NULL
            )
        """)
        
        # Create Hotel table
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

        # Create RoomCategory table
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

        # Create Amenities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Amenities (
                Amenity_ID INT AUTO_INCREMENT PRIMARY KEY,
                amenity_name VARCHAR(50) NOT NULL,
                amenity_icon VARCHAR(20)
            )
        """)

        # Create Hotel_Amenities junction table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Hotel_Amenities (
                Hotel_ID INT NOT NULL,
                Amenity_ID INT NOT NULL,
                PRIMARY KEY (Hotel_ID, Amenity_ID),
                FOREIGN KEY (Hotel_ID) REFERENCES Hotel(Hotel_ID) ON DELETE CASCADE,
                FOREIGN KEY (Amenity_ID) REFERENCES Amenities(Amenity_ID) ON DELETE CASCADE
            )
        """)
        
        # Commit the changes
        connection.commit()
        return True
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Setup Error", f"Error setting up database: {err}")
        return False
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_sample_hotels():
    """Add sample hotels if Hotel table is empty"""
    connection = None
    try:
        connection = connect_db()
        if connection is None:
            return False
            
        cursor = connection.cursor()
        
        # Check if Hotel table is empty
        cursor.execute("SELECT COUNT(*) FROM Hotel")
        hotel_count = cursor.fetchone()[0]
        
        if hotel_count == 0:
            # Add sample hotels
            hotels = [
                ("Luxury Grand Hotel", "New York, USA", 
                 "Experience luxury in the heart of New York City. Our 5-star hotel offers premium amenities, exceptional service, and stunning views of the city skyline.", 
                 5),
                ("Ocean View Resort", "Miami, USA", 
                 "Relax and unwind at our beautiful beachfront resort. Enjoy direct beach access, multiple pools, and world-class dining options.", 
                 4),
                ("Mountain Retreat Lodge", "Aspen, USA", 
                 "Escape to the mountains at our cozy lodge. Perfect for both winter skiing and summer hiking adventures with breathtaking views.", 
                 4),
                ("City Center Hotel", "Chicago, USA", 
                 "Conveniently located in downtown Chicago, our modern hotel is perfect for business and leisure travelers alike.", 
                 3),
                ("Beachfront Villa", "Malibu, USA", 
                 "Experience the ultimate beach getaway in our exclusive villas with private access to pristine beaches.", 
                 5)
            ]
            
            for hotel in hotels:
                cursor.execute(
                    """
                    INSERT INTO Hotel (hotel_name, location, description, star_rating, created_by)
                    VALUES (%s, %s, %s, %s, 1)
                    """,
                    hotel
                )
                
                # Get the new hotel ID
                hotel_id = cursor.lastrowid
                
                # Add room categories for this hotel
                if hotel[0] == "Luxury Grand Hotel":
                    room_categories = [
                        (hotel_id, "Standard Room", "Comfortable room with city view", 150.00, 2),
                        (hotel_id, "Deluxe Room", "Spacious room with premium amenities", 250.00, 2),
                        (hotel_id, "Executive Suite", "Luxury suite with separate living area", 350.00, 4)
                    ]
                elif hotel[0] == "Ocean View Resort":
                    room_categories = [
                        (hotel_id, "Garden View Room", "Peaceful room with garden views", 180.00, 2),
                        (hotel_id, "Ocean View Room", "Beautiful room with ocean views", 250.00, 2),
                        (hotel_id, "Beach Suite", "Spacious suite steps from the beach", 380.00, 4)
                    ]
                elif hotel[0] == "Mountain Retreat Lodge":
                    room_categories = [
                        (hotel_id, "Standard Cabin", "Cozy cabin with mountain views", 120.00, 2),
                        (hotel_id, "Deluxe Cabin", "Larger cabin with fireplace", 200.00, 4),
                        (hotel_id, "Family Lodge", "Large lodge for families or groups", 320.00, 6)
                    ]
                elif hotel[0] == "City Center Hotel":
                    room_categories = [
                        (hotel_id, "Economy Room", "Compact room for the budget traveler", 90.00, 1),
                        (hotel_id, "Business Room", "Comfortable room with work desk", 150.00, 2),
                        (hotel_id, "Business Suite", "Suite with separate work area", 240.00, 2)
                    ]
                else:  # Beachfront Villa
                    room_categories = [
                        (hotel_id, "Standard Villa", "Beautiful villa with partial ocean view", 400.00, 4),
                        (hotel_id, "Premium Villa", "Luxurious villa with full ocean view", 600.00, 4),
                        (hotel_id, "Family Villa", "Expansive villa for large groups", 800.00, 8)
                    ]
                
                cursor.executemany(
                    """
                    INSERT INTO RoomCategory (Hotel_ID, category_name, description, base_price, capacity)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    room_categories
                )
                
                # Add some amenities for each hotel
                # First, get amenity IDs
                cursor.execute("SELECT Amenity_ID FROM Amenities")
                amenity_ids = [row[0] for row in cursor.fetchall()]
                
                # Assign different sets of amenities to each hotel
                if hotel[0] == "Luxury Grand Hotel":
                    hotel_amenities = amenity_ids[:7]  # First 7 amenities
                elif hotel[0] == "Ocean View Resort":
                    hotel_amenities = amenity_ids[2:9]  # Amenities 3-9
                elif hotel[0] == "Mountain Retreat Lodge":
                    hotel_amenities = amenity_ids[4:11]  # Amenities 5-11
                elif hotel[0] == "City Center Hotel":
                    hotel_amenities = amenity_ids[0:5]  # First 5 amenities
                else:  # Beachfront Villa
                    hotel_amenities = amenity_ids[-6:]  # Last 6 amenities
                
                # Insert hotel-amenity relationships
                for amenity_id in hotel_amenities:
                    cursor.execute(
                        "INSERT INTO Hotel_Amenities (Hotel_ID, Amenity_ID) VALUES (%s, %s)",
                        (hotel_id, amenity_id)
                    )
            
            connection.commit()
            print("Sample hotels added successfully")
            return True
            
    except mysql.connector.Error as err:
        print(f"Error adding sample hotels: {err}")
        return False
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

def add_sample_data():
    """Add sample admin, rooms, and users if tables are empty"""
    connection = None
    try:
        connection = connect_db()
        if connection is None:
            return False
            
        cursor = connection.cursor()
        
        # Check if Admin table is empty
        cursor.execute("SELECT COUNT(*) FROM Admin")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Add a default admin
            hashed_password = hash_password("admin123")
            cursor.execute(
                "INSERT INTO Admin (AdminName, AdminEmail, AdminPassword) VALUES (%s, %s, %s)",
                ("Admin", "admin@hotel.com", hashed_password)
            )
        
        # Check if Room table is empty
        cursor.execute("SELECT COUNT(*) FROM Room")
        room_count = cursor.fetchone()[0]
        
        if room_count == 0:
            # Add sample rooms/hotels
            room_data = [
                ("Luxury Grand Hotel - Single Room", 150.00, "Available", 1),
                ("Luxury Grand Hotel - Double Room", 250.00, "Available", 1),
                ("Luxury Grand Hotel - Suite", 350.00, "Available", 1),
                ("Ocean View Resort - Standard Room", 200.00, "Available", 1),
                ("Ocean View Resort - Deluxe Room", 300.00, "Available", 1),
                ("Mountain Retreat Lodge - Cabin", 180.00, "Available", 1),
                ("Mountain Retreat Lodge - Family Suite", 280.00, "Available", 1),
                ("City Center Hotel - Economy Room", 120.00, "Available", 1),
                ("City Center Hotel - Business Room", 220.00, "Available", 1),
                ("Beachfront Villa - Standard", 400.00, "Available", 1)
            ]
            
            cursor.executemany(
                "INSERT INTO Room (Room_Type, Price_per_Night, Availability_status, Updated_By) VALUES (%s, %s, %s, %s)",
                room_data
            )
        
        # Add a test user if Users table is empty
        cursor.execute("SELECT COUNT(*) FROM Users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Add a test user
            hashed_password = hash_password("test123")
            hashed_security_answer = hash_password("testanswer")
            cursor.execute(
                """
                INSERT INTO Users (first_name, last_name, email, phone, password, user_address, user_role, security_question, security_answer) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                ("Test", "User", "test@example.com", "123-456-7890", hashed_password, 
                 "123 Test St, Test City", "customer", 
                 "What is your mother's maiden name?", hashed_security_answer)
            )
        
        connection.commit()
        return True
        
    except mysql.connector.Error as err:
        messagebox.showerror("Sample Data Error", f"Error adding sample data: {err}")
        print(f"Error adding sample data: {err}")
        return False
    finally:
        if connection is not None and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Navigation Functions -------------------
def open_login():
    """Open the login page"""
    try:
        subprocess.Popen([sys.executable, "login.py"])
        app.destroy()  # Close the current window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open login page: {e}")

def open_signup():
    """Open the signup page"""
    try:
        subprocess.Popen([sys.executable, "signup.py"])
        app.destroy()  # Close the current window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open signup page: {e}")

def open_admin_login():
    """Open the admin login page"""
    try:
        subprocess.Popen([sys.executable, "admin/admin_login.py"])
        app.destroy()  # Close the current window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open admin login page: {e}")

def exit_app():
    """Exit the application"""
    app.destroy()

# ------------------- Check Files Exist -------------------
def check_required_files():
    """Check if the required Python files exist"""
    required_files = ["login.py", "signup.py", "admin/admin_login.py", "home.py", "admin/admin.py"]
    missing_files = []
    
    for file in required_files:
        if not os.path.isfile(file):
            missing_files.append(file)
    
    if missing_files:
        messagebox.showwarning("Missing Files", 
            f"The following required files are missing:\n\n" + 
            "\n".join(missing_files) + 
            "\n\nSome functionality may not work correctly.")
        return False
    
    return True

# ------------------- Main Application -------------------
def main():
    """Main application function"""
    global app, content_frame
    
    # Setup the database and add sample data
    if not setup_database():
        messagebox.showerror("Setup Error", "Failed to set up the database. The application will exit.")
        return
    else:
        if not add_sample_data():
            messagebox.showwarning("Data Warning", "Failed to add sample data. The application will continue, but some features may not work as expected.")
        add_sample_hotels()
    
    # Check if all required files exist
    check_required_files()
    
    # Create the main application window
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    app.title("Hotel Booking System - Launcher")
    app.geometry("1000x700")
    app.resizable(True, True)
    
    # Main Container
    main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
    main_frame.pack(expand=True, fill="both")
    
    # Left Side - Image
    left_frame = ctk.CTkFrame(main_frame, fg_color="#2C3E50", width=400, corner_radius=0)
    left_frame.pack(side="left", fill="both", expand=True)
    
    # Try to load the hotel image
    try:
        # Create a label to hold the image
        image_label = ctk.CTkLabel(left_frame, text="", fg_color="#2C3E50")
        image_label.pack(fill="both", expand=True)
        
        try:
            # Try to load the image
            image_path = "images/city_hotel.png"
            hotel_image = Image.open(image_path)
            
            # Resize the image
            width, height = 400, 300
            hotel_image = hotel_image.resize((width, height), Image.LANCZOS)
            
            # Convert to PhotoImage for display
            hotel_photo = ImageTk.PhotoImage(hotel_image)
            
            # Set the image to the label
            image_label.configure(image=hotel_photo)
            
            # Keep a reference to avoid garbage collection
            image_label.image = hotel_photo
        except:
            # Display a placeholder if image can't be loaded
            image_label.configure(text="Hotel Booking System", font=("Arial", 24, "bold"), text_color="white")
    except:
        # Handle case where PIL may not be installed
        ctk.CTkLabel(left_frame, text="Hotel Booking System", 
                   font=("Arial", 24, "bold"), text_color="white").pack(pady=300)
    
    # Right Side - Launcher Options
    right_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)
    
    # Content Container
    content_frame = ctk.CTkFrame(right_frame, fg_color="white", width=400)
    content_frame.pack(expand=True, fill="both", padx=50)
    
    # Hotel Booking Title
    ctk.CTkLabel(content_frame, text="🏨", font=("Arial", 60)).pack(pady=(80, 0))
    ctk.CTkLabel(content_frame, text="Hotel Booking System", font=("Arial", 30, "bold")).pack(pady=(0, 10))
    ctk.CTkLabel(content_frame, text="Welcome to our hotel management platform", font=("Arial", 16)).pack(pady=(0, 50))
    
    # Login Button
    login_btn = ctk.CTkButton(content_frame, text="User Login", font=("Arial", 16, "bold"), 
                            fg_color="#0F2D52", hover_color="#1E4D88", 
                            width=300, height=50, corner_radius=8, command=open_login)
    login_btn.pack(pady=10)
    
    # Sign Up Button
    signup_btn = ctk.CTkButton(content_frame, text="Sign Up", font=("Arial", 16, "bold"), 
                             fg_color="#2C3E50", hover_color="#34495E", 
                             width=300, height=50, corner_radius=8, command=open_signup)
    signup_btn.pack(pady=10)
    
    # Admin Login Button
    admin_btn = ctk.CTkButton(content_frame, text="Admin Access", font=("Arial", 16, "bold"), 
                            fg_color="#8E44AD", hover_color="#9B59B6", 
                            width=300, height=50, corner_radius=8, command=open_admin_login)
    admin_btn.pack(pady=10)
    
    # Exit Button
    exit_btn = ctk.CTkButton(content_frame, text="Exit", font=("Arial", 16, "bold"), 
                           fg_color="#E74C3C", hover_color="#C0392B", 
                           width=300, height=50, corner_radius=8, command=exit_app)
    exit_btn.pack(pady=10)
    
    # Version and Credits
    ctk.CTkLabel(content_frame, text="Hotel Booking System v1.0.0", font=("Arial", 12), text_color="gray").pack(pady=(50, 0))
    ctk.CTkLabel(content_frame, text="© 2023 All Rights Reserved", font=("Arial", 10), text_color="gray").pack(pady=(5, 0))
    
    # Run the application
    app.mainloop()

# Run the application
if __name__ == "__main__":
    main()