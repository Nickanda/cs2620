import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
import socket
import json


def search(s: socket.SocketType, root: tk.Tk, search: tk.StringVar):
    search_str = search.get().strip()

    if search_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    if not search_str.isalnum() and ("*" not in search_str):
        messagebox.showerror("Error", "Search characters must be alphanumeric or *")
        return

    message_dict = {"search": search_str}
    message = f"search {json.dumps(message_dict)}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def pagination(index: int, operation: str):
    if operation == "next":
        index += 25
    elif operation == "prev":
        index -= 25


def launch_home(s: socket.SocketType, root: tk.Tk, username: str):
    message_dict = {"username": username}
    message = f"refresh_home {json.dumps(message_dict)}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def launch_window(s: socket.SocketType, user_list: list[str], username: str):
    current_index = 0

    if current_index + 25 >= len(user_list):
        to_display = user_list[current_index:]
    else:
        to_display = user_list[current_index : current_index + 25]

    # Create main window
    root = tk.Tk()
    root.title("User List")
    root.geometry("400x600")

    # Search Label and Entry
    tk.Label(root, text="Enter search pattern (* for all):").pack()
    search_var = tk.StringVar(root)
    tk.Entry(root, textvariable=search_var).pack()

    # List users
    text_area = scrolledtext.ScrolledText(root)
    text_area.insert(tk.INSERT, "Users:\n" + "\n".join(to_display))
    text_area.configure(state="disabled")
    text_area.pack()

    # Pagination Buttons
    tk.Button(
        root,
        text="Previous 25",
        command=lambda: pagination(current_index, "prev"),
        state=tk.DISABLED if current_index == 0 else tk.NORMAL,
    ).pack()

    # Submit Button
    tk.Button(root, text="Search", command=lambda: search(s, root, search_var)).pack()

    # Pagination Button
    tk.Button(
        root,
        text="Next 25",
        command=lambda: pagination(current_index, "next"),
        state=tk.DISABLED if current_index + 25 >= len(user_list) else tk.NORMAL,
    ).pack()

    # Back to home
    tk.Button(root, text="Home", command=lambda: launch_home(s, root, username)).pack(
        pady=10
    )

    root.mainloop()
