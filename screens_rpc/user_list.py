"""
User List Search and Pagination GUI (gRPC Version)

This script implements a Tkinter-based GUI that allows users to:
- View a paginated list of users (displaying up to 25 users at a time).
- Perform a search query using alphanumeric characters or '*' as a wildcard.
- Navigate between pages of users using "Next" and "Previous" buttons.
- Return to the home screen by invoking the appropriate gRPC method (or returning a command).

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext
import chat_pb2  # Generated from chat.proto
import chat_pb2_grpc


def search(stub, root, search_var):
    """
    Handles the search functionality by sending the search query via the gRPC stub.
    Ensures that the input is not empty and contains only alphanumeric characters or '*'.
    If successful, closes the window and returns a command dictionary with the new user list.
    """
    search_str = search_var.get().strip()
    if search_str == "":
        messagebox.showerror("Error", "All fields are required")
        return
    if not all(ch.isalnum() or ch == "*" for ch in search_str):
        messagebox.showerror("Error", "Search characters must be alphanumeric or *")
        return

    # Build and send the SearchUsersRequest via gRPC.
    request = chat_pb2.SearchUsersRequest(pattern=search_str)
    response = stub.SearchUsers(request)
    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return

    # Close the current window and return a command dict with the new user list.
    return {
        "command": "user_list",
        "data": {"user_list": list(response.users), "username": None},
    }


def launch_home(stub, root, username):
    """
    Navigates back to the home screen.
    (Optionally, you could invoke a RefreshHome RPC here.)
    This function closes the current window and returns a command dictionary.
    """
    # Build and send the RefreshHomeRequest via gRPC
    request = chat_pb2.RefreshHomeRequest(username=username)
    response = stub.RefreshHome(request)

    if response.status != "success":
        messagebox.showerror("Error", response.message)
        return

    # On success, close the window and return a command dict for state transition.
    return {
        "command": "refresh_home",
        "data": {"undeliv_messages": response.undeliv_messages},
    }


def update_display(text_area, user_list, current_index, prev_button, next_button):
    """
    Updates the displayed user list based on the current pagination index.
    """
    start = current_index.get()
    end = start + 25 if start + 25 < len(user_list) else len(user_list)
    to_display = user_list[start:end]
    text_area.configure(state="normal")
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.INSERT, "Users:\n" + "\n".join(to_display))
    text_area.configure(state="disabled")
    prev_button.config(state=tk.NORMAL if start > 0 else tk.DISABLED)
    next_button.config(state=tk.NORMAL if end < len(user_list) else tk.DISABLED)


def launch_window(stub, user_list, username):
    """
    Launches the main Tkinter window displaying a paginated user list with search functionality.
    Returns a command dictionary indicating the next state.
    """
    root = tk.Tk()
    root.title("User List")
    root.geometry("400x600")

    current_index = tk.IntVar(root, 0)
    result = {}

    # Search bar
    tk.Label(root, text="Enter search pattern (* for all):").pack(pady=(10, 0))
    search_var = tk.StringVar(root)
    tk.Entry(root, textvariable=search_var).pack(pady=(0, 10))

    # Scrolled text area for displaying the user list
    text_area = scrolledtext.ScrolledText(root, width=50, height=20)
    text_area.pack(pady=(10, 10))

    # Pagination buttons
    prev_button = tk.Button(root, text="Previous 25", state=tk.DISABLED)
    prev_button.pack()
    next_button = tk.Button(
        root, text="Next 25", state=tk.NORMAL if len(user_list) > 25 else tk.DISABLED
    )
    next_button.pack()

    # Search button
    def on_search():
        nonlocal result
        command = search(stub, root, search_var)
        if command:
            result = command
            root.destroy()

    tk.Button(root, text="Search", command=on_search).pack(pady=(10, 10))

    # Home button to navigate back
    def on_home():
        nonlocal result
        command = launch_home(stub, root, username)
        if command:
            result = command
            root.destroy()

    tk.Button(root, text="Home", command=on_home).pack(pady=(10, 10))

    # Pagination button callbacks
    prev_button.config(
        command=lambda: (
            current_index.set(max(0, current_index.get() - 25)),
            update_display(
                text_area, user_list, current_index, prev_button, next_button
            ),
        )
    )
    next_button.config(
        command=lambda: (
            current_index.set(current_index.get() + 25),
            update_display(
                text_area, user_list, current_index, prev_button, next_button
            ),
        )
    )

    update_display(text_area, user_list, current_index, prev_button, next_button)

    root.mainloop()
    return result
