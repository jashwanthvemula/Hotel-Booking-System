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

# ------------------- Open Sign Up Page -------------------
def open_signup(event=None):
    try:
        subprocess.Popen([sys.executable, "signup.py"])
        app.destroy()  # Close the current login window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open signup page: {e}")

# ------------------- Open Admin Login -------------------
def open_admin_login():
    try:
        subprocess.Popen([sys.executable, "admin_login.py"])
        app.destroy()  # Close the current login window
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open admin login: {e}")

# ------------------- Forgot Password -------------------
def forgot_password(event=None):
    email = email_entry.get()
    if not email:
        messagebox.showwarning("Input Required", "Please enter your email address first.")
        return
        
    try:
        connection = connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            # In a real application, you would send a password reset email
            # For now, just show a message
            messagebox.showinfo("Password Reset", 
                f"A password reset link has been sent to {email}.\n\n"
                f"Please check your email.")
        else:
            messagebox.showwarning("Account Not Found", "No account found with this email address.")
    
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Login Function -------------------
def login_user():
    email = email_entry.get()
    password = password_entry.get()

    if not email or not password:
        messagebox.showwarning("Input Error", "Please enter both email and password.")
        return

    hashed_password = hash_password(password)

    try:
        connection = connect_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, first_name, last_name FROM Users WHERE email = %s AND password = %s",
            (email, hashed_password)
        )
        user = cursor.fetchone()

        if user:
            messagebox.showinfo("Success", f"Welcome {user['first_name']} {user['last_name']}!")
            
            # Remember the login if checkbox is checked
            if remember_var.get():
                # In a real app, you would use a more secure method
                # For this example, we'll just simulate remembering the login
                print(f"Remembering login for: {email}")
            
            # Open home page with user ID
            app.destroy()  # Close the login window
            open_home_page(user['user_id'])
        else:
            messagebox.showerror("Login Failed", "Invalid Email or Password.")
    
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Open Home Page -------------------
def open_home_page(user_id):
    try:
        # Launch the home page and pass the user ID
        subprocess.Popen([sys.executable, "home.py", str(user_id)])
    except Exception as e:
        messagebox.showerror("Error", f"Unable to open home page: {e}")

# ------------------- Handle Key Press -------------------
def handle_enter(event):
    login_user()

# ----------------- Setup -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking Login")
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
        image_path = "city_hotel.png"  # Update this with your PNG file name
        
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

# ----------------- Right Frame (Login Form) -----------------
right_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
right_frame.pack(side="right", fill="both", expand=True)

# Content Container (to center the form)
content_frame = ctk.CTkFrame(right_frame, fg_color="white", width=400)
content_frame.pack(expand=True, fill="both", padx=50)

# Hotel Icon and Title
ctk.CTkLabel(content_frame, text="🏨", font=("Arial", 40)).pack(pady=(80, 0))
ctk.CTkLabel(content_frame, text="Hotel Booking", font=("Arial", 30, "bold")).pack(pady=(0, 10))
ctk.CTkLabel(content_frame, text="Login to Your Account", font=("Arial", 20)).pack(pady=(0, 30))

# Email
ctk.CTkLabel(content_frame, text="✉️ Email", font=("Arial", 14), anchor="center").pack()
email_entry = ctk.CTkEntry(content_frame, width=400, height=40, placeholder_text="Enter your email")
email_entry.pack(pady=(5, 20))
email_entry.focus()  # Set initial focus to email field

# Password
ctk.CTkLabel(content_frame, text="🔒 Password", font=("Arial", 14), anchor="center").pack()
password_entry = ctk.CTkEntry(content_frame, width=400, height=40, show="•", placeholder_text="Enter your password")
password_entry.pack(pady=(5, 10))
# Bind Enter key to login function
password_entry.bind("<Return>", handle_enter)

# Remember Me and Forgot Password
options_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
options_frame.pack(fill="x", pady=(0, 20))

remember_var = ctk.IntVar()
remember_checkbox = ctk.CTkCheckBox(options_frame, text="Remember Me", variable=remember_var, 
                                  font=("Arial", 12), checkbox_height=20, checkbox_width=20)
remember_checkbox.pack(side="left")

forgot_password_link = ctk.CTkLabel(options_frame, text="Forgot Password?", text_color="#1E90FF", 
                                 font=("Arial", 12, "bold"), cursor="hand2")
forgot_password_link.pack(side="right")
forgot_password_link.bind("<Button-1>", forgot_password)

# Login Button
login_btn = ctk.CTkButton(content_frame, text="Login", font=("Arial", 14, "bold"), 
                        fg_color="#0F2D52", hover_color="#1E4D88", 
                        width=400, height=45, corner_radius=5, command=login_user)
login_btn.pack(pady=(0, 20))

# Sign Up
signup_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
signup_frame.pack()

ctk.CTkLabel(signup_frame, text="Don't have an account? ", font=("Arial", 12)).pack(side="left")
signup_link = ctk.CTkLabel(signup_frame, text="Sign Up", text_color="#1E90FF", 
                         font=("Arial", 12, "bold"), cursor="hand2")
signup_link.pack(side="left")
signup_link.bind("<Button-1>", open_signup)

# Admin Login Link
admin_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
admin_frame.pack(pady=(20, 0))

admin_link = ctk.CTkLabel(admin_frame, text="Admin Login", text_color="#6c757d", 
                        font=("Arial", 12), cursor="hand2")
admin_link.pack()
admin_link.bind("<Button-1>", lambda e: open_admin_login())

# Version info
version_label = ctk.CTkLabel(content_frame, text="v1.0.0", text_color="#6c757d", font=("Arial", 10))
version_label.pack(pady=(30, 0))

# Run App
app.mainloop()