import mysql.connector
import hashlib
import sys

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Database connection function
def connect_db():
    return mysql.connector.connect(
        host="141.209.241.57",
        user="cheru4a",  # Replace with your MySQL username
        password="mypass",  # Replace with your MySQL password
        database="BIS698M1530_GRP1"  # Replace with your database name
    )

# Function to add a new admin
def add_admin(name, email, password):
    hashed_password = hash_password(password)
    
    try:
        connection = connect_db()
        cursor = connection.cursor()
        
        # Check if admin with this email already exists
        cursor.execute("SELECT Admin_ID FROM Admin WHERE AdminEmail = %s", (email,))
        existing_admin = cursor.fetchone()
        
        if existing_admin:
            print(f"Admin with email {email} already exists.")
            return False
        
        # Insert the new admin
        cursor.execute(
            """
            INSERT INTO Admin (AdminName, AdminEmail, AdminPassword) 
            VALUES (%s, %s, %s)
            """,
            (name, email, hashed_password)
        )
        
        connection.commit()
        print(f"Admin '{name}' with email '{email}' created successfully!")
        return True
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

# Main function
def main():
    print("===== Hotel Booking System - Admin Creation =====")
    
    # Get admin details
    name = input("Enter admin name: ")
    email = input("Enter admin email: ")
    password = input("Enter admin password: ")
    
    # Validate inputs
    if not name or not email or not password:
        print("Error: All fields are required.")
        return
    
    # Add the admin
    add_admin(name, email, password)

# Direct execution for creating a specific admin account
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-default":
        # Create a default admin account
        add_admin("Admin", "admin@hotel.com", "admin123")
    else:
        main()