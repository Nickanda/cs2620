"""
User List Search and Pagination GUI

This script implements a Tkinter-based graphical user interface (GUI) that allows users to:
- View a paginated list of users (displaying up to 25 users at a time).
- Perform a search query using alphanumeric characters or '*' as a wildcard.
- Navigate between pages of users using "Next" and "Previous" buttons.
- Return to the home screen by sending a refresh request to the server.

Last updated: February 12, 2025
"""

import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import socket


def search(s: socket.SocketType, root: tk.Tk, search: tk.StringVar):
    """
    Handles the search functionality by sending the search query to the server.
    Ensures that input is not empty and contains only alphanumeric characters or '*'.
    """
    search_str = search.get().strip()

    if search_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    # Validate input
    if not search_str.isalnum() and ("*" not in search_str):
        messagebox.showerror("Error", "Search characters must be alphanumeric or *")
        return

    # Send search query to the server
    message = f"0 search {search_str}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def pagination(index: int, operation: str):
    """
    Handles pagination by adjusting the index for displaying users.
    """
    if operation == "next":
        index += 25
    elif operation == "prev":
        index -= 25


def launch_home(s: socket.SocketType, root: tk.Tk, username: str):
    """
    Handles navigation back to the home screen by sending a refresh request to the server.
    """
    message = f"0 refresh_home {username}".encode("utf-8")
    s.sendall(message)
    # Close the current window
    root.destroy()


def update_display(text_area, user_list, current_index, prev_button, next_button):
    """
    Updates the displayed user list based on the current index.
    """
    start = current_index.get()
    end = start + 25 if start + 25 < len(user_list) else len(user_list)
    to_display = user_list[start:end]

    # Clear and update text area
    text_area.configure(state="normal")
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.INSERT, "Users:\n" + "\n".join(to_display))
    text_area.configure(state="disabled")

    # Enable/Disable buttons based on index
    prev_button.config(state=tk.NORMAL if start > 0 else tk.DISABLED)
    next_button.config(state=tk.NORMAL if end < len(user_list) else tk.DISABLED)


def launch_window(s: socket.SocketType, user_list: list[str], username: str):
    """
    Launches the main Tkinter window displaying a paginated user list with search functionality.
    """
    # Create main Tkinter window
    root = tk.Tk()
    root.title("User List")
    root.geometry("400x600")

    current_index = tk.IntVar(root, 0)  # Initialize pagination index

    # Search bar
    tk.Label(root, text="Enter search pattern (* for all):").pack()
    search_var = tk.StringVar(root)
    tk.Entry(root, textvariable=search_var).pack()

    # Scrolled text area for displaying user list
    text_area = scrolledtext.ScrolledText(root)
    text_area.pack()

    prev_button = tk.Button(
        root,
        text="Previous 25",
        state=tk.DISABLED,  # Initially disabled
        command=lambda: (
            current_index.set(current_index.get() - 25),
            update_display(
                text_area, user_list, current_index, prev_button, next_button
            ),
        ),
    )
    prev_button.pack()

    next_button = tk.Button(
        root,
        text="Next 25",
        state=tk.NORMAL if len(user_list) > 25 else tk.DISABLED,
        command=lambda: (
            current_index.set(current_index.get() + 25),
            update_display(
                text_area, user_list, current_index, prev_button, next_button
            ),
        ),
    )
    next_button.pack()

    # Search button
    tk.Button(root, text="Search", command=lambda: search(s, root, search_var)).pack()

    # Home button to navigate back
    tk.Button(root, text="Home", command=lambda: launch_home(s, root, username)).pack(
        pady=10
    )

    update_display(text_area, user_list, current_index, prev_button, next_button)

    # Run Tkinter event loop
    root.mainloop()
