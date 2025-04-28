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
        host="127.0.0.1",
        user="root",  # Replace with your MySQL username
        password="new_password",   # Replace with your MySQL password
        database="hotel_book"  # Replace with your database name
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
        subprocess.Popen([sys.executable, "admin/admin_login.py"])
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
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT user_id, security_question FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if user:
            # Create a new window for security question
            security_window = ctk.CTkToplevel(app)
            security_window.title("Security Verification")
            security_window.geometry("400x300")
            security_window.resizable(False, False)
            
            # Center the window
            security_window.transient(app)
            security_window.grab_set()
            
            user_id = user['user_id']
            
            # Security Question Label
            ctk.CTkLabel(security_window, text=user['security_question'], 
                        font=("Montserrat", 14), wraplength=350).pack(pady=(20, 10))
            
            # Answer Entry
            answer_entry = ctk.CTkEntry(security_window, width=300, height=40, 
                                      placeholder_text="Enter your answer", show="•")
            answer_entry.pack(pady=10)
            
            def verify_answer():
                answer = answer_entry.get()
                if not answer:
                    messagebox.showwarning("Input Required", "Please enter your answer.")
                    return
                
                # Connect to database within the function
                try:
                    verify_connection = connect_db()
                    verify_cursor = verify_connection.cursor(dictionary=True)
                    
                    # Process security answer
                    processed_answer = answer.lower().strip()
                    hashed_answer = hash_password(processed_answer)
                    
                    # Verify the answer
                    verify_cursor.execute("SELECT security_answer FROM Users WHERE email = %s", (email,))
                    stored_answer_result = verify_cursor.fetchone()
                    
                    if stored_answer_result and 'security_answer' in stored_answer_result:
                        stored_answer = stored_answer_result['security_answer']
                        
                        if hashed_answer == stored_answer:
                            # Close verification window
                            security_window.destroy()
                            # Open password reset window
                            show_password_reset_window(user_id, email)
                        else:
                            messagebox.showerror("Verification Failed", "Incorrect answer.")
                    else:
                        messagebox.showerror("Error", "Could not retrieve security answer information.")
                
                except mysql.connector.Error as err:
                    messagebox.showerror("Database Error", f"Verification failed: {err}")
                finally:
                    if 'verify_connection' in locals() and verify_connection.is_connected():
                        verify_cursor.close()
                        verify_connection.close()
            
            # Verify Button
            verify_btn = ctk.CTkButton(security_window, text="Verify Answer", 
                                     command=verify_answer, width=300, height=40)
            verify_btn.pack(pady=20)
            
            # Cancel Button
            cancel_btn = ctk.CTkButton(security_window, text="Cancel", 
                                     command=security_window.destroy, 
                                     fg_color="#E74C3C", width=300, height=40)
            cancel_btn.pack(pady=10)
            
        else:
            messagebox.showwarning("Account Not Found", "No account found with this email address.")
    
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def show_password_reset_window(user_id, email):
    """Show the password reset window where user can enter a new password"""
    # Create a new window for password reset
    reset_window = ctk.CTkToplevel(app)
    reset_window.title("Reset Password")
    reset_window.geometry("400x350")
    reset_window.resizable(False, False)
    
    # Center the window
    reset_window.transient(app)
    reset_window.grab_set()
    
    # Header
    ctk.CTkLabel(reset_window, text="Reset Your Password", 
                font=("Montserrat", 18, "bold")).pack(pady=(25, 20))
    
    ctk.CTkLabel(reset_window, text=f"Enter a new password for {email}", 
                font=("Montserrat", 12)).pack(pady=(0, 20))
    
    # New Password Entry
    password_label = ctk.CTkLabel(reset_window, text="New Password", 
                                font=("Montserrat", 12))
    password_label.pack(anchor="w", padx=50, pady=(0, 5))
    
    new_password_entry = ctk.CTkEntry(reset_window, width=300, height=40, 
                                    placeholder_text="Enter new password", show="•")
    new_password_entry.pack(pady=(0, 15))
    
    # Confirm Password Entry
    confirm_label = ctk.CTkLabel(reset_window, text="Confirm Password", 
                                font=("Montserrat", 12))
    confirm_label.pack(anchor="w", padx=50, pady=(0, 5))
    
    confirm_password_entry = ctk.CTkEntry(reset_window, width=300, height=40, 
                                        placeholder_text="Confirm new password", show="•")
    confirm_password_entry.pack(pady=(0, 20))
    
    def update_password():
        new_password = new_password_entry.get()
        confirm_password = confirm_password_entry.get()
        
        # Validate passwords
        if not new_password or not confirm_password:
            messagebox.showwarning("Input Required", "Please fill in all fields.")
            return
            
        if new_password != confirm_password:
            messagebox.showwarning("Password Mismatch", "Passwords do not match.")
            return
            
        if len(new_password) < 6:
            messagebox.showwarning("Password Too Short", "Password must be at least 6 characters.")
            return
        
        # Connect to database
        try:
            update_connection = connect_db()
            update_cursor = update_connection.cursor()
            
            # Hash the new password
            hashed_password = hash_password(new_password)
            
            # Update the password in the database
            update_cursor.execute(
                "UPDATE Users SET password = %s WHERE user_id = %s", 
                (hashed_password, user_id)
            )
            update_connection.commit()
            
            messagebox.showinfo("Success", "Password has been reset successfully!")
            reset_window.destroy()
            
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Password update failed: {err}")
        finally:
            if 'update_connection' in locals() and update_connection.is_connected():
                update_cursor.close()
                update_connection.close()
    
    # Update Button
    update_btn = ctk.CTkButton(reset_window, text="Update Password", 
                             command=update_password, width=300, height=40,
                             fg_color="#2C3E50", hover_color="#1E88E5")
    update_btn.pack(pady=10)
    
    # Cancel Button
    cancel_btn = ctk.CTkButton(reset_window, text="Cancel", 
                             command=reset_window.destroy, 
                             fg_color="#E74C3C", hover_color="#C0392B", 
                             width=300, height=40)
    cancel_btn.pack(pady=10)
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
            "SELECT user_id, first_name, last_name, is_active FROM Users WHERE email = %s AND password = %s",
            (email, hashed_password)
        )
        user = cursor.fetchone()

        if user:
            # Check if user is active
            if not user.get('is_active', 1):  # Default to active if column doesn't exist yet
                messagebox.showerror("Account Deactivated", 
                    "Your account has been deactivated. Please contact support for assistance.")
                return
                
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

