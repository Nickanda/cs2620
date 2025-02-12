"""
Message Viewing and Retrieval GUI for User Messaging System

This script implements a Tkinter-based graphical user interface (GUI) for managing and viewing user messages.
Users can:
- Request a specified number of undelivered or delivered messages from the server.
- View messages in a paginated scrolled text area.
- Navigate through messages using "Next" and "Previous" buttons.
- Return to the home screen.

This script uses JSON format to structure and send search queries and refresh requests to the server.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import json


def get_undelivered_messages(
    s: socket.socket, root: tk.Tk, num_messages_var: tk.IntVar, current_user: str
):
    """
    Sends a request to the server to fetch undelivered messages for the current user.
    If the number of messages is less than or equal to 0, an error message is displayed.
    """
    num_messages = num_messages_var.get()

    if num_messages <= 0:
        messagebox.showerror("Error", "Number of messages must be greater than 0")
        return

    message_dict = {"username": current_user, "num_messages": num_messages}
    
    # Send the request to fetch undelivered messages
    s.sendall(f"get_undelivered {json.dumps(message_dict)}".encode("utf-8"))
    
    # Close the current Tkinter window    
    root.destroy()


def get_delivered_messages(
    s: socket.socket, root: tk.Tk, num_messages_var: tk.IntVar, current_user: str
):
    """
    Sends a request to the server to fetch delivered messages for the current user.
    If the number of messages is less than or equal to 0, an error message is displayed.
    """
    num_messages = num_messages_var.get()

    if num_messages <= 0:
        messagebox.showerror("Error", "Number of messages must be greater than 0")
        return

    message_dict = {"username": current_user, "num_messages": num_messages}
    
    # Send the request to fetch delivered messages
    s.sendall(f"get_delivered {json.dumps(message_dict)}".encode("utf-8"))
    
    # Close the current Tkinter window
    root.destroy()


def pagination(index: int, operation: str):
    """
    Adjusts the index for pagination based on the operation ('next' or 'prev').
    """
    if operation == "next":
        index += 25
    elif operation == "prev":
        index -= 25


def launch_home(s: socket.SocketType, root: tk.Tk, username: str):
    """
    Sends a request to refresh the home screen for the given username and closes the current window.
    """
    message_dict = {"username": username}
    message = f"refresh_home {json.dumps(message_dict)}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def launch_window(s: socket.SocketType, messages: list[str], current_user: str):
    """
    Creates the main window for displaying messages with options to fetch delivered/undelivered messages
    and navigate through paginated messages.
    """
    current_index = 0

    # Determine the subset of messages to display
    if current_index + 25 >= len(messages):
        to_display = messages[current_index:]
    else:
        to_display = messages[current_index : current_index + 25]
    
    # Format messages for display
    messages_to_display = [
        f"[{msg['sender']}, ID#{msg['id']}]: {msg['message']}" for msg in to_display
    ]

    # Create the main window
    root = tk.Tk()
    root.title(f"Messages - {current_user}")
    root.geometry("400x600")

    # Input field for specifying the number of messages to fetch
    tk.Label(root, text="Number of Messages to Get:").pack()
    num_messages_var = tk.IntVar(root)
    tk.Entry(root, textvariable=num_messages_var).pack()

    # Buttons to fetch undelivered or delivered messages
    tk.Button(
        root,
        text="Get # Undelivered Messages",
        command=lambda: get_undelivered_messages(
            s, root, num_messages_var, current_user
        ),
    ).pack()
    tk.Button(
        root,
        text="Get # Delivered Messages",
        command=lambda: get_delivered_messages(s, root, num_messages_var, current_user),
    ).pack()

    # Scrolled text area to display messages
    message_list = scrolledtext.ScrolledText(root)
    message_list.insert(tk.INSERT, "Messages:\n" + "\n".join(messages_to_display))
    message_list.configure(state="disabled")
    message_list.pack()

    # Pagination buttons
    tk.Button(
        root,
        text="Previous 25",
        command=lambda: pagination(current_index, "prev"),
        state=tk.DISABLED if current_index == 0 else tk.NORMAL,
    ).pack()

    tk.Button(
        root,
        text="Next 25",
        command=lambda: pagination(current_index, "next"),
        state=tk.DISABLED if current_index + 25 >= len(messages) else tk.NORMAL,
    ).pack()

    # Home button to return to the main menu
    tk.Button(
        root, text="Home", command=lambda: launch_home(s, root, current_user)
    ).pack(pady=10)

    # Run the Tkinter event loop
    root.mainloop()
