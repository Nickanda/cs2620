"""
Message Sending GUI for User Messaging System

This script implements a Tkinter-based graphical user interface (GUI) for sending messages between users.
Users can:
- Enter the recipient's username and a message.
- Validate that the recipient's username is alphanumeric.
- Send the message to the server via a socket connection.
- Navigate back to the home screen.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import socket


def send_message(
    s: socket.SocketType,
    root: tk.Tk,
    recipient: tk.StringVar,
    message: tk.Text,
    current_user: str,
):
    """
    Sends a message from the current user to the specified recipient.
    """
    recipient_str = recipient.get().strip()
    message_str = message.get("1.0", tk.END).strip()

    # Ensure that both fields are not empty
    if recipient_str == "" or message_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    # Validate that the recipient's username is alphanumeric
    if not recipient_str.isalnum():
        messagebox.showerror("Error", "Username must be alphanumeric")
        return

    # Format the message string for sending over the socket
    message = f"send_msg {current_user} {recipient_str} {message_str}".encode("utf-8")
    s.sendall(message)

    # Close the message window
    root.destroy()


def launch_home(s: socket.SocketType, root: tk.Tk, username: str):
    """
    Sends a request to refresh the home screen and closes the current window.
    """
    message = f"refresh_home {username}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def launch_window(s: socket.SocketType, current_user: str):
    """
    Launches the message sending window for the current user.
    """
    # Create the main Tkinter window
    root = tk.Tk()
    root.title(f"Send Message - {current_user}")
    root.geometry("300x600")

    # Label and input field for recipient username
    tk.Label(root, text="Recipient (alphanumeric only):").pack()
    recipient_var = tk.StringVar(root)
    tk.Entry(root, textvariable=recipient_var).pack()

    # Label and input field for message content
    tk.Label(root, text="Message:").pack()
    entry_message = tk.Text(root)
    entry_message.pack()

    # Button to send the message
    button_submit = tk.Button(
        root,
        text="Send Message",
        command=lambda: send_message(
            s, root, recipient_var, entry_message, current_user
        ),
    )
    button_submit.pack()

    # Button to navigate back to the home screen
    tk.Button(
        root, text="Home", command=lambda: launch_home(s, root, current_user)
    ).pack(pady=10)

    root.mainloop()
