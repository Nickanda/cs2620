import tkinter as tk
from tkinter import messagebox
from argon2 import PasswordHasher
import socket

hasher = PasswordHasher()

def create_user(s: socket.SocketType, username: tk.StringVar, password: tk.StringVar):
    username_str = username.get()
    password_str = password.get()

    if username_str != "" and password_str != "":
        if username_str.isalnum() == False:
            messagebox.showerror("Error", "Username must be alphanumeric")
            return
        
        hashed_password = hasher.hash(password_str)
        message = f"create {username_str} {hashed_password}".encode("utf-8")
        s.sendall(message)
    else:
        messagebox.showerror("Error", "All fields are required")

def launch_window(s: socket.SocketType):
    # Create main window
    root = tk.Tk()
    root.title("User Creation")
    root.geometry("300x200")

    # Username Label and Entry
    label_username = tk.Label(root, text="Username: (alphanumeric only)")
    label_username.pack()
    username_var = tk.StringVar(root)
    entry_username = tk.Entry(root, textvariable=username_var)
    entry_username.pack()

    # Password Label and Entry
    label_password = tk.Label(root, text="Password:")
    label_password.pack()
    password_var = tk.StringVar()
    entry_password = tk.Entry(root, show="*", textvariable=password_var)
    entry_password.pack()

    # Submit Button
    button_submit = tk.Button(root, text="Create User", command=lambda: create_user(s, username_var, password_var))
    button_submit.pack()

    # Run the Tkinter loop
    root.mainloop()