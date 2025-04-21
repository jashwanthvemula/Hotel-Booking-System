# utils.py
import hashlib
import subprocess
import sys
from tkinter import messagebox

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def open_page(page_name, user_id=None):
    """Open another page and close the current one"""
    try:
        # Pass the user ID to the next page if provided
        user_param = [str(user_id)] if user_id else []
        
        # Construct the command to run the appropriate Python file
        command = [sys.executable, f"{page_name.lower()}.py"] + user_param
        
        subprocess.Popen(command)
    except Exception as e:
        messagebox.showerror("Navigation Error", f"Unable to open {page_name} page: {e}")