"""
User Home Screen GUI with Messaging and Account Management

This script implements a Tkinter-based graphical user interface (GUI) for the main home screen of a user messaging application.
From this interface, users can:
- Read messages, with an indicator for unread messages.
- Send messages to other users.
- Delete messages from their inbox.
- View a list of users in the system.
- Log out or delete their account.

This screen acts as a central navigation hub for user interactions.
Also note that this script uses JSON format to structure and send search queries and refresh requests to the server.

Last updated: February 12, 2025
"""

import tkinter as tk
import socket
import screens_json.signup
import screens_json.user_list
import screens_json.send_message
import screens_json.messages
import screens_json.delete_messages
import json


def open_read_messages(s: socket.socket, root: tk.Tk, username: str):
    """
    Closes the current window and opens the read messages window.
    """
    root.destroy()
    screens_json.messages.launch_window(s, [], username)


def open_send_message(s: socket.socket, root: tk.Tk, current_user: str):
    """
    Closes the current window and opens the send message window.
    """
    root.destroy()
    screens_json.send_message.launch_window(s, current_user)


def open_delete_messages(s: socket.socket, root: tk.Tk, current_user: str):
    """
    Closes the current window and opens the delete messages window.
    """
    root.destroy()
    screens_json.delete_messages.launch_window(s, current_user)


def open_user_list(s: socket.socket, root: tk.Tk, username: str):
    """
    Closes the current window and opens the user list window.
    """
    root.destroy()
    screens_json.user_list.launch_window(s, [], username)


def logout(s: socket.socket, root: tk.Tk, username: str):
    """
    Sends a logout request to the server and closes the application.
    """
    message_dict = {"version": 0, "command": "logout", "data": {"username": username}}
    s.sendall(json.dumps(message_dict).encode("utf-8"))
    root.destroy()


def delete_account(s: socket.socket, root: tk.Tk, username: str):
    """
    Sends an account deletion request to the server and closes the application.
    """
    message_dict = {
        "version": 0,
        "command": "delete_acct",
        "data": {"username": username},
    }
    s.sendall(json.dumps(message_dict).encode("utf-8"))
    root.destroy()


def launch_window(s: socket.SocketType, username: str, num_messages: int):
    """
    Creates and displays the main home window with user options.
    """
    # Create the main window
    home_root = tk.Tk()
    home_root.title(f"Home - {username}")
    home_root.geometry("300x200")

    # Button to read messages, displays the number of unread messages
    tk.Button(
        home_root,
        text=f"Read Messages ({num_messages})",
        command=lambda: open_read_messages(s, home_root, username),
    ).pack()

    # Button to open the send message window
    tk.Button(
        home_root,
        text="Send Message",
        command=lambda: open_send_message(s, home_root, username),
    ).pack()

    # Button to open the delete messages window
    tk.Button(
        home_root,
        text="Delete Messages",
        command=lambda: open_delete_messages(s, home_root, username),
    ).pack()

    # Button to open the user list window
    tk.Button(
        home_root,
        text="User List",
        command=lambda: open_user_list(s, home_root, username),
    ).pack()

    # Button to log out the user
    tk.Button(
        home_root, text="Logout", command=lambda: logout(s, home_root, username)
    ).pack()

    # Button to delete the user's account
    tk.Button(
        home_root,
        text="Delete Account",
        command=lambda: delete_account(s, home_root, username),
    ).pack()

    # Run the main event loop
    home_root.mainloop()
