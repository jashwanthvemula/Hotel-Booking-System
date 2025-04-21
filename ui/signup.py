import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import hashlib
import subprocess
import sys

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="new_password",
        database="hotel_book"
    )

# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Sign Up Function -------------------
def signup_user():
    full_name = fullname_entry.get()
    email = email_entry.get()
    phone = phone_entry.get()
    password = password_entry.get()
    confirm_password = confirm_password_entry.get()

    # Simple validation
    if not full_name or not email or not password or not confirm_password:
        messagebox.showwarning("Input Error", "Please fill in all required fields.")
        return

    # Check if passwords match
    if password != confirm_password:
        messagebox.showwarning("Password Error", "Passwords do not match.")
        return
    
    # Check if terms are accepted
    if not agree_var.get():
        messagebox.showwarning("Terms Error", "You must agree to the Terms & Conditions.")
        return

    # Extract first name and last name from full name
    name_parts = full_name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    # Hash the password
    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Insert the user data into the database
        cursor.execute(
            "INSERT INTO Users (first_name, last_name, email, phone, password) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, phone, hashed_password)
        )

        connection.commit()
        messagebox.showinfo("Success", "Account created successfully!")
        
        # After successful registration, redirect to login page
        open_login_page()

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Open Login Page -------------------
def open_login_page(event=None):
    try:
        subprocess.Popen([sys.executable, "login.py"])
        app.destroy()  # Close the current signup window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open login page: {e}")

# ----------------- Setup -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - Sign Up")
app.geometry("1000x800")
app.resizable(False, False)

# ----------------- Main Frame -----------------
main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
main_frame.pack(expand=True, fill="both")

# ----------------- Left Frame (Illustration) -----------------
left_frame = ctk.CTkFrame(main_frame, fg_color="#3A546E", width=500, corner_radius=0)
left_frame.pack(side="left", fill="both", expand=True)

# Load and display the PNG image
try:
    from PIL import Image, ImageTk
    
    # Create a frame for the image
    image_frame = ctk.CTkFrame(left_frame, fg_color="#3A546E")
    image_frame.pack(fill="both", expand=True)
    
    # Create a label to hold the image
    image_label = ctk.CTkLabel(image_frame, text="", fg_color="#3A546E")
    image_label.pack(fill="both", expand=True)
    
    try:
        # Replace 'city_image.png' with the actual name of your PNG file
        image_path = "city_hotel.png"  # Use the same image as the login page
        
        # Load and resize the image
        hotel_image = Image.open(image_path)
        
        # Get the dimensions of the frame
        width, height = 400, 300
        
        # Resize the image while maintaining aspect ratio
        hotel_image = hotel_image.resize((width, height), Image.LANCZOS)
        
        # Convert to PhotoImage for display
        hotel_photo = ImageTk.PhotoImage(hotel_image)
        
        # Set the image to the label
        image_label.configure(image=hotel_photo)
        
        # Keep a reference to avoid garbage collection
        image_label.image = hotel_photo
    
    except Exception as e:
        print(f"Error loading image: {e}")
        # Fallback text if image can't be loaded
        image_label.configure(text="Hotel Image Not Found\n\nPlease place your PNG file in the same directory\nand update the image path in the code.", 
                              font=("Arial", 14), text_color="white")
except ImportError:
    # Fallback if PIL is not installed
    error_label = ctk.CTkLabel(left_frame, text="PIL module not found\nPlease install PIL/Pillow with:\npip install Pillow", 
                             font=("Arial", 14), text_color="white")
    error_label.pack(pady=300)

# ----------------- Right Frame (Sign Up Form) -----------------
right_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
right_frame.pack(side="right", fill="both", expand=True)

# Content Container (to center the form)
content_frame = ctk.CTkFrame(right_frame, fg_color="white", width=400)
content_frame.pack(expand=True, fill="both", padx=50)

# Hotel Icon and Title
ctk.CTkLabel(content_frame, text="🏨", font=("Arial", 30)).pack(pady=(30, 0))
ctk.CTkLabel(content_frame, text="Hotel Booking", font=("Arial", 30, "bold")).pack(pady=(0, 5))
ctk.CTkLabel(content_frame, text="Create a New Account", font=("Arial", 20)).pack(pady=(0, 20))

# Full Name
ctk.CTkLabel(content_frame, text="👤 Full Name", font=("Arial", 14), anchor="center").pack()
fullname_entry = ctk.CTkEntry(content_frame, width=400, height=40, placeholder_text="Enter your full name")
fullname_entry.pack(pady=(5, 15))

# Email
ctk.CTkLabel(content_frame, text="✉️ Email", font=("Arial", 14), anchor="center").pack()
email_entry = ctk.CTkEntry(content_frame, width=400, height=40, placeholder_text="Enter your email")
email_entry.pack(pady=(5, 15))

# Phone Number
ctk.CTkLabel(content_frame, text="📞 Phone Number", font=("Arial", 14), anchor="center").pack()
phone_entry = ctk.CTkEntry(content_frame, width=400, height=40, placeholder_text="Enter your phone number")
phone_entry.pack(pady=(5, 15))

# Password
ctk.CTkLabel(content_frame, text="🔒 Password", font=("Arial", 14), anchor="center").pack()
password_entry = ctk.CTkEntry(content_frame, width=400, height=40, show="•", placeholder_text="Enter your password")
password_entry.pack(pady=(5, 15))

# Confirm Password
ctk.CTkLabel(content_frame, text="🔒 Confirm Password", font=("Arial", 14), anchor="center").pack()
confirm_password_entry = ctk.CTkEntry(content_frame, width=400, height=40, show="•", placeholder_text="Confirm your password")
confirm_password_entry.pack(pady=(5, 15))

# Terms & Conditions
agree_var = ctk.IntVar()
terms_checkbox = ctk.CTkCheckBox(content_frame, text="I agree to the Terms & Conditions", 
                                variable=agree_var, font=("Arial", 12))
terms_checkbox.pack(pady=(5, 15))

# Sign Up Button
signup_btn = ctk.CTkButton(content_frame, text="Sign Up", font=("Arial", 14, "bold"), 
                          fg_color="#0F2D52", hover_color="#1E4D88", 
                          width=400, height=45, corner_radius=5, command=signup_user)
signup_btn.pack(pady=(5, 15))

# Login Link
login_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
login_frame.pack(pady=(0, 20))

ctk.CTkLabel(login_frame, text="Already have an account? ", font=("Arial", 12)).pack(side="left")
login_link = ctk.CTkLabel(login_frame, text="Login", text_color="#1E90FF", 
                        font=("Arial", 12, "bold"), cursor="hand2")
login_link.pack(side="left")
login_link.bind("<Button-1>", open_login_page)

# Run App
app.mainloop()