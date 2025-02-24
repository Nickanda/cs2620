"""
User Signup GUI with Secure Password Hashing (gRPC Version)

This script implements a Tkinter-based GUI for account creation using gRPC.
Users can enter a username and password; the password is hashed with SHA‑256,
and the CreateAccount RPC is invoked on the stub. Depending on the response,
the screen either shows an error or signals the client to switch state.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import hashlib
import chat_pb2  # Generated from chat.proto
import screens_rpc.login  # Import the RPC-based login screen


def create_user(stub, root, username_var, password_var):
    """
    Handles user creation by calling the CreateAccount RPC.
    Validates input, hashes the password, and calls the stub.
    If account creation is successful, the window is closed and a
    response dict is returned. Otherwise, an error message is shown.
    """
    username_str = username_var.get().strip()
    password_str = password_var.get().strip()

    # Ensure fields are not empty
    if not username_str or not password_str:
        messagebox.showerror("Error", "All fields are required")
        return

    # Validate username (must be alphanumeric)
    if not username_str.isalnum():
        messagebox.showerror("Error", "Username must be alphanumeric")
        return

    # Hash the password using SHA-256
    hashed_password = hashlib.sha256(password_str.encode("utf-8")).hexdigest()

    # Create the gRPC request message
    request = chat_pb2.CreateAccountRequest(
        username=username_str, password=hashed_password
    )
    response = stub.CreateAccount(request)

    # If the server indicates an error, show it
    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return

    # On success, destroy the window and return a command dict.
    root.destroy()
    # For example, we assume that a successful create implies the user is now logged in.
    return {
        "command": "login",
        "data": {"username": username_str, "undeliv_messages": 0},
    }


def launch_login(stub, root):
    """
    Closes the current signup window and switches to the login window.
    Returns the result of the login screen.
    """
    root.destroy()
    return screens_rpc.login.launch_window(stub)


def launch_window(stub):
    """
    Initializes and displays the signup window.
    Returns a dictionary indicating the next command (e.g. "login")
    and associated data (such as the username).
    """
    # Create the main window
    root = tk.Tk()
    root.title("User Signup")
    root.geometry("300x200")

    # Username label and input field
    tk.Label(root, text="Username (alphanumeric only):").pack(pady=(10, 0))
    username_var = tk.StringVar(root)
    tk.Entry(root, textvariable=username_var).pack(pady=(0, 10))

    # Password label and input field (masked)
    tk.Label(root, text="Password:").pack()
    password_var = tk.StringVar(root)
    tk.Entry(root, show="*", textvariable=password_var).pack(pady=(0, 10))

    # This variable will store the result to return when the window closes.
    result = {}

    def on_create_user():
        nonlocal result
        ret = create_user(stub, root, username_var, password_var)
        if ret:
            result = ret

    def on_switch_to_login():
        nonlocal result
        ret = launch_login(stub, root)
        if ret:
            result = ret

    # Button to create a new user
    tk.Button(root, text="Create User", command=on_create_user).pack(pady=(0, 5))
    # Button to switch to login screen
    tk.Button(root, text="Switch to Login", command=on_switch_to_login).pack()

    # Run the Tkinter event loop; when root.destroy() is called the loop exits.
    root.mainloop()
    return result
