import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("TkAgg")
from datetime import datetime, timedelta
import calendar
import sys
from tkinter import messagebox

import config
from custom.navigation_frame_admin import AdminNavigationFrame

# ------------------- Global Variables -------------------
current_admin = None

# ------------------- Admin Session Management -------------------
def load_admin_session():
    """Load admin information from database"""
    global current_admin
    
    # Check if any admin_id was passed as a command line argument
    if len(sys.argv) > 1:
        try:
            admin_id = int(sys.argv[1])
            
            connection = config.connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM Admin WHERE Admin_ID = %s",
                (admin_id,)
            )
            admin_data = cursor.fetchone()
            
            if admin_data:
                current_admin = admin_data
                return True
                
        except Exception as err:
            print(f"Error loading admin session: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    
    return False

# ------------------- Data Fetching Functions -------------------
def get_dashboard_stats():
    """Fetch statistics for dashboard"""
    stats = {
        "total_bookings": 0,
        "total_revenue": 0,
        "active_users": 0,
        "hotels_listed": 0
    }
    
    try:
        connection = config.connect_db()
        cursor = connection.cursor()
        
        # Get total bookings
        cursor.execute("SELECT COUNT(*) FROM Booking")
        stats["total_bookings"] = cursor.fetchone()[0]
        
        # Get total revenue
        cursor.execute("SELECT SUM(Total_Cost) FROM Booking")
        total_revenue = cursor.fetchone()[0]
        stats["total_revenue"] = total_revenue if total_revenue else 0
        
        # Get active users
        cursor.execute("SELECT COUNT(*) FROM Users")
        stats["active_users"] = cursor.fetchone()[0]
        
        # Get hotels (rooms) listed - assuming Room table contains hotel rooms
        cursor.execute("SELECT COUNT(*) FROM Room")
        stats["hotels_listed"] = cursor.fetchone()[0]
        
    except Exception as err:
        print(f"Database Error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    
    return stats

def get_monthly_data():
    """Fetch monthly revenue and booking data for the last 6 months"""
    months = []
    revenue = []
    bookings = []
    
    try:
        connection = config.connect_db()
        cursor = connection.cursor()
        
        # Get current date and date 6 months ago
        today = datetime.today()
        six_months_ago = today - timedelta(days=180)
        
        # Get data for each month
        current = six_months_ago
        while current <= today:
            month_start = datetime(current.year, current.month, 1)
            if current.month == 12:
                next_month = datetime(current.year + 1, 1, 1)
            else:
                next_month = datetime(current.year, current.month + 1, 1)
            
            # Get bookings count for this month
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM Booking 
                WHERE Check_IN_Date >= %s AND Check_IN_Date < %s
                """,
                (month_start, next_month)
            )
            month_bookings = cursor.fetchone()[0]
            
            # Get revenue for this month
            cursor.execute(
                """
                SELECT SUM(Total_Cost) 
                FROM Booking 
                WHERE Check_IN_Date >= %s AND Check_IN_Date < %s
                """,
                (month_start, next_month)
            )
            month_revenue = cursor.fetchone()[0]
            
            # Add to lists
            months.append(calendar.month_abbr[current.month])
            bookings.append(month_bookings)
            revenue.append(month_revenue if month_revenue else 0)
            
            # Move to next month
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
        
    except Exception as err:
        print(f"Database Error: {err}")
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
    
    return months, revenue, bookings

# ------------------- Main Function -------------------
def main():
    global current_admin
    
    # Check if admin is logged in
    if not load_admin_session():
        messagebox.showwarning("Login Required", "Admin login required to access this page")
        import subprocess
        subprocess.Popen([sys.executable, "custom/auth.py", "--mode=admin"])
        return
    
    # Initialize the app
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    app = ctk.CTk()
    app.title("Hotel Booking - Admin Dashboard")
    app.geometry("1200x700")
    app.resizable(False, False)
    
    # Main frame
    main_frame = ctk.CTkFrame(app, fg_color="white", corner_radius=0)
    main_frame.pack(expand=True, fill="both")
    
    # Add navigation sidebar
    nav_frame = AdminNavigationFrame(main_frame, current_admin)
    
    # Create content frame
    content_frame = ctk.CTkFrame(main_frame, fg_color="white", corner_radius=0)
    content_frame.pack(side="right", fill="both", expand=True)
    
    # ----------------- Header -----------------
    header_frame = ctk.CTkFrame(content_frame, fg_color="white", height=60)
    header_frame.pack(fill="x", padx=30, pady=(30, 20))
    
    header_title = ctk.CTkLabel(header_frame, text="Admin", 
                              font=("Arial", 28, "bold"), text_color="#2C3E50")
    header_title.pack(anchor="center")
    
    header_subtitle = ctk.CTkLabel(header_frame, text="Dashboard", 
                                 font=("Arial", 28, "bold"), text_color="#2C3E50")
    header_subtitle.pack(anchor="center")
    
    # ----------------- Stats Cards Section -----------------
    # Fetch stats from database
    stats = get_dashboard_stats()
    
    stats_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    stats_frame.pack(fill="x", padx=30, pady=(0, 20))
    
    # Create stat cards
    stat_cards = [
        ("Total\nBookings", f"{stats['total_bookings']:,}"),
        ("Total\nRevenue", f"${stats['total_revenue']:,}"),
        ("Active\nUsers", f"{stats['active_users']:,}"),
        ("Hotels\nListed", f"{stats['hotels_listed']:,}")
    ]
    
    for title, value in stat_cards:
        card = ctk.CTkFrame(stats_frame, fg_color="white", corner_radius=10,
                          border_width=1, border_color="#E5E5E5", width=150, height=100)
        card.pack(side="left", padx=10, expand=True, fill="both")
        
        ctk.CTkLabel(card, text=title, font=("Arial", 14, "bold"), 
                   text_color="#2C3E50").pack(pady=(15, 5))
        ctk.CTkLabel(card, text=value, font=("Arial", 24, "bold"), 
                   text_color="#2C3E50").pack(pady=(5, 15))
    
    # ----------------- Chart Section -----------------
    chart_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10,
                             border_width=1, border_color="#E5E5E5")
    chart_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
    
    # Chart Header
    chart_header = ctk.CTkFrame(chart_frame, fg_color="white", height=40)
    chart_header.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(chart_header, text="Revenue & Bookings Overview", 
               font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w")
    
    # Fetch chart data from database
    months, revenue, bookings = get_monthly_data()
    
    # Create matplotlib figure for the chart
    fig = Figure(figsize=(10, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    # Plot revenue
    revenue_line, = ax.plot(months, revenue, marker='o', linewidth=2, color='#007BFF', label='Revenue ($)')
    
    # Create a second y-axis for bookings
    ax2 = ax.twinx()
    booking_line, = ax2.plot(months, bookings, marker='s', linewidth=2, color='#28A745', label='Bookings')
    
    # Add grid and legends
    ax.grid(True, linestyle='--', alpha=0.7)
    lines = [revenue_line, booking_line]
    labels = [line.get_label() for line in lines]
    ax.legend(lines, labels, loc='upper left')
    
    # Set labels and title
    ax.set_xlabel('Month')
    ax.set_ylabel('Revenue ($)', color='#007BFF')
    ax2.set_ylabel('Bookings', color='#28A745')
    
    # Format the chart for better appearance
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax2.spines['top'].set_visible(False)
    ax2.tick_params(axis='y', colors='#28A745')
    ax.tick_params(axis='y', colors='#007BFF')
    
    # Format y-axis labels with commas for thousands
    ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    
    # Adjust margins
    fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
    
    # Embed the chart in the tkinter window
    chart_canvas = FigureCanvasTkAgg(fig, master=chart_frame)
    chart_canvas.draw()
    chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
    
    # Run the application
    app.mainloop()

if __name__ == "__main__":
    main()