import customtkinter as ctk
import subprocess
import sys

class UserNavigationFrame:
    """Navigation sidebar for user pages"""
    
    def __init__(self, parent, user_data=None):
        self.parent = parent
        self.user_data = user_data
        self.frame = None
        self.create_frame()
        
    def create_frame(self):
        """Create the navigation sidebar frame"""
        self.frame = ctk.CTkFrame(self.parent, fg_color="#2C3E50", width=200, corner_radius=0)
        self.frame.pack(side="left", fill="y")
        self.frame.pack_propagate(False)  # Prevent the frame from shrinking
        
        # Header with logo
        ctk.CTkLabel(self.frame, text="🏨 Hotel Booking", 
                   font=("Arial", 18, "bold"), text_color="white").pack(pady=(30, 20))
        
        # Navigation buttons with icons
        nav_buttons = [
            ("🏠 Home", self.go_to_home),
            ("📅 Bookings", self.go_to_bookings),
            ("👤 Profile", self.go_to_profile),
            ("💬 Feedback", self.go_to_feedback),
            ("🚪 Logout", self.logout)
        ]
        
        for btn_text, btn_command in nav_buttons:
            # Check if this is the current page to highlight it
            current_file = sys.argv[0].lower()
            is_active = False
            
            if "home.py" in current_file and "Home" in btn_text:
                is_active = True
            elif "book" in current_file and "Bookings" in btn_text:
                is_active = True
            elif "profile" in current_file and "Profile" in btn_text:
                is_active = True
            elif "feedback" in current_file and "Feedback" in btn_text:
                is_active = True
            
            btn = ctk.CTkButton(self.frame, text=btn_text, font=("Arial", 14), 
                              fg_color="#34495E" if is_active else "transparent", 
                              hover_color="#34495E",
                              anchor="w", height=40, width=180, 
                              command=btn_command)
            btn.pack(pady=5, padx=10)
        
        # Welcome message with username if available
        if self.user_data:
            username = f"{self.user_data['first_name']} {self.user_data['last_name']}"
            ctk.CTkLabel(self.frame, text=f"Welcome, {username}", 
                       font=("Arial", 12), text_color="white").pack(pady=(50, 10))
    
    def go_to_home(self):
        """Navigate to home page"""
        self.navigate_to("home")
    
    def go_to_bookings(self):
        """Navigate to bookings page"""
        self.navigate_to("booking")
    
    def go_to_profile(self):
        """Navigate to profile page"""
        self.navigate_to("user_profile")
    
    def go_to_feedback(self):
        """Navigate to feedback page"""
        self.navigate_to("feedback")
    
    def logout(self):
        """Log out and return to login page"""
        self.navigate_to("auth")
    
    def navigate_to(self, page_name):
        """Navigate to another page"""
        try:
            # Pass the current user ID to the next page if a user is logged in
            user_param = []
            if self.user_data and 'user_id' in self.user_data:
                user_param = [str(self.user_data['user_id'])]
            
            # Construct the command to run the appropriate Python file
            if page_name == "auth":
                # For logout, go to the auth page
                command = [sys.executable, "custom/auth.py"]
            else:
                # For other pages, go to the custom module
                command = [sys.executable, f"custom/{page_name}.py"] + user_param
            
            subprocess.Popen(command)
            self.parent.winfo_toplevel().destroy()  # Close the current window
        except Exception as e:
            print(f"Navigation Error: {e}")