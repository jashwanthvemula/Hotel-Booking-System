import customtkinter as ctk
from tkinter import messagebox
import subprocess
import sys
import hashlib
from PIL import Image, ImageTk
import config
from utils import hash_password

# Global variables
mode = "login"  # Default mode

# ------------------- User Authentication Functions -------------------
def login_user():
    email = email_entry.get()
    password = password_entry.get()

    if not email or not password:
        messagebox.showwarning("Input Error", "Please enter both email and password.")
        return

    hashed_password = hash_password(password)

    try:
        connection = config.connect_db()
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
            subprocess.Popen([sys.executable, "custom/home.py", str(user['user_id'])])
            app.destroy()  # Close the login window
        else:
            messagebox.showerror("Login Failed", "Invalid Email or Password.")
    
    except Exception as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

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
        connection = config.connect_db()
        cursor = connection.cursor()

        # Insert the user data into the database
        cursor.execute(
            "INSERT INTO Users (first_name, last_name, email, phone, password) VALUES (%s, %s, %s, %s, %s)",
            (first_name, last_name, email, phone, hashed_password)
        )

        connection.commit()
        messagebox.showinfo("Success", "Account created successfully!")
        
        # After successful registration, redirect to login page
        show_login_screen()

    except Exception as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def login_admin():
    email = email_entry.get()
    password = password_entry.get()

    if not email or not password:
        messagebox.showwarning("Input Error", "Please enter both email and password.")
        return

    hashed_password = hash_password(password)

    try:
        connection = config.connect_db()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT Admin_ID, AdminName FROM Admin WHERE AdminEmail = %s AND AdminPassword = %s",
            (email, hashed_password)
        )
        admin = cursor.fetchone()

        if admin:
            messagebox.showinfo("Success", f"Welcome {admin['AdminName']}!")
            
            # Remember the login if checkbox is checked
            if remember_var.get():
                # In a real app, you would use a more secure method
                # For this example, we'll just simulate remembering the login
                print(f"Remembering admin login for: {email}")
            
            # Open admin dashboard with admin ID
            subprocess.Popen([sys.executable, "custom/admin_dashboard.py", str(admin['Admin_ID'])])
            app.destroy()  # Close the login window
        else:
            messagebox.showerror("Login Failed", "Invalid Admin Credentials.")
    
    except Exception as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def forgot_password(event=None):
    if mode == "admin":
        forgot_admin_password()
    else:
        forgot_user_password()

def forgot_user_password():
    email = email_entry.get()
    if not email:
        messagebox.showwarning("Input Required", "Please enter your email address first.")
        return
        
    try:
        connection = config.connect_db()
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
    
    except Exception as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

def forgot_admin_password():
    email = email_entry.get()
    if not email:
        messagebox.showwarning("Input Required", "Please enter your email address first.")
        return
        
    try:
        connection = config.connect_db()
        cursor = connection.cursor()
        cursor.execute("SELECT Admin_ID FROM Admin WHERE AdminEmail = %s", (email,))
        admin = cursor.fetchone()
        
        if admin:
            # In a real application, you would send a password reset email
            # For now, just show a message
            messagebox.showinfo("Password Reset", 
                f"A password reset link has been sent to {email}.\n\n"
                f"Please check your email.")
        else:
            messagebox.showwarning("Account Not Found", "No admin account found with this email address.")
    
    except Exception as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ------------------- Navigation Functions -------------------
def back_to_main():
    subprocess.Popen([sys.executable, "main.py"])
    app.destroy()  # Close the current window

def show_login_screen(event=None):
    global mode
    mode = "login"
    reset_frame()
    build_login_screen()

def show_signup_screen(event=None):
    global mode
    mode = "signup"
    reset_frame()
    build_signup_screen()

def show_admin_login_screen(event=None):
    global mode
    mode = "admin"
    reset_frame()
    build_admin_login_screen()

def handle_enter(event):
    if mode == "login":
        login_user()
    elif mode == "admin":
        login_admin()
    elif mode == "signup" and 'confirm_password_entry' in globals():
        signup_user()

# ------------------- UI Building Functions -------------------
def reset_frame():
    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()

def build_login_screen():
    global email_entry, password_entry, remember_var

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
    signup_link.bind("<Button-1>", show_signup_screen)

    # Admin Login Link
    admin_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    admin_frame.pack(pady=(20, 0))

    admin_link = ctk.CTkLabel(admin_frame, text="Admin Login", text_color="#6c757d", 
                            font=("Arial", 12), cursor="hand2")
    admin_link.pack()
    admin_link.bind("<Button-1>", show_admin_login_screen)

    # Back button
    back_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    back_frame.pack(pady=(20, 0))
    back_btn = ctk.CTkButton(back_frame, text="Back to Main Menu", font=("Arial", 12),
                           fg_color="#6c757d", hover_color="#5a6268",
                           height=30, width=200, command=back_to_main)
    back_btn.pack()

    # Version info
    version_label = ctk.CTkLabel(content_frame, text="v1.0.0", text_color="#6c757d", font=("Arial", 10))
    version_label.pack(pady=(20, 0))

