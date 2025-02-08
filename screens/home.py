import tkinter as tk
from argon2 import PasswordHasher
import socket
import screens.signup
import screens.user_list
import screens.send_message

hasher = PasswordHasher()

# Global variable holding the currently logged in username.
# current_user = None

# We keep a reference to the home window so that we can close it on logout or account deletion.
# home_root = None

def open_read_messages():
    pass


def open_send_message(s: socket.socket, root: tk.Tk, current_user: str):
    root.destroy()
    screens.send_message.launch_window(s, current_user)

def open_user_list(s: socket.socket, root: tk.Tk, username: str):
    root.destroy()
    screens.user_list.launch_window(s, [], username)

def logout(s: socket.socket, root: tk.Tk, username: str):
    message = f"logout {username}".encode("utf-8")
    s.sendall(message)
    root.destroy()

def delete_account(s: socket.socket, root: tk.Tk, username: str):
    message = f"delete_acct {username}".encode("utf-8")
    s.sendall(message)
    root.destroy()

def launch_window(s: socket.SocketType, username: str, num_messages: int):
    # Create main window
    home_root = tk.Tk()
    home_root.title("Home")
    home_root.geometry("300x200")

    button_submit = tk.Button(home_root, text=f"Read Messages ({num_messages})", command=lambda: open_read_messages)
    button_submit.pack()

    button_submit = tk.Button(home_root, text=f"Send Message", command=lambda: open_send_message(s, home_root, username))
    button_submit.pack()

    button_submit = tk.Button(home_root, text=f"User List", command=lambda: open_user_list(s, home_root, username))
    button_submit.pack()

    button_submit = tk.Button(home_root, text=f"Logout", command=lambda: logout(s, home_root, username))
    button_submit.pack()

    button_submit = tk.Button(home_root, text="Delete Account", command=lambda: delete_account(s, home_root, username))
    button_submit.pack()

    home_root.mainloop()