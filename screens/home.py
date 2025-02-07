import tkinter as tk
from tkinter import messagebox
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
    win = tk.Toplevel()
    win.title("Read Messages")
    win.geometry("400x300")

    tk.Label(win, text="Enter number of messages to retrieve:").pack(pady=5)
    count_entry = tk.Entry(win)
    count_entry.pack(pady=5)

    text_area = tk.Text(win, height=12, width=50)
    text_area.pack(pady=5)

    def retrieve():
        try:
            count = int(count_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer.")
            return
        
        #! fix to support multiple clients
        # msgs = backend.get_messages(current_user, count)
        # text_area.delete("1.0", tk.END)
        # if not msgs:
        #     text_area.insert(tk.END, "No new messages.\n")
        # else:
        #     for m in msgs:
        #         text_area.insert(
        #             tk.END,
        #             f"From: {m['sender']}\nTime: {m['timestamp']}\nMessage: {m['message']}\n{'-'*40}\n"
        #         )

    tk.Button(win, text="Retrieve", command=retrieve).pack(pady=5)


def open_send_message(s: socket.socket, root: tk.Tk, current_user: str):
    screens.send_message.launch_window(s, current_user)
    root.destroy()

def open_user_list(s: socket.socket, root: tk.Tk):
    screens.user_list.launch_window(s, "")
    root.destroy()

def logout(s: socket.socket, root: tk.Tk, username: str):
    message = f"logout {username}".encode("utf-8")
    s.sendall(message)
    root.destroy()

def delete_account(s: socket.socket, root: tk.Tk, username: str):
    message = f"delete_account {username}".encode("utf-8")
    s.sendall(message)
    root.destroy()

def launch_window(s: socket.SocketType, username: str):
    # Create main window
    home_root = tk.Tk()
    home_root.title("Home")
    home_root.geometry("300x200")

    button_submit = tk.Button(home_root, text=f"Read Messages {1}", command=open_read_messages)
    button_submit.pack()

    button_submit = tk.Button(home_root, text=f"Send Message", command=open_send_message(s, home_root, username))
    button_submit.pack()

    button_submit = tk.Button(home_root, text=f"User List", command=open_user_list(s, home_root))
    button_submit.pack()

    button_submit = tk.Button(home_root, text=f"Logout", command=lambda: logout(s, home_root, username))
    button_submit.pack()

    button_submit = tk.Button(home_root, text="Delete Account", command=lambda: delete_account(s, home_root, username))
    button_submit.pack()

    home_root.mainloop()