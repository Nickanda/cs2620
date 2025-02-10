import tkinter as tk
from tkinter import scrolledtext, messagebox
from argon2 import PasswordHasher
import socket

hasher = PasswordHasher()

def get_undelivered_messages(s: socket.socket, root: tk.Tk, num_messages_var: tk.IntVar, current_user: str):
    num_messages = num_messages_var.get()

    if num_messages > 0:
        s.sendall(f"get_undelivered {current_user} {num_messages}".encode("utf-8"))
        root.destroy()
    else:
        messagebox.showerror("Error", "Number of messages must be greater than 0")
    
def get_delivered_messages(s: socket.socket, root: tk.Tk, num_messages_var: tk.IntVar, current_user: str):
    num_messages = num_messages_var.get()

    if num_messages > 0:
        s.sendall(f"get_delivered {current_user} {num_messages}".encode("utf-8"))
        root.destroy()
    else:
        messagebox.showerror("Error", "Number of messages must be greater than 0")

def pagination(index: int, operation: str):
    if operation == "next":
        index += 25
    elif operation == "prev":
        index -= 25

def launch_home(s: socket.SocketType, root: tk.Tk, username: str): 
    message = f"refresh_home {username}".encode("utf-8")
    s.sendall(message)
    root.destroy()

def launch_window(s: socket.SocketType, messages: list[str], current_user: str):
    current_index = 0

    if current_index + 25 >= len(messages):
        to_display = messages[current_index:]
    else:
        to_display = messages[current_index:current_index + 25]
    messages_to_display = [f'[{msg[1]}, ID#{msg[0]}]: {"_".join(msg[2:])}' for msg in to_display]

    # Create main window
    root = tk.Tk()
    root.title("Messages")
    root.geometry("300x200")

    # Undelivered Messages
    tk.Label(root, text="Number of Messages to Get:").pack()
    num_messages_var = tk.IntVar(root)
    tk.Entry(root, textvariable=num_messages_var).pack()
    
    tk.Button(root, text=f"Get # Undelivered Messages", command=lambda: get_undelivered_messages(s, root, num_messages_var, current_user)).pack()
    tk.Button(root, text=f"Get # Delivered Messages", command=lambda: get_delivered_messages(s, root, num_messages_var, current_user)).pack()

    message_list = scrolledtext.ScrolledText(root)
    message_list.insert(tk.INSERT, "Messages:\n" + '\n'.join(messages_to_display)) 
    message_list.configure(state ='disabled') 
    message_list.pack()

    # Pagination Buttons
    tk.Button(root, text="Previous 25", command=lambda: pagination(current_index, "prev"), state=tk.DISABLED if current_index == 0 else tk.NORMAL).pack()

    # Pagination Button
    tk.Button(root, text="Next 25", command=lambda: pagination(current_index, "next"), state=tk.DISABLED if current_index + 25 >= len(messages) else tk.NORMAL).pack()

    tk.Button(root, text="Home", command=lambda: launch_home(s, root, current_user)).pack(pady=10)

    root.mainloop()