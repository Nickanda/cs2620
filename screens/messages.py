import tkinter as tk
from tkinter import scrolledtext, messagebox
import chat_pb2

def launch_window_grpc(stub, messages, username):
    root = tk.Tk()
    root.title(f"Messages - {username}")
    root.geometry("400x600")

    result = {"action": None, "data": None}

    num_messages_var = tk.IntVar(root)
    tk.Label(root, text="Number of Messages to Get:").pack()
    tk.Entry(root, textvariable=num_messages_var).pack()

    tk.Button(root, text="Get Undelivered Messages", command=lambda: set_action("get_undelivered")).pack()
    tk.Button(root, text="Get Delivered Messages", command=lambda: set_action("get_delivered")).pack()

    message_list = scrolledtext.ScrolledText(root)
    message_list.pack()

    for msg in messages:
        message_list.insert(tk.END, f"[{msg['sender']}, ID#{msg['id']}]: {msg['message']}\n")

    tk.Button(root, text="Delete Selected Messages", command=lambda: set_action("delete_messages")).pack()
    tk.Button(root, text="Home", command=lambda: set_action("back_to_home")).pack()

    def set_action(action):
        if action in ["get_undelivered", "get_delivered"]:
            result["action"] = action
            result["data"] = num_messages_var.get()
        elif action == "delete_messages":
            # Implement message selection and deletion logic here
            pass
        else:
            result["action"] = action
        root.quit()

    root.mainloop()
    root.destroy()
    return result["action"], result["data"]