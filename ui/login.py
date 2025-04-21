import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import hashlib
import subprocess
import sys
import os

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

# ------------------- Create Hover Effect -------------------
def on_enter(e, button, hover_color):
    button.configure(fg_color=hover_color)

def on_leave(e, button, default_color):
    button.configure(fg_color=default_color)

# ----------------- Setup -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking Login")
app.geometry("1000x800")
app.resizable(False, False)

# Load custom font if available
try:
    from tkinter import font
    app.option_add("*Font", "Montserrat 10")  # Set default font if available
except:
    pass

# ----------------- Color Scheme -----------------
# Consistent color palette
PRIMARY_COLOR = "#2C3E50"  # Dark blue for main elements
SECONDARY_COLOR = "#3498DB"  # Lighter blue for accents
HOVER_COLOR = "#1E88E5"  # Hover state color
TEXT_COLOR = "#333333"  # Dark gray for text
LIGHT_TEXT = "#7F8C8D"  # Light gray for secondary text
BORDER_COLOR = "#E0E0E0"  # Light gray for borders

# ----------------- Main Frame -----------------
main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
main_frame.pack(expand=True, fill="both")

# ----------------- Left Frame (Illustration) -----------------
left_frame = ctk.CTkFrame(main_frame, fg_color=PRIMARY_COLOR, width=500, corner_radius=0)
left_frame.pack(side="left", fill="both", expand=True)

# Create a semi-transparent overlay for the image to match the UI better
overlay_frame = ctk.CTkFrame(left_frame, fg_color=PRIMARY_COLOR, corner_radius=0)
overlay_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

# Load and display the PNG image
try:
    from PIL import Image, ImageTk
    
    # Create a frame for the image
    image_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
    image_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Create a label to hold the image
    image_label = ctk.CTkLabel(image_frame, text="", fg_color="transparent")
    image_label.pack(fill="both", expand=True)
    
    try:
        # Path to hotel image
        image_path = "city_hotel.png"
        
        # Check if image exists, if not create a resources directory and search there
        if not os.path.exists(image_path):
            resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
            if os.path.exists(resources_dir):
                potential_image = os.path.join(resources_dir, "city_hotel.png")
                if os.path.exists(potential_image):
                    image_path = potential_image
        
        # Load and resize the image
        hotel_image = Image.open(image_path)
        
        # Get the dimensions of the frame
        width, height = 420, 320
        
        # Resize the image while maintaining aspect ratio
        hotel_image = hotel_image.resize((width, height), Image.LANCZOS)
        
        # Add a slight shadow effect by creating a darker copy behind
        shadow = Image.new('RGBA', hotel_image.size, (0, 0, 0, 0))
        
        # Convert to PhotoImage for display
        hotel_photo = ImageTk.PhotoImage(hotel_image)
        
        # Set the image to the label
        image_label.configure(image=hotel_photo)
        
        # Keep a reference to avoid garbage collection
        image_label.image = hotel_photo
        
        # Add hotel tagline below image
        tagline_label = ctk.CTkLabel(
            image_frame, 
            text="Experience Luxury & Comfort", 
            font=("Montserrat", 18, "bold"),
            text_color="white"
        )
        tagline_label.pack(pady=(10, 0))
    
    except Exception as e:
        print(f"Error loading image: {e}")
        # Fallback text if image can't be loaded
        image_label.configure(
            text="Hotel Image Not Found", 
            font=("Montserrat", 18, "bold"), 
            text_color="white"
        )
        
except ImportError:
    # Fallback if PIL is not installed
    error_label = ctk.CTkLabel(
        left_frame, 
        text="PIL module not found\nPlease install PIL/Pillow with:\npip install Pillow", 
        font=("Arial", 14), 
        text_color="white"
    )
    error_label.pack(pady=300)

# Company info at bottom of left panel
company_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
company_frame.pack(side="bottom", fill="x", padx=20, pady=20)

ctk.CTkLabel(
    company_frame, 
    text="Luxury Hotels Inc.", 
    font=("Montserrat", 12, "bold"), 
    text_color="white"
).pack(anchor="w")

ctk.CTkLabel(
    company_frame, 
    text="Your home away from home", 
    font=("Montserrat", 10), 
    text_color="#B3B3B3"
).pack(anchor="w")

# ----------------- Right Frame (Login Form) -----------------
right_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
right_frame.pack(side="right", fill="both", expand=True)

# Content Container (to center the form)
content_frame = ctk.CTkFrame(right_frame, fg_color="white", width=400)
content_frame.pack(expand=True, fill="both", padx=50)

