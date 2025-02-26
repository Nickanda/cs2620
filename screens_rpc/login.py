"""
User Login GUI with Secure Password Handling (gRPC Version)

This script implements a Tkinter-based GUI for user authentication using gRPC.
Users can enter their username and password to log in. The password is securely hashed
with SHA-256 before being sent via a LoginRequest to the server. On successful login,
the window closes and a command dictionary is returned to update the client state.
Users can also switch to the signup screen.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import hashlib
import chat_pb2  # Generated from chat.proto
import screens_rpc.signup
import signal


def login(stub, root, username_var, password_var):
    """
    Handles the login process by validating inputs, hashing the password, and sending
    a LoginRequest via the gRPC stub.
    """
    username_str = username_var.get().strip()
    password_str = password_var.get().strip()

    # Validate that fields are not empty
    if not username_str or not password_str:
        messagebox.showerror("Error", "All fields are required")
        return

    # Ensure username is alphanumeric
    if not username_str.isalnum():
        messagebox.showerror("Error", "Username must be alphanumeric")
        return

    # Hash the password using SHA-256 for security
    hashed_password = hashlib.sha256(password_str.encode("utf-8")).hexdigest()

    # Create the LoginRequest message and call the Login RPC
    request = chat_pb2.LoginRequest(username=username_str, password=hashed_password)
    response = stub.Login(request)

    # Check for errors in the response
    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return

    # On successful login, destroy the window and return a command dictionary.
    root.destroy()
    return {
        "command": "login",
        "data": {
            "username": username_str,
            "undeliv_messages": response.undelivered_count,
        },
    }


def launch_signup(stub, root):
    """
    Destroys the current login window and launches the signup window.
    """
    root.destroy()
    return screens_rpc.signup.launch_window(stub)


def on_close(stub, root: tk.Tk, username: str):
    """
    Handles the window close event.
    """
    root.destroy()
    exit()


def launch_window(stub):
    """
    Creates and launches the login window.
    Returns a dictionary containing a command and associated data for state transition.
    """
    # Create the main window
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(stub, root))
    root.bind("<Control-c>", lambda event: on_close(stub, root))
    signal.signal(signal.SIGTERM, lambda s, f: on_close(stub, root))
    signal.signal(signal.SIGINT, lambda s, f: on_close(stub, root))
    root.title("User Login")
    root.geometry("300x200")

    # Create Username label and input field
    tk.Label(root, text="Username (alphanumeric only):").pack(pady=(10, 0))
    username_var = tk.StringVar(root)
    tk.Entry(root, textvariable=username_var).pack(pady=(0, 10))

    # Create Password label and input field (masked)
    tk.Label(root, text="Password:").pack()
    password_var = tk.StringVar()
    tk.Entry(root, show="*", textvariable=password_var).pack(pady=(0, 10))

    result = {}

    def on_login():
        nonlocal result
        ret = login(stub, root, username_var, password_var)
        if ret:
            result = ret

    def on_switch_to_signup():
        nonlocal result
        ret = launch_signup(stub, root)
        if ret:
            result = ret

    # Create Login button that calls the login function
    tk.Button(root, text="Login", command=on_login).pack(pady=(0, 5))
    # Create button to switch to the signup window
    tk.Button(root, text="Switch to Signup", command=on_switch_to_signup).pack(
        pady=(0, 5)
    )

    root.mainloop()
    return result
