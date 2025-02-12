"""
Message Deletion GUI for User Messaging System

This script implements a Tkinter-based graphical user interface (GUI) for deleting user messages.
Users can:
- Enter message IDs as a comma-separated list to specify which messages to delete.
- Validate that input consists only of alphanumeric characters and commas.
- Send a delete request to the server over a socket connection.
- Navigate back to the home screen.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import socket
import re


def delete_message(
    s: socket.SocketType, root: tk.Tk, delete_ids: tk.StringVar, current_user: str
):
    """
    Sends a request to delete specified messages at delete_ids
    """
    delete_ids_str = delete_ids.get().strip()

    # Ensure the input is not empty
    if delete_ids_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    # Validate that input is alphanumeric and comma-separated
    if re.match("^[a-zA-Z0-9,]+$", delete_ids_str) is None:
        messagebox.showerror(
            "Error", "Delete IDs must be alphanumeric comma-separated list"
        )
        return

    # Format the delete message request and send it to the server
    message = f"0 delete_msg {current_user} {delete_ids_str}".encode("utf-8")
    s.sendall(message)

    # Close the Tkinter window after sending the request
    root.destroy()


def launch_home(s: socket.SocketType, root: tk.Tk, username: str):
    """
    Sends a request to refresh the home screen.
    """
    message = f"0 refresh_home {username}".encode("utf-8")
    s.sendall(message)

    # Close the Tkinter window to return to home screen
    root.destroy()


def launch_window(s: socket.SocketType, current_user: str):
    """
    Launches a Tkinter window for deleting messages for current_user.
    """
    # Create main window
    root = tk.Tk()
    root.title(f"Delete Messages - {current_user}")
    root.geometry("600x400")

    # Label instructing the user to input message IDs
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
