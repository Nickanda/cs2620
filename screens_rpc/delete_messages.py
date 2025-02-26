"""
Message Deletion GUI for User Messaging System (gRPC Version)

This script implements a Tkinter-based GUI for deleting messages using gRPC.
Users enter a comma-separated list of message IDs to delete; the input is validated,
converted into a list of integers, and a DeleteMessage RPC is called via the stub.
On success, the window closes and a command dict is returned for state transition.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import re
import chat_pb2  # Generated from chat.proto
import chat_pb2_grpc
import signal


def delete_message(stub, root, delete_ids_var, current_user):
    """
    Sends a DeleteMessageRequest via the gRPC stub.
    Validates input, converts it to a list of integers, and processes the server response.
    """
    delete_ids_str = delete_ids_var.get().strip()

    # Ensure the input is not empty
    if delete_ids_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    # Validate that input consists of numbers and commas only
    if re.match("^[0-9,]+$", delete_ids_str) is None:
        messagebox.showerror(
            "Error", "Delete IDs must be a comma-separated list of numbers"
        )
        return

    try:
        # Convert the comma-separated string to a list of integers
        message_ids = [int(x) for x in delete_ids_str.split(",") if x]
    except Exception:
        messagebox.showerror("Error", "Invalid input for message IDs")
        return

    # Create and send the DeleteMessage RPC request
    request = chat_pb2.DeleteMessageRequest(
        username=current_user, message_ids=message_ids
    )
    response = stub.DeleteMessage(request)

    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return

    # Close the window and return a command to refresh the home screen
    return {
        "command": "refresh_home",
        "data": {"undeliv_messages": response.undeliv_messages},
    }


def launch_home(stub, root, current_user):
    """
    Closes the window and returns a command to refresh the home screen.
    (Optionally, you could call an RPC to get updated home data here.)
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
    Launches a Tkinter window for deleting messages for the given user.
    Returns a dictionary indicating the next command (e.g. refresh_home).
    """
    # Create the main window
    root = tk.Tk()
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(stub, current_user))
    root.bind("<Control-c>", lambda event: on_close(stub, current_user))
    signal.signal(signal.SIGTERM, lambda s, f: on_close(stub, current_user))
    signal.signal(signal.SIGINT, lambda s, f: on_close(stub, current_user))
    root.title(f"Delete Messages - {current_user}")
    root.geometry("600x400")

    # Instruction label and input field for comma-separated message IDs
    tk.Label(
        root,
        text="Message IDs of the messages you wish to delete (comma-separated, no spaces):",
    ).pack(pady=10)
    delete_var = tk.StringVar(root)
    tk.Entry(root, textvariable=delete_var).pack(pady=10)

    result = {}

    def on_delete():
        nonlocal result
        ret = delete_message(stub, root, delete_var, current_user)
        if ret:
            result = ret
            root.destroy()

    def on_home():
        nonlocal result
        ret = launch_home(stub, root, current_user)
        if ret:
            result = ret
            root.destroy()

    # Button to submit delete request
    tk.Button(root, text="Delete Message", command=on_delete).pack(pady=10)
    # Button to return to home screen
    tk.Button(root, text="Home", command=on_home).pack(pady=10)

    root.mainloop()
    return result
