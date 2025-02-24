"""
User Home Screen GUI with Messaging and Account Management (gRPC Version)

This script implements a Tkinter-based GUI for the main home screen of a user messaging application,
using gRPC to communicate with the server. From this interface, users can:
- Read messages (with an indicator for unread messages)
- Send messages
- Delete messages
- View the user list
- Log out or delete their account

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
import chat_pb2  # Generated from chat.proto
import chat_pb2_grpc
import screens_rpc.signup
import screens_rpc.user_list
import screens_rpc.send_message
import screens_rpc.messages
import screens_rpc.delete_messages


def open_read_messages(stub, root, username):
    """
    Closes the current window and opens the read messages window.
    """
    root.destroy()
    # Launch the messages screen with an empty list (or preloaded messages) and the username.
    return screens_rpc.messages.launch_window(stub, [], username)


def open_send_message(stub, root, current_user):
    """
    Closes the current window and opens the send message window.
    """
    root.destroy()
    return screens_rpc.send_message.launch_window(stub, current_user)


def open_delete_messages(stub, root, current_user):
    """
    Closes the current window and opens the delete messages window.
    """
    root.destroy()
    return screens_rpc.delete_messages.launch_window(stub, current_user)


def open_user_list(stub, root, username):
    """
    Closes the current window and opens the user list window.
    """
    root.destroy()
    return screens_rpc.user_list.launch_window(stub, [], username)


def logout(stub, root, username):
    """
    Sends a logout request via the gRPC stub and then closes the window.
    Returns a command dict to signal a logout state.
    """
    request = chat_pb2.LogoutRequest(username=username)
    response = stub.Logout(request)
    if response.status != "success":
        messagebox.showerror("Error", response.message)
    root.destroy()
    return {"command": "logout", "data": {}}


def delete_account(stub, root, username):
    """
    Sends an account deletion request via the gRPC stub and then closes the window.
    Returns a command dict (typically to log out the user).
    """
    request = chat_pb2.DeleteAccountRequest(username=username)
    response = stub.DeleteAccount(request)
    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return
    root.destroy()
    return {"command": "logout", "data": {}}


def launch_window(stub, username, num_messages):
    """
    Creates and displays the main home window for the user.
    The window includes buttons to read messages, send messages, delete messages,
    view the user list, log out, and delete the account.
    Returns a dictionary indicating the next command.
    """
    home_root = tk.Tk()
    home_root.title(f"Home - {username}")
    home_root.geometry("300x250")

    result = {}

    def on_read_messages():
        nonlocal result
        result = open_read_messages(stub, home_root, username)

    def on_send_message():
        nonlocal result
        result = open_send_message(stub, home_root, username)

    def on_delete_messages():
        nonlocal result
        result = open_delete_messages(stub, home_root, username)

    def on_user_list():
        nonlocal result
        result = open_user_list(stub, home_root, username)

    def on_logout():
        nonlocal result
        result = logout(stub, home_root, username)

    def on_delete_account():
        nonlocal result
        ret = delete_account(stub, home_root, username)
        if ret:
            result = ret

    tk.Button(
        home_root, text=f"Read Messages ({num_messages})", command=on_read_messages
    ).pack(pady=5)
    tk.Button(home_root, text="Send Message", command=on_send_message).pack(pady=5)
    tk.Button(home_root, text="Delete Messages", command=on_delete_messages).pack(
        pady=5
    )
    tk.Button(home_root, text="User List", command=on_user_list).pack(pady=5)
    tk.Button(home_root, text="Logout", command=on_logout).pack(pady=5)
    tk.Button(home_root, text="Delete Account", command=on_delete_account).pack(pady=5)

    home_root.mainloop()
    return result