# Hotel Logo and Title
logo_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
logo_frame.pack(pady=(80, 0))

# We're using a CTkLabel with a background color for a more professional look
# Instead of the emoji character
logo_label = ctk.CTkLabel(
    logo_frame, 
    text="H", 
    font=("Montserrat", 36, "bold"), 
    text_color="white",
    fg_color=PRIMARY_COLOR,
    corner_radius=12,
    width=70,
    height=70
)
logo_label.pack()

ctk.CTkLabel(
    content_frame, 
    text="Hotel Booking", 
    font=("Montserrat", 28, "bold"),
    text_color=TEXT_COLOR
).pack(pady=(10, 5))

ctk.CTkLabel(
    content_frame, 
    text="Login to Your Account", 
    font=("Montserrat", 16),
    text_color=LIGHT_TEXT
).pack(pady=(0, 30))

# Enhanced Email Field
email_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
email_frame.pack(fill="x", pady=(0, 15))

ctk.CTkLabel(
    email_frame, 
    text="Email", 
    font=("Montserrat", 14),
    text_color=TEXT_COLOR,
    anchor="w"
).pack(fill="x")

email_entry = ctk.CTkEntry(
    email_frame, 
    width=400, 
    height=45, 
    placeholder_text="Enter your email",
    border_color=BORDER_COLOR,
    corner_radius=6
)
email_entry.pack(fill="x", pady=(5, 0))
email_entry.focus()  # Set initial focus to email field

# Enhanced Password Field
password_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
password_frame.pack(fill="x", pady=(0, 5))

ctk.CTkLabel(
    password_frame, 
    text="Password", 
    font=("Montserrat", 14),
    text_color=TEXT_COLOR,
    anchor="w"
).pack(fill="x")

password_entry = ctk.CTkEntry(
    password_frame, 
    width=400, 
    height=45, 
    show="•", 
    placeholder_text="Enter your password",
    border_color=BORDER_COLOR,
    corner_radius=6
)
password_entry.pack(fill="x", pady=(5, 0))
# Bind Enter key to login function
password_entry.bind("<Return>", handle_enter)

# Remember Me and Forgot Password
options_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
options_frame.pack(fill="x", pady=(5, 25))

remember_var = ctk.IntVar()
remember_checkbox = ctk.CTkCheckBox(
    options_frame, 
    text="Remember Me", 
    variable=remember_var, 
    font=("Montserrat", 12), 
    checkbox_height=20, 
    checkbox_width=20,
    border_color=SECONDARY_COLOR,
    fg_color=SECONDARY_COLOR,
    hover_color=HOVER_COLOR
)
remember_checkbox.pack(side="left")

forgot_password_link = ctk.CTkLabel(
    options_frame, 
    text="Forgot Password?", 
    text_color=SECONDARY_COLOR, 
    font=("Montserrat", 12, "bold"), 
    cursor="hand2"
)
forgot_password_link.pack(side="right")
forgot_password_link.bind("<Button-1>", forgot_password)

# Enhanced Login Button
login_btn = ctk.CTkButton(
    content_frame, 
    text="Login", 
    font=("Montserrat", 14, "bold"), 
    fg_color=PRIMARY_COLOR, 
    hover_color=HOVER_COLOR, 
    width=400, 
    height=50, 
    corner_radius=6, 
    command=login_user
)
login_btn.pack(pady=(0, 20))

# Sign Up with enhanced styling
signup_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
signup_frame.pack()

ctk.CTkLabel(
    signup_frame, 
    text="Don't have an account? ", 
    font=("Montserrat", 12),
    text_color=LIGHT_TEXT
).pack(side="left")

signup_link = ctk.CTkLabel(
    signup_frame, 
    text="Sign Up", 
    text_color=SECONDARY_COLOR, 
    font=("Montserrat", 12, "bold"), 
    cursor="hand2"
)
signup_link.pack(side="left")
signup_link.bind("<Button-1>", open_signup)

# Admin Login Link with enhanced styling
admin_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
admin_frame.pack(pady=(20, 0))

admin_link = ctk.CTkLabel(
    admin_frame, 
    text="Admin Login", 
    text_color=LIGHT_TEXT, 
    font=("Montserrat", 12), 
    cursor="hand2"
)
admin_link.pack()
admin_link.bind("<Button-1>", lambda e: open_admin_login())

# Version info with enhanced styling
version_label = ctk.CTkLabel(
    content_frame, 
    text="v1.0.1", 
    text_color=LIGHT_TEXT,
    font=("Montserrat", 10)
)
version_label.pack(pady=(30, 0))

# Run App
app.mainloop()