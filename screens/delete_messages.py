import tkinter as tk
from tkinter import messagebox
from argon2 import PasswordHasher
import socket
import re

hasher = PasswordHasher()


def delete_message(
    s: socket.SocketType, root: tk.Tk, delete_ids: tk.StringVar, current_user: str
):
    delete_ids_str = delete_ids.get().strip()

    if delete_ids_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    if re.match("^[a-zA-Z0-9,]+$", delete_ids_str) is None:
        messagebox.showerror(
            "Error", "Delete IDs must be alphanumeric comma-separated list"
        )
        return

    message = f"delete_msg {current_user} {delete_ids_str}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def launch_home(s: socket.SocketType, root: tk.Tk, username: str):
    message = f"refresh_home {username}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def launch_window(s: socket.SocketType, current_user: str):
    # Create main window
    root = tk.Tk()
    root.title(f"Delete Messages - {current_user}")
    root.geometry("600x400")

    # Recipient Label and Entry
    tk.Label(
        root,
        text="Message IDs of the messages you wish to delete (comma-separated, no spaces):",
    ).pack()
    delete_var = tk.StringVar(root)
    tk.Entry(root, textvariable=delete_var).pack()

    # Submit Button
    button_submit = tk.Button(
        root,
        text="Delete Message",
        command=lambda: delete_message(s, root, delete_var, current_user),
    )
    button_submit.pack()

    # Back to home
    tk.Button(
        root, text="Home", command=lambda: launch_home(s, root, current_user)
    ).pack(pady=10)

    root.mainloop()
