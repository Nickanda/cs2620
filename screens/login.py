"""
User Login GUI with Secure Password Handling

This script implements a Tkinter-based graphical user interface (GUI) for user authentication.
Users can:
- Enter their username and password to log in.
- Validate that the username is alphanumeric and fields are not empty.
- Securely hash the password using SHA-256 before sending it to the server.
- Switch to the signup screen if they do not have an account.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import hashlib
import socket
import screens.signup


def login(
    s: socket.SocketType, root: tk.Tk, username: tk.StringVar, password: tk.StringVar
):
    """
    Handles the login process by sending username and hashed password to the server.
    """
    username_str = username.get().strip()
    password_str = password.get().strip()

    # Validate that fields are not empty
    if username_str == "" or password_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    # Ensure username is alphanumeric
    if not username_str.isalnum():
        messagebox.showerror("Error", "Username must be alphanumeric")
        return

    # Hash the password using SHA-256 for security
    message = f"0 login {username_str} {hashlib.sha256(password_str.encode('utf-8')).hexdigest()}".encode(
        "utf-8"
    )

    # Send login request to the server
    s.sendall(message)

    # Close the login window after sending the credentials
    root.destroy()


def launch_signup(s: socket.SocketType, root: tk.Tk):
    """
    Destroys the current login window and launches the signup window.
    """
    root.destroy()
    screens.signup.launch_window(s)


def launch_window(s: socket.SocketType):
    """
    Creates and launches the login window.
    """
    # Create the main window
    root = tk.Tk()
    root.title("User Login")
    root.geometry("300x200")

    # Create Username label and input field
    label_username = tk.Label(root, text="Username (alphanumeric only):")
    label_username.pack()
    username_var = tk.StringVar(root)
    entry_username = tk.Entry(root, textvariable=username_var)
    entry_username.pack()

    # Create Password label and input field (hidden input)
    label_password = tk.Label(root, text="Password:")
    label_password.pack()
    password_var = tk.StringVar()
    entry_password = tk.Entry(root, show="*", textvariable=password_var)
    entry_password.pack()

    # Create Login button that calls login function
    button_submit = tk.Button(
        root, text="Login", command=lambda: login(s, root, username_var, password_var)
    )
    button_submit.pack()

    # Create Switch to Signup button that calls launch_signup function
    button_submit = tk.Button(
        root, text="Switch to Signup", command=lambda: launch_signup(s, root)
    )
    button_submit.pack()

    # Start the Tkinter event loop
    root.mainloop()
