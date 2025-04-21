import customtkinter as ctk
from tkinter import messagebox
import mysql.connector
import subprocess
import sys
from datetime import datetime

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="new_password",  # Replace with your MySQL password
        database="hotel_book"  # Replace with your database name
    )

# ------------------- Global Variables -------------------
current_user = None
selected_rating = 0

# ------------------- User Session Management -------------------
def load_user_session():
    """Load user information from database"""
    global current_user
    
    # Check if any user_id was passed as a command line argument
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
            
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Users WHERE user_id = %s",
                (user_id,)
            )
            user_data = cursor.fetchone()
            
            if user_data:
                current_user = user_data
                # Pre-fill name field with user's name if available
                if name_entry:
                    name_entry.delete(0, 'end')
                    name_entry.insert(0, f"{user_data['first_name']} {user_data['last_name']}")
                return True
                
        except (ValueError, IndexError, mysql.connector.Error) as err:
            print(f"Error loading user session: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    return False

# ------------------- Navigation Functions -------------------
def open_page(page_name):
    """Open another page and close the current one"""
    try:
        # Pass the current user ID to the next page if a user is logged in
        user_param = [str(current_user['user_id'])] if current_user else []
        
        # Construct the command to run the appropriate Python file
        command = [sys.executable, f"{page_name.lower()}.py"] + user_param
        
        subprocess.Popen(command)
        app.destroy()  # Close the current window
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Unable to open {page_name} page: {e}")

def go_to_home():
    open_page("home")

def go_to_bookings():
    open_page("bookings")

def go_to_profile():
    open_page("profile")

def go_to_feedback():
    open_page("feedback")

def logout():
    """Log out the current user and return to login page"""
    global current_user
    current_user = None
    open_page("login")

# ------------------- Rating Functions -------------------
def set_rating(rating):
    """Set the selected rating value and update star appearance"""
    global selected_rating
    selected_rating = rating
    
    # Update star appearance based on rating
    for i in range(1, 6):
        if i <= rating:
            # Set filled star
            star_buttons[i-1].configure(text="★", text_color="#FFD700", font=("Arial", 24))
        else:
            # Set empty star
            star_buttons[i-1].configure(text="☆", text_color="#B0B0B0", font=("Arial", 24))

# ------------------- Submit Feedback -------------------
def submit_feedback():
    """Submit the feedback to the database"""
    # Get form values
    name = name_entry.get()
    comment = feedback_text.get("1.0", "end-1c")  # Get text from the text area
    
    # Validate inputs
    if not name:
        messagebox.showwarning("Input Error", "Please enter your name.")
        return
    
    if selected_rating == 0:
        messagebox.showwarning("Input Error", "Please select a rating.")
        return
    
    if not comment or len(comment.strip()) < 5:
        messagebox.showwarning("Input Error", "Please provide feedback comments (minimum 5 characters).")
        return
    
    # Determine user ID (use current_user if available, otherwise use name to lookup)
    user_id = None
    if current_user:
        user_id = current_user['user_id']
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # If we don't have a user ID but have a name, try to look up the user
        if not user_id:
            cursor.execute(
                "SELECT user_id FROM Users WHERE CONCAT(first_name, ' ', last_name) = %s LIMIT 1",
                (name,)
            )
            user_result = cursor.fetchone()
            if user_result:
                user_id = user_result[0]
        
        # Insert feedback into the database
        # Adjust table/column names according to your schema
        cursor.execute(
            """
            INSERT INTO Review (User_ID, Rating, Comments, Review_Date)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, selected_rating, comment, datetime.now().strftime('%Y-%m-%d'))
        )
        
        connection.commit()
        messagebox.showinfo("Success", "Thank you for your feedback!")
        
        # Clear form
        name_entry.delete(0, 'end')
        feedback_text.delete("1.0", "end")
        set_rating(0)
        
        # Optionally redirect back to home page
        # go_to_home()
        
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# ----------------- Initialize App -----------------
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Hotel Booking - Feedback")
app.geometry("1200x700")
app.resizable(False, False)

# ----------------- Main Frame -----------------
main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
main_frame.pack(expand=True, fill="both")

# ----------------- Sidebar (Navigation) -----------------
sidebar = ctk.CTkFrame(main_frame, fg_color="#2C3E50", width=200, corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)  # Prevent the frame from shrinking

# Header with logo
ctk.CTkLabel(sidebar, text="🏨 Hotel Booking", font=("Arial", 18, "bold"), text_color="white").pack(pady=(30, 20))

# Navigation buttons with icons
nav_buttons = [
    ("🏠 Home", go_to_home),
    ("📅 Bookings", go_to_bookings),
    ("👤 Profile", go_to_profile),
    ("💬 Feedback", go_to_feedback),
    ("🚪 Logout", logout)
]

for btn_text, btn_command in nav_buttons:
    is_active = "Feedback" in btn_text
    btn = ctk.CTkButton(sidebar, text=btn_text, font=("Arial", 14), 
                      fg_color="#34495E" if is_active else "transparent", 
                      hover_color="#34495E",
                      anchor="w", height=40, width=180, 
                      command=btn_command)
    btn.pack(pady=5, padx=10)

# Welcome message with username if available
if current_user:
    username = f"{current_user['first_name']} {current_user['last_name']}"
    ctk.CTkLabel(sidebar, text=f"Welcome, {username}", 
               font=("Arial", 12), text_color="white").pack(pady=(50, 10))

# ----------------- Content Area -----------------
content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
content_frame.pack(side="right", fill="both", expand=True)

# ----------------- Feedback Header -----------------
header_frame = ctk.CTkFrame(content_frame, fg_color="white", height=100)
header_frame.pack(fill="x", padx=30, pady=(30, 0))

ctk.CTkLabel(header_frame, text="Give Your", 
           font=("Arial", 30, "bold"), text_color="#2C3E50").pack(anchor="center")
ctk.CTkLabel(header_frame, text="Feedback", 
           font=("Arial", 30, "bold"), text_color="#2C3E50").pack(anchor="center")

# ----------------- Feedback Form -----------------
form_frame = ctk.CTkFrame(content_frame, fg_color="white", border_width=1, 
                        border_color="#E5E5E5", corner_radius=10)
form_frame.pack(fill="both", expand=True, padx=100, pady=30)

# Form content
form_content = ctk.CTkFrame(form_frame, fg_color="white")
form_content.pack(fill="both", expand=True, padx=30, pady=30)

# Title
title_frame = ctk.CTkFrame(form_content, fg_color="white")
title_frame.pack(fill="x", pady=(0, 20))
ctk.CTkLabel(title_frame, text="💬 We Value Your Feedback", 
           font=("Arial", 20, "bold"), text_color="#2C3E50").pack(anchor="center")

# Name Input
name_label = ctk.CTkLabel(form_content, text="👤 Full Name", font=("Arial", 14))
name_label.pack(anchor="center", pady=(0, 5))
name_entry = ctk.CTkEntry(form_content, width=400, height=40, placeholder_text="Enter your full name")
name_entry.pack(anchor="center", pady=(0, 20))

# Rating Stars
rating_label = ctk.CTkLabel(form_content, text="⭐ Rate Your Experience", font=("Arial", 14))
rating_label.pack(anchor="center", pady=(0, 5))

# Star rating buttons
stars_frame = ctk.CTkFrame(form_content, fg_color="white", height=50)
stars_frame.pack(fill="x", pady=(0, 20))

star_buttons = []
for i in range(1, 6):
    star_btn = ctk.CTkButton(stars_frame, text="☆", width=30, height=30, 
                           font=("Arial", 24), text_color="#B0B0B0",
                           command=lambda i=i: set_rating(i))
    star_btn.pack(side="left", padx=5, expand=True)
    star_buttons.append(star_btn)

# Feedback Text
feedback_label = ctk.CTkLabel(form_content, text="💭 Your Feedback", font=("Arial", 14))
feedback_label.pack(anchor="center", pady=(0, 5))
feedback_text = ctk.CTkTextbox(form_content, width=600, height=150, 
                             corner_radius=5, border_width=1, border_color="#E5E5E5")
feedback_text.pack(anchor="center", pady=(0, 20))
feedback_text.insert("1.0", "Write your feedback here...")
feedback_text.bind("<FocusIn>", lambda e: feedback_text.delete("1.0", "end") if 
                 feedback_text.get("1.0", "end-1c") == "Write your feedback here..." else None)

# Submit Button
submit_btn = ctk.CTkButton(form_content, text="Submit Feedback", 
                         font=("Arial", 14, "bold"),
                         fg_color="#0F2D52", hover_color="#1E4D88",
                         height=45, width=400, command=submit_feedback)
submit_btn.pack(anchor="center", pady=(10, 0))

# Try to load user session
load_user_session()

# Run the application
if __name__ == "__main__":
    app.mainloop()