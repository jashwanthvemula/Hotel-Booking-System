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
import io
import hashlib
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None
import pandas as pd

# ------------------- Database Connection -------------------
def connect_db():
    """Establish connection to the hotel_book database"""
    try:
        return mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="new_password",
            database="hotel_book"
        )
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Failed to connect to database: {err}")
        return None

# ------------------- Main Application Class -------------------
class HotelBookingApp:
    def __init__(self, root):
        """Initialize the Hotel Booking Admin Dashboard"""
        self.root = root
        self.root.title("Hotel Booking - Admin Dashboard")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 700)
        self.root.resizable(True, True)

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Global variables
        self.current_admin = None
        self.selected_booking = None
        self.selected_user = None
        self.selected_hotel = None
        self.hotel_image_path = None
        self.current_report_data = None

    def load_admin_session(self):
        """Load admin information from database"""
        try:
            admin_id = 1  # Replace with actual admin ID from login
            connection = connect_db()
            if not connection:
                return False
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Admin WHERE Admin_ID = %s", (admin_id,))
            admin_data = cursor.fetchone()
            if admin_data:
                self.current_admin = admin_data
                return True
            else:
                messagebox.showwarning("Login Required", "Admin login required")
                self.root.destroy()
                return False
        except mysql.connector.Error as err:
            print(f"Error loading admin session: {err}")
            messagebox.showerror("Database Error", f"Error loading admin session: {err}")
            return False
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def setup_ui(self):
        """Set up the main application UI with sidebar and content area"""
        self.main_frame = ctk.CTkFrame(self.root, fg_color="white", corner_radius=0)
        self.main_frame.pack(expand=True, fill="both")

        # Sidebar
        self.setup_sidebar()

        # Content area
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="white", corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Initialize section frames
        self.frames = {
            "dashboard": self.create_dashboard_frame(),
            "bookings": self.create_bookings_frame(),
            "users": self.create_users_frame(),
            "hotels": self.create_hotels_frame(),
            "reports": self.create_reports_frame()
        }

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
            ctk.CTkButton(
                sidebar,
                text=btn_text,
                font=("Arial", 14),
                fg_color="transparent",
                hover_color="#34495E",
                anchor="w",
                height=45,
                width=200,
                command=btn_command
            ).pack(pady=5, padx=10)

        # Admin welcome message
        if self.current_admin:
            admin_frame = ctk.CTkFrame(sidebar, fg_color="transparent", height=80)
            admin_frame.pack(side="bottom", fill="x", pady=20, padx=10)
            admin_name = self.current_admin['AdminName']
            ctk.CTkLabel(admin_frame, text="Welcome,", font=("Arial", 12), text_color="#8395a7").pack(anchor="w")
            ctk.CTkLabel(admin_frame, text=admin_name, font=("Arial", 14, "bold"), text_color="white").pack(anchor="w")

    def show_frame(self, frame_name):
        """Show the specified frame and hide others"""
        for frame in self.frames.values():
            frame.pack_forget()
        frame = self.frames[frame_name]
        frame.pack(fill="both", expand=True)
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
        self.root.destroy()

    # ------------------- Dashboard Section -------------------
    def create_dashboard_frame(self):
        """Create the dashboard frame with stats and chart"""
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 20))
        ctk.CTkLabel(header_frame, text="Admin Dashboard", font=("Arial", 28, "bold"), text_color="#2C3E50").pack(anchor="center")

        self.stats_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=30, pady=(0, 20))
        self.stats_cards = []

        chart_frame = ctk.CTkFrame(frame, fg_color="white", corner_radius=10, border_width=1, border_color="#E5E5E5")
        chart_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        ctk.CTkLabel(chart_frame, text="Revenue & Bookings Overview", font=("Arial", 18, "bold"), text_color="#2C3E50").pack(anchor="w", padx=20, pady=10)
        self.fig = Figure(figsize=(10, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
        return frame

    def get_dashboard_stats(self):
        """Fetch dashboard statistics from database"""
        stats = {"total_bookings": 0, "total_revenue": 0, "active_users": 0, "hotels_listed": 0}
        connection = connect_db()
        if not connection:
            return stats
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM Booking WHERE User_ID IN (SELECT user_id FROM Users WHERE is_active = 1)")
            stats["total_bookings"] = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(Total_Cost) FROM Booking WHERE User_ID IN (SELECT user_id FROM Users WHERE is_active = 1)")
            total_revenue = cursor.fetchone()[0]
            stats["total_revenue"] = total_revenue if total_revenue else 0
            cursor.execute("SELECT COUNT(*) FROM Users WHERE is_active = 1")
            stats["active_users"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Hotel")
            stats["hotels_listed"] = cursor.fetchone()[0]
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
        return stats

    def get_monthly_data(self):
        """Fetch monthly revenue and booking data for chart"""
        months, revenue, bookings = [], [], []
        connection = connect_db()
        if not connection:
            return months, revenue, bookings
        try:
            cursor = connection.cursor()
            today = datetime.today()
            six_months_ago = today - timedelta(days=180)
            current = six_months_ago
            while current <= today:
                month_start = datetime(current.year, current.month, 1)
                next_month = datetime(current.year + 1, 1, 1) if current.month == 12 else datetime(current.year, current.month + 1, 1)
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM Booking 
                    WHERE Check_IN_Date >= %s AND Check_IN_Date < %s 
                    AND User_ID IN (SELECT user_id FROM Users WHERE is_active = 1)
                    """,
                    (month_start, next_month)
                )
                month_bookings = cursor.fetchone()[0]
                cursor.execute(
                    """
                    SELECT SUM(Total_Cost) FROM Booking 
                    WHERE Check_IN_Date >= %s AND Check_IN_Date < %s 
                    AND User_ID IN (SELECT user_id FROM Users WHERE is_active = 1)
                    """,
                    (month_start, next_month)
                )
                month_revenue = cursor.fetchone()[0]
                months.append(calendar.month_abbr[current.month])
                bookings.append(month_bookings)
                revenue.append(month_revenue if month_revenue else 0)
                current = next_month
        except mysql.connector.Error as err:
            print(f"Database Error: {err}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
        return months, revenue, bookings

    def populate_dashboard(self):
        """Populate dashboard with stats and chart"""
        for card in self.stats_cards:
            card.destroy()
        self.stats_cards.clear()
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
        """Create the bookings management frame"""
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header_frame, text="Manage Bookings", font=("Arial", 28, "bold"), text_color="#2C3E50").pack(anchor="w")

        filter_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#E5E5E5", corner_radius=10)
        filter_frame.pack(fill="x", padx=30, pady=(0, 10))
        filter_header = ctk.CTkFrame(filter_frame, fg_color="white", height=40)
        filter_header.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(filter_header, text="Filter Bookings", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(anchor="w")
        filter_options = ctk.CTkFrame(filter_frame, fg_color="white")
        filter_options.pack(fill="x", padx=20, pady=(0, 10))

        search_frame = ctk.CTkFrame(filter_options, fg_color="white")
        search_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(search_frame, text="Search", font=("Arial", 12)).pack(anchor="w")
        self.bookings_search_entry = ctk.CTkEntry(search_frame, width=150, placeholder_text="Customer or Room")
        self.bookings_search_entry.pack(pady=5)

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

        status_frame = ctk.CTkFrame(filter_options, fg_color="white")
        status_frame.pack(side="left", padx=(10, 10))
        ctk.CTkLabel(status_frame, text="Status", font=("Arial", 12)).pack(anchor="w")
        self.bookings_status_var = ctk.StringVar(value="All")
        status_options = ["All", "Pending", "Confirmed", "Cancelled"]
        self.bookings_status_dropdown = ctk.CTkComboBox(status_frame, values=status_options, variable=self.bookings_status_var, width=120)
        self.bookings_status_dropdown.pack(pady=5)

        button_frame = ctk.CTkFrame(filter_options, fg_color="white")
        button_frame.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(button_frame, text=" ", font=("Arial", 12)).pack(anchor="w")
        ctk.CTkButton(button_frame, text="Apply Filters", font=("Arial", 12), fg_color="#0F2D52", hover_color="#1E4D88", command=self.filter_bookings, width=100, height=30).pack(side="left", pady=5, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Reset", font=("Arial", 12), fg_color="#6C757D", hover_color="#5A6268", command=self.reset_booking_filters, width=80, height=30).pack(side="left", pady=5)

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
        """Load bookings from database, only for active users"""
        connection = connect_db()
        if not connection:
            return []
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT b.Booking_ID, CONCAT(u.first_name, ' ', u.last_name) AS Customer,
                       r.Room_Type, b.Check_IN_Date, b.Check_Out_Date, 
                       b.Total_Cost, b.Booking_Status
                FROM Booking b
                JOIN Users u ON b.User_ID = u.user_id
                JOIN Room r ON b.Room_ID = r.Room_ID
                WHERE u.is_active = 1
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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def load_booking_details(self, booking_id):
        """Load detailed information for a specific booking"""
        connection = connect_db()
        if not connection:
            return None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT b.*, u.first_name, u.last_name, u.email, u.phone, 
                       r.Room_Type, r.Price_per_Night
                FROM Booking b
                JOIN Users u ON b.User_ID = u.user_id
                JOIN Room r ON b.Room_ID = r.Room_ID
                WHERE b.Booking_ID = %s AND u.is_active = 1
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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_booking_status(self, booking_id, status):
        """Update the status of a booking"""
        connection = connect_db()
        if not connection:
            return False
        try:
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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def delete_booking(self, booking_id):
        """Delete a booking and update room availability"""
        connection = connect_db()
        if not connection:
            return False
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT Room_ID FROM Booking WHERE Booking_ID = %s", (booking_id,))
            room_id = cursor.fetchone()
            if not room_id:
                messagebox.showerror("Error", f"Booking #{booking_id} not found")
                return False
            room_id = room_id[0]
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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def populate_booking_table(self):
        """Populate the bookings table with data"""
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
        """Update booking status counts in UI"""
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
        """Display details of selected booking"""
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
        """Confirm selected booking"""
        if not self.selected_booking:
            return
        if self.update_booking_status(self.selected_booking['Booking_ID'], "Confirmed"):
            self.populate_booking_table()
            self.selected_booking['Booking_Status'] = "Confirmed"
            self.bookings_details_status.configure(text=f"Status: Confirmed")
            self.bookings_confirm_btn.configure(state="disabled")
            self.bookings_cancel_btn.configure(state="normal")

    def cancel_booking(self):
        """Cancel selected booking"""
        if not self.selected_booking:
            return
        confirmed = messagebox.askyesno("Confirm Cancellation", f"Are you sure you want to cancel booking #{self.selected_booking['Booking_ID']}?")
        if not confirmed:
            return
        if self.update_booking_status(self.selected_booking['Booking_ID'], "Cancelled"):
            self.populate_booking_table()
            self.selected_booking['Booking_Status'] = "Cancelled"
            self.bookings_details_status.configure(text=f"Status: Cancelled")
            self.bookings_confirm_btn.configure(state="normal")
            self.bookings_cancel_btn.configure(state="disabled")

    def delete_booking_ui(self):
        """Delete selected booking with confirmation"""
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
        """Apply filters to bookings table"""
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
        """Reset booking filters to default"""
        self.bookings_search_entry.delete(0, 'end')
        try:
            self.bookings_start_date_entry.set_date(None)
            self.bookings_end_date_entry.set_date(None)
        except:
            self.bookings_start_date_entry.delete(0, 'end')
            self.bookings_end_date_entry.delete(0, 'end')
        self.bookings_status_var.set("All")
        self.populate_booking_table()

    # ------------------- Manage Users Section -------------------
    def create_users_frame(self):
        """Create the users management frame"""
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
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
        ctk.CTkLabel(form_fields, text="Account Status", font=("Arial", 12), anchor="w").grid(row=6, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.users_active_var = ctk.BooleanVar(value=True)
        self.users_active_switch = ctk.CTkSwitch(form_fields, text="Active", variable=self.users_active_var, onvalue=True, offvalue=False)
        self.users_active_switch.grid(row=7, column=0, sticky="w", padx=(0, 10), pady=(0, 15))

        buttons_frame = ctk.CTkFrame(form_fields, fg_color="transparent")
        buttons_frame.grid(row=8, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        button_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        button_container.grid(row=0, column=1, columnspan=2)
        self.users_create_btn = ctk.CTkButton(button_container, text="Create User", font=("Arial", 13, "bold"), fg_color="#28A745", hover_color="#218838", command=self.create_user, width=140, height=40, corner_radius=8)
        self.users_update_btn = ctk.CTkButton(button_container, text="Update User", font=("Arial", 13, "bold"), fg_color="#2C3E50", hover_color="#1E4D88", command=self.update_user, width=140, height=40, corner_radius=8, state="disabled")
        self.users_delete_btn = ctk.CTkButton(button_container, text="Delete User", font=("Arial", 13, "bold"), fg_color="#DC3545", hover_color="#C82333", command=self.delete_user, width=140, height=40, corner_radius=8, state="disabled")
        self.users_clear_btn = ctk.CTkButton(button_container, text="Clear Form", font=("Arial", 13, "bold"), fg_color="#6C757D", hover_color="#5A6268", command=self.clear_user_form, width=140, height=40, corner_radius=8)
        self.users_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.users_clear_btn.grid(row=0, column=1)

        table_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        table_header = ctk.CTkFrame(table_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        table_header.pack(fill="x")
        ctk.CTkLabel(table_header, text="User List", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)
        self.users_user_count_label = ctk.CTkLabel(table_header, text="Total Users: 0", font=("Arial", 12))
        self.users_user_count_label.pack(side="right", padx=20, pady=10)

        table_container = ctk.CTkFrame(table_frame, fg_color="white")
        table_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        columns = ('ID', 'Name', 'Email', 'Phone', 'Address', 'Bookings', 'Status')
        self.users_table = ttk.Treeview(table_container, columns=columns, show='headings', height=8)
        for col in columns:
            self.users_table.heading(col, text=col)
            self.users_table.column(col, width=100, anchor='w')
        table_scroll_y = ttk.Scrollbar(table_container, orient='vertical', command=self.users_table.yview)
        table_scroll_x = ttk.Scrollbar(table_container, orient='horizontal', command=self.users_table.xview)
        self.users_table.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)
        table_scroll_y.pack(side='right', fill='y')
        table_scroll_x.pack(side='bottom', fill='x')
        self.users_table.pack(expand=True, fill='both')
        self.users_table.bind('<<TreeviewSelect>>', self.show_user_details)

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
        self.users_details_status = ctk.CTkLabel(details_info_frame, text="Status: ", font=("Arial", 13), text_color="#6C757D")
        self.users_details_status.grid(row=2, column=0, sticky="w", pady=(0, 5))
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
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def load_users(self):
        """Load all users from database"""
        connection = connect_db()
        if not connection:
            return []
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone, 
                       u.user_address, COUNT(b.Booking_ID) as bookings, u.is_active
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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def load_user_details(self, user_id):
        """Load detailed information for a specific user"""
        connection = connect_db()
        if not connection:
            return None
        try:
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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def create_user(self):
        """Create a new user"""
        first_name = self.users_first_name_entry.get().strip()
        last_name = self.users_last_name_entry.get().strip()
        email = self.users_email_entry.get().strip()
        phone = self.users_phone_entry.get().strip()
        address = self.users_address_entry.get().strip()
        password = self.users_password_entry.get()
        is_active = 1 if self.users_active_var.get() else 0
        if not first_name or not last_name or not email or not password:
            messagebox.showwarning("Input Error", "First name, last name, email, and password are required")
            return
        hashed_password = self.hash_password(password)
        connection = connect_db()
        if not connection:
            return
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
            if cursor.fetchone():
                messagebox.showwarning("Input Error", "A user with this email already exists")
                return
            cursor.execute(
                """
                INSERT INTO Users (first_name, last_name, email, phone, password, user_address, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (first_name, last_name, email, phone or None, hashed_password, address or None, is_active)
            )
            connection.commit()
            messagebox.showinfo("Success", "User created successfully")
            self.clear_user_form()
            self.populate_user_table()
        except mysql.connector.Error as err:
            print(f"Error creating user: {err}")
            messagebox.showerror("Database Error", f"Error creating user: {err}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def update_user(self):
        """Update selected user's information"""
        if not self.selected_user:
            messagebox.showwarning("Selection Error", "No user selected")
            return
        first_name = self.users_first_name_entry.get().strip()
        last_name = self.users_last_name_entry.get().strip()
        email = self.users_email_entry.get().strip()
        phone = self.users_phone_entry.get().strip()
        address = self.users_address_entry.get().strip()
        password = self.users_password_entry.get()
        is_active = 1 if self.users_active_var.get() else 0
        if not first_name or not last_name or not email:
            messagebox.showwarning("Input Error", "First name, last name, and email are required")
            return
        connection = connect_db()
        if not connection:
            return
        try:
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
                        phone = %s, user_address = %s, password = %s, is_active = %s
                    WHERE user_id = %s
                    """,
                    (first_name, last_name, email, phone or None, address or None, hashed_password, is_active, self.selected_user['user_id'])
                )
            else:
                cursor.execute(
                    """
                    UPDATE Users
                    SET first_name = %s, last_name = %s, email = %s, 
                        phone = %s, user_address = %s, is_active = %s
                    WHERE user_id = %s
                    """,
                    (first_name, last_name, email, phone or None, address or None, is_active, self.selected_user['user_id'])
                )
            connection.commit()
            messagebox.showinfo("Success", "User updated successfully")
            self.selected_user = self.load_user_details(self.selected_user['user_id'])
            self.show_user_details(None)
            self.populate_user_table()
        except mysql.connector.Error as err:
            print(f"Error updating user: {err}")
            messagebox.showerror("Database Error", f"Error updating user: {err}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def delete_user(self):
        """Delete selected user"""
        if not self.selected_user:
            messagebox.showwarning("Selection Error", "No user selected")
            return
        confirmed = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete user {self.selected_user['first_name']} {self.selected_user['last_name']}?\n\nThis will also delete all their bookings.\nThis action cannot be undone.")
        if not confirmed:
            return
        connection = connect_db()
        if not connection:
            return
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM Booking WHERE User_ID = %s", (self.selected_user['user_id'],))
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
            if connection.is_connected():
                cursor.close()
                connection.close()

    def populate_user_table(self):
        """Populate the users table with data"""
        for row in self.users_table.get_children():
            self.users_table.delete(row)
        users = self.load_users()
        for user in users:
            full_name = f"{user['first_name']} {user['last_name']}"
            phone = user['phone'] if user['phone'] else "N/A"
            address = user['user_address'] if user['user_address'] else "N/A"
            bookings = str(user['bookings'])
            status = "Active" if user['is_active'] else "Inactive"
            self.users_table.insert('', 'end', iid=user['user_id'], values=(
                user['user_id'],
                full_name,
                user['email'],
                phone,
                address,
                bookings,
                status
            ))
        self.users_user_count_label.configure(text=f"Total Users: {len(users)}")

    def show_user_details(self, event):
        """Display details of selected user"""
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
        self.users_active_var.set(self.selected_user['is_active'])
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
        self.users_details_status.configure(text=f"Status: {'Active' if self.selected_user['is_active'] else 'Inactive'}")
        total_bookings = self.selected_user['bookings'] if self.selected_user['bookings'] else 0
        total_spent = self.selected_user['total_spent'] if self.selected_user['total_spent'] else 0
        self.users_details_bookings.configure(text=f"Total Bookings: {total_bookings}")
        self.users_details_spent.configure(text=f"Total Spent: ${total_spent:,.2f}")
        for row in self.users_bookings_table.get_children():
            self.users_bookings_table.delete(row)
        if 'recent_bookings' in self.selected_user and self.selected_user['recent_bookings']:
            for booking in self.selected_user['recent_bookings']:
                check_in = booking['Check_IN_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_IN_Date'], datetime) else booking['Check_IN_Date']
                check_out = booking['Check_Out_Date'].strftime('%Y-%m-%d') if isinstance(booking['Check_Out_Date'], datetime) else booking['Check_Out_Date']
                self.users_bookings_table.insert('', 'end', values=(
                    booking['Booking_ID'],
                    booking['Room_Type'],
                    check_in,
                    check_out,
                    f"${booking['Total_Cost']}",
                    booking['Booking_Status']
                ), tags=(booking['Booking_Status'].lower(),))

    def new_user_mode(self):
        """Switch to new user creation mode"""
        self.clear_user_form()
        self.selected_user = None
        self.users_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.users_clear_btn.grid(row=0, column=1)
        self.users_update_btn.grid_forget()
        self.users_delete_btn.grid_forget()
        self.users_details_frame.pack_forget()
        self.users_active_var.set(True)

    def clear_user_form(self):
        """Clear the user form fields"""
        self.users_first_name_entry.delete(0, 'end')
        self.users_last_name_entry.delete(0, 'end')
        self.users_email_entry.delete(0, 'end')
        self.users_phone_entry.delete(0, 'end')
        self.users_address_entry.delete(0, 'end')
        self.users_password_entry.delete(0, 'end')
        self.users_active_var.set(True)
        self.users_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.users_clear_btn.grid(row=0, column=1)
        self.users_update_btn.grid_forget()
        self.users_delete_btn.grid_forget()
        self.users_details_frame.pack_forget()
        self.selected_user = None

    def search_users(self):
        """Search users based on input term"""
        search_term = self.users_search_entry.get().lower()
        for row in self.users_table.get_children():
            self.users_table.delete(row)
        users = self.load_users()
        filtered_users = []
        for user in users:
            if search_term in f"{user['first_name']} {user['last_name']}".lower() or search_term in user['email'].lower():
                filtered_users.append(user)
        for user in filtered_users:
            full_name = f"{user['first_name']} {user['last_name']}"
            phone = user['phone'] if user['phone'] else "N/A"
            address = user['user_address'] if user['user_address'] else "N/A"
            bookings = str(user['bookings'])
            status = "Active" if user['is_active'] else "Inactive"
            self.users_table.insert('', 'end', iid=user['user_id'], values=(
                user['user_id'],
                full_name,
                user['email'],
                phone,
                address,
                bookings,
                status
            ))
        self.users_user_count_label.configure(text=f"Total Users: {len(filtered_users)}")

    # ------------------- Manage Hotels Section -------------------
    def create_hotels_frame(self):
        """Create the hotels management frame with a scrollable area"""
        # Main frame for the hotels section
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        
        # Create a scrollable frame as the main container
        scrollable_frame = ctk.CTkScrollableFrame(frame, fg_color="white", corner_radius=0)
        scrollable_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header frame
        header_frame = ctk.CTkFrame(scrollable_frame, fg_color="white", height=60)
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

        # Form frame
        form_frame = ctk.CTkFrame(scrollable_frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        form_frame.pack(fill="x", padx=30, pady=(0, 20))
        form_header = ctk.CTkFrame(form_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        form_header.pack(fill="x")
        ctk.CTkLabel(form_header, text="Hotel Information", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)
        form_fields = ctk.CTkFrame(form_frame, fg_color="white")
        form_fields.pack(fill="x", padx=20, pady=(20, 20))
        form_fields.columnconfigure(0, weight=1)
        form_fields.columnconfigure(1, weight=1)

        ctk.CTkLabel(form_fields, text="Hotel Name *", font=("Arial", 12), anchor="w").grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.hotels_name_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter hotel name")
        self.hotels_name_entry.grid(row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Location *", font=("Arial", 12), anchor="w").grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.hotels_location_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Enter location")
        self.hotels_location_entry.grid(row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Description", font=("Arial", 12), anchor="w").grid(row=4, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.hotels_description_entry = ctk.CTkTextbox(form_fields, height=100, width=300, corner_radius=8)
        self.hotels_description_entry.grid(row=5, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        ctk.CTkLabel(form_fields, text="Star-rating *", font=("Arial", 12), anchor="w").grid(row=6, column=0, sticky="ew", padx=(0, 10), pady=(0, 5))
        self.hotels_star_rating_var = ctk.StringVar(value="3")
        star_frame = ctk.CTkFrame(form_fields, fg_color="transparent")
        star_frame.grid(row=7, column=0, sticky="ew", padx=(0, 10), pady=(0, 15))
        for i, rating in enumerate([1, 2, 3, 4, 5], 1):
            ctk.CTkRadioButton(star_frame, text=str(rating), variable=self.hotels_star_rating_var, value=str(rating)).pack(side="left", padx=5)

        ctk.CTkLabel(form_fields, text="Image", font=("Arial", 12), anchor="w").grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
        self.hotels_image_entry = ctk.CTkEntry(form_fields, height=35, placeholder_text="Select image", state="readonly")
        self.hotels_image_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(0, 15))
        ctk.CTkButton(form_fields, text="Browse", font=("Arial", 12), fg_color="#6C757D", hover_color="#5A6268", command=self.browse_image, width=100, height=35).grid(row=1, column=2, padx=(5, 0), pady=(0, 15))

        ctk.CTkLabel(form_fields, text="Amenities", font=("Arial", 12), anchor="w").grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=(0, 5))
        self.hotels_amenity_vars = {}
        self.hotels_amenities_frame = ctk.CTkFrame(form_fields, fg_color="transparent")
        self.hotels_amenities_frame.grid(row=3, column=1, rowspan=4, sticky="nsew", padx=(10, 0), pady=(0, 15))
        connection = connect_db()
        if connection:
            try:
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
                if connection.is_connected():
                    cursor.close()
                    connection.close()

        buttons_frame = ctk.CTkFrame(form_fields, fg_color="transparent")
        buttons_frame.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        button_container = ctk.CTkFrame(buttons_frame, fg_color="transparent")
        button_container.grid(row=0, column=1, columnspan=2)
        self.hotels_create_btn = ctk.CTkButton(button_container, text="Create Hotel", font=("Arial", 13, "bold"), fg_color="#CAA745", hover_color="#218838", command=self.create_hotel, width=140, height=40, corner_radius=8)
        self.hotels_update_btn = ctk.CTkButton(button_container, text="Update Hotel", font=("Arial", 13, "bold"), fg_color="#2C3E50", hover_color="#1E4D88", command=self.update_hotel, width=140, height=40, corner_radius=8, state="disabled")
        self.hotels_delete_btn = ctk.CTkButton(button_container, text="Delete Hotel", font=("Arial", 13, "bold"), fg_color="#DC3545", hover_color="#C82333", command=self.delete_hotel, width=140, height=40, corner_radius=8, state="disabled")
        self.hotels_clear_btn = ctk.CTkButton(button_container, text="Clear Form", font=("Arial", 13, "bold"), fg_color="#6C757D", hover_color="#5A6268", command=self.clear_hotel_form, width=140, height=40, corner_radius=8)
        self.hotels_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.hotels_clear_btn.grid(row=0, column=1)

        # Table frame
        table_frame = ctk.CTkFrame(scrollable_frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        table_frame.pack(fill="both", padx=30, pady=(0, 20))
        table_header = ctk.CTkFrame(table_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        table_header.pack(fill="x")
        ctk.CTkLabel(table_header, text="Hotel List", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(side="left", padx=20, pady=10)
        self.hotels_count_label = ctk.CTkLabel(table_header, text="Total Hotels: 0", font=("Arial", 12))
        self.hotels_count_label.pack(side="right", padx=20, pady=10)

        table_container = ctk.CTkFrame(table_frame, fg_color="white")
        table_container.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        columns = ('ID', 'Name', 'Location', 'Rooms', 'Bookings')
        self.hotels_table = ttk.Treeview(table_container, columns=columns, show='headings', height=8)
        for col in columns:
            self.hotels_table.heading(col, text=col)
            self.hotels_table.column(col, width=100, anchor='w')
        table_scroll_y = ttk.Scrollbar(table_container, orient='vertical', command=self.hotels_table.yview)
        table_scroll_x = ttk.Scrollbar(table_container, orient='horizontal', command=self.hotels_table.xview)
        self.hotels_table.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)
        table_scroll_y.pack(side='right', fill='y')
        table_scroll_x.pack(side='bottom', fill='x')
        self.hotels_table.pack(expand=True, fill='both')
        self.hotels_table.bind('<<TreeviewSelect>>', self.show_hotel_details)

        # Details frame
        self.hotels_details_frame = ctk.CTkFrame(scrollable_frame, fg_color="white", border_width=1, border_color="#DEE2E6", corner_radius=10)
        details_header = ctk.CTkFrame(self.hotels_details_frame, fg_color="#E9ECEF", height=50, corner_radius=0)
        details_header.pack(fill="x")
        self.hotels_details_hotel_id = ctk.CTkLabel(details_header, text="Hotel #", font=("Arial", 16, "bold"), text_color="#2C3E50")
        self.hotels_details_hotel_id.pack(side="left", padx=20, pady=10)
        details_content = ctk.CTkFrame(self.hotels_details_frame, fg_color="white")
        details_content.pack(fill="x", padx=20, pady=(15, 15))
        self.hotels_details_name = ctk.CTkLabel(details_content, text="Hotel Name", font=("Arial", 16, "bold"), text_color="#2C3E50")
        self.hotels_details_name.pack(anchor="w", pady=(0, 5))
        self.hotels_details_location = ctk.CTkLabel(details_content, text="Location", font=("Arial", 13), text_color="#6C757D")
        self.hotels_details_location.pack(anchor="w", pady=(0, 5))
        self.hotels_details_description = ctk.CTkLabel(details_content, text="Description", font=("Arial", 13), text_color="#6C757D")
        self.hotels_details_description.pack(anchor="w", pady=(0, 10))
        self.hotels_details_image_label = ctk.CTkLabel(details_content, text="No image available", font=("Arial", 12), text_color="#6C757D")
        self.hotels_details_image_label.pack(anchor="w", pady=(0, 15))
        stats_frame = ctk.CTkFrame(details_content, fg_color="#E9ECEF", corner_radius=8)
        stats_frame.pack(fill="x", pady=(0, 15))
        stats_frame.columnconfigure(0, weight=1)
        stats_frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(stats_frame, text="🏠", font=("Arial", 20)).grid(row=0, column=0, padx=(15, 5), pady=15, sticky="e")
        self.hotels_details_rooms = ctk.CTkLabel(stats_frame, text="Total Rooms: 0", font=("Arial", 13, "bold"), text_color="#2C3E50")
        self.hotels_details_rooms.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="w")
        ctk.CTkLabel(stats_frame, text="🗓️", font=("Arial", 20)).grid(row=0, column=2, padx=(15, 5), pady=15, sticky="e")
        self.hotels_details_bookings = ctk.CTkLabel(stats_frame, text="Total Bookings: 0", font=("Arial", 13, "bold"), text_color="#2C3E50")
        self.hotels_details_bookings.grid(row=0, column=3, padx=(0, 15), pady=15, sticky="w")
        rooms_header = ctk.CTkFrame(details_content, fg_color="white")
        rooms_header.pack(fill="x", pady=(5, 10))
        ctk.CTkLabel(rooms_header, text="Available Rooms", font=("Arial", 14, "bold"), text_color="#2C3E50").pack(side="left")
        rooms_container = ctk.CTkFrame(details_content, fg_color="white")
        rooms_container.pack(fill="x", pady=(0, 10))
        room_columns = ('Room ID', 'Room Type', 'Price/Night', 'Status')
        self.hotels_rooms_table = ttk.Treeview(rooms_container, columns=room_columns, show='headings', height=4)
        for col in room_columns:
            self.hotels_rooms_table.heading(col, text=col)
            self.hotels_rooms_table.column(col, width=100, anchor='center')
        self.hotels_rooms_table.tag_configure('available', background='#d4edda')
        self.hotels_rooms_table.tag_configure('occupied', background='#f8d7da')
        rooms_scroll_y = ttk.Scrollbar(rooms_container, orient='vertical', command=self.hotels_rooms_table.yview)
        rooms_scroll_x = ttk.Scrollbar(rooms_container, orient='horizontal', command=self.hotels_rooms_table.xview)
        self.hotels_rooms_table.configure(yscrollcommand=rooms_scroll_y.set, xscrollcommand=rooms_scroll_x.set)
        rooms_scroll_y.pack(side='right', fill='y')
        rooms_scroll_x.pack(side='bottom', fill='x')
        self.hotels_rooms_table.pack(fill="x")

        return frame

    def load_hotels(self):
        """Load all hotels from database with room and booking counts"""
        connection = connect_db()
        if not connection:
            return []
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT h.Hotel_ID, h.hotel_name, h.location, 
                    COUNT(DISTINCT rc.Category_ID) as rooms, 
                    COUNT(DISTINCT b.Booking_ID) as bookings
                FROM Hotel h
                LEFT JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
                LEFT JOIN Booking b ON rc.Category_ID = b.Room_ID
                WHERE b.User_ID IS NULL OR b.User_ID IN (SELECT user_id FROM Users WHERE is_active = 1)
                GROUP BY h.Hotel_ID, h.hotel_name, h.location
                ORDER BY h.hotel_name
                """
            )
            hotels = cursor.fetchall()
            return hotels
        except mysql.connector.Error as err:
            print(f"Error loading hotels: {err}")
            messagebox.showerror("Database Error", f"Error loading hotels: {err}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def show_hotel_details(self, event):
        """Display details of selected hotel"""
        if event is not None:
            selected_id = self.hotels_table.focus()
            if not selected_id:
                return
            hotel_id = int(selected_id)
            hotel = self.load_hotel_details(hotel_id)
            if not hotel:
                return
            self.selected_hotel = hotel
        self.hotels_name_entry.delete(0, 'end')
        self.hotels_name_entry.insert(0, self.selected_hotel['Hotel_Name'])
        self.hotels_location_entry.delete(0, 'end')
        self.hotels_location_entry.insert(0, self.selected_hotel['Location'])
        self.hotels_description_entry.delete("1.0", "end")
        if self.selected_hotel['Description']:
            self.hotels_description_entry.insert("1.0", self.selected_hotel['Description'])
        self.hotels_star_rating_var.set(str(self.selected_hotel['Star_Rating']))
        self.hotels_image_entry.configure(state="normal")
        self.hotels_image_entry.delete(0, 'end')
        if self.selected_hotel['Image_Path']:
            self.hotels_image_entry.insert(0, os.path.basename(self.selected_hotel['Image_Path']))
        self.hotels_image_entry.configure(state="readonly")
        self.hotel_image_path = self.selected_hotel['Image_Path'] if self.selected_hotel['Image_Path'] else None
        self.hotels_create_btn.grid_forget()
        self.hotels_update_btn.grid(row=0, column=0, padx=(0, 10))
        self.hotels_delete_btn.grid(row=0, column=1, padx=(0, 10))
        self.hotels_clear_btn.grid(row=0, column=2)
        self.hotels_update_btn.configure(state="normal")
        self.hotels_delete_btn.configure(state="normal")
        self.hotels_details_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self.hotels_details_hotel_id.configure(text=f"Hotel #{self.selected_hotel['Hotel_ID']}")
        self.hotels_details_name.configure(text=f"{self.selected_hotel['Hotel_Name']}")
        self.hotels_details_location.configure(text=f"{self.selected_hotel['Location']}")
        self.hotels_details_description.configure(text=f"{self.selected_hotel['Description'] if self.selected_hotel['Description'] else 'No description available'}")
        star_rating_display = "★" * self.selected_hotel['Star_Rating']
        self.hotels_details_description.configure(text=f"{self.selected_hotel['Description'] if self.selected_hotel['Description'] else 'No description available'}\nRating: {star_rating_display}")
        if self.selected_hotel['Image_Path']:
            try:
                image = Image.open(self.selected_hotel['Image_Path'])
                image = image.resize((150, 150), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.hotels_details_image_label.configure(image=photo, text="")
                self.hotels_details_image_label.image = photo
            except Exception as e:
                print(f"Error loading image: {e}")
                self.hotels_details_image_label.configure(image=None, text="No image available")
        else:
            self.hotels_details_image_label.configure(image=None, text="No image available")
        total_rooms = len(self.selected_hotel['rooms']) if self.selected_hotel['rooms'] else 0
        total_bookings = self.selected_hotel['bookings'] if self.selected_hotel['bookings'] else 0
        self.hotels_details_rooms.configure(text=f"Total Rooms: {total_rooms}")
        self.hotels_details_bookings.configure(text=f"Total Bookings: {total_bookings}")
        for row in self.hotels_rooms_table.get_children():
            self.hotels_rooms_table.delete(row)
        if 'rooms' in self.selected_hotel and self.selected_hotel['rooms']:
            for room in self.selected_hotel['rooms']:
                status = room['Availability_status'].lower()
                self.hotels_rooms_table.insert('', 'end', values=(
                    room['Room_ID'],
                    room['Room_Type'],
                    f"${room['Price_per_Night']}",
                    room['Availability_status']
                ), tags=(status,))
        # Display amenities (optional, add to UI if needed)
        if 'amenities' in self.selected_hotel and self.selected_hotel['amenities']:
            amenities_text = ", ".join([f"{a['Amenity_Icon']} {a['Amenity_Name']}" for a in self.selected_hotel['amenities']])
            self.hotels_details_description.configure(text=f"{self.selected_hotel['Description'] if self.selected_hotel['Description'] else 'No description available'}\nRating: {star_rating_display}\nAmenities: {amenities_text}")

    def create_hotel(self):
        """Create a new hotel with details from the form"""
        hotel_name = self.hotels_name_entry.get().strip()
        location = self.hotels_location_entry.get().strip()
        description = self.hotels_description_entry.get("1.0", "end-1c").strip()  # Get text from Textbox
        star_rating = int(self.hotels_star_rating_var.get())
        image_path = self.hotel_image_path
        created_by = self.current_admin['Admin_ID'] if self.current_admin else 1  # Default to admin ID 1 if not set

        if not hotel_name or not location:
            messagebox.showwarning("Input Error", "Hotel name and location are required")
            return

        # Save hotel image
        if image_path:
            try:
                image_destination = self.save_hotel_image()
                if not image_destination:
                    messagebox.showwarning("Image Error", "Failed to save hotel image")
                    return
            except Exception as e:
                print(f"Error saving image: {e}")
                messagebox.showwarning("Image Error", "Error saving hotel image")
                return
        else:
            image_destination = None

        connection = connect_db()
        if not connection:
            return
        try:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT Hotel_ID FROM Hotel WHERE Hotel_Name = %s AND Location = %s",
                (hotel_name, location)
            )
            if cursor.fetchone():
                messagebox.showwarning("Input Error", "A hotel with this name and location already exists")
                return

            cursor.execute(
                """
                INSERT INTO Hotel (Hotel_Name, Location, Description, Star_Rating, Image_Path, Created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (hotel_name, location, description or None, star_rating, image_destination, created_by)
            )

            # Get the last inserted hotel ID
            hotel_id = cursor.lastrowid

            # Handle amenities
            for amenity_id, var in self.hotels_amenity_vars.items():
                if var.get():
                    cursor.execute(
                        "INSERT INTO Hotel_Amenities (Hotel_ID, Amenity_ID) VALUES (%s, %s)",
                        (hotel_id, amenity_id)
                    )

            connection.commit()
            messagebox.showinfo("Success", "Hotel created successfully!")
            self.clear_hotel_form()
            self.populate_hotel_table()
        except mysql.connector.Error as err:
            print(f"Error creating hotel: {err}")
            messagebox.showerror("Database Error", f"Error creating hotel: {err}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def save_hotel_image(self):
        """Save the selected hotel image to a directory"""
        if not self.hotel_image_path:
            return None
        try:
            img = Image.open(self.hotel_image_path)
            img = img.resize((800, 600), Image.Resampling.LANCZOS)  # Resize for consistency
            extension = os.path.splitext(self.hotel_image_path)[1]
            new_filename = f"hotel_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
            destination = os.path.join("hotel_images", new_filename)
            os.makedirs("hotel_images", exist_ok=True)
            img.save(destination)
            return destination
        except Exception as e:
            print(f"Error saving hotel image: {e}")
            return None

    def update_hotel(self):
        """Update selected hotel's information"""
        if not self.selected_hotel:
            messagebox.showwarning("Selection Error", "No hotel selected")
            return
        name = self.hotels_name_entry.get().strip()
        location = self.hotels_location_entry.get().strip()
        description = self.hotels_description_entry.get("1.0", "end-1c").strip()
        star_rating = int(self.hotels_star_rating_var.get())
        image_path = self.hotel_image_path
        if not name or not location:
            messagebox.showwarning("Input Error", "Hotel name and location are required")
            return
        try:
            connection = connect_db()
            cursor = connection.cursor()
            # Check for duplicate hotel name and location
            cursor.execute(
                """
                SELECT Hotel_ID FROM Hotel 
                WHERE Hotel_Name = %s AND Location = %s AND Hotel_ID != %s
                """,
                (name, location, self.selected_hotel['Hotel_ID'])
            )
            if cursor.fetchone():
                messagebox.showwarning("Input Error", "Another hotel with this name and location already exists")
                return
            # Handle image update
            image_destination = None
            if image_path and image_path != self.selected_hotel['image_path']:
                image_destination = self.save_hotel_image()
                if not image_destination:
                    messagebox.showwarning("Image Error", "Failed to save hotel image")
                    return
            else:
                image_destination = self.selected_hotel['image_path']
            # Update hotel details
            cursor.execute(
                """
                UPDATE Hotel
                SET Hotel_Name = %s, Location = %s, Description = %s, Star_Rating = %s, Image_Path = %s
                WHERE Hotel_ID = %s
                """,
                (name, location, description or None, star_rating, image_destination, self.selected_hotel['Hotel_ID'])
            )
            # Update amenities
            cursor.execute("DELETE FROM Hotel_Amenities WHERE Hotel_ID = %s", (self.selected_hotel['Hotel_ID'],))
            for amenity_id, var in self.hotels_amenity_vars.items():
                if var.get():
                    cursor.execute(
                        "INSERT INTO Hotel_Amenities (Hotel_ID, Amenity_ID) VALUES (%s, %s)",
                        (self.selected_hotel['Hotel_ID'], amenity_id)
                    )
            connection.commit()
            messagebox.showinfo("Success", "Hotel updated successfully")
            self.selected_hotel = self.load_hotel_details(self.selected_hotel['Hotel_ID'])
            self.show_hotel_details(None)
            self.populate_hotel_table()
        except mysql.connector.Error as err:
            print(f"Error updating hotel: {err}")
            messagebox.showerror("Database Error", f"Error updating hotel: {err}")
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()

    def delete_hotel(self):
        """Delete selected hotel"""
        if not self.selected_hotel:
            messagebox.showwarning("Selection Error", "No hotel selected")
            return
        confirmed = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the hotel {self.selected_hotel['hotel_name']}?\n\nThis will also delete all associated rooms and bookings.\nThis action cannot be undone."
        )
        if not confirmed:
            return
        try:
            connection = connect_db()
            cursor = connection.cursor()
            # Delete associated bookings
            cursor.execute(
                """
                DELETE FROM Booking 
                WHERE Room_ID IN (SELECT Category_ID FROM RoomCategory WHERE Hotel_ID = %s)
                """,
                (self.selected_hotel['Hotel_ID'],)
            )
            # Delete associated rooms
            cursor.execute("DELETE FROM RoomCategory WHERE Hotel_ID = %s", (self.selected_hotel['Hotel_ID'],))
            # Delete hotel amenities
            cursor.execute("DELETE FROM Hotel_Amenities WHERE Hotel_ID = %s", (self.selected_hotel['Hotel_ID'],))
            # Delete the hotel
            cursor.execute("DELETE FROM Hotel WHERE Hotel_ID = %s", (self.selected_hotel['Hotel_ID'],))
            connection.commit()
            messagebox.showinfo("Success", "Hotel deleted successfully")
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

    def browse_image(self):
        """Open file dialog to select hotel image"""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if file_path:
            self.hotel_image_path = file_path
            self.hotels_image_entry.configure(state="normal")
            self.hotels_image_entry.delete(0, 'end')
            self.hotels_image_entry.insert(0, os.path.basename(file_path))
            self.hotels_image_entry.configure(state="readonly")

    def populate_hotel_table(self):
        """Populate the hotels table with data"""
        for row in self.hotels_table.get_children():
            self.hotels_table.delete(row)
        hotels = self.load_hotels()
        for hotel in hotels:
            self.hotels_table.insert('', 'end', iid=hotel['Hotel_ID'], values=(
                hotel['Hotel_ID'],
                hotel['hotel_name'],  # Updated column name to match database
                hotel['location'],    # Updated column name to match database
                hotel['rooms'],
                hotel['bookings']
            ))
        self.hotels_count_label.configure(text=f"Total Hotels: {len(hotels)}")

    def show_hotel_details(self, event):
        """Display details of selected hotel"""
        if event is not None:
            selected_id = self.hotels_table.focus()
            if not selected_id:
                return
            hotel_id = int(selected_id)
            hotel = self.load_hotel_details(hotel_id)
            if not hotel:
                return
            self.selected_hotel = hotel
        
        # Update form fields with selected hotel data
        self.hotels_name_entry.delete(0, 'end')
        self.hotels_name_entry.insert(0, self.selected_hotel['hotel_name'])
        
        self.hotels_location_entry.delete(0, 'end')
        self.hotels_location_entry.insert(0, self.selected_hotel['location'])
        
        self.hotels_description_entry.delete("1.0", "end")
        if self.selected_hotel['description']:
            self.hotels_description_entry.insert("1.0", self.selected_hotel['description'])
        
        self.hotels_star_rating_var.set(str(self.selected_hotel['star_rating']))
        
        self.hotels_image_entry.configure(state="normal")
        self.hotels_image_entry.delete(0, 'end')
        if self.selected_hotel['image_path']:
            self.hotels_image_entry.insert(0, os.path.basename(self.selected_hotel['image_path']))
        self.hotels_image_entry.configure(state="readonly")
        
        self.hotel_image_path = self.selected_hotel['image_path'] if self.selected_hotel['image_path'] else None
        
        # Update amenities checkboxes
        for amenity_id, var in self.hotels_amenity_vars.items():
            var.set(0)  # Reset all first
        
        if 'amenities' in self.selected_hotel and self.selected_hotel['amenities']:
            for amenity in self.selected_hotel['amenities']:
                if amenity['Amenity_ID'] in self.hotels_amenity_vars:
                    self.hotels_amenity_vars[amenity['Amenity_ID']].set(1)
        
        # Update UI buttons
        self.hotels_create_btn.grid_forget()
        self.hotels_update_btn.grid(row=0, column=0, padx=(0, 10))
        self.hotels_delete_btn.grid(row=0, column=1, padx=(0, 10))
        self.hotels_clear_btn.grid(row=0, column=2)
        self.hotels_update_btn.configure(state="normal")
        self.hotels_delete_btn.configure(state="normal")
        
        # Show details frame and populate it
        self.hotels_details_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self.hotels_details_hotel_id.configure(text=f"Hotel #{self.selected_hotel['Hotel_ID']}")
        self.hotels_details_name.configure(text=f"{self.selected_hotel['hotel_name']}")
        self.hotels_details_location.configure(text=f"{self.selected_hotel['location']}")
        
        # Display description and star rating
        star_rating_display = "★" * self.selected_hotel['star_rating']
        description_text = f"{self.selected_hotel['description'] if self.selected_hotel['description'] else 'No description available'}\nRating: {star_rating_display}"
        
        # Display amenities if available
        if 'amenities' in self.selected_hotel and self.selected_hotel['amenities']:
            amenities_text = ", ".join([f"{a['Amenity_Icon']} {a['Amenity_Name']}" for a in self.selected_hotel['amenities']])
            description_text += f"\nAmenities: {amenities_text}"
        
        self.hotels_details_description.configure(text=description_text)
        
        # Display image if available
        if self.selected_hotel['image_path']:
            try:
                image = Image.open(self.selected_hotel['image_path'])
                image = image.resize((150, 150), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.hotels_details_image_label.configure(image=photo, text="")
                self.hotels_details_image_label.image = photo
            except Exception as e:
                print(f"Error loading image: {e}")
                self.hotels_details_image_label.configure(image=None, text="No image available")
        else:
            self.hotels_details_image_label.configure(image=None, text="No image available")
        
        # Update room and booking counts
        total_rooms = len(self.selected_hotel['rooms']) if 'rooms' in self.selected_hotel and self.selected_hotel['rooms'] else 0
        total_bookings = self.selected_hotel['bookings'] if 'bookings' in self.selected_hotel else 0
        self.hotels_details_rooms.configure(text=f"Total Rooms: {total_rooms}")
        self.hotels_details_bookings.configure(text=f"Total Bookings: {total_bookings}")
        
        # Clear and populate rooms table
        for row in self.hotels_rooms_table.get_children():
            self.hotels_rooms_table.delete(row)
        
        if 'rooms' in self.selected_hotel and self.selected_hotel['rooms']:
            for room in self.selected_hotel['rooms']:
                self.hotels_rooms_table.insert('', 'end', values=(
                    room['Room_ID'],
                    room['Room_Type'],
                    f"${room['Price_per_Night']}",
                    room['Availability_status']
                ), tags=(room['Availability_status'].lower(),))
    def load_hotel_details(self, hotel_id):
        """Load detailed information for a specific hotel"""
        connection = connect_db()
        if not connection:
            return None
        try:
            cursor = connection.cursor(dictionary=True)
            # Get hotel basic information
            cursor.execute(
                """
                SELECT h.*, 
                    COUNT(DISTINCT rc.Category_ID) as room_count,
                    COUNT(DISTINCT b.Booking_ID) as bookings
                FROM Hotel h
                LEFT JOIN RoomCategory rc ON h.Hotel_ID = rc.Hotel_ID
                LEFT JOIN Booking b ON rc.Category_ID = b.Room_ID
                WHERE h.Hotel_ID = %s
                GROUP BY h.Hotel_ID
                """,
                (hotel_id,)
            )
            hotel = cursor.fetchone()
            
            if hotel:
                # Get hotel rooms
                cursor.execute(
                    """
                    SELECT rc.Category_ID as Room_ID, rc.category_name as Room_Type, 
                        rc.base_price as Price_per_Night,
                        CASE 
                            WHEN b.Booking_ID IS NULL THEN 'Available' 
                            ELSE 'Booked' 
                        END as Availability_status
                    FROM RoomCategory rc
                    LEFT JOIN Booking b ON rc.Category_ID = b.Room_ID AND b.Booking_Status != 'Cancelled'
                    WHERE rc.Hotel_ID = %s
                    """,
                    (hotel_id,)
                )
                hotel['rooms'] = cursor.fetchall()
                
                # Get hotel amenities
                cursor.execute(
                    """
                    SELECT a.Amenity_ID, a.amenity_name as Amenity_Name, a.amenity_icon as Amenity_Icon
                    FROM Hotel_Amenities ha
                    JOIN Amenities a ON ha.Amenity_ID = a.Amenity_ID
                    WHERE ha.Hotel_ID = %s
                    """,
                    (hotel_id,)
                )
                hotel['amenities'] = cursor.fetchall()
            
            return hotel
        except mysql.connector.Error as err:
            print(f"Error loading hotel details: {err}")
            messagebox.showerror("Database Error", f"Error loading hotel details: {err}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def new_hotel_mode(self):
        """Switch to new hotel creation mode"""
        self.clear_hotel_form()
        self.selected_hotel = None
        self.hotels_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.hotels_clear_btn.grid(row=0, column=1)
        self.hotels_update_btn.grid_forget()
        self.hotels_delete_btn.grid_forget()
        self.hotels_details_frame.pack_forget()

    def clear_hotel_form(self):
        """Clear the hotel form fields"""
        self.hotels_name_entry.delete(0, 'end')
        self.hotels_location_entry.delete(0, 'end')
        self.hotels_description_entry.delete("1.0", "end-1c")  # Fixed: Use "1.0" to "end-1c" for CTkTextbox
        self.hotels_image_entry.configure(state="normal")
        self.hotels_image_entry.delete(0, 'end')
        self.hotels_image_entry.configure(state="readonly")
        self.hotel_image_path = None
        self.hotels_star_rating_var.set("3")  # Reset star rating to default
        for amenity_id, var in self.hotels_amenity_vars.items():
            var.set(0)  # Reset all amenities
        self.hotels_create_btn.grid(row=0, column=0, padx=(0, 10))
        self.hotels_clear_btn.grid(row=0, column=1)
        self.hotels_update_btn.grid_forget()
        self.hotels_delete_btn.grid_forget()
        self.hotels_details_frame.pack_forget()
        self.selected_hotel = None

    def search_hotels(self):
        """Search hotels based on input term"""
        search_term = self.hotels_search_entry.get().lower()
        for row in self.hotels_table.get_children():
            self.hotels_table.delete(row)
        hotels = self.load_hotels()
        filtered_hotels = []
        for hotel in hotels:
            if search_term in hotel['Hotel_Name'].lower() or search_term in hotel['Location'].lower():
                filtered_hotels.append(hotel)
        for hotel in filtered_hotels:
            self.hotels_table.insert('', 'end', iid=hotel['Hotel_ID'], values=(
                hotel['Hotel_ID'],
                hotel['Hotel_Name'],
                hotel['Location'],
                hotel['rooms'],
                hotel['bookings']
            ))
        self.hotels_count_label.configure(text=f"Total Hotels: {len(filtered_hotels)}")

    # ------------------- Reports Section -------------------
    def create_reports_frame(self):
        """Create the reports and analytics frame"""
        frame = ctk.CTkFrame(self.content_frame, fg_color="white")
        header_frame = ctk.CTkFrame(frame, fg_color="white", height=60)
        header_frame.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header_frame, text="Reports & Analytics", font=("Arial", 28, "bold"), text_color="#2C3E50").pack(anchor="w")
        filter_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#E5E5E5", corner_radius=10)
        filter_frame.pack(fill="x", padx=30, pady=(0, 10))
        filter_header = ctk.CTkFrame(filter_frame, fg_color="white", height=40)
        filter_header.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(filter_header, text="Report Filters", font=("Arial", 16, "bold"), text_color="#2C3E50").pack(anchor="w")
        filter_options = ctk.CTkFrame(filter_frame, fg_color="white")
        filter_options.pack(fill="x", padx=20, pady=(0, 10))
        date_frame = ctk.CTkFrame(filter_options, fg_color="white")
        date_frame.pack(side="left", padx=(0, 10))
        ctk.CTkLabel(date_frame, text="Date Range", font=("Arial", 12)).pack(anchor="w")
        date_fields = ctk.CTkFrame(date_frame, fg_color="white")
        date_fields.pack(fill="x")
        self.reports_start_date_entry = DateEntry(date_fields, width=10, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd') if DateEntry else ctk.CTkEntry(date_fields, width=100, placeholder_text="YYYY-MM-DD")
        self.reports_start_date_entry.pack(side="left", padx=(0, 5))
        ctk.CTkLabel(date_fields, text="to", font=("Arial", 10)).pack(side="left", padx=5)
        self.reports_end_date_entry = DateEntry(date_fields, width=10, background='darkblue', foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd') if DateEntry else ctk.CTkEntry(date_fields, width=100, placeholder_text="YYYY-MM-DD")
        self.reports_end_date_entry.pack(side="left", padx=(5, 0))
        report_type_frame = ctk.CTkFrame(filter_options, fg_color="white")
        report_type_frame.pack(side="left", padx=(10, 10))
        ctk.CTkLabel(report_type_frame, text="Report Type", font=("Arial", 12)).pack(anchor="w")
        self.reports_type_var = ctk.StringVar(value="Revenue")
        report_types = ["Revenue", "Bookings", "User Activity"]
        self.reports_type_dropdown = ctk.CTkComboBox(report_type_frame, values=report_types, variable=self.reports_type_var, width=150)
        self.reports_type_dropdown.pack(pady=5)
        button_frame = ctk.CTkFrame(filter_options, fg_color="white")
        button_frame.pack(side="left", padx=(10, 0))
        ctk.CTkLabel(button_frame, text=" ", font=("Arial", 12)).pack(anchor="w")
        ctk.CTkButton(button_frame, text="Generate Report", font=("Arial", 12), fg_color="#0F2D52", hover_color="#1E4D88", command=self.generate_report, width=120, height=30).pack(side="left", pady=5, padx=(0, 5))
        ctk.CTkButton(button_frame, text="Export", font=("Arial", 12), fg_color="#6C757D", hover_color="#5A6268", command=self.export_report, width=80, height=30).pack(side="left", pady=5)
        chart_frame = ctk.CTkFrame(frame, fg_color="white", border_width=1, border_color="#E5E5E5", corner_radius=10)
        chart_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        self.reports_chart_label = ctk.CTkLabel(chart_frame, text="Report Chart", font=("Arial", 18, "bold"), text_color="#2C3E50")
        self.reports_chart_label.pack(anchor="w", padx=20, pady=10)
        self.reports_fig = Figure(figsize=(10, 4), dpi=100)
        self.reports_ax = self.reports_fig.add_subplot(111)
        self.reports_canvas = FigureCanvasTkAgg(self.reports_fig, master=chart_frame)
        self.reports_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 20))
        return frame

    def generate_report(self):
        """Generate a report based on selected filters"""
        report_type = self.reports_type_var.get()
        try:
            start_date = self.reports_start_date_entry.get_date() if hasattr(self.reports_start_date_entry, 'get_date') else None
            end_date = self.reports_end_date_entry.get_date() if hasattr(self.reports_end_date_entry, 'get_date') else None
        except:
            start_date = end_date = None
        if not start_date or not end_date:
            messagebox.showwarning("Input Error", "Please select a valid date range")
            return
        data = []
        labels = []
        try:
            connection = connect_db()
            cursor = connection.cursor()
            current_date = start_date
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                if report_type == "Revenue":
                    cursor.execute(
                        """
                        SELECT SUM(Total_Cost)
                        FROM Booking
                        JOIN Users u ON Booking.User_ID = u.user_id
                        WHERE Check_IN_Date >= %s AND Check_IN_Date < %s AND u.is_active = 1
                        """,
                        (current_date, next_date)
                    )
                    value = cursor.fetchone()[0] or 0
                    data.append(value)
                    labels.append(current_date.strftime('%Y-%m-%d'))
                elif report_type == "Bookings":
                    cursor.execute(
                        """
                        SELECT COUNT(*)
                        FROM Booking
                        JOIN Users u ON Booking.User_ID = u.user_id
                        WHERE Check_IN_Date >= %s AND Check_IN_Date < %s AND u.is_active = 1
                        """,
                        (current_date, next_date)
                    )
                    value = cursor.fetchone()[0]
                    data.append(value)
                    labels.append(current_date.strftime('%Y-%m-%d'))
                elif report_type == "User Activity":
                    cursor.execute(
                        """
                        SELECT COUNT(DISTINCT Booking.User_ID)
                        FROM Booking
                        JOIN Users u ON Booking.User_ID = u.user_id
                        WHERE Check_IN_Date >= %s AND Check_IN_Date < %s AND u.is_active = 1
                        """,
                        (current_date, next_date)
                    )
                    value = cursor.fetchone()[0]
                    data.append(value)
                    labels.append(current_date.strftime('%Y-%m-%d'))
                current_date = next_date
        except mysql.connector.Error as err:
            print(f"Error generating report: {err}")
            messagebox.showerror("Database Error", f"Error generating report: {err}")
            return
        finally:
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
        self.reports_ax.clear()
        self.reports_ax.bar(labels, data, color='#007BFF')
        self.reports_ax.set_xlabel('Date')
        self.reports_ax.set_ylabel(report_type)
        self.reports_ax.set_title(f'{report_type} Report')
        self.reports_ax.grid(True, linestyle='--', alpha=0.7)
        self.reports_ax.get_yaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        self.reports_fig.autofmt_xdate()
        self.reports_fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)
        self.reports_canvas.draw()
        self.reports_chart_label.configure(text=f"{report_type} Report")
        self.current_report_data = {'labels': labels, 'data': data, 'type': report_type}

    def export_report(self):
        """Export the current report to CSV"""
        if not hasattr(self, 'current_report_data') or not self.current_report_data:
            messagebox.showwarning("Export Error", "Generate a report first")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        try:
            df = pd.DataFrame({
                'Date': self.current_report_data['labels'],
                self.current_report_data['type']: self.current_report_data['data']
            })
            df.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"Report exported to {file_path}")
        except Exception as e:
            print(f"Error exporting report: {e}")
            messagebox.showerror("Export Error", f"Error exporting report: {e}")

    def populate_reports(self):
        """Reset reports chart to initial state"""
        self.reports_ax.clear()
        self.reports_canvas.draw()
        self.reports_chart_label.configure(text="Report Chart")
        self.current_report_data = None

    # ------------------- Main Application Start -------------------
    def run(self):
        """Start the application"""
        if self.load_admin_session():
            self.setup_ui()
            self.show_frame("dashboard")
            self.root.mainloop()

if __name__ == "__main__":
    root = ctk.CTk()
    app = HotelBookingApp(root)
    app.run()