# ------------------- Icon Loader Function -------------------
def load_icon(icon_path, size=(20, 20)):
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

# ----------------- Color Scheme -----------------
# Consistent color palette
PRIMARY_COLOR = "#2C3E50"  # Dark blue for main elements
SECONDARY_COLOR = "#3498DB"  # Lighter blue for accents
HOVER_COLOR = "#1E88E5"  # Hover state color
TEXT_COLOR = "#333333"  # Dark gray for text
LIGHT_TEXT = "#7F8C8D"  # Light gray for secondary text
BORDER_COLOR = "#E0E0E0"  # Light gray for borders

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

# Try to load a hotel logo image
hotel_logo_image = None
logo_path = "images/hotel_logo.png"  # Replace with your actual logo file
hotel_logo_image = load_icon(logo_path, size=(70, 70))

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

# --------------------- Email Field with Centered Label ---------------------
email_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
email_label_frame.pack(fill="x", pady=(0, 5))

# Load email icon
email_icon_image = None
email_icon_path = "images/email_icon.png"  # Replace with your actual icon file
email_icon_image = load_icon(email_icon_path)

# Create a label frame to contain both icon and text
email_label_container = ctk.CTkFrame(email_label_frame, fg_color="transparent")
email_label_container.pack(anchor="center")

# Add icon if available
if email_icon_image:
    email_icon_label = ctk.CTkLabel(
        email_label_container,
        text="",
        image=email_icon_image,
        width=20
    )
    email_icon_label.image = email_icon_image  # Keep a reference
    email_icon_label.pack(side="left", padx=(0, 5))

# Add text label
email_label = ctk.CTkLabel(
    email_label_container,
    text="Email",
    font=("Montserrat", 12),
    text_color=LIGHT_TEXT
)
email_label.pack(side="left")

# Email entry field
email_entry = ctk.CTkEntry(
    content_frame,
    width=400,
    height=45,
    placeholder_text="Enter your email",
    border_color=BORDER_COLOR,
    corner_radius=6
)
email_entry.pack(pady=(0, 15))
email_entry.focus()  # Set initial focus to email field

# --------------------- Password Field with Centered Label ---------------------
password_label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
password_label_frame.pack(fill="x", pady=(0, 5))

# Load password icon
password_icon_image = None
password_icon_path = "images/lock_icon.png"  # Replace with your actual icon file
password_icon_image = load_icon(password_icon_path)

# Create a label frame to contain both icon and text
password_label_container = ctk.CTkFrame(password_label_frame, fg_color="transparent")
password_label_container.pack(anchor="center")

# Add icon if available
if password_icon_image:
    password_icon_label = ctk.CTkLabel(
        password_label_container,
        text="",
        image=password_icon_image,
        width=20
    )
    password_icon_label.image = password_icon_image  # Keep a reference
    password_icon_label.pack(side="left", padx=(0, 5))

# Add text label
password_label = ctk.CTkLabel(
    password_label_container,
    text="Password",
    font=("Montserrat", 12),
    text_color=LIGHT_TEXT
)
password_label.pack(side="left")

# Password entry field
password_entry = ctk.CTkEntry(
    content_frame,
    width=400,
    height=45,
    show="•",
    placeholder_text="Enter your password",
    border_color=BORDER_COLOR,
    corner_radius=6
)
password_entry.pack(pady=(0, 15))
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