import tkinter as tk
from tkinter import scrolledtext, messagebox
import chat_pb2

def launch_window_grpc(stub, users, username):
    root = tk.Tk()
    root.title("User List")
    root.geometry("400x600")

    result = {"action": None, "data": None}

    search_var = tk.StringVar(root)
    tk.Label(root, text="Search Pattern:").pack()
    tk.Entry(root, textvariable=search_var).pack()
    tk.Button(root, text="Search", command=lambda: set_action("search")).pack()

    user_list = scrolledtext.ScrolledText(root)
    user_list.pack()

    for user in users:
        user_list.insert(tk.END, f"{user}\n")

    recipient_var = tk.StringVar(root)
    message_var = tk.StringVar(root)
    tk.Label(root, text="Recipient:").pack()
    tk.Entry(root, textvariable=recipient_var).pack()
    tk.Label(root, text="Message:").pack()
    tk.Entry(root, textvariable=message_var).pack()
    tk.Button(root, text="Send Message", command=lambda: set_action("send_message")).pack()

    tk.Button(root, text="Home", command=lambda: set_action("back_to_home")).pack()

    def set_action(action):
        if action == "search":
            result["action"] = action
            result["data"] = search_var.get()
        elif action == "send_message":
            result["action"] = action
            result["data"] = (recipient_var.get(), message_var.get())
        else:
            result["action"] = action
        root.quit()

    root.mainloop()
    root.destroy()
    return result["action"], result["data"]