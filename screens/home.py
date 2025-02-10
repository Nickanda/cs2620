import tkinter as tk
from argon2 import PasswordHasher
import socket
import screens.signup
import screens.user_list
import screens.send_message
import screens.messages
import screens.delete_messages

hasher = PasswordHasher()

def open_read_messages(s: socket.socket, root: tk.Tk, username: str):
    root.destroy()
    screens.messages.launch_window(s, [], username)

def open_send_message(s: socket.socket, root: tk.Tk, current_user: str):
    root.destroy()
    screens.send_message.launch_window(s, current_user)

def open_delete_messages(s: socket.socket, root: tk.Tk, current_user: str):
    root.destroy()
    screens.delete_messages.launch_window(s, current_user)

def open_user_list(s: socket.socket, root: tk.Tk, username: str):
    root.destroy()
    screens.user_list.launch_window(s, [], username)

def logout(s: socket.socket, root: tk.Tk, username: str):
    s.sendall(f"logout {username}".encode("utf-8"))
    root.destroy()

def delete_account(s: socket.socket, root: tk.Tk, username: str):
    s.sendall(f"delete_acct {username}".encode("utf-8"))
    root.destroy()

def launch_window(s: socket.SocketType, username: str, num_messages: int):
    # Create main window
    home_root = tk.Tk()
    home_root.title(f"Home - {username}")
    home_root.geometry("300x200")

    tk.Button(home_root, text=f"Read Messages ({num_messages})", command=lambda: open_read_messages(s, home_root, username)).pack()
    tk.Button(home_root, text="Send Message", command=lambda: open_send_message(s, home_root, username)).pack()
    tk.Button(home_root, text="Delete Messages", command=lambda: open_delete_messages(s, home_root, username)).pack()
    tk.Button(home_root, text="User List", command=lambda: open_user_list(s, home_root, username)).pack()
    tk.Button(home_root, text="Logout", command=lambda: logout(s, home_root, username)).pack()
    tk.Button(home_root, text="Delete Account", command=lambda: delete_account(s, home_root, username)).pack()

    home_root.mainloop()