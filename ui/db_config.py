import mysql


def connect_mysql():
    """Connect to MySQL without specifying a database"""
    try:
        return mysql.connector.connect(
        host="127.0.0.1",
        user="root",  # Replace with your MySQL username
        password="new_password", 
        )
    
    except mysql.connector.Error as err:
        return None
def connect_db():
    return mysql.connector.connect(
        host="127.0.0.1",
        user="root",  # Replace with your MySQL username
        password="new_password", 
        database="hotel_book"
    )
database_name = "hotel_book"