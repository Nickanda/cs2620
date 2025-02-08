import tkinter as tk
from tkinter import messagebox
from argon2 import PasswordHasher
import socket

hasher = PasswordHasher()

def login(s: socket.SocketType, root: tk.Tk, recipient: tk.StringVar, message, current_user: str):
    recipient_str = recipient.get().strip()
    message_str = message.get().strip()

    if recipient_str != "" and message_str != "":
        if recipient_str.isalnum() == False:
            messagebox.showerror("Error", "Username must be alphanumeric")
            return
        
        message = f"send_msg {current_user} {recipient_str} {message_str}".encode("utf-8")
        s.sendall(message)
        root.destroy()
    else:
        messagebox.showerror("Error", "All fields are required")

def launch_window(s: socket.SocketType, current_user: str):
    # Create main window
    root = tk.Tk()
    root.title("Send Message")
    root.geometry("300x200")

    # Recipient Label and Entry
    label_recipient = tk.Label(root, text="Recipient (alphanumeric only):")
    label_recipient.pack()
    recipient_var = tk.StringVar(root)
    entry_recipient = tk.Entry(root, textvariable=recipient_var)
    entry_recipient.pack()

    # Message Label and Entry
    label_message = tk.Label(root, text="Message:")
    label_message.pack()
    entry_message = tk.Text(root)
    entry_message.pack()

    # Submit Button
    button_submit = tk.Button(root, text="Send Message", command=lambda: login(s, root, recipient_var, entry_message, current_user))
    button_submit.pack()

    root.mainloop()