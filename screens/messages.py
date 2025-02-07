import tkinter as tk
from tkinter import messagebox
from argon2 import PasswordHasher
import socket

hasher = PasswordHasher()



def launch_window(s: socket.SocketType):
    # Create main window
    root = tk.Tk()
    root.title("Messages")
    root.geometry("300x200")

    

    root.mainloop()