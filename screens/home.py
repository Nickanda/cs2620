import tkinter as tk
from argon2 import PasswordHasher
import socket
import screens.signup
import screens.user_list
import screens.send_message
import screens.messages
import screens.delete_messages

# Initialize password hasher
hasher = PasswordHasher()


def open_read_messages(s: socket.socket, root: tk.Tk, username: str):
    """
    Closes the current window and opens the read messages window.
    """
    root.destroy()
    screens.messages.launch_window(s, [], username)


def open_send_message(s: socket.socket, root: tk.Tk, current_user: str):
    """
    Closes the current window and opens the send message window.
    """
    root.destroy()
    screens.send_message.launch_window(s, current_user)


def open_delete_messages(s: socket.socket, root: tk.Tk, current_user: str):
    """
    Closes the current window and opens the delete messages window.
    """
    root.destroy()
    screens.delete_messages.launch_window(s, current_user)


def open_user_list(s: socket.socket, root: tk.Tk, username: str):
    """
    Closes the current window and opens the user list window.
    """
    root.destroy()
    screens.user_list.launch_window(s, [], username)


def logout(s: socket.socket, root: tk.Tk, username: str):
    """
    Sends a logout request to the server and closes the application.
    """
    s.sendall(f"logout {username}".encode("utf-8"))
    root.destroy()


def delete_account(s: socket.socket, root: tk.Tk, username: str):
    """
    Sends an account deletion request to the server and closes the application.
    """
    s.sendall(f"delete_acct {username}".encode("utf-8"))
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