# ------------------- Main Function -------------------
def main():
    global app, content_frame, mode
    
    # Process command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--mode=signup":
            mode = "signup"
        elif sys.argv[1] == "--mode=admin":
            mode = "admin"
        else:
            mode = "login"
    
    # Create the main application window
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    
    if mode == "signup":
        app.title("Hotel Booking - Sign Up")
    elif mode == "admin":
        app.title("Hotel Booking - Admin Login")
    else:
        app.title("Hotel Booking - Login")
        
    app.geometry("1000x800")
    app.resizable(False, False)
    
    # Create main layout
    main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
    main_frame.pack(expand=True, fill="both")
    
    # Left Frame (Image)
    if mode == "admin":
        bg_color = "#1A365D"  # Darker blue for admin
    else:
        bg_color = "#3A546E"
        
    left_frame = ctk.CTkFrame(main_frame, fg_color=bg_color, width=500, corner_radius=0)
    left_frame.pack(side="left", fill="both", expand=True)
    
    # Try to load the hotel image
    try:
        image_frame = ctk.CTkFrame(left_frame, fg_color=bg_color)
        image_frame.pack(fill="both", expand=True)
        
        image_label = ctk.CTkLabel(image_frame, text="", fg_color=bg_color)
        image_label.pack(fill="both", expand=True)
        
        try:
            image_path = "static/images/city_hotel.png"
            hotel_image = Image.open(image_path)
            
            width, height = 400, 300
            hotel_image = hotel_image.resize((width, height), Image.LANCZOS)
            
            hotel_photo = ImageTk.PhotoImage(hotel_image)
            
            image_label.configure(image=hotel_photo)
            image_label.image = hotel_photo
        except:
            image_label.configure(text="Hotel Image Not Found", font=("Arial", 24, "bold"), text_color="white")
    except:
        ctk.CTkLabel(left_frame, text="Hotel Booking System", 
                   font=("Arial", 24, "bold"), text_color="white").pack(pady=300)
    
    # Right Frame (Form)
    right_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
    right_frame.pack(side="right", fill="both", expand=True)
    
    # Content Container
    content_frame = ctk.CTkFrame(right_frame, fg_color="white", width=400)
    content_frame.pack(expand=True, fill="both", padx=50)
    
    # Build the appropriate screen based on mode
    if mode == "signup":
        build_signup_screen()
    elif mode == "admin":
        build_admin_login_screen()
    else:
        build_login_screen()
    
    app.mainloop()

if __name__ == "__main__":
    main()

def build_signup_screen():
    global fullname_entry, email_entry, phone_entry, password_entry, confirm_password_entry, agree_var

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
    confirm_password_entry.bind("<Return>", handle_enter)

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
    login_frame.pack(pady=(0, 10))

    ctk.CTkLabel(login_frame, text="Already have an account? ", font=("Arial", 12)).pack(side="left")
    login_link = ctk.CTkLabel(login_frame, text="Login", text_color="#1E90FF", 
                            font=("Arial", 12, "bold"), cursor="hand2")
    login_link.pack(side="left")
    login_link.bind("<Button-1>", show_login_screen)
    
    # Back button
    back_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    back_frame.pack(pady=(10, 0))
    back_btn = ctk.CTkButton(back_frame, text="Back to Main Menu", font=("Arial", 12),
                           fg_color="#6c757d", hover_color="#5a6268",
                           height=30, width=200, command=back_to_main)
    back_btn.pack()
    
def build_admin_login_screen():
    global email_entry, password_entry, remember_var

    # Admin Icon and Title
    ctk.CTkLabel(content_frame, text="👤", font=("Arial", 40)).pack(pady=(80, 0))
    ctk.CTkLabel(content_frame, text="Admin Login", font=("Arial", 30, "bold")).pack(pady=(0, 10))
    ctk.CTkLabel(content_frame, text="Hotel Management System", font=("Arial", 20)).pack(pady=(0, 30))

    # Email
    ctk.CTkLabel(content_frame, text="✉️ Admin Email", font=("Arial", 14), anchor="center").pack()
    email_entry = ctk.CTkEntry(content_frame, width=400, height=40, placeholder_text="Enter your admin email")
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
    login_btn = ctk.CTkButton(content_frame, text="Admin Login", font=("Arial", 14, "bold"), 
                            fg_color="#192F59", hover_color="#2C3E50",  # Darker color for admin login
                            width=400, height=45, corner_radius=5, command=login_admin)
    login_btn.pack(pady=(0, 20))

    # Back to User Login
    back_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    back_frame.pack(pady=(20, 0))

    back_link = ctk.CTkLabel(back_frame, text="← Back to User Login", text_color="#1E90FF", 
                           font=("Arial", 12, "bold"), cursor="hand2")
    back_link.pack()
    back_link.bind("<Button-1>", show_login_screen)

    # Security Notice
    security_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    security_frame.pack(pady=(20, 0))

    security_label = ctk.CTkLabel(security_frame, 
                                text="This area is restricted to authorized personnel only.", 
                                text_color="#DC3545", font=("Arial", 11))
    security_label.pack()
    
    # Back to main menu
    main_back_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    main_back_frame.pack(pady=(20, 0))
    back_btn = ctk.CTkButton(main_back_frame, text="Back to Main Menu", font=("Arial", 12),
                           fg_color="#6c757d", hover_color="#5a6268",
                           height=30, width=200, command=back_to_main)
    back_btn.pack()

    # Version info
    version_label = ctk.CTkLabel(content_frame, text="v1.0.0", text_color="#6c757d", font=("Arial", 10))
    version_label.pack(pady=(20, 0))