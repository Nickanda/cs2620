"""
Message Sending GUI for User Messaging System (gRPC Version)

This script implements a Tkinter-based GUI for sending messages between users using gRPC.
Users can enter the recipient's username and a message. The recipient's username is validated,
the message is sent via the SendMessage RPC, and the interface returns to the home screen.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import chat_pb2  # Generated from chat.proto
import screens_rpc.home
import signal


def send_message(stub, root, recipient_var, message_widget, current_user):
    """
    Sends a message from the current user to the specified recipient via gRPC.
    Validates the recipient's username and the message content.
    If the RPC call indicates an error, an error message is shown.
    On success, the window is closed and a command dictionary is returned.
    """
    recipient_str = recipient_var.get().strip()
    message_str = message_widget.get("1.0", tk.END).strip()

    # Validate that both fields are not empty
    if not recipient_str or not message_str:
        messagebox.showerror("Error", "All fields are required")
        return

    # Validate that the recipient's username is alphanumeric
    if not recipient_str.isalnum():
        messagebox.showerror("Error", "Username must be alphanumeric")
        return

    # Build and send the SendMessageRequest via gRPC
    request = chat_pb2.SendMessageRequest(
        sender=current_user, receiver=recipient_str, message=message_str
    )
    response = stub.SendMessage(request)

    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return

    # On success, close the window and return a command dict for state transition.
    return {
        "command": "refresh_home",
        "data": {"undeliv_messages": response.undeliv_messages},
    }


def launch_home(stub, root, current_user):
    """
    Returns to the home screen by closing the current window and returning a command dict.
    Optionally, you could invoke a RefreshHome RPC here.
    """
    # Build and send the RefreshHomeRequest via gRPC
    request = chat_pb2.RefreshHomeRequest(username=current_user)
    response = stub.RefreshHome(request)

    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return

    # On success, close the window and return a command dict for state transition.
    return {
        "command": "refresh_home",
        "data": {"undeliv_messages": response.undeliv_messages},
    }


def on_close(stub, username: str):
    """
    Handles the window close event by logging the user out.
    """

    # Build and send the LogoutRequest via gRPC
    request = chat_pb2.LogoutRequest(username=username)
    stub.Logout(request)
    exit()


def launch_window(stub, current_user):
    """
    Launches the message sending window for the current user.
    Returns a dictionary indicating the next command for the client (e.g. refresh home).
    """
    # Create the main Tkinter window
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(stub, current_user))
    root.bind("<Control-c>", lambda event: on_close(stub, current_user))
    signal.signal(signal.SIGTERM, lambda s, f: on_close(stub, current_user))
    signal.signal(signal.SIGINT, lambda s, f: on_close(stub, current_user))
    root.title(f"Send Message - {current_user}")
    root.geometry("300x600")

    # Label and input field for recipient's username
    tk.Label(root, text="Recipient (alphanumeric only):").pack(pady=(10, 0))
    recipient_var = tk.StringVar(root)
    tk.Entry(root, textvariable=recipient_var).pack(pady=(0, 10))

    # Label and input field for message content
    tk.Label(root, text="Message:").pack(pady=(10, 0))
    message_widget = tk.Text(root)
    message_widget.pack(pady=(0, 10))

    result = {}

    def on_send():
        nonlocal result
        ret = send_message(stub, root, recipient_var, message_widget, current_user)
        if ret:
            result = ret
            root.destroy()

    def on_home():
        nonlocal result
        ret = launch_home(stub, root, current_user)
        if ret:
            result = ret
            root.destroy()

    # Button to send the message
    tk.Button(root, text="Send Message", command=on_send).pack(pady=(5, 5))
    # Button to return to the home screen
    tk.Button(root, text="Home", command=on_home).pack(pady=(5, 5))

    root.mainloop()
    return result
