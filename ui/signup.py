import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import hashlib
import subprocess
import sys
import os
from PIL import Image, ImageTk
from db_config import connect_db  # Assuming you have a separate file for DB config

# ------------------- Database Connection -------------------


# ------------------- Password Hashing -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ------------------- Icon Loader Function -------------------
def load_icon(icon_path, size=(16, 16)):  # Reduced icon size
    """Load an icon image and resize it to the specified size"""
    try:
        # Check if the icon exists
        if not os.path.exists(icon_path):
            # Try looking in a resources/icons directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(base_dir, "resources", "icons", os.path.basename(icon_path))
            if os.path.exists(alt_path):
                icon_path = alt_path
            else:
                print(f"Icon not found: {icon_path}")
                return None
                
        icon = Image.open(icon_path)
        icon = icon.resize(size, Image.LANCZOS)
        return ImageTk.PhotoImage(icon)
    except Exception as e:
        print(f"Error loading icon {icon_path}: {e}")
        return None

# ------------------- Sign Up Function -------------------
def signup_user():
    full_name = fullname_entry.get()
    email = email_entry.get()
    phone = phone_entry.get()
    password = password_entry.get()
    confirm_password = confirm_password_entry.get()
    security_question = security_question_var.get()
    security_answer = security_answer_entry.get()

    # Simple validation
    if not full_name or not email or not password or not confirm_password or not security_question or not security_answer:
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

    # Hash the password and security answer
    hashed_password = hash_password(password)
    
    # Process security answer consistently - lowercase and strip whitespace
    processed_answer = security_answer.lower().strip()
    hashed_security_answer = hash_password(processed_answer)
    
    # Debug prints to help troubleshoot the hashing issue
    print(f"Debug - During signup - Original Answer: {security_answer}")
    print(f"Debug - During signup - Processed Answer: {processed_answer}")
    print(f"Debug - During signup - Answer Hash: {hashed_security_answer}")

    try:
        connection = connect_db()
        cursor = connection.cursor()

        # Insert the user data into the database
        cursor.execute(
            "INSERT INTO Users (first_name, last_name, email, phone, password, security_question, security_answer) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (first_name, last_name, email, phone, hashed_password, security_question, hashed_security_answer)
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

# ----------------- Color Constants -----------------
PRIMARY_COLOR = "#2C3E50"      # Dark blue for main elements
SECONDARY_COLOR = "#3498DB"    # Lighter blue for accents
HOVER_COLOR = "#1E88E5"        # Hover state color
TEXT_COLOR = "#333333"         # Dark gray for text
LIGHT_TEXT = "#7F8C8D"         # Light gray for secondary text
BORDER_COLOR = "#E0E0E0"       # Light gray for borders
BG_COLOR = "#FFFFFF"           # White background

# ----------------- Setup -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# Import necessary tkinter modules for scrolling
import tkinter as tk

app = ctk.CTk()
app.title("Hotel Booking - Sign Up")
app.geometry("800x600")  # Further reduced height to emphasize scrolling need
app.resizable(True, True)  # Allow resizing to see scrolling behavior

# ----------------- Main Frame -----------------
main_frame = ctk.CTkFrame(app, fg_color=BG_COLOR, corner_radius=0)
main_frame.pack(expand=True, fill="both")

# ----------------- Left Frame (Illustration) -----------------
left_frame = ctk.CTkFrame(main_frame, fg_color=PRIMARY_COLOR, width=350, corner_radius=0)  # Reduced width
left_frame.pack(side="left", fill="both", expand=True)

# Load and display the PNG image
try:
    # Create a frame for the image
    image_frame = ctk.CTkFrame(left_frame, fg_color=PRIMARY_COLOR)
    image_frame.pack(fill="both", expand=True, padx=20, pady=20)  # Reduced padding
    
    # Create a label to hold the image
    image_label = ctk.CTkLabel(image_frame, text="", fg_color=PRIMARY_COLOR)
    image_label.pack(fill="both", expand=True)
    
    try:
        # Path to hotel image
        image_path = "images/city_hotel.png"
        
        # Check if image exists, if not create a resources directory and search there
        if not os.path.exists(image_path):
            resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
            if os.path.exists(resources_dir):
                potential_image = os.path.join(resources_dir, "city_hotel.png")
                if os.path.exists(potential_image):
                    image_path = potential_image
        
        # Load and resize the image
        hotel_image = Image.open(image_path)
        
        # Get the dimensions of the frame - reduced size
        width, height = 300, 225
        
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
        image_label.configure(
            text="Hotel Image Not Found", 
            font=("Montserrat", 16, "bold"),  # Smaller font
            text_color="white"
        )
        
except Exception as e:
    # Fallback if PIL is not installed or other error occurs
    error_label = ctk.CTkLabel(
        left_frame, 
        text=f"Error loading image: {e}\nPlease install PIL/Pillow with:\npip install Pillow", 
        font=("Arial", 12),  # Smaller font
        text_color="white"
    )
    error_label.pack(pady=200)  # Reduced padding

# ----------------- Right Frame (Sign Up Form) -----------------
right_frame = ctk.CTkFrame(main_frame, fg_color=BG_COLOR, corner_radius=0)
right_frame.pack(side="right", fill="both", expand=True)

# Create a canvas with scrollbar for the content
canvas = ctk.CTkCanvas(right_frame, bg=BG_COLOR, highlightthickness=0)
scrollbar = ctk.CTkScrollbar(right_frame, orientation="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scrollbar.set)

# Pack the canvas and scrollbar
scrollbar.pack(side="right", fill="y")
canvas.pack(side="left", fill="both", expand=True, padx=10)

# Content Container (to center the form)
content_frame = ctk.CTkFrame(canvas, fg_color=BG_COLOR, width=350)  # Reduced width
canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw", width=canvas.winfo_width())

# Hotel Logo and Title
logo_frame = ctk.CTkFrame(content_frame, fg_color="transparent", height=40)  # Reduced height
logo_frame.pack(pady=(20, 0))  # Reduced top padding

# Try to load a hotel logo image
hotel_logo_image = None
logo_path = "images/hotel_logo.png"  # Replace with your actual logo file
hotel_logo_image = load_icon(logo_path, size=(40, 40))  # Reduced logo size

if hotel_logo_image:
    logo_label = ctk.CTkLabel(
        logo_frame,
        text="",
        image=hotel_logo_image
    )
    logo_label.image = hotel_logo_image  # Keep a reference
else:
    # Fallback to text-based logo
    logo_label = ctk.CTkLabel(
        logo_frame, 
        text="H", 
        font=("Arial", 24, "bold"),  # Smaller font
        text_color="white",
        fg_color=PRIMARY_COLOR,
        corner_radius=8,
        width=40,
        height=40
    )
logo_label.pack()

ctk.CTkLabel(
    content_frame, 
    text="Hotel Booking", 
    font=("Arial", 20, "bold"),  # Smaller font
    text_color=PRIMARY_COLOR
).pack(pady=(5, 0))

ctk.CTkLabel(
    content_frame, 
    text="Create a New Account", 
    font=("Arial", 14),  # Smaller font
    text_color=LIGHT_TEXT
).pack(pady=(2, 15))  # Reduced padding

# --------------------- Form Fields with Icons ---------------------
# Setting consistent form field sizes
FORM_WIDTH = 300  # Reduced width
FORM_HEIGHT = 35  # Reduced height
FIELD_PADDING = 8  # Reduced padding between fields

# Full Name Field with Icon
name_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
name_label_frame.pack(fill="x", pady=(0, 2))  # Reduced padding

# Load person icon
person_icon_image = None
person_icon_path = "images/user_icon.png"  # Replace with your actual icon file
person_icon_image = load_icon(person_icon_path)

# Create a label frame to contain both icon and text
person_label_frame = ctk.CTkFrame(name_label_frame, fg_color="transparent")
person_label_frame.pack(anchor="w", padx=10)  # Left-aligned, added padding

# Add icon if available
if person_icon_image:
    person_icon_label = ctk.CTkLabel(
        person_label_frame,
        text="",
        image=person_icon_image,
        width=16  # Reduced width
    )
    person_icon_label.image = person_icon_image  # Keep a reference
    person_icon_label.pack(side="left", padx=(0, 3))  # Reduced padding

# Add text label
name_label = ctk.CTkLabel(
    person_label_frame,
    text="Full Name",
    font=("Arial", 10),  # Smaller font
    text_color=LIGHT_TEXT
)
name_label.pack(side="left")

# Full Name entry
fullname_entry = ctk.CTkEntry(
    content_frame,
    width=FORM_WIDTH,
    height=FORM_HEIGHT,
    placeholder_text="Name",  # Shorter placeholder
    border_color=BORDER_COLOR,
    corner_radius=5
)
fullname_entry.pack(pady=(0, FIELD_PADDING))

# Email Field with Icon
email_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
email_label_frame.pack(fill="x", pady=(0, 2))  # Reduced padding

# Load email icon
email_icon_image = None
email_icon_path = "images/email_icon.png"  # Replace with your actual icon file
email_icon_image = load_icon(email_icon_path)

# Create a label frame to contain both icon and text
email_label_container = ctk.CTkFrame(email_label_frame, fg_color="transparent")
email_label_container.pack(anchor="w", padx=10)  # Left-aligned, added padding

# Add icon if available
if email_icon_image:
    email_icon_label = ctk.CTkLabel(
        email_label_container,
        text="",
        image=email_icon_image,
        width=16  # Reduced width
    )
    email_icon_label.image = email_icon_image  # Keep a reference
    email_icon_label.pack(side="left", padx=(0, 3))  # Reduced padding

# Add text label
email_label = ctk.CTkLabel(
    email_label_container,
    text="Email",
    font=("Arial", 10),  # Smaller font
    text_color=LIGHT_TEXT
)
email_label.pack(side="left")

# Email entry
email_entry = ctk.CTkEntry(
    content_frame,
    width=FORM_WIDTH,
    height=FORM_HEIGHT,
    placeholder_text="Email",  # Shorter placeholder
    border_color=BORDER_COLOR,
    corner_radius=5
)
email_entry.pack(pady=(0, FIELD_PADDING))

# Phone Number Field with Icon
phone_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
phone_label_frame.pack(fill="x", pady=(0, 2))  # Reduced padding

# Load phone icon
phone_icon_image = None
phone_icon_path = "images/phone_icon.png"  # Replace with your actual icon file
phone_icon_image = load_icon(phone_icon_path)

# Create a label frame to contain both icon and text
phone_label_container = ctk.CTkFrame(phone_label_frame, fg_color="transparent")
phone_label_container.pack(anchor="w", padx=10)  # Left-aligned, added padding

# Add icon if available
if phone_icon_image:
    phone_icon_label = ctk.CTkLabel(
        phone_label_container,
        text="",
        image=phone_icon_image,
        width=16  # Reduced width
    )
    phone_icon_label.image = phone_icon_image  # Keep a reference
    phone_icon_label.pack(side="left", padx=(0, 3))  # Reduced padding

# Add text label
phone_label = ctk.CTkLabel(
    phone_label_container,
    text="Phone Number",
    font=("Arial", 10),  # Smaller font
    text_color=LIGHT_TEXT
)
phone_label.pack(side="left")

# Phone number entry
phone_entry = ctk.CTkEntry(
    content_frame,
    width=FORM_WIDTH,
    height=FORM_HEIGHT,
    placeholder_text="Phone",  # Shorter placeholder
    border_color=BORDER_COLOR,
    corner_radius=5
)
phone_entry.pack(pady=(0, FIELD_PADDING))

# Security Question Field
security_question_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
security_question_label_frame.pack(fill="x", pady=(0, 2))  # Reduced padding

security_question_label_container = ctk.CTkFrame(security_question_label_frame, fg_color="transparent")
security_question_label_container.pack(anchor="w", padx=10)  # Left-aligned, added padding

# Add security question icon if available
security_icon_image = load_icon("lock_icon.png")  # Reuse lock icon
if security_icon_image:
    security_icon_label = ctk.CTkLabel(
        security_question_label_container,
        text="",
        image=security_icon_image,
        width=16  # Reduced width
    )
    security_icon_label.image = security_icon_image
    security_icon_label.pack(side="left", padx=(0, 3))  # Reduced padding

security_question_label = ctk.CTkLabel(
    security_question_label_container,
    text="Security Question",
    font=("Arial", 10),  # Smaller font
    text_color=LIGHT_TEXT
)
security_question_label.pack(side="left")

# Security Question Dropdown
security_questions = [
    "What is your mother's maiden name?",
    "What was your first pet's name?",
    "What was your childhood nickname?",
    "What is your favorite book?",
    "What is the name of your elementary school?"
]
security_question_var = ctk.StringVar(value=security_questions[0])
security_question_dropdown = ctk.CTkOptionMenu(
    content_frame,
    width=FORM_WIDTH,
    height=FORM_HEIGHT,
    values=security_questions,
    variable=security_question_var,
    fg_color=BG_COLOR,
    button_color=SECONDARY_COLOR,
    button_hover_color=HOVER_COLOR,
    dropdown_fg_color=BG_COLOR,
    font=("Arial", 10)  # Smaller font
)
security_question_dropdown.pack(pady=(0, FIELD_PADDING))

# Security Answer Field
security_answer_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
security_answer_label_frame.pack(fill="x", pady=(0, 2))  # Reduced padding

security_answer_label_container = ctk.CTkFrame(security_answer_label_frame, fg_color="transparent")
security_answer_label_container.pack(anchor="w", padx=10)  # Left-aligned, added padding

if security_icon_image:
    security_answer_icon_label = ctk.CTkLabel(
        security_answer_label_container,
        text="",
        image=security_icon_image,
        width=16  # Reduced width
    )
    security_answer_icon_label.image = security_icon_image
    security_answer_icon_label.pack(side="left", padx=(0, 3))  # Reduced padding

security_answer_label = ctk.CTkLabel(
    security_answer_label_container,
    text="Security Answer",
    font=("Arial", 10),  # Smaller font
    text_color=LIGHT_TEXT
)
security_answer_label.pack(side="left")

security_answer_entry = ctk.CTkEntry(
    content_frame,
    width=FORM_WIDTH,
    height=FORM_HEIGHT,
    placeholder_text="Answer",  # Shorter placeholder
    border_color=BORDER_COLOR,
    corner_radius=5,
    show="•"
)
security_answer_entry.pack(pady=(0, FIELD_PADDING))

# Password Field with Icon
password_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
password_label_frame.pack(fill="x", pady=(0, 2))  # Reduced padding

# Load password icon
password_icon_image = None
password_icon_path = "images/lock_icon.png"  # Replace with your actual icon file
password_icon_image = load_icon(password_icon_path)

# Create a label frame to contain both icon and text
password_label_container = ctk.CTkFrame(password_label_frame, fg_color="transparent")
password_label_container.pack(anchor="w", padx=10)  # Left-aligned, added padding

# Add icon if available
if password_icon_image:
    password_icon_label = ctk.CTkLabel(
        password_label_container,
        text="",
        image=password_icon_image,
        width=16  # Reduced width
    )
    password_icon_label.image = password_icon_image  # Keep a reference
    password_icon_label.pack(side="left", padx=(0, 3))  # Reduced padding

# Add text label
password_label = ctk.CTkLabel(
    password_label_container,
    text="Password",
    font=("Arial", 10),  # Smaller font
    text_color=LIGHT_TEXT
)
password_label.pack(side="left")

# Password entry
password_entry = ctk.CTkEntry(
    content_frame,
    width=FORM_WIDTH,
    height=FORM_HEIGHT,
    show="•",
    placeholder_text="Password",  # Shorter placeholder
    border_color=BORDER_COLOR,
    corner_radius=5
)
password_entry.pack(pady=(0, FIELD_PADDING))

# Confirm Password Field with Icon
confirm_password_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
confirm_password_label_frame.pack(fill="x", pady=(0, 2))  # Reduced padding

# Create a label frame to contain both icon and text
confirm_password_label_container = ctk.CTkFrame(confirm_password_label_frame, fg_color="transparent")
confirm_password_label_container.pack(anchor="w", padx=10)  # Left-aligned, added padding

# Add icon if available (reuse the password icon)
if password_icon_image:
    confirm_icon_label = ctk.CTkLabel(
        confirm_password_label_container,
        text="",
        image=password_icon_image,
        width=16  # Reduced width
    )
    confirm_icon_label.image = password_icon_image  # Keep a reference
    confirm_icon_label.pack(side="left", padx=(0, 3))  # Reduced padding

# Add text label
confirm_password_label = ctk.CTkLabel(
    confirm_password_label_container,
    text="Confirm Password",
    font=("Arial", 10),  # Smaller font
    text_color=LIGHT_TEXT
)
confirm_password_label.pack(side="left")

# Confirm password entry
confirm_password_entry = ctk.CTkEntry(
    content_frame,
    width=FORM_WIDTH,
    height=FORM_HEIGHT,
    show="•",
    placeholder_text="Confirm",  # Shorter placeholder
    border_color=BORDER_COLOR,
    corner_radius=5
)
confirm_password_entry.pack(pady=(0, FIELD_PADDING))

# Terms & Conditions with improved styling
terms_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
terms_frame.pack(fill="x", pady=(5, 10))  # Reduced padding

agree_var = ctk.IntVar()
terms_checkbox = ctk.CTkCheckBox(
    terms_frame, 
    text="I agree to the Terms & Conditions", 
    variable=agree_var, 
    font=("Arial", 10),  # Smaller font
    checkbox_height=16,  # Smaller checkbox
    checkbox_width=16,   # Smaller checkbox
    border_color=SECONDARY_COLOR,
    fg_color=SECONDARY_COLOR,
    hover_color=HOVER_COLOR,
    text_color=LIGHT_TEXT
)
terms_checkbox.pack(side="left", padx=10)  # Added padding

# Sign Up Button with improved styling
signup_btn = ctk.CTkButton(
    content_frame, 
    text="Sign Up", 
    font=("Arial", 12, "bold"),  # Smaller font
    fg_color=PRIMARY_COLOR, 
    hover_color=HOVER_COLOR, 
    width=FORM_WIDTH, 
    height=40,  # Slightly taller for better visibility
    corner_radius=5, 
    command=signup_user
)
signup_btn.pack(pady=(0, 10))  # Reduced padding

# Login Link with improved styling
login_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
login_frame.pack(pady=(0, 10))  # Reduced padding

ctk.CTkLabel(
    login_frame, 
    text="Already have an account? ", 
    font=("Arial", 10),  # Smaller font
    text_color=LIGHT_TEXT
).pack(side="left")

login_link = ctk.CTkLabel(
    login_frame, 
    text="Login", 
    text_color=SECONDARY_COLOR, 
    font=("Arial", 10, "bold"),  # Smaller font
    cursor="hand2"
)
login_link.pack(side="left")
login_link.bind("<Button-1>", open_login_page)

# Configure the scrolling region when content size changes
def configure_scroll_region(event):
    canvas.configure(scrollregion=canvas.bbox("all"))
    
    # Make sure canvas window fills the width of the canvas
    if canvas.winfo_width() > 1:  # Avoid zero-width issue at initialization
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

content_frame.bind("<Configure>", configure_scroll_region)

# Enable mousewheel scrolling
def _on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Adjust the canvas window width when the canvas is resized
def on_canvas_configure(event):
    if canvas.winfo_width() > 1:  # Avoid zero-width issue at initialization
        canvas.itemconfig(canvas_window, width=canvas.winfo_width())

canvas.bind("<Configure>", on_canvas_configure)

# Run App
app.mainloop()