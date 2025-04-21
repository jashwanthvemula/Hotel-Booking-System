# config.py
import mysql.connector

def connect_db():
    """Connect to the hotel_booking database"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="new_password",
        database="hotel_book"
    )

def connect_mysql():
    """Connect to MySQL without specifying a database"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="new_password"
    )