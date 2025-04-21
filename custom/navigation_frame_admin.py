import customtkinter as ctk
import subprocess
import sys

class AdminNavigationFrame:
    """Navigation sidebar for admin pages"""
    
    def __init__(self, parent, admin_data=None):
        self.parent = parent
        self.admin_data = admin_data
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
            ("📊 Dashboard", self.go_to_dashboard),
            ("📅 Manage Bookings", self.go_to_bookings),
            ("👤 Manage Users", self.go_to_users),
            ("🚪 Logout", self.logout)
        ]
        
        for btn_text, btn_command in nav_buttons:
            # Check if this is the current page to highlight it
            current_file = sys.argv[0].lower()
            is_active = False
            
            if "admin_dashboard" in current_file and "Dashboard" in btn_text:
                is_active = True
            elif "manage_bookings" in current_file and "Bookings" in btn_text:
                is_active = True
            elif "manage_users" in current_file and "Users" in btn_text:
                is_active = True
            
            btn = ctk.CTkButton(self.frame, text=btn_text, font=("Arial", 14), 
                              fg_color="#34495E" if is_active else "transparent", 
                              hover_color="#34495E",
                              anchor="w", height=40, width=180, 
                              command=btn_command)
            btn.pack(pady=5, padx=10)
        
        # Welcome message with admin name if available
        if self.admin_data and 'AdminName' in self.admin_data:
            admin_name = self.admin_data['AdminName']
            ctk.CTkLabel(self.frame, text=f"Welcome, {admin_name}", 
                       font=("Arial", 12), text_color="white").pack(pady=(50, 10))
    
    def go_to_dashboard(self):
        """Navigate to admin dashboard"""
        self.navigate_to("admin_dashboard")
    
    def go_to_bookings(self):
        """Navigate to booking management page"""
        self.navigate_to("manage_bookings")
    
    def go_to_users(self):
        """Navigate to user management page"""
        self.navigate_to("manage_users")
    
    def logout(self):
        """Log out and return to login page"""
        self.navigate_to("auth")
    
    def navigate_to(self, page_name):
        """Navigate to another page"""
        try:
            # Pass the current admin ID to the next page if an admin is logged in
            admin_param = []
            if self.admin_data and 'Admin_ID' in self.admin_data:
                admin_param = [str(self.admin_data['Admin_ID'])]
            
            # Construct the command to run the appropriate Python file
            if page_name == "auth":
                # For logout, go to auth page for login
                command = [sys.executable, "custom/auth.py"]
            else:
                # For other pages, go to the custom module
                command = [sys.executable, f"custom/{page_name}.py"] + admin_param
            
            subprocess.Popen(command)
            self.parent.winfo_toplevel().destroy()  # Close the current window
        except Exception as e:
            print(f"Navigation Error: {e}")