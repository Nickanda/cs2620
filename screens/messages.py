import tkinter as tk
from tkinter import messagebox
from argon2 import PasswordHasher
import socket

hasher = PasswordHasher()



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
    button_submit = tk.Button(root, text="Login", command=lambda: login(s, root, username_var, password_var))
    button_submit.pack()

    # Signup Button
    button_submit = tk.Button(root, text="Signup", command=lambda: launch_signup(s, root))
    button_submit.pack()

    root.mainloop()