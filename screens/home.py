import tkinter as tk
import chat_pb2

def launch_window_grpc(stub, username, undelivered_count):
    root = tk.Tk()
    root.title(f"Home - {username}")
    root.geometry("300x300")

    result = {"action": None, "data": None}

    tk.Button(root, text=f"Read Messages ({undelivered_count})", command=lambda: set_action("view_messages")).pack()
    tk.Button(root, text="Send Message", command=lambda: set_action("search_users", "*")).pack()
    tk.Button(root, text="Delete Messages", command=lambda: set_action("view_messages")).pack()
    tk.Button(root, text="User List", command=lambda: set_action("search_users", "*")).pack()
    tk.Button(root, text="Logout", command=lambda: set_action("logout")).pack()
    tk.Button(root, text="Delete Account", command=lambda: set_action("delete_account")).pack()

    def set_action(action, data=None):
        result["action"] = action
        result["data"] = data
        root.quit()

    root.mainloop()
    root.destroy()
    return result["action"], result["data"]