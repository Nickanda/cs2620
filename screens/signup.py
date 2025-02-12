import tkinter as tk
from tkinter import messagebox
import socket
import screens.login
import hashlib


def create_user(
    s: socket.SocketType, root: tk.Tk, username: tk.StringVar, password: tk.StringVar
):
    username_str = username.get()
    password_str = password.get()

    if username_str == "" or password_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    if not username_str.isalnum():
        messagebox.showerror("Error", "Username must be alphanumeric")
        return

    hashed_password = hashlib.sha256(password_str.encode("utf-8")).hexdigest()
    message = f"create {username_str} {hashed_password}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def launch_login(s: socket.SocketType, root: tk.Tk):
    root.destroy()
    screens.login.launch_window(s)


def launch_window(s: socket.SocketType):
    # Create main window
    root = tk.Tk()
    root.title("User Signup")
    root.geometry("300x200")

    # Username Label and Entry
    tk.Label(root, text="Username (alphanumeric only):").pack()
    username_var = tk.StringVar(root)
    tk.Entry(root, textvariable=username_var).pack()

    # Password Label and Entry
    tk.Label(root, text="Password:").pack()
    password_var = tk.StringVar()
    tk.Entry(root, show="*", textvariable=password_var).pack()

    # Submit Button
    tk.Button(
        root,
        text="Create User",
        command=lambda: create_user(s, root, username_var, password_var),
    ).pack()

    # Login Button
    tk.Button(
        root, text="Switch to Login", command=lambda: launch_login(s, root)
    ).pack()

    root.mainloop()
