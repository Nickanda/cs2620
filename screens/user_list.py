import tkinter as tk
from tkinter import messagebox
import socket

def search(s: socket.SocketType, root: tk.Tk, search: tk.StringVar):
    search_str = search.get().strip()

    if search_str != "":
        if search_str.isalnum() == False:
            messagebox.showerror("Error", "Username must be alphanumeric")
            return
        
        message = f"search {search_str}".encode("utf-8")
        s.sendall(message)
        root.destroy()
    else:
        messagebox.showerror("Error", "All fields are required")

def pagination(index: int, operation: str):
    if operation == "next":
        index += 25
    elif operation == "prev":
        index -= 25

def launch_window(s: socket.SocketType, user_list: list[str]):
    current_index = 0

    if current_index + 25 >= len(user_list):
        to_display = user_list[current_index:]
    else:
        to_display = user_list[current_index:current_index + 25]
  
    # Create main window
    root = tk.Tk()
    root.title("User List")
    root.geometry("300x200")

    # Search Label and Entry
    label_search = tk.Label(root, text="Enter search pattern (* for all):")
    label_search.pack()
    search_var = tk.StringVar(root)
    entry_search = tk.Entry(root, textvariable=search_var)
    entry_search.pack()

    # List users
    text_area = tk.ScrolledText(root)
    text_area.insert(tk.INSERT, f"Users:\n{'\n'.join(to_display)}") 
    text_area.configure(state ='disabled') 

    # Pagination Buttons
    button_prev = tk.Button(root, text="Previous 25", command=lambda: pagination(current_index, "prev"), state=tk.DISABLED if current_index == 0 else tk.NORMAL)
    button_prev.pack(side=tk.LEFT, padx=10, pady=10)

    # Submit Button
    button_submit = tk.Button(root, text="Search", command=lambda: search(s, root, search_var))
    button_submit.pack(side=tk.LEFT, padx=10, pady=10)

    button_next = tk.Button(root, text="Next 25", command=lambda: pagination(current_index, "nexr"), state=tk.DISABLED if current_index + 25 >= len(user_list) else tk.NORMAL)
    button_next.pack(side=tk.RIGHT, padx=10, pady=10)

    root.mainloop()