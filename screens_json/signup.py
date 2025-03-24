"""
User Signup GUI with Secure Password Hashing

This script implements a Tkinter-based graphical user interface (GUI) for user account creation.
Users can enter a username and password to create an account, with the following functionality:
- Input validation to ensure the username is alphanumeric and fields are not empty.
- Secure password handling via SHA-256 hashing before transmission.
- Communication with a server over a socket connection to send the user creation request.
- Option to switch to the login screen.

This script uses JSON format to structure and send search queries and refresh requests to the server.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import socket
import screens_json.login
import hashlib
import json


def create_user(
    s: socket.SocketType, root: tk.Tk, username: tk.StringVar, password: tk.StringVar
):
    """
    Handles user creation by sending a request to the server.
    Validates input fields and ensures the username is alphanumeric.
    Hashes the password using SHA-256 before sending it over the socket.
    """
    username_str = username.get()
    password_str = password.get()

    # Ensure fields are not empty
    if username_str == "" or password_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    # Validate username (must be alphanumeric)
    if not username_str.isalnum():
        messagebox.showerror("Error", "Username must be alphanumeric")
        return

    # Construct message and send to server, including hashed password
    message_dict = {
        "version": 0,
        "command": "create",
        "data": {
            "username": username_str,
            "password": hashlib.sha256(password_str.encode("utf-8")).hexdigest(),
        },
    }
    message = json.dumps(message_dict).encode("utf-8")
    s().sendall(message)

    # Close the signup window upon successful user creation request
    root.destroy()


def launch_login(s: socket.SocketType, root: tk.Tk):
    """
    Closes the current signup window and switches to the login window.
    """
    root.destroy()
    screens_json.login.launch_window(s)


def launch_window(s):
    """
    Initializes and displays the user signup window.
    Provides input fields for username and password, and buttons for signup and login.
    """
    # Create main window
    root = tk.Tk()
    root.title("User Signup")
    root.geometry("300x200")

    # Username label and input field
    tk.Label(root, text="Username (alphanumeric only):").pack()
    username_var = tk.StringVar(root)
    tk.Entry(root, textvariable=username_var).pack()

    # Password label and input field (masked for security)
    tk.Label(root, text="Password:").pack()
    password_var = tk.StringVar()
    tk.Entry(root, show="*", textvariable=password_var).pack()

    # Button to create a new user
    tk.Button(
        root,
        text="Create User",
        command=lambda: create_user(s, root, username_var, password_var),
    ).pack()

    # Button to switch to login window
    tk.Button(
        root, text="Switch to Login", command=lambda: launch_login(s, root)
    ).pack()

    # Run the Tkinter main event loop
    root.mainloop()
