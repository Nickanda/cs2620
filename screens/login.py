import tkinter as tk
from tkinter import messagebox
import chat_pb2

def launch_window_grpc(stub):
    root = tk.Tk()
    root.title("User Login")
    root.geometry("300x200")

    username_var = tk.StringVar(root)
    password_var = tk.StringVar()

    tk.Label(root, text="Username:").pack()
    tk.Entry(root, textvariable=username_var).pack()
    tk.Label(root, text="Password:").pack()
    tk.Entry(root, show="*", textvariable=password_var).pack()

    result = {"action": None, "data": None}

    def login():
        username = username_var.get().strip()
        password = password_var.get().strip()
        if username and password:
            result["action"] = "login"
            result["data"] = (username, password)
            root.quit()
        else:
            messagebox.showerror("Error", "All fields are required")

    def switch_to_signup():
        result["action"] = "switch_to_signup"
        root.quit()

    tk.Button(root, text="Login", command=login).pack()
    tk.Button(root, text="Switch to Signup", command=switch_to_signup).pack()

    root.mainloop()
    root.destroy()
    return result["action"], result["data"]