import customtkinter as ctk
from tkinter import messagebox
import subprocess
import sys
import os
from PIL import Image, ImageTk
import config
from utils import hash_password

# ------------------- Database Setup Functions -------------------
def setup_database():
    """Create database and tables if they don't exist"""
    try:
        # Connect to MySQL (without specifying a database)
        connection = config.connect_mysql()
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute("CREATE DATABASE IF NOT EXISTS hotel_book")
        cursor.execute("USE hotel_book")
        
        # Create Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                phone VARCHAR(20),
                password VARCHAR(255) NOT NULL,
                user_address VARCHAR(255),
                user_role VARCHAR(20) DEFAULT 'customer'
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
        
        # Commit the changes
        connection.commit()
        return True
        
    except Exception as err:
        messagebox.showerror("Database Setup Error", f"Error setting up database: {err}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def add_sample_data():
    """Add sample admin, rooms, and users if tables are empty"""
    try:
        connection = config.connect_db()
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
            cursor.execute(
                """
                INSERT INTO Users (first_name, last_name, email, phone, password, user_address, user_role) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                ("Test", "User", "test@example.com", "123-456-7890", hashed_password, "123 Test St, Test City", "customer")
            )
        
        connection.commit()
        return True
        
    except Exception as err:
        messagebox.showerror("Sample Data Error", f"Error adding sample data: {err}")
        print(f"Error adding sample data: {err}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Navigation Functions -------------------
def open_login():
    """Open the login page"""
    try:
        subprocess.Popen([sys.executable, "custom/auth.py", "--mode=login"])
        app.destroy()  # Close the current window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open login page: {e}")

def open_signup():
    """Open the signup page"""
    try:
        subprocess.Popen([sys.executable, "custom/auth.py", "--mode=signup"])
        app.destroy()  # Close the current window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open signup page: {e}")

def open_admin_login():
    """Open the admin login page"""
    try:
        subprocess.Popen([sys.executable, "custom/auth.py", "--mode=admin"])
        app.destroy()  # Close the current window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open admin login page: {e}")

def exit_app():
    """Exit the application"""
    app.destroy()

# ------------------- Check Files Exist -------------------
def check_required_files():
    """Check if the required Python files exist"""
    required_files = [
        "custom/auth.py",
        "custom/home.py",
        "custom/admin_dashboard.py",
        "custom/booking.py"
    ]
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
    global app
    
    # Setup the database and add sample data
    if not setup_database():
        messagebox.showerror("Setup Error", "Failed to set up the database. The application may not function correctly.")
    else:
        if not add_sample_data():
            messagebox.showwarning("Data Warning", "Failed to add sample data. The application will continue, but some features may not work as expected.")
    
    # Check if all required files exist
    check_required_files()
    
    # Create the main application window
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    app.title("Hotel Booking System - Launcher")
    app.geometry("1000x700")
    app.resizable(False, False)
    
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
            image_path = "static/images/city_hotel.png"
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