import tkinter as tk
from tkinter import messagebox
import socket
import json


def send_message(
    s: socket.SocketType,
    root: tk.Tk,
    recipient: tk.StringVar,
    message: tk.Text,
    current_user: str,
):
    recipient_str = recipient.get().strip()
    message_str = message.get("1.0", tk.END).strip()

    if recipient_str == "" or message_str == "":
        messagebox.showerror("Error", "All fields are required")
        return

    if not recipient_str.isalnum():
        messagebox.showerror("Error", "Username must be alphanumeric")
        return

    message_dict = {
        "sender": current_user,
        "recipient": recipient_str,
        "message": message_str,
    }
    message = f"send_msg {json.dumps(message_dict)}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def launch_home(s: socket.SocketType, root: tk.Tk, username: str):
    message_dict = {"username": username}
    message = f"refresh_home {json.dumps(message_dict)}".encode("utf-8")
    s.sendall(message)
    root.destroy()


def launch_window(s: socket.SocketType, current_user: str):
    # Create main window
    root = tk.Tk()
    root.title(f"Send Message - {current_user}")
    root.geometry("300x600")

    # Recipient Label and Entry
    tk.Label(root, text="Recipient (alphanumeric only):").pack()
    recipient_var = tk.StringVar(root)
    tk.Entry(root, textvariable=recipient_var).pack()

    # Message Label and Entry
    tk.Label(root, text="Message:").pack()
    entry_message = tk.Text(root)
    entry_message.pack()

    # Submit Button
    button_submit = tk.Button(
        root,
        text="Send Message",
        command=lambda: send_message(
            s, root, recipient_var, entry_message, current_user
        ),
    )
    button_submit.pack()

    # Back to home
    tk.Button(
        root, text="Home", command=lambda: launch_home(s, root, current_user)
    ).pack(pady=10)

    root.mainloop()
