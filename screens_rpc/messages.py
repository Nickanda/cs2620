"""
Message Viewing and Retrieval GUI for User Messaging System (gRPC Version)

This script implements a Tkinter-based GUI for managing and viewing user messages,
using gRPC to communicate with the server. Users can request a specified number of
undelivered or delivered messages, view messages in a paginated scrolled text area,
navigate through messages using "Next" and "Previous" buttons, and return to the home screen.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import chat_pb2  # Generated from chat.proto
import chat_pb2_grpc


def update_display(text_area, messages_list, current_index, prev_button, next_button):
    """
    Updates the displayed messages in the text area based on the current index.
    messages_list is a list of Message objects from the RPC response.
    """
    start = current_index.get()
    end = start + 25 if start + 25 < len(messages_list) else len(messages_list)
    to_display = messages_list[start:end]
    formatted = [f"[{msg.sender}, ID#{msg.id}]: {msg.message}" for msg in to_display]

    text_area.configure(state="normal")
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.INSERT, "\n".join(formatted))
    text_area.configure(state="disabled")

    # Enable or disable pagination buttons
    prev_button.config(state=tk.NORMAL if start > 0 else tk.DISABLED)
    next_button.config(state=tk.NORMAL if end < len(messages_list) else tk.DISABLED)


def get_undelivered_messages(stub, num_messages, current_user):
    """
    Calls the GetUndelivered RPC to fetch undelivered messages.
    Returns a list of Message objects on success; shows an error and returns None on failure.
    """
    request = chat_pb2.GetUndeliveredRequest(
        username=current_user, num_messages=num_messages
    )
    response = stub.GetUndelivered(request)
    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return None
    return list(response.messages)


def get_delivered_messages(stub, num_messages, current_user):
    """
    Calls the GetDelivered RPC to fetch delivered messages.
    Returns a list of Message objects on success; shows an error and returns None on failure.
    """
    request = chat_pb2.GetDeliveredRequest(
        username=current_user, num_messages=num_messages
    )
    response = stub.GetDelivered(request)
    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return None
    return list(response.messages)


def launch_home(stub, root, current_user):
    """
    Closes the current window and returns a command dict for transitioning to the home screen.
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


def launch_window(stub, initial_messages, current_user):
    """
    Creates and displays the messages window.

    Parameters:
      stub: The gRPC stub used to call RPC methods.
      initial_messages: A list of Message objects to initially display.
      current_user: The username of the logged-in user.

    Returns a command dictionary (e.g. to go back to home).
    """
    # Create the main window
    root = tk.Tk()
    root.title(f"Messages - {current_user}")
    root.geometry("400x600")

    # Initialize pagination and messages list
    current_index = tk.IntVar(root, 0)
    messages_list = initial_messages[:]  # start with the provided messages
    result = {}

    # Input field for specifying the number of messages to fetch
    tk.Label(root, text="Number of Messages to Get:").pack(pady=(10, 0))
    num_messages_var = tk.IntVar(root, 0)
    tk.Entry(root, textvariable=num_messages_var).pack(pady=(0, 10))

    # Scrolled text area to display messages
    text_area = scrolledtext.ScrolledText(root, width=50, height=20)
    text_area.pack(pady=(10, 10))

    # Pagination buttons (initially disabled/enabled based on messages_list)
    prev_button = tk.Button(root, text="Previous 25", state=tk.DISABLED)
    prev_button.pack(side=tk.LEFT, padx=(20, 10))
    next_button = tk.Button(
        root,
        text="Next 25",
        state=tk.NORMAL if len(messages_list) > 25 else tk.DISABLED,
    )
    next_button.pack(side=tk.RIGHT, padx=(10, 20))

    # Function to fetch undelivered messages and update the display
    def on_get_undelivered():
        num = num_messages_var.get()
        if num <= 0:
            messagebox.showerror("Error", "Number of messages must be greater than 0")
            return
        result = get_undelivered_messages(stub, num, current_user)
        if result is not None:
            nonlocal messages_list
            messages_list = result
            current_index.set(0)
            update_display(
                text_area, messages_list, current_index, prev_button, next_button
            )

    # Function to fetch delivered messages and update the display
    def on_get_delivered():
        num = num_messages_var.get()
        if num <= 0:
            messagebox.showerror("Error", "Number of messages must be greater than 0")
            return
        result = get_delivered_messages(stub, num, current_user)
        if result is not None:
            nonlocal messages_list
            messages_list = result
            current_index.set(0)
            update_display(
                text_area, messages_list, current_index, prev_button, next_button
            )

    def on_home():
        nonlocal result
        command = launch_home(stub, root, current_user)
        if command:
            result = command
            root.destroy()

    # Buttons to fetch messages
    tk.Button(root, text="Get # Undelivered Messages", command=on_get_undelivered).pack(
        pady=(5, 5)
    )
    tk.Button(root, text="Get # Delivered Messages", command=on_get_delivered).pack(
        pady=(5, 10)
    )

    # Configure pagination buttons
    prev_button.config(
        command=lambda: (
            current_index.set(max(0, current_index.get() - 25)),
            update_display(
                text_area, messages_list, current_index, prev_button, next_button
            ),
        )
    )
    next_button.config(
        command=lambda: (
            current_index.set(current_index.get() + 25),
            update_display(
                text_area, messages_list, current_index, prev_button, next_button
            ),
        )
    )

    # Home button to return to the main menu
    tk.Button(root, text="Home", command=on_home).pack(pady=(10, 10))

    # Initialize display with any initial messages
    update_display(text_area, messages_list, current_index, prev_button, next_button)

    root.mainloop()
    return result
