import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
import mysql.connector
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib
matplotlib.use("TkAgg")
from datetime import datetime, timedelta
import calendar
import os
from PIL import Image, ImageTk
import shutil
import hashlib
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None
import pandas as pd
import uuid

# ------------------- Database Connection -------------------
def connect_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="new_password",
        database="hotel_book"
    )

# ------------------- Main Application Class -------------------
class HotelBookingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hotel Booking - Admin Dashboard")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 700)
        self.root.resizable(False, False)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Global variables
        self.current_admin = None
        self.selected_booking = None
        self.selected_user = None
        self.selected_hotel = None
        self.hotel_image_path = None

        # Load admin session
        self.load_admin_session()

        # Initialize UI
        self.setup_ui()

        # Initialize database tables for hotels
        self.setup_hotel_tables()

        # Show dashboard by default
        self.show_frame("dashboard")

    def load_admin_session(self):
        """Load admin information from database"""
        try:
            admin_id = 1  # Replace with actual admin ID logic (e.g., from login)
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Admin WHERE Admin_ID = %s", (admin_id,))
            admin_data = cursor.fetchone()
            if admin_data:
                self.current_admin = admin_data
                return True
        except mysql.connector.Error as err:
            print(f"Error loading admin session: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
        messagebox.showwarning("Login Required", "Admin login required")
        self.root.destroy()  # Close app if no admin session
        return False

    def setup_ui(self):
        """Set up the main application UI with sidebar and content area"""
        self.main_frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=0)
        self.main_frame.pack(expand=True, fill="both")

        # Sidebar
        self.setup_sidebar()

        # Content area
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Dictionary to hold section frames
        self.frames = {}

        # Initialize section frames
        self.frames["dashboard"] = self.create_dashboard_frame()
        self.frames["bookings"] = self.create_bookings_frame()
        self.frames["users"] = self.create_users_frame()
        self.frames["hotels"] = self.create_hotels_frame()
        self.frames["reports"] = self.create_reports_frame()

        # Hide all frames initially
        for frame in self.frames.values():
            frame.pack_forget()

    def setup_sidebar(self):
        """Set up the sidebar with navigation buttons"""
        sidebar = ctk.CTkFrame(self.main_frame, fg_color="#2C3E50", width=220, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=100)
        logo_frame.pack(fill="x", pady=(20, 10))
        ctk.CTkLabel(
            logo_frame,
            text="H",
            font=("Arial", 32, "bold"),
            text_color="white",
            fg_color="#3498DB",
            corner_radius=12,
            width=60,
            height=60
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(sidebar, text="Hotel Booking", font=("Arial", 18, "bold"), text_color="white").pack(pady=(0, 20))

        # Navigation buttons
        nav_buttons = [
            ("📊 Dashboard", lambda: self.show_frame("dashboard")),
            ("📅 Manage Bookings", lambda: self.show_frame("bookings")),
            ("👤 Manage Users", lambda: self.show_frame("users")),
            ("🏨 Manage Hotels", lambda: self.show_frame("hotels")),
            ("📈 Reports", lambda: self.show_frame("reports")),
            ("🚪 Logout", self.logout)
        ]

        for btn_text, btn_command in nav_buttons:
            btn = ctk.CTkButton(
                sidebar,
                text=btn_text,
                font=("Arial", 14),
                fg_color="transparent",
                hover_color="#34495E",
                anchor="w",
                height=45,
                width=200,
                command=btn_command
            )
            btn.pack(pady=5, padx=10)

        # Welcome message
        if self.current_admin:
            admin_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=80)
            admin_frame.pack(side="bottom", fill="x", pady=20, padx=10)
            admin_name = self.current_admin['AdminName']
            ctk.CTkLabel(admin_frame, text="Welcome,", font=("Arial", 12), text_color="#8395a7").pack(anchor="w")
            ctk.CTkLabel(admin_frame, text=admin_name, font=("Arial", 14, "bold"), text_color="white").pack(anchor="w")

    def show_frame(self, frame_name):
        """Show the specified frame and hide others"""
        # Hide all frames
        for frame in self.frames.values():
            frame.pack_forget()

        # Show the selected frame
        frame = self.frames[frame_name]
        frame.pack(fill="both", expand=True)

        # Refresh data for the frame
        if frame_name == "dashboard":
            self.populate_dashboard()
        elif frame_name == "bookings":
            self.populate_booking_table()
        elif frame_name == "users":
            self.populate_user_table()
        elif frame_name == "hotels":
            self.populate_hotel_table()
        elif frame_name == "reports":
            self.populate_reports()

    def logout(self):
        """Log out and close the application"""
        self.current_admin = None
        self.root.destroy()  # In a real app, redirect to login screen

    # ------------------- Dashboard Section -------------------
    def create_dashboard_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        ctk.CTkLabel(header_frame, text="Admin Dashboard", font=("Arial", 28, "bold"), text_color="#2C3E50").pack(anchor="center")

        # Stats Cards
        self.stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=30, pady=(0, 20))
        self.stats_cards = []

        # Chart Section
        chart_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E5E5")
        chart_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        ctk.CTkLabel(chart_frame, text="Revenue & Bookings Overview", font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w", padx=20, pady=10)
        
        self.fig = Figure(figsize=(10, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))

        return frame

    def get_dashboard_stats(self):
        stats = {"total_bookings": 0, "total_revenue": 0, "active_users": 0, "hotels_listed": 0}
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM Booking")
            stats["total_bookings"] = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(Total_Cost) FROM Booking")
            total_revenue = cursor.fetchone()[0]
            stats["total_revenue"] = total_revenue if total_revenue else 0
            cursor.execute("SELECT COUNT(*) FROM Users")
            stats["active_users"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Hotel")
            stats["hotels_listed"] = cursor.fetchone()[0]
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
        return stats

    def get_monthly_data(self):
        months, revenue, bookings = [], [], []
        try:
            connection = connect_db()
            cursor = connection.cursor()
            today = datetime.today()
            six_months_ago = today - timedelta(days=180)
            current = six_months_ago
            while current <= today:
                month_start = datetime(current.year, current.month, 1)
                next_month = datetime(current.year + 1, 1, 1) if current.month == 12 else datetime(current.year, current.month + 1, 1)
                cursor.execute("SELECT COUNT(*) FROM Booking WHERE Check_IN_Date >= %s AND Check_IN_Date < %s", (month_start, next_month))
                month_bookings = cursor.fetchone()[0]
                cursor.execute("SELECT SUM(Total_Cost) FROM Booking WHERE Check_IN_Date >= %s AND Check_IN_Date < %s", (month_start, next_month))
                month_revenue = cursor.fetchone()[0]
                months.append(calendar.month_abbr[current.month])
                bookings.append(month_bookings)
                revenue.append(month_revenue if month_revenue else 0)
                current = datetime(current.year + 1, 1, 1) if current.month == 12 else datetime(current.year, current.month + 1, 1)
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
        return months, revenue, bookings

    def populate_dashboard(self):
        # Clear existing stats cards
        for card in self.stats_cards:
            card.destroy()
        self.stats_cards.clear()

        # Fetch and display stats
        stats = self.get_dashboard_stats()
        stat_cards = [
            ("Total\nBookings", f"{stats['total_bookings']:,}"),
            ("Total\nRevenue", f"${stats['total_revenue']:,}"),
            ("Active\nUsers", f"{stats['active_users']:,}"),
            ("Hotels\nListed", f"{stats['hotels_listed']:,}")
        ]
        for title, value in stat_cards:
            card = ctk.CTkFrame(self.stats_frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E5E5", width=150, height=100)
            card.pack(side="left", padx=10, expand=True, fill="both")
            ctk.CTkLabel(card, text=title, font=("Arial", 14, "bold"), text_color="#2C3E50").pack(pady=(15, 5))
            ctk.CTkLabel(card, text=value, font=("Arial", 24, "bold"), text_color="#2C3E50").pack(pady=(5, 15))
            self.stats_cards.append(card)

        # Update chart
        months, revenue, bookings = self.get_monthly_data()
        self.ax.clear()
        revenue_line, = self.ax.plot(months, revenue, marker='o', linewidth=2, color='#007BFF', label='Revenue ($)')
        ax2 = self.ax.twinx()
        booking_line, = ax2.plot(months, bookings, marker='s', linewidth=2, color='#28A745', label='Bookings')
        self.ax.grid(True, linestyle='--', alpha=0.7)
        lines = [revenue_line, booking_line]
        self.ax.legend(lines, [line.get_label() for line in lines], loc='upper left')
        self.ax.set_xlabel('Month')
        self.ax.set_ylabel('Revenue ($)', color='#007BFF')
        ax2.set_ylabel('Bookings', color='#28A745')
        self.ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        ax2.spines['top'].set_visible(False)
        ax2.tick_params(axis='y', colors='#28A745')
        self.ax.tick_params(axis='y', colors='#007BFF')
        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
        self.chart_canvas.draw()

    # ------------------- Manage Bookings Section -------------------
    def create_bookings_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header_frame, text="Manage Bookings", font=("Arial", 28, "bold"), text_color="#2C3E50").pack(anchor="w")

        # Filter Section
        filter_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#E5E5E5", corner_radius=10)
        filter_frame.pack(fill="x", padx=30, pady=(0, 10))
        filter_header = ctk.CTkFrame(filter_frame, fg_color="white", height=40)
        filter_header.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(filter_header, text="Filter Bookings", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(anchor="w")
        
        filter_options = ctk.CTkFrame(filter_frame, fg_color="white")
        filter_options.pack(fill="x", padx=20, pady=(0, 10))
        
        # Search
        search_frame = ctk.CTkFrame(filter_options, fg_color="white")
        search_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(search_frame, text="Search", font=("Arial", 12)).pack(anchor="w")
        self.bookings_search_entry = ctk.CTkEntry(search_frame, width=150, placeholder_text="Customer or Room")
        self.bookings_search_entry.pack(pady=5)

        # Date Range
        date_frame = ctk.CTkFrame(filter_options, fg_color="white")
        date_frame.pack(side="left", padx=(10, 10))
        ctk.CTkLabel(date_frame, text="Date Range", font=("Arial", 12)).pack(anchor="w")
        date_fields = ctk.CTkFrame(date_frame, fg_color="white")
        date_fields.pack(fill="x")
        self.bookings_start_date_entry = DateEntry(date_fields, width=10, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd') if DateEntry else ctk.CTkEntry(date_fields, width=100, placeholder_text="YYYY-MM-DD")
        self.bookings_start_date_entry.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(date_fields, text="to", font=("Arial", 10)).pack(side="left", padx=5)
        self.bookings_end_date_entry = DateEntry(date_fields, width=10, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd') if DateEntry else ctk.CTkEntry(date_fields, width=100, placeholder_text="YYYY-MM-DD")
        self.bookings_end_date_entry.pack(side="left", padx=(5, 0))

        # Status Filter
        status_frame = ctk.CTkFrame(filter_options, fg_color="white")
        status_frame.pack(side="left", padx=(10, 10))
        ctk.CTkLabel(status_frame, text="Status", font=("Arial", 12)).pack(anchor="w")
        self.bookings_status_var = ctk.StringVar(value="All")
        status_options = ["All", "Pending", "Confirmed", "Cancelled"]
        self.bookings_status_dropdown = ctk.CTkComboBox(status_frame, values=status_options, variable=self.bookings_status_var, width=120)
        self.bookings_status_dropdown.pack(pady=5)

        # Filter Buttons
        button_frame = ctk.CTkFrame(filter_options, fg_color="white")
        button_frame.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(button_frame, text=" ", font=("Arial", 12)).pack(anchor="w")
        ctk.CTkButton(button_frame, text="Apply Filters", font=("Arial", 12), fg_color="#0F2D52", hover_color="#1E4D88", command=self.filter_bookings, width=100, height=30).pack(side="left", pady=5, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Reset", font=("Arial", 12), fg_color="#6C757D", hover_color="#5A6268", command=self.reset_booking_filters, width=80, height=30).pack(side="left", pady=5)

        # Booking Table
        table_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#E5E5E5", corner_radius=10)
        table_frame.pack(fill="x", padx=30, pady=(0, 10))
        table_header = ctk.CTkFrame(table_frame, fg_color="white", height=40)
        table_header.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(table_header, text="Bookings", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left")
        
        status_counts = ctk.CTkFrame(table_header, fg_color="white")
        status_counts.pack(side="right")
        self.bookings_total_count_label = ctk.CTkLabel(status_counts, text="Total: 0", font=("Arial", 12))
        self.bookings_total_count_label.pack(side="left", padx=(0, 15))
        self.bookings_confirmed_count_label = ctk.CTkLabel(status_counts, text="Confirmed: 0", font=("Arial", 12), text_color="#28A745")
        self.bookings_confirmed_count_label.pack(side="left", padx=(0, 15))
        self.bookings_pending_count_label = ctk.CTkLabel(status_counts, text="Pending: 0", font=("Arial", 12), text_color="#FFC107")
        self.bookings_pending_count_label.pack(side="left", padx=(0, 15))
        self.bookings_cancelled_count_label = ctk.CTkLabel(status_counts, text="Cancelled: 0", font=("Arial", 12), text_color="#DC3545")
        self.bookings_cancelled_count_label.pack(side="left")

        columns = ('Booking ID', 'Customer', 'Room Type', 'Check-in', 'Check-out', 'Amount', 'Status')
        self.bookings_table = ttk.Treeview(table_frame, columns=columns, show='headings', height=10)
        for col in columns:
            self.bookings_table.heading(col, text=col)
            self.bookings_table.column(col, width=100, anchor='center')
        self.bookings_table.tag_configure('confirmed', background='#d4edda')
        self.bookings_table.tag_configure('pending', background='#fff3cd')
        self.bookings_table.tag_configure('cancelled', background='#f8d7da')
        table_scroll = ttk.Scrollbar(table_frame, orient='vertical', command=self.bookings_table.yview)
        self.bookings_table.configure(yscrollcommand=table_scroll.set)
        table_scroll.pack(side='right', fill='y')
        self.bookings_table.pack(expand=True, fill='both', padx=20, pady=(0, 20))
        self.bookings_table.bind('<<TreeviewSelect>>', self.show_booking_details)

        # Booking Details
        self.bookings_details_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#E5E5E5", corner_radius=10, height=200)
        details_header = ctk.CTkFrame(self.bookings_details_frame, fg_color="white", height=40)
        details_header.pack(fill="x", padx=20, pady=10)
        self.bookings_details_booking_id = ctk.CTkLabel(details_header, text="Booking #", font=("Arial", 16, "bold"), text_color="#2C3E50")
        self.bookings_details_booking_id.pack(side="left")
        action_btns = ctk.CTkFrame(details_header, fg_color="white")
        action_btns.pack(side="right")
        self.bookings_confirm_btn = ctk.CTkButton(action_btns, text="Confirm", font=("Arial", 12), fg_color="#28A745", hover_color="#218838", command=self.confirm_booking, width=100, height=30, state="disabled")
        self.bookings_confirm_btn.pack(side="left", padx=(0, 5))
        self.bookings_cancel_btn = ctk.CTkButton(action_btns, text="Cancel", font=("Arial", 12), fg_color="#DC3545", hover_color="#C82333", command=self.cancel_booking, width=100, height=30, state="disabled")
        self.bookings_cancel_btn.pack(side="left", padx=(0, 5))
        ctk.CTkButton(action_btns, text="Delete", font=("Arial", 12), fg_color="#6C757D", hover_color="#5A6268", command=self.delete_booking_ui, width=100, height=30).pack(side="left")
        
        details_content = ctk.CTkFrame(self.bookings_details_frame, fg_color="white")
        details_content.pack(fill="x", padx=20, pady=(0, 20))
        self.bookings_details_customer = ctk.CTkLabel(details_content, text="Customer Name", font=("Arial", 14, "bold"), text_color="#2C3E50")
        self.bookings_details_customer.pack(anchor="w", pady=(0, 5))
        self.bookings_details_contact = ctk.CTkLabel(details_content, text="Email | Phone", font=("Arial", 12), text_color="#6C757D")
        self.bookings_details_contact.pack(anchor="w", pady=(0, 10))
        info_columns = ctk.CTkFrame(details_content, fg_color="white")
        info_columns.pack(fill="x")
        info_left = ctk.CTkFrame(info_columns, fg_color="white")
        info_left.pack(side="left", fill="both", expand=True)
        self.bookings_details_room = ctk.CTkLabel(info_left, text="Room Type", font=("Arial", 12), text_color="#2C3E50")
        self.bookings_details_room.pack(anchor="w", pady=2)
        self.bookings_details_dates = ctk.CTkLabel(info_left, text="Check-in: | Check-out:", font=("Arial", 12), text_color="#2C3E50")
        self.bookings_details_dates.pack(anchor="w", pady=2)
        info_right = ctk.CTkFrame(info_columns, fg_color="white")
        info_right.pack(side="right", fill="both", expand=True)
        self.bookings_details_price = ctk.CTkLabel(info_right, text="Price/night | Total", font=("Arial", 12), text_color="#2C3E50")
        self.bookings_details_price.pack(anchor="w", pady=2)
        self.bookings_details_status = ctk.CTkLabel(info_right, text="Status: ", font=("Arial", 12, "bold"), text_color="#2C3E50")
        self.bookings_details_status.pack(anchor="w", pady=2)

        return frame

    def load_bookings(self):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT b.Booking_ID, CONCAT(u.first_name, ' ', u.last_name) AS Customer,
                       r.Room_Type, b.Check_IN_Date, b.Check_Out_Date, 
                       b.Total_Cost, b.Booking_Status
                FROM Booking b
                JOIN Users u ON b.User_ID = u.user_id
                JOIN Room r ON b.Room_ID = r.Room_ID
                ORDER BY b.Check_IN_Date DESC
                """
            )
            bookings = cursor.fetchall()
            return bookings
        except mysql.connector.Error as err:
            print(f"Error loading bookings: {err}")
            messagebox.showerror("Database Error", f"Error loading bookings: {err}")
            return []
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def load_booking_details(self, booking_id):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT b.*, u.first_name, u.last_name, u.email, u.phone, 
                       r.Room_Type, r.Price_per_Night
                FROM Booking b
                JOIN Users u ON b.User_ID = u.user_id
                JOIN Room r ON b.Room_ID = r.Room_ID
                WHERE b.Booking_ID = %s
                """,
                (booking_id,)
            )
            booking = cursor.fetchone()
            return booking
        except mysql.connector.Error as err:
            print(f"Error loading booking details: {err}")
            messagebox.showerror("Database Error", f"Error loading booking details: {err}")
            return None
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def update_booking_status(self, booking_id, status):
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("UPDATE Booking SET Booking_Status = %s WHERE Booking_ID = %s", (status, booking_id))
            if status == "Cancelled":
                cursor.execute(
                    """
                    UPDATE Room r
                    JOIN Booking b ON r.Room_ID = b.Room_ID
                    SET r.Availability_status = 'Available'
                    WHERE b.Booking_ID = %s
                    """,
                    (booking_id,)
                )
            connection.commit()
            messagebox.showinfo("Success", f"Booking #{booking_id} status updated to {status}")
            return True
        except mysql.connector.Error as err:
            print(f"Error updating booking status: {err}")
            messagebox.showerror("Database Error", f"Error updating booking status: {err}")
            return False
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def delete_booking(self, booking_id):
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("SELECT Room_ID FROM Booking WHERE Booking_ID = %s", (booking_id,))
            room_id = cursor.fetchone()[0]
            cursor.execute("DELETE FROM Booking WHERE Booking_ID = %s", (booking_id,))
            cursor.execute("UPDATE Room SET Availability_status = 'Available' WHERE Room_ID = %s", (room_id,))
            connection.commit()
            messagebox.showinfo("Success", f"Booking #{booking_id} has been deleted")
            return True
        except mysql.connector.Error as err:
            print(f"Error deleting booking: {err}")
            messagebox.showerror("Database Error", f"Error deleting booking: {err}")
            return False
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def populate_booking_table(self):
        for row in self.bookings_table.get_children():
            self.bookings_table.delete(row)
        bookings = self.load_bookings()
        for booking in bookings:
            check_in = booking['Check_IN_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_IN_Date'], datetime) else booking['Check_IN_Date']
            check_out = booking['Check_Out_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_Out_Date'], datetime) else booking['Check_Out_Date']
            amount = f"${booking['Total_Cost']}"
            status = booking['Booking_Status']
            status_tag = status.lower()
            self.bookings_table.insert('', 'end', iid=booking['Booking_ID'], values=(
                booking['Booking_ID'],
                booking['Customer'],
                booking['Room_Type'],
                check_in,
                check_out,
                amount,
                status
            ), tags=(status_tag,))
        self.update_booking_status_counts()

    def update_booking_status_counts(self):
        bookings = self.bookings_table.get_children()
        total = len(bookings)
        confirmed = pending = cancelled = 0
        for booking_id in bookings:
            status = self.bookings_table.item(booking_id, 'values')[6]
            if status == "Confirmed":
                confirmed += 1
            elif status == "Pending":
                pending += 1
            elif status == "Cancelled":
                cancelled += 1
        self.bookings_total_count_label.configure(text=f"Total: {total}")
        self.bookings_confirmed_count_label.configure(text=f"Confirmed: {confirmed}")
        self.bookings_pending_count_label.configure(text=f"Pending: {pending}")
        self.bookings_cancelled_count_label.configure(text=f"Cancelled: {cancelled}")

    def show_booking_details(self, event):
        selected_id = self.bookings_table.focus()
        if not selected_id:
            return
        booking_id = int(selected_id)
        booking = self.load_booking_details(booking_id)
        if not booking:
            return
        self.selected_booking = booking
        self.bookings_details_booking_id.configure(text=f"Booking #{booking['Booking_ID']}")
        self.bookings_details_customer.configure(text=f"{booking['first_name']} {booking['last_name']}")
        self.bookings_details_contact.configure(text=f"{booking['email']} | {booking['phone'] if booking['phone'] else 'No phone'}")
        self.bookings_details_room.configure(text=f"{booking['Room_Type']}")
        self.bookings_details_dates.configure(text=(
            f"Check-in: {booking['Check_IN_Date'].strftime('%Y-%m-%d')} | "
            f"Check-out: {booking['Check_Out_Date'].strftime('%Y-%m-%d')}"
        ))
        self.bookings_details_price.configure(text=(
            f"${booking['Price_per_Night']}/night | "
            f"Total: ${booking['Total_Cost']}"
        ))
        self.bookings_details_status.configure(text=f"Status: {booking['Booking_Status']}")
        if booking['Booking_Status'] == "Pending":
            self.bookings_confirm_btn.configure(state="normal")
            self.bookings_cancel_btn.configure(state="normal")
        elif booking['Booking_Status'] == "Confirmed":
            self.bookings_confirm_btn.configure(state="disabled")
            self.bookings_cancel_btn.configure(state="normal")
        elif booking['Booking_Status'] == "Cancelled":
            self.bookings_confirm_btn.configure(state="normal")
            self.bookings_cancel_btn.configure(state="disabled")
        self.bookings_details_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def confirm_booking(self):
        if not self.selected_booking:
            return
        if self.update_booking_status(self.selected_booking['Booking_ID'], "Confirmed"):
            self.populate_booking_table()
            self.selected_booking['Booking_Status'] = "Confirmed"
            self.bookings_details_status.configure(text=f"Status: {self.selected_booking['Booking_Status']}")
            self.bookings_confirm_btn.configure(state="disabled")
            self.bookings_cancel_btn.configure(state="normal")

    def cancel_booking(self):
        if not self.selected_booking:
            return
        confirmed = messagebox.askyesno("Confirm Cancellation", f"Are you sure you want to cancel booking #{self.selected_booking['Booking_ID']}?")
        if not confirmed:
            return
        if self.update_booking_status(self.selected_booking['Booking_ID'], "Cancelled"):
            self.populate_booking_table()
            self.selected_booking['Booking_Status'] = "Cancelled"
            self.bookings_details_status.configure(text=f"Status: {self.selected_booking['Booking_Status']}")
            self.bookings_confirm_btn.configure(state="normal")
            self.bookings_cancel_btn.configure(state="disabled")

    def delete_booking_ui(self):
        if not self.selected_booking:
            return
        confirmed = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to DELETE booking #{self.selected_booking['Booking_ID']}?\n\nThis action cannot be undone.")
        if not confirmed:
            return
        if self.delete_booking(self.selected_booking['Booking_ID']):
            self.populate_booking_table()
            self.bookings_details_frame.pack_forget()
            self.selected_booking = None

    def filter_bookings(self):
        search_term = self.bookings_search_entry.get().lower()
        try:
            start_date = self.bookings_start_date_entry.get_date() if hasattr(self.bookings_start_date_entry, 'get_date') else None
            end_date = self.bookings_end_date_entry.get_date() if hasattr(self.bookings_end_date_entry, 'get_date') else None
        except:
            start_date = end_date = None
        status_filter = self.bookings_status_var.get()
        for row in self.bookings_table.get_children():
            self.bookings_table.delete(row)
        bookings = self.load_bookings()
        filtered_bookings = []
        for booking in bookings:
            if search_term and search_term not in booking['Customer'].lower() and search_term not in booking['Room_Type'].lower():
                continue
            booking_date = booking['Check_IN_Date']
            if isinstance(booking_date, str):
                try:
                    booking_date = datetime.strptime(booking_date, '%Y-%m-%d')
                except:
                    booking_date = None
            if start_date and booking_date and booking_date < start_date:
                continue
            if end_date and booking_date and booking_date > end_date:
                continue
            if status_filter != "All" and booking['Booking_Status'] != status_filter:
                continue
            filtered_bookings.append(booking)
        for booking in filtered_bookings:
            check_in = booking['Check_IN_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_IN_Date'], datetime) else booking['Check_IN_Date']
            check_out = booking['Check_Out_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_Out_Date'], datetime) else booking['Check_Out_Date']
            amount = f"${booking['Total_Cost']}"
            status = booking['Booking_Status']
            status_tag = status.lower()
            self.bookings_table.insert('', 'end', iid=booking['Booking_ID'], values=(
                booking['Booking_ID'],
                booking['Customer'],
                booking['Room_Type'],
                check_in,
                check_out,
                amount,
                status
            ), tags=(status_tag,))
        self.update_booking_status_counts()

    def reset_booking_filters(self):
        self.bookings_search_entry.delete(0, 'end')
        try:
            self.bookings_start_date_entry.set_date(None)
            self.bookings_end_date_entry.set_date(None)
        except:
            pass
        self.bookings_status_var.set("All")
        self.populate_booking_table()

    # ------------------- Manage Users Section -------------------
    def create_users_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header_frame, text="Manage Users", font=("Arial", 28, "bold"), text_color="#2C3E50").pack(side="left")
        
        action_frame = ctk.CTkFrame(header_frame, fg_color="white")
        action_frame.pack(side="right")
        ctk.CTkButton(action_frame, text="+ New User", font=("Arial", 12, "bold"), fg_color="#28A745", hover_color="#218838", command=self.new_user_mode, width=120, height=35, corner_radius=8).pack(side="left", padx=(0, 15))
        search_frame = ctk.CTkFrame(action_frame, fg_color="#E9ECEF", corner_radius=8, height=35)
        search_frame.pack(side="left", fill="y")
        self.users_search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Search users...", border_width=0, fg_color="#E9ECEF", height=35)
        self.users_search_entry.pack(side="left", padx=(10, 0))
        ctk.CTkButton(search_frame, text="🔍", font=("Arial", 12, "bold"), fg_color="#E9ECEF", text_color="#343A40", hover_color="#DEE2E6", width=35, height=35, corner_radius=0, command=self.search_users).pack(side="right")

        # User Form
        form_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        form_frame.pack(fill="x", padx=30, pady=(0, 20))
        form_header = ctk.CTkFrame(form_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        form_header.pack(fill="x")
        ctk.CTkLabel(form_header, text="User Information", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)
        
        form_fields = ctk.CTkFrame(form_frame, fg_color="white")
        form_fields.pack(fill="x", padx=20, pady=(20, 20))
        form_fields.columnconfigure(0, weight=1)
        form_fields.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(form_fields, text="First Name *", font=("Arial", 12), anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.users_first_name_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter first name")
        self.users_first_name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Last Name *", font=("Arial", 12), anchor="w").grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.users_last_name_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter last name")
        self.users_last_name_entry.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Email *", font=("Arial", 12), anchor="w").grid(row=4, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.users_email_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter email address")
        self.users_email_entry.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Phone", font=("Arial", 12), anchor="w").grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
        self.users_phone_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter phone number")
        self.users_phone_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Address", font=("Arial", 12), anchor="w").grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
        self.users_address_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter address")
        self.users_address_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Password *", font=("Arial", 12), anchor="w").grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
        self.users_password_entry = ctk.CTkEntry(form_fields, height=35, show="•", placeholder_text="Enter password")
        self.users_password_entry.grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))
        
        buttons_frame = ctk.CTkFrame(form_fields, fg_color="transparent")
        buttons_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        button_container.grid(row=0, column=1, columnspan=2)
        self.users_create_btn = ctk.CTkButton(button_container, text="Create User", font=("Arial", 13, "bold"), fg_color="#28A745", hover_color="#218838", command=self.create_user, width=140, height=40, corner_radius=8)
        self.users_update_btn = ctk.CTkButton(button_container, text="Update User", font=("Arial", 13, "bold"), fg_color="#2C3E50", hover_color="#1E4D88", command=self.update_user, width=140, height=40, corner_radius=8, state="disabled")
        self.users_delete_btn = ctk.CTkButton(button_container, text="Delete User", font=("Arial", 13, "bold"), fg_color="#DC3545", hover_color="#C82333", command=self.delete_user, width=140, height=40, corner_radius=8, state="disabled")
        self.users_clear_btn = ctk.CTkButton(button_container, text="Clear Form", font=("Arial", 13, "bold"), fg_color="#6C757D", hover_color="#5A6268", command=self.clear_user_form, width=140, height=40, corner_radius=8)
        self.users_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.users_clear_btn.grid(row=0, column=1)

        # User Table
        table_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        table_header = ctk.CTkFrame(table_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        table_header.pack(fill="x")
        ctk.CTkLabel(table_header, text="User List", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)
        self.users_user_count_label = ctk.CTkLabel(table_header, text="Total Users: 0", font=("Arial", 12))
        self.users_user_count_label.pack(side="right", padx=20, pady=10)
        
        table_container = ctk.CTkFrame(table_frame, fg_color="white")
        table_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        columns = ('ID', 'Name', 'Email', 'Phone', 'Address', 'Bookings')
        self.users_table = ttk.Treeview(table_container, columns=columns, show='headings', height=8)
        for col in columns:
            self.users_table.heading(col, text=col)
            self.users_table.column(col, width=120, anchor='w')
        table_scroll_y = ttk.Scrollbar(table_container, orient='vertical', command=self.users_table.yview)
        table_scroll_x = ttk.Scrollbar(table_container, orient='horizontal', command=self.users_table.xview)
        self.users_table.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)
        table_scroll_y.pack(side='right', fill='y')
        table_scroll_x.pack(side='bottom', fill='x')
        self.users_table.pack(expand=True, fill='both')
        self.users_table.bind('<<TreeviewSelect>>', self.show_user_details)

        # User Details
        self.users_details_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        details_header = ctk.CTkFrame(self.users_details_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        details_header.pack(fill="x")
        self.users_details_user_id = ctk.CTkLabel(details_header, text="User #", font=("Arial", 16, "bold"), text_color="#2C3E50")
        self.users_details_user_id.pack(side="left", padx=20, pady=10)
        
        details_content = ctk.CTkFrame(self.users_details_frame, fg_color="white")
        details_content.pack(fill="x", padx=20, pady=(15, 15))
        self.users_details_name = ctk.CTkLabel(details_content, text="Full Name", font=("Arial", 16, "bold"), text_color="#2C3E50")
        self.users_details_name.pack(anchor="w", pady=(0, 5))
        self.users_details_email = ctk.CTkLabel(details_content, text="Email", font=("Arial", 13), text_color="#6C757D")
        self.users_details_email.pack(anchor="w", pady=(0, 10))
        details_info_frame = ctk.CTkFrame(details_content, fg_color="white")
        details_info_frame.pack(fill="x", pady=(0, 15))
        details_info_frame.columnconfigure(0, weight=1)
        details_info_frame.columnconfigure(1, weight=1)
        self.users_details_phone = ctk.CTkLabel(details_info_frame, text="Phone: ", font=("Arial", 13), text_color="#6C757D")
        self.users_details_phone.grid(row=0, column=0, sticky="w", pady=(0, 5))
        self.users_details_address = ctk.CTkLabel(details_info_frame, text="Address: ", font=("Arial", 13), text_color="#6C757D")
        self.users_details_address.grid(row=1, column=0, sticky="w", pady=(0, 5))
        stats_frame = ctk.CTkFrame(details_content, fg_color="#E9ECEF", corner_radius=8)
        stats_frame.pack(fill="x", pady=(0, 15))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(stats_frame, text="🗓️", font=("Arial", 20)).grid(row=0, column=0, padx=(15, 5), pady=15, sticky="e")
        self.users_details_bookings = ctk.CTkLabel(stats_frame, text="Total Bookings: 0", font=("Arial", 13, "bold"), text_color="#2C3E50")
        self.users_details_bookings.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="w")
        ctk.CTkLabel(stats_frame, text="💰", font=("Arial", 20)).grid(row=0, column=2, padx=(15, 5), pady=15, sticky="e")
        self.users_details_spent = ctk.CTkLabel(stats_frame, text="Total Spent: $0", font=("Arial", 13, "bold"), text_color="#2C3E50")
        self.users_details_spent.grid(row=0, column=3, padx=(0, 15), pady=15, sticky="w")
        bookings_header = ctk.CTkFrame(details_content, fg_color="white")
        bookings_header.pack(fill="x", pady=(5, 10))
        ctk.CTkLabel(bookings_header, text="Recent Bookings", font=("Arial", 14, "bold"), text_color="#2C3E50").pack(side="left")
        bookings_container = ctk.CTkFrame(details_content, fg_color="white")
        bookings_container.pack(fill="x", pady=(0, 10))
        booking_columns = ('Booking ID', 'Room Type', 'Check-in', 'Check-out', 'Amount', 'Status')
        self.users_bookings_table = ttk.Treeview(bookings_container, columns=booking_columns, show='headings', height=4)
        for col in booking_columns:
            self.users_bookings_table.heading(col, text=col)
            self.users_bookings_table.column(col, width=100, anchor='center')
        self.users_bookings_table.tag_configure('confirmed', background='#d4edda')
        self.users_bookings_table.tag_configure('pending', background='#fff3cd')
        self.users_bookings_table.tag_configure('cancelled', background='#f8d7da')
        bookings_scroll_y = ttk.Scrollbar(bookings_container, orient='vertical', command=self.users_bookings_table.yview)
        bookings_scroll_x = ttk.Scrollbar(bookings_container, orient='horizontal', command=self.users_bookings_table.xview)
        self.users_bookings_table.configure(yscrollcommand=bookings_scroll_y.set, xscrollcommand=bookings_scroll_x.set)
        bookings_scroll_y.pack(side='right', fill='y')
        bookings_scroll_x.pack(side='bottom', fill='x')
        self.users_bookings_table.pack(fill="x")

        return frame

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def load_users(self):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone, 
                       u.user_address, COUNT(b.Booking_ID) as bookings
                FROM Users u
                LEFT JOIN Booking b ON u.user_id = b.User_ID
                GROUP BY u.user_id
                ORDER BY u.user_id
                """
            )
            users = cursor.fetchall()
            return users
        except mysql.connector.Error as err:
            print(f"Error loading users: {err}")
            messagebox.showerror("Database Error", f"Error loading users: {err}")
            return []
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def load_user_details(self, user_id):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT u.*, COUNT(b.Booking_ID) as bookings,
                       SUM(b.Total_Cost) as total_spent
                FROM Users u
                LEFT JOIN Booking b ON u.user_id = b.User_ID
                WHERE u.user_id = %s
                GROUP BY u.user_id
                """,
                (user_id,)
            )
            user = cursor.fetchone()
            if user:
                cursor.execute(
                    """
                    SELECT b.Booking_ID, r.Room_Type, b.Check_IN_Date, 
                           b.Check_Out_Date, b.Total_Cost, b.Booking_Status
                    FROM Booking b
                    JOIN Room r ON b.Room_ID = r.Room_ID
                    WHERE b.User_ID = %s
                    ORDER BY b.Check_IN_Date DESC
                    LIMIT 5
                    """,
                    (user_id,)
                )
                user['recent_bookings'] = cursor.fetchall()
            return user
        except mysql.connector.Error as err:
            print(f"Error loading user details: {err}")
            messagebox.showerror("Database Error", f"Error loading user details: {err}")
            return None
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def create_user(self):
        first_name = self.users_first_name_entry.get()
        last_name = self.users_last_name_entry.get()
        email = self.users_email_entry.get()
        phone = self.users_phone_entry.get()
        address = self.users_address_entry.get()
        password = self.users_password_entry.get()
        if not first_name or not last_name or not email or not password:
            messagebox.showwarning("Input Error", "First name, last name, email, and password are required")
            return
        hashed_password = self.hash_password(password)
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
            if cursor.fetchone():
                messagebox.showwarning("Input Error", "A user with this email already exists")
                return
            cursor.execute(
                """
                INSERT INTO Users (first_name, last_name, email, phone, password, user_address)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (first_name, last_name, email, phone, hashed_password, address)
            )
            connection.commit()
            messagebox.showinfo("Success", "User created successfully")
            self.clear_user_form()
            self.populate_user_table()
        except mysql.connector.Error as err:
            print(f"Error creating user: {err}")
            messagebox.showerror("Database Error", f"Error creating user: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def update_user(self):
        if not self.selected_user:
            messagebox.showwarning("Selection Error", "No user selected")
            return
        first_name = self.users_first_name_entry.get()
        last_name = self.users_last_name_entry.get()
        email = self.users_email_entry.get()
        phone = self.users_phone_entry.get()
        address = self.users_address_entry.get()
        password = self.users_password_entry.get()
        if not first_name or not last_name or not email:
            messagebox.showwarning("Input Error", "First name, last name, and email are required")
            return
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("SELECT user_id FROM Users WHERE email = %s AND user_id != %s", (email, self.selected_user['user_id']))
            if cursor.fetchone():
                messagebox.showwarning("Input Error", "Another user with this email already exists")
                return
            if password:
                hashed_password = self.hash_password(password)
                cursor.execute(
                    """
                    UPDATE Users
                    SET first_name = %s, last_name = %s, email = %s, 
                        phone = %s, user_address = %s, password = %s
                    WHERE user_id = %s
                    """,
                    (first_name, last_name, email, phone, address, hashed_password, self.selected_user['user_id'])
                )
            else:
                cursor.execute(
                    """
                    UPDATE Users
                    SET first_name = %s, last_name = %s, email = %s, 
                        phone = %s, user_address = %s
                    WHERE user_id = %s
                    """,
                    (first_name, last_name, email, phone, address, self.selected_user['user_id'])
                )
            connection.commit()
            messagebox.showinfo("Success", "User updated successfully")
            self.selected_user = self.load_user_details(self.selected_user['user_id'])
            self.show_user_details()
            self.populate_user_table()
        except mysql.connector.Error as err:
            print(f"Error updating user: {err}")
            messagebox.showerror("Database Error", f"Error updating user: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def delete_user(self):
        if not self.selected_user:
            messagebox.showwarning("Selection Error", "No user selected")
            return
        confirmed = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the user {self.selected_user['first_name']} {self.selected_user['last_name']}?\n\nThis will also delete all their bookings and reviews.\nThis action cannot be undone.")
        if not confirmed:
            return
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM Users WHERE user_id = %s", (self.selected_user['user_id'],))
            connection.commit()
            messagebox.showinfo("Success", "User deleted successfully")
            self.clear_user_form()
            self.users_details_frame.pack_forget()
            self.selected_user = None
            self.populate_user_table()
        except mysql.connector.Error as err:
            print(f"Error deleting user: {err}")
            messagebox.showerror("Database Error", f"Error deleting user: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def populate_user_table(self):
        for row in self.users_table.get_children():
            self.users_table.delete(row)
        users = self.load_users()
        for user in users:
            full_name = f"{user['first_name']} {user['last_name']}"
            phone = user['phone'] if user['phone'] else "N/A"
            address = user['user_address'] if user['user_address'] else "N/A"
            bookings = str(user['bookings'])
            self.users_table.insert('', 'end', iid=user['user_id'], values=(
                user['user_id'],
                full_name,
                user['email'],
                phone,
                address,
                bookings
            ))
        self.users_user_count_label.configure(text=f"Total Users: {len(users)}")

    def show_user_details(self, event=None):
        if event is not None:
            selected_id = self.users_table.focus()
            if not selected_id:
                return
            user_id = int(selected_id)
            user = self.load_user_details(user_id)
            if not user:
                return
            self.selected_user = user
        self.users_first_name_entry.delete(0, 'end')
        self.users_first_name_entry.insert(0, self.selected_user['first_name'])
        self.users_last_name_entry.delete(0, 'end')
        self.users_last_name_entry.insert(0, self.selected_user['last_name'])
        self.users_email_entry.delete(0, 'end')
        self.users_email_entry.insert(0, self.selected_user['email'])
        self.users_phone_entry.delete(0, 'end')
        if self.selected_user['phone']:
            self.users_phone_entry.insert(0, self.selected_user['phone'])
        self.users_address_entry.delete(0, 'end')
        if self.selected_user['user_address']:
            self.users_address_entry.insert(0, self.selected_user['user_address'])
        self.users_password_entry.delete(0, 'end')
        self.users_create_btn.grid_forget()
        self.users_update_btn.grid(row=0, column=0, padx=(0, 10))
        self.users_delete_btn.grid(row=0, column=1, padx=(0, 10))
        self.users_clear_btn.grid(row=0, column=2)
        self.users_update_btn.configure(state="normal")
        self.users_delete_btn.configure(state="normal")
        self.users_details_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self.users_details_user_id.configure(text=f"User #{self.selected_user['user_id']}")
        self.users_details_name.configure(text=f"{self.selected_user['first_name']} {self.selected_user['last_name']}")
        self.users_details_email.configure(text=f"{self.selected_user['email']}")
        self.users_details_phone.configure(text=f"Phone: {self.selected_user['phone'] if self.selected_user['phone'] else 'N/A'}")
        self.users_details_address.configure(text=f"Address: {self.selected_user['user_address'] if self.selected_user['user_address'] else 'N/A'}")
        total_bookings = self.selected_user['bookings'] if self.selected_user['bookings'] else 0
        total_spent = self.selected_user['total_spent'] if self.selected_user['total_spent'] else 0
        self.users_details_bookings.configure(text=f"Total Bookings: {total_bookings}")
        self.users_details_spent.configure(text=f"Total Spent: ${total_spent}")
        for row in self.users_bookings_table.get_children():
            self.users_bookings_table.delete(row)
        if 'recent_bookings' in self.selected_user and self.selected_user['recent_bookings']:
            for booking in self.selected_user['recent_bookings']:
                self.users_bookings_table.insert('', 'end', values=(
                    booking['Booking_ID'],
                    booking['Room_Type'],
                    booking['Check_IN_Date'].strftime('%Y-%m-%d') if hasattr(booking['Check_IN_Date'], 'strftime') else booking['Check_IN_Date'],
                    booking['Check_Out_Date'].strftime('%Y-%m-%d') if hasattr(booking['Check_OUT_Date'], 'strftime') else booking['Check_OUT_Date'],
                    f"${booking['Total_Cost']}",
                    booking['Booking_Status']
                ))

    def clear_user_form(self):
        self.users_first_name_entry.delete(0, 'end')
        self.users_last_name_entry.delete(0, 'end')
        self.users_email_entry.delete(0, 'end')
        self.users_phone_entry.delete(0, 'end')
        self.users_address_entry.delete(0, 'end')
        self.users_password_entry.delete(0, 'end')
        self.selected_user = None
        self.new_user_mode()

    def new_user_mode(self):
        self.users_details_frame.pack_forget()
        self.users_update_btn.grid_forget()
        self.users_delete_btn.grid_forget()
        self.users_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.users_clear_btn.grid(row=0, column=1)
        self.users_create_btn.configure(state="normal")
        self.users_first_name_entry.focus_set()

    def search_users(self):
        search_term = self.users_search_entry.get().lower()
        if not search_term:
            self.populate_user_table()
            return
        for row in self.users_table.get_children():
            self.users_table.delete(row)
        users = self.load_users()
        filtered_users = []
        for user in users:
            full_name = f"{user['first_name']} {user['last_name']}".lower()
            email = user['email'].lower()
            address = user['user_address'].lower() if user['user_address'] else ""
            if search_term in full_name or search_term in email or search_term in address:
                filtered_users.append(user)
        for user in filtered_users:
            full_name = f"{user['first_name']} {user['last_name']}"
            phone = user['phone'] if user['phone'] else "N/A"
            address = user['user_address'] if user['user_address'] else "N/A"
            bookings = str(user['bookings'])
            self.users_table.insert('', 'end', iid=user['user_id'], values=(
                user['user_id'],
                full_name,
                user['email'],
                phone,
                address,
                bookings
            ))
        self.users_user_count_label.configure(text=f"Filtered Users: {len(filtered_users)}")

    # ------------------- Manage Hotels Section -------------------
    def create_hotels_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header_frame, text="Manage Hotels", font=("Arial", 28, "bold"), text_color="#2C3E50").pack(side="left")
        
        action_frame = ctk.CTkFrame(header_frame, fg_color="white")
        action_frame.pack(side="right")
        ctk.CTkButton(action_frame, text="+ New Hotel", font=("Arial", 12, "bold"), fg_color="#28A745", hover_color="#218838", command=self.new_hotel_mode, width=120, height=35, corner_radius=8).pack(side="left", padx=(0, 15))
        search_frame = ctk.CTkFrame(action_frame, fg_color="#E9ECEF", corner_radius=8, height=35)
        search_frame.pack(side="left", fill="y")
        self.hotels_search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Search hotels...", border_width=0, fg_color="#E9ECEF", height=35)
        self.hotels_search_entry.pack(side="left", padx=(10, 0))
        ctk.CTkButton(search_frame, text="🔍", font=("Arial", 12, "bold"), fg_color="#E9ECEF", text_color="#343A40", hover_color="#DEE2E6", width=35, height=35, corner_radius=0, command=self.search_hotels).pack(side="right")

        # Hotel Form
        form_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        form_frame.pack(fill="x", padx=30, pady=(0, 20))
        form_header = ctk.CTkFrame(form_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        form_header.pack(fill="x")
        ctk.CTkLabel(form_header, text="Hotel Information", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)
        
        form_fields = ctk.CTkFrame(form_frame, fg_color="white")
        form_fields.pack(fill="x", padx=20, pady=(20, 20))
        form_fields.columnconfigure(0, weight=1)
        form_fields.columnconfigure(1, weight=1)
        
        ctk.CTkLabel(form_fields, text="Hotel Name *", font=("Arial", 12), anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.hotels_hotel_name_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter hotel name")
        self.hotels_hotel_name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Location *", font=("Arial", 12), anchor="w").grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.hotels_location_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter location (city, country)")
        self.hotels_location_entry.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Description", font=("Arial", 12), anchor="w").grid(row=4, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.hotels_description_text = ctk.CTkTextbox(form_fields, height=100)
        self.hotels_description_text.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        
        right_column = ctk.CTkFrame(form_fields, fg_color="white")
        right_column.grid(row=0, column=1, rowspan=6, sticky="nsew", padx=(10, 0))
        ctk.CTkLabel(right_column, text="Star Rating *", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
        star_frame = ctk.CTkFrame(right_column, fg_color="white")
        star_frame.pack(fill="x", pady=(0, 15))
        self.hotels_star_rating_var = ctk.StringVar(value="3")
        for i in range(1, 6):
            ctk.CTkRadioButton(star_frame, text=f"{i} ⭐", variable=self.hotels_star_rating_var, value=str(i)).pack(side="left", padx=(0, 10))
        ctk.CTkLabel(right_column, text="Hotel Image", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
        image_frame = ctk.CTkFrame(right_column, fg_color="white")
        image_frame.pack(fill="x", pady=(0, 15))
        self.hotels_image_preview_label = ctk.CTkLabel(image_frame, text="No image selected", width=150, height=100, fg_color="#E9ECEF", corner_radius=5)
        self.hotels_image_preview_label.pack(side="left", padx=(0, 10))
        ctk.CTkButton(image_frame, text="Browse Image", font=("Arial", 12), fg_color="#6C757D", hover_color="#5A6268", command=self.browse_image, width=100, height=35).pack(side="left", pady=(30, 0))
        ctk.CTkLabel(right_column, text="Amenities", font=("Arial", 12), anchor="w").pack(fill="x", pady=(0, 5))
        self.hotels_amenities_frame = ctk.CTkScrollableFrame(right_column, fg_color="white", height=150)
        self.hotels_amenities_frame.pack(fill="x", pady=(0, 15))
        self.hotels_amenity_vars = {}
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Amenities ORDER BY amenity_name")
            amenities = cursor.fetchall()
            for i, amenity in enumerate(amenities):
                row = i // 3
                col = i % 3
                var = ctk.IntVar(value=0)
                self.hotels_amenity_vars[amenity['Amenity_ID']] = var
                ctk.CTkCheckBox(self.hotels_amenities_frame, text=f"{amenity['amenity_icon']} {amenity['amenity_name']}", variable=var, font=("Arial", 11)).grid(row=row, column=col, sticky="w", padx=5, pady=2)
        except mysql.connector.Error as err:
            print(f"Error loading amenities: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
        
        buttons_frame = ctk.CTkFrame(form_fields, fg_color="white")
        buttons_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_container = ctk.CTkFrame(buttons_frame, fg_color="white")
        button_container.pack()
        self.hotels_create_btn = ctk.CTkButton(button_container, text="Create Hotel", font=("Arial", 13, "bold"), fg_color="#28A745", hover_color="#218838", command=self.create_hotel, width=140, height=40, corner_radius=8)
        self.hotels_update_btn = ctk.CTkButton(button_container, text="Update Hotel", font=("Arial", 13, "bold"), fg_color="#2C3E50", hover_color="#1E4D88", command=self.update_hotel, width=140, height=40, corner_radius=8, state="disabled")
        self.hotels_delete_btn = ctk.CTkButton(button_container, text="Delete Hotel", font=("Arial", 13, "bold"), fg_color="#DC3545", hover_color="#C82333", command=self.delete_hotel, width=140, height=40, corner_radius=8, state="disabled")
        self.hotels_clear_btn = ctk.CTkButton(button_container, text="Clear Form", font=("Arial", 13, "bold"), fg_color="#6C757D", hover_color="#5A6268", command=self.clear_hotel_form, width=140, height=40, corner_radius=8)
        self.hotels_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.hotels_clear_btn.grid(row=0, column=1)

        # Hotel Table
        table_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        table_frame.pack(fill="x", padx=30, pady=(0, 20))
        table_header = ctk.CTkFrame(table_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        table_header.pack(fill="x")
        ctk.CTkLabel(table_header, text="Hotel List", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)
        self.hotels_hotel_count_label = ctk.CTkLabel(table_header, text="Total Hotels: 0", font=("Arial", 12))
        self.hotels_hotel_count_label.pack(side="right", padx=20, pady=10)
        
        table_container = ctk.CTkFrame(table_frame, fg_color="white")
        table_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        columns = ('ID', 'Name', 'Location', 'Rating', 'Room Categories', 'Price Range')
        self.hotels_table = ttk.Treeview(table_container, columns=columns, show='headings', height=6)
        for col in columns:
            self.hotels_table.heading(col, text=col)
            self.hotels_table.column(col, width=120, anchor='center')
        table_scroll_y = ttk.Scrollbar(table_container, orient='vertical', command=self.hotels_table.yview)
        table_scroll_x = ttk.Scrollbar(table_container, orient='horizontal', command=self.hotels_table.xview)
        self.hotels_table.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)
        table_scroll_y.pack(side='right', fill='y')
        table_scroll_x.pack(side='bottom', fill='x')
        self.hotels_table.pack(expand=True, fill='both')
        self.hotels_table.bind('<<TreeviewSelect>>', self.show_hotel_details)

        return frame

    def setup_hotel_tables(self):
        """Ensure necessary tables exist and are initialized"""
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Hotel (
                    Hotel_ID INT AUTO_INCREMENT PRIMARY KEY,
                    Hotel_Name VARCHAR(100) NOT NULL,
                    Location VARCHAR(100) NOT NULL,
                    Description TEXT,
                    Star_Rating INT NOT NULL,
                    Image_Path VARCHAR(255)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Hotel_Amenities (
                    Hotel_ID INT,
                    Amenity_ID INT,
                    PRIMARY KEY (Hotel_ID, Amenity_ID),
                    FOREIGN KEY (Hotel_ID) REFERENCES Hotel(Hotel_ID),
                    FOREIGN KEY (Amenity_ID) REFERENCES Amenities(Amenity_ID)
                )
            """)
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Error setting up hotel tables: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def browse_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")])
        if file_path:
            self.hotel_image_path = file_path
            try:
                img = Image.open(file_path)
                img = img.resize((150, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.hotels_image_preview_label.configure(image=photo, text="")
                self.hotels_image_preview_label.image = photo
            except Exception as e:
                print(f"Error loading image: {e}")
                messagebox.showerror("Image Error", "Failed to load image")

    def save_hotel_image(self, hotel_id):
        if not self.hotel_image_path:
            return None
        try:
            extension = os.path.splitext(self.hotel_image_path)[1]
            new_filename = f"hotel_{hotel_id}{extension}"
            destination = os.path.join("hotel_images", new_filename)
            os.makedirs("hotel_images", exist_ok=True)
            shutil.copy(self.hotel_image_path, destination)
            return destination
        except Exception as e:
            print(f"Error saving hotel image: {e}")
            return None

    def load_hotels(self):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT h.Hotel_ID, h.hotel_name, h.location, h.star_rating,
                    GROUP_CONCAT(DISTINCT rc.category_name) as room_types,
                    MIN(rc.base_price) as min_price,
                    MAX(rc.base_price) as max_price
                FROM Hotel h
                LEFT JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
                GROUP BY h.Hotel_ID, h.hotel_name, h.location, h.star_rating
                ORDER BY h.Hotel_ID
                """
            )
            hotels = cursor.fetchall()
            return hotels
        except mysql.connector.Error as err:
            print(f"Error loading hotels: {err}")
            messagebox.showerror("Database Error", f"Error loading hotels: {err}")
            return []
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
    def load_hotel_details(self, hotel_id):
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT h.*, 
                    GROUP_CONCAT(DISTINCT rc.category_name) as room_types,
                    MIN(rc.base_price) as min_price,
                    MAX(rc.base_price) as max_price
                FROM Hotel h
                LEFT JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
                WHERE h.Hotel_ID = %s
                GROUP BY h.Hotel_ID, h.hotel_name, h.location, h.description, h.star_rating, h.image_path, h.created_by
                """,
                (hotel_id,)
            )
            hotel = cursor.fetchone()
            if hotel:
                cursor.execute(
                    """
                    SELECT Amenity_ID FROM Hotel_Amenities
                    WHERE Hotel_ID = %s
                    """,
                    (hotel_id,)
                )
                hotel['amenities'] = [row[0] for row in cursor.fetchall()]
            return hotel
        except mysql.connector.Error as err:
            print(f"Error loading hotel details: {err}")
            messagebox.showerror("Database Error", f"Error loading hotel details: {err}")
            return None
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def create_hotel(self):
        hotel_name = self.hotels_hotel_name_entry.get()
        location = self.hotels_location_entry.get()
        description = self.hotels_description_text.get("1.0", "end-1c")
        star_rating = int(self.hotels_star_rating_var.get())
        if not hotel_name or not location or not star_rating:
            messagebox.showwarning("Input Error", "Hotel name, location, and star rating are required")
            return
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO Hotel (Hotel_Name, Location, Description, Star_Rating)
                VALUES (%s, %s, %s, %s)
                """,
                (hotel_name, location, description, star_rating)
            )
            hotel_id = cursor.lastrowid
            image_path = self.save_hotel_image(hotel_id)
            if image_path:
                cursor.execute("UPDATE Hotel SET Image_Path = %s WHERE Hotel_ID = %s", (image_path, hotel_id))
            selected_amenities = [(hotel_id, amenity_id) for amenity_id, var in self.hotels_amenity_vars.items() if var.get() == 1]
            if selected_amenities:
                cursor.executemany(
                    "INSERT INTO Hotel_Amenities (Hotel_ID, Amenity_ID) VALUES (%s, %s)",
                    selected_amenities
                )
            connection.commit()
            messagebox.showinfo("Success", f"Hotel '{hotel_name}' created successfully")
            self.clear_hotel_form()
            self.populate_hotel_table()
        except mysql.connector.Error as err:
            print(f"Error creating hotel: {err}")
            messagebox.showerror("Database Error", f"Error creating hotel: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def update_hotel(self):
        if not self.selected_hotel:
            messagebox.showwarning("Selection Error", "No hotel selected")
            return
        hotel_name = self.hotels_hotel_name_entry.get()
        location = self.hotels_location_entry.get()
        description = self.hotels_description_text.get("1.0", "end-1c")
        star_rating = int(self.hotels_star_rating_var.get())
        if not hotel_name or not location or not star_rating:
            messagebox.showwarning("Input Error", "Hotel name, location, and star rating are required")
            return
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE Hotel
                SET Hotel_Name = %s, Location = %s, Description = %s, Star_Rating = %s
                WHERE Hotel_ID = %s
                """,
                (hotel_name, location, description, star_rating, self.selected_hotel['Hotel_ID'])
            )
            if self.hotel_image_path:
                image_path = self.save_hotel_image(self.selected_hotel['Hotel_ID'])
                if image_path:
                    cursor.execute("UPDATE Hotel SET Image_Path = %s WHERE Hotel_ID = %s", (image_path, self.selected_hotel['Hotel_ID']))
            cursor.execute("DELETE FROM Hotel_Amenities WHERE Hotel_ID = %s", (self.selected_hotel['Hotel_ID'],))
            selected_amenities = [(self.selected_hotel['Hotel_ID'], amenity_id) for amenity_id, var in self.hotels_amenity_vars.items() if var.get() == 1]
            if selected_amenities:
                cursor.executemany(
                    "INSERT INTO Hotel_Amenities (Hotel_ID, Amenity_ID) VALUES (%s, %s)",
                    selected_amenities
                )
            connection.commit()
            messagebox.showinfo("Success", f"Hotel '{hotel_name}' updated successfully")
            self.selected_hotel = self.load_hotel_details(self.selected_hotel['Hotel_ID'])
            self.show_hotel_details()
            self.populate_hotel_table()
        except mysql.connector.Error as err:
            print(f"Error updating hotel: {err}")
            messagebox.showerror("Database Error", f"Error updating hotel: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def delete_hotel(self):
        if not self.selected_hotel:
            messagebox.showwarning("Selection Error", "No hotel selected")
            return
        confirmed = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the hotel '{self.selected_hotel['Hotel_Name']}'\n\nThis will also delete all associated rooms and bookings.\nThis action cannot be undone.")
        if not confirmed:
            return
        try:
            connection = connect_db()
            cursor = connection.cursor()
            cursor.execute("DELETE FROM Hotel WHERE Hotel_ID = %s", (self.selected_hotel['Hotel_ID'],))
            connection.commit()
            messagebox.showinfo("Success", f"Hotel '{self.selected_hotel['Hotel_Name']}' deleted successfully")
            self.clear_hotel_form()
            self.hotels_details_frame.pack_forget()
            self.selected_hotel = None
            self.populate_hotel_table()
        except mysql.connector.Error as err:
            print(f"Error deleting hotel: {err}")
            messagebox.showerror("Database Error", f"Error deleting hotel: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def populate_hotel_table(self):
        for row in self.hotels_table.get_children():
            self.hotels_table.delete(row)
        hotels = self.load_hotels()
        for hotel in hotels:
            rating = f"{hotel['Star_Rating']} ★"
            room_types = hotel['room_types'] if hotel['room_types'] else "No rooms"
            price_range = f"${hotel['min_price']}-${hotel['max_price']}" if hotel['min_price'] and hotel['max_price'] else "N/A"
            self.hotels_table.insert('', 'end', iid=hotel['Hotel_ID'], values=(
                hotel['Hotel_ID'],
                hotel['Hotel_Name'],
                hotel['Location'],
                rating,
                room_types,
                price_range
            ))
        self.hotels_hotel_count_label.configure(text=f"Total Hotels: {len(hotels)}")

    def show_hotel_details(self, event=None):
        if event is not None:
            selected_id = self.hotels_table.focus()
            if not selected_id:
                return
            hotel_id = int(selected_id)
            hotel = self.load_hotel_details(hotel_id)
            if not hotel:
                return
            self.selected_hotel = hotel
        self.hotels_hotel_name_entry.delete(0, 'end')
        self.hotels_hotel_name_entry.insert(0, self.selected_hotel['Hotel_Name'])
        self.hotels_location_entry.delete(0, 'end')
        self.hotels_location_entry.insert(0, self.selected_hotel['Location'])
        self.hotels_description_text.delete("1.0", "end")
        if self.selected_hotel['Description']:
            self.hotels_description_text.insert("1.0", self.selected_hotel['Description'])
        self.hotels_star_rating_var.set(str(self.selected_hotel['Star_Rating']))
        for amenity_id, var in self.hotels_amenity_vars.items():
            var.set(1 if amenity_id in self.selected_hotel['amenities'] else 0)
        if self.selected_hotel['Image_Path'] and os.path.exists(self.selected_hotel['Image_Path']):
            try:
                img = Image.open(self.selected_hotel['Image_Path'])
                img = img.resize((150, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.hotels_image_preview_label.configure(image=photo, text="")
                self.hotels_image_preview_label.image = photo
                self.hotel_image_path = self.selected_hotel['Image_Path']
            except:
                self.hotels_image_preview_label.configure(image=None, text="No image selected")
                self.hotels_image_preview_label.image = None
                self.hotel_image_path = None
        else:
            self.hotels_image_preview_label.configure(image=None, text="No image selected")
            self.hotels_image_preview_label.image = None
            self.hotel_image_path = None
        self.hotels_create_btn.grid_forget()
        self.hotels_update_btn.grid(row=0, column=0, padx=(0, 10))
        self.hotels_delete_btn.grid(row=0, column=1, padx=(0, 10))
        self.hotels_clear_btn.grid(row=0, column=2)
        self.hotels_update_btn.configure(state="normal")
        self.hotels_delete_btn.configure(state="normal")
        self.hotels_details_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

    def clear_hotel_form(self):
        self.hotels_hotel_name_entry.delete(0, 'end')
        self.hotels_location_entry.delete(0, 'end')
        self.hotels_description_text.delete("1.0", "end")
        self.hotels_star_rating_var.set("3")
        for var in self.hotels_amenity_vars.values():
            var.set(0)
        self.hotels_image_preview_label.configure(image=None, text="No image selected")
        self.hotels_image_preview_label.image = None
        self.hotel_image_path = None
        self.selected_hotel = None
        self.new_hotel_mode()

    def new_hotel_mode(self):
        self.hotels_details_frame.pack_forget()
        self.hotels_update_btn.grid_forget()
        self.hotels_delete_btn.grid_forget()
        self.hotels_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.hotels_clear_btn.grid(row=0, column=1)
        self.hotels_create_btn.configure(state="normal")
        self.hotels_hotel_name_entry.focus_set()

    def search_hotels(self):
        search_term = self.hotels_search_entry.get().lower()
        if not search_term:
            self.populate_hotel_table()
            return
        for row in self.hotels_table.get_children():
            self.hotels_table.delete(row)
        hotels = self.load_hotels()
        filtered_hotels = []
        for hotel in hotels:
            if search_term in hotel['Hotel_Name'].lower() or search_term in hotel['Location'].lower():
                filtered_hotels.append(hotel)
        for hotel in filtered_hotels:
            rating = f"{hotel['Star_Rating']} ★"
            room_types = hotel['room_types'] if hotel['room_types'] else "No rooms"
            price_range = f"${hotel['min_price']}-${hotel['max_price']}" if hotel['min_price'] and hotel['max_price'] else "N/A"
            self.hotels_table.insert('', 'end', iid=hotel['Hotel_ID'], values=(
                hotel['Hotel_ID'],
                hotel['Hotel_Name'],
                hotel['Location'],
                rating,
                room_types,
                price_range
            ))
        self.hotels_hotel_count_label.configure(text=f"Filtered Hotels: {len(filtered_hotels)}")

    # ------------------- Reports Section -------------------
    def create_reports_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")

        # Header
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header_frame, text="Reports", font=("Arial", 28, "bold"), text_color="#2C3E50").pack(anchor="w")

        # Report Selection and Filters
        filter_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#E5E5E5", corner_radius=10)
        filter_frame.pack(fill="x", padx=30, pady=(0, 10))
        filter_header = ctk.CTkFrame(filter_frame, fg_color="white", height=40)
        filter_header.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(filter_header, text="Generate Report", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(anchor="w")

        filter_options = ctk.CTkFrame(filter_frame, fg_color="white")
        filter_options.pack(fill="x", padx=20, pady=(0, 10))

        # Report Type
        report_type_frame = ctk.CTkFrame(filter_options, fg_color="white")
        report_type_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(report_type_frame, text="Report Type", font=("Arial", 12)).pack(anchor="w")
        self.reports_type_var = ctk.StringVar(value="Revenue")
        report_types = ["Revenue", "Booking Statistics", "Hotel Performance"]
        self.reports_type_dropdown = ctk.CTkComboBox(report_type_frame, values=report_types, variable=self.reports_type_var, width=150, command=self.update_report_form)
        self.reports_type_dropdown.pack(pady=5)

        # Date Range
        date_frame = ctk.CTkFrame(filter_options, fg_color="white")
        date_frame.pack(side="left", padx=(10, 10))
        ctk.CTkLabel(date_frame, text="Date Range", font=("Arial", 12)).pack(anchor="w")
        date_fields = ctk.CTkFrame(date_frame, fg_color="white")
        date_fields.pack(fill="x")
        self.reports_start_date_entry = DateEntry(date_fields, width=10, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd') if DateEntry else ctk.CTkEntry(date_fields, width=100, placeholder_text="YYYY-MM-DD")
        self.reports_start_date_entry.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(date_fields, text="to", font=("Arial", 10)).pack(side="left", padx=5)
        self.reports_end_date_entry = DateEntry(date_fields, width=10, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd') if DateEntry else ctk.CTkEntry(date_fields, width=100, placeholder_text="YYYY-MM-DD")
        self.reports_end_date_entry.pack(side="left", padx=(5, 0))

        # Hotel Filter (for Hotel Performance report)
        self.reports_hotel_frame = ctk.CTkFrame(filter_options, fg_color="white")
        ctk.CTkLabel(self.reports_hotel_frame, text="Select Hotel", font=("Arial", 12)).pack(anchor="w")
        self.reports_hotel_var = ctk.StringVar()
        self.reports_hotel_dropdown = ctk.CTkComboBox(self.reports_hotel_frame, values=["All"], variable=self.reports_hotel_var, width=150)
        self.reports_hotel_dropdown.pack(pady=5)

        # Generate Button
        button_frame = ctk.CTkFrame(filter_options, fg_color="white")
        button_frame.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(button_frame, text=" ", font=("Arial", 12)).pack(anchor="w")
        ctk.CTkButton(button_frame, text="Generate Report", font=("Arial", 12), fg_color="#0F2D52", hover_color="#1E4D88", command=self.generate_report, width=120, height=30).pack(side="left", pady=5, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Export CSV", font=("Arial", 12), fg_color="#6C757D", hover_color="#5A6268", command=self.export_report, width=100, height=30).pack(side="left", pady=5)

        # Report Results
        results_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#E5E5E5", corner_radius=10)
        results_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        results_header = ctk.CTkFrame(results_frame, fg_color="white", height=40)
        results_header.pack(fill="x", padx=20, pady=10)
        self.reports_title_label = ctk.CTkLabel(results_header, text="Report Results", font=("Arial", 16, "bold"), text_color="#2C3E50")
        self.reports_title_label.pack(side="left")

        # Results Table
        table_container = ctk.CTkFrame(results_frame, fg_color="white")
        table_container.pack(fill="both", expand=True, padx=20, pady=(10, 10))
        self.reports_table = ttk.Treeview(table_container, show='headings', height=8)
        table_scroll_y = ttk.Scrollbar(table_container, orient='vertical', command=self.reports_table.yview)
        table_scroll_x = ttk.Scrollbar(table_container, orient='horizontal', command=self.reports_table.xview)
        self.reports_table.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)
        table_scroll_y.pack(side='right', fill='y')
        table_scroll_x.pack(side='bottom', fill='x')
        self.reports_table.pack(expand=True, fill='both')

        # Chart
        chart_frame = ctk.CTkFrame(results_frame, fg_color="white")
        chart_frame.pack(fill="x", padx=20, pady=(10, 20))
        self.reports_fig = Figure(figsize=(8, 3), dpi=100)
        self.reports_ax = self.reports_fig.add_subplot(111)
        self.reports_canvas = FigureCanvasTkAgg(self.reports_fig, master=chart_frame)
        self.reports_canvas.get_tk_widget().pack(fill="both", expand=True)

        return frame

    def populate_reports(self):
        """Initialize reports section with default settings"""
        # Populate hotel dropdown
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT Hotel_ID, Hotel_Name FROM Hotel ORDER BY Hotel_Name")
            hotels = cursor.fetchall()
            hotel_options = ["All"] + [hotel['Hotel_Name'] for hotel in hotels]
            self.reports_hotel_dropdown.configure(values=hotel_options)
            self.reports_hotel_var.set("All")
            self.hotel_id_map = {hotel['Hotel_Name']: hotel['Hotel_ID'] for hotel in hotels}
        except mysql.connector.Error as err:
            print(f"Error loading hotels for reports: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
        self.update_report_form(None)

    def update_report_form(self, event):
        """Update form visibility based on report type"""
        report_type = self.reports_type_var.get()
        if report_type == "Hotel Performance":
            self.reports_hotel_frame.pack(side="left", padx=(10, 10))
        else:
            self.reports_hotel_frame.pack_forget()
        self.clear_report_results()

    def clear_report_results(self):
        """Clear existing report results and chart"""
        for row in self.reports_table.get_children():
            self.reports_table.delete(row)
        self.reports_table.configure(columns=())
        self.reports_ax.clear()
        self.reports_canvas.draw()
        self.reports_title_label.configure(text="Report Results")

    def generate_report(self):
        """Generate the selected report based on filters"""
        report_type = self.reports_type_var.get()
        try:
            start_date = self.reports_start_date_entry.get_date() if hasattr(self.reports_start_date_entry, 'get_date') else None
            end_date = self.reports_end_date_entry.get_date() if hasattr(self.reports_end_date_entry, 'get_date') else None
        except:
            messagebox.showwarning("Input Error", "Invalid date format")
            return

        if report_type == "Revenue":
            self.generate_revenue_report(start_date, end_date)
        elif report_type == "Booking Statistics":
            self.generate_booking_stats_report(start_date, end_date)
        elif report_type == "Hotel Performance":
            hotel_name = self.reports_hotel_var.get()
            hotel_id = self.hotel_id_map.get(hotel_name) if hotel_name != "All" else None
            self.generate_hotel_performance_report(start_date, end_date, hotel_id)

    def generate_revenue_report(self, start_date, end_date):
        """Generate revenue report"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT DATE_FORMAT(Check_IN_Date, '%Y-%m') as Month, 
                       SUM(Total_Cost) as Revenue
                FROM Booking
                WHERE Booking_Status = 'Confirmed'
            """
            params = []
            if start_date and end_date:
                query += " AND Check_IN_Date BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            query += " GROUP BY DATE_FORMAT(Check_IN_Date, '%Y-%m') ORDER BY Month"
            cursor.execute(query, params)
            data = cursor.fetchall()

            # Update table
            columns = ('Month', 'Revenue')
            self.reports_table.configure(columns=columns)
            for col in columns:
                self.reports_table.heading(col, text=col)
                self.reports_table.column(col, width=150, anchor='center')
            for row in data:
                self.reports_table.insert('', 'end', values=(
                    row['Month'],
                    f"${row['Revenue']:,}"
                ))

            # Update chart
            self.reports_ax.clear()
            months = [row['Month'] for row in data]
            revenues = [row['Revenue'] for row in data]
            self.reports_ax.bar(months, revenues, color='#007BFF')
            self.reports_ax.set_xlabel('Month')
            self.reports_ax.set_ylabel('Revenue ($)')
            self.reports_ax.set_title('Monthly Revenue')
            self.reports_ax.grid(True, linestyle='--', alpha=0.7)
            self.reports_fig.tight_layout()
            self.reports_canvas.draw()

            self.reports_title_label.configure(text="Revenue Report")
            self.current_report_data = pd.DataFrame(data)

        except mysql.connector.Error as err:
            print(f"Error generating revenue report: {err}")
            messagebox.showerror("Database Error", f"Error generating report: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def generate_booking_stats_report(self, start_date, end_date):
        """Generate booking statistics report"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT DATE_FORMAT(Check_IN_Date, '%Y-%m') as Month,
                       SUM(CASE WHEN Booking_Status = 'Confirmed' THEN 1 ELSE 0 END) as Confirmed,
                       SUM(CASE WHEN Booking_Status = 'Pending' THEN 1 ELSE 0 END) as Pending,
                       SUM(CASE WHEN Booking_Status = 'Cancelled' THEN 1 ELSE 0 END) as Cancelled
                FROM Booking
            """
            params = []
            if start_date and end_date:
                query += " WHERE Check_IN_Date BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            query += " GROUP BY DATE_FORMAT(Check_IN_Date, '%Y-%m') ORDER BY Month"
            cursor.execute(query, params)
            data = cursor.fetchall()

            # Update table
            columns = ('Month', 'Confirmed', 'Pending', 'Cancelled')
            self.reports_table.configure(columns=columns)
            for col in columns:
                self.reports_table.heading(col, text=col)
                self.reports_table.column(col, width=100, anchor='center')
            for row in data:
                self.reports_table.insert('', 'end', values=(
                    row['Month'],
                    row['Confirmed'],
                    row['Pending'],
                    row['Cancelled']
                ))

            # Update chart
            self.reports_ax.clear()
            months = [row['Month'] for row in data]
            confirmed = [row['Confirmed'] for row in data]
            pending = [row['Pending'] for row in data]
            cancelled = [row['Cancelled'] for row in data]
            self.reports_ax.plot(months, confirmed, marker='o', label='Confirmed', color='#28A745')
            self.reports_ax.plot(months, pending, marker='o', label='Pending', color='#FFC107')
            self.reports_ax.plot(months, cancelled, marker='o', label='Cancelled', color='#DC3545')
            self.reports_ax.set_xlabel('Month')
            self.reports_ax.set_ylabel('Number of Bookings')
            self.reports_ax.set_title('Booking Status Trends')
            self.reports_ax.legend()
            self.reports_ax.grid(True, linestyle='--', alpha=0.7)
            self.reports_fig.tight_layout()
            self.reports_canvas.draw()

            self.reports_title_label.configure(text="Booking Statistics Report")
            self.current_report_data = pd.DataFrame(data)

        except mysql.connector.Error as err:
            print(f"Error generating booking stats report: {err}")
            messagebox.showerror("Database Error", f"Error generating report: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def generate_hotel_performance_report(self, start_date, end_date, hotel_id):
        """Generate hotel performance report"""
        try:
            connection = connect_db()
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT h.Hotel_Name, 
                       COUNT(b.Booking_ID) as Bookings,
                       SUM(b.Total_Cost) as Revenue,
                       AVG(r.rating_value) as Avg_Rating
                FROM Hotel h
                LEFT JOIN Room rm ON h.Hotel_ID = rm.Hotel_ID
                LEFT JOIN Booking b ON rm.Room_ID = b.Room_ID
                LEFT JOIN Review r ON h.Hotel_ID = r.Hotel_ID
                WHERE b.Booking_Status = 'Confirmed'
            """
            params = []
            if hotel_id:
                query += " AND h.Hotel_ID = %s"
                params.append(hotel_id)
            if start_date and end_date:
                query += " AND b.Check_IN_Date BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            query += " GROUP BY h.Hotel_ID, h.Hotel_Name ORDER BY Revenue DESC"
            cursor.execute(query, params)
            data = cursor.fetchall()

            # Update table
            columns = ('Hotel', 'Bookings', 'Revenue', 'Average Rating')
            self.reports_table.configure(columns=columns)
            for col in columns:
                self.reports_table.heading(col, text=col)
                self.reports_table.column(col, width=150, anchor='center')
            for row in data:
                self.reports_table.insert('', 'end', values=(
                    row['Hotel_Name'],
                    row['Bookings'],
                    f"${row['Revenue']:,}" if row['Revenue'] else "$0",
                    f"{row['Avg_Rating']:.1f}" if row['Avg_Rating'] else "N/A"
                ))

            # Update chart
            self.reports_ax.clear()
            hotels = [row['Hotel_Name'][:15] + "..." if len(row['Hotel_Name']) > 15 else row['Hotel_Name'] for row in data]
            revenues = [row['Revenue'] if row['Revenue'] else 0 for row in data]
            self.reports_ax.bar(hotels, revenues, color='#007BFF')
            self.reports_ax.set_xlabel('Hotel')
            self.reports_ax.set_ylabel('Revenue ($)')
            self.reports_ax.set_title('Hotel Performance')
            self.reports_ax.grid(True, linestyle='--', alpha=0.7)
            self.reports_ax.tick_params(axis='x', rotation=45)
            self.reports_fig.tight_layout()
            self.reports_canvas.draw()

            self.reports_title_label.configure(text="Hotel Performance Report")
            self.current_report_data = pd.DataFrame(data)

        except mysql.connector.Error as err:
            print(f"Error generating hotel performance report: {err}")
            messagebox.showerror("Database Error", f"Error generating report: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def export_report(self):
        """Export the current report to CSV"""
        if not hasattr(self, 'current_report_data') or self.current_report_data.empty:
            messagebox.showwarning("Export Error", "No report data to export")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"{self.reports_type_var.get().replace(' ', '_')}_Report_{datetime.now().strftime('%Y%m%d')}"
        )
        if file_path:
            try:
                self.current_report_data.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Report exported to {file_path}")
            except Exception as e:
                print(f"Error exporting report: {e}")
                messagebox.showerror("Export Error", f"Failed to export report: {e}")

# ------------------- Main Application -------------------
if __name__ == "__main__":
    root = ctk.CTk()
    app = HotelBookingApp(root)
    root.mainloop()