import tkinter as tk
from argon2 import PasswordHasher
import socket

hasher = PasswordHasher()



def launch_window(s: socket.SocketType, messages: list[str]):
    # Create main window
    root = tk.Tk()
    root.title("Messages")
    root.geometry("300x200")

    

    root.mainloop()

# import tkinter as tk
# from tkinter import ttk, messagebox, scrolledtext
# import socket

# def send_message(s, recipient_var, message_var):
#     recipient = recipient_var.get().strip()
#     message = message_var.get().strip()

#     if not recipient or not message:
#         messagebox.showerror("Error", "Recipient and message are required")
#         return

#     if not recipient.isalnum():
#         messagebox.showerror("Error", "Recipient must be alphanumeric")
#         return

#     try:
#         s.sendall(f"send {recipient} {message}".encode('utf-8'))
#         response = s.recv(1024).decode()
#         if response == "OK":
#             messagebox.showinfo("Success", "Message sent successfully")
#             recipient_var.set("")
#             message_var.set("")
#         else:
#             messagebox.showerror("Error", response)
#     except Exception as e:
#         messagebox.showerror("Error", f"Connection error: {str(e)}")

# def read_messages(s, count_var, current_index_var, text_area, prev_btn, next_btn):
#     try:
#         count = count_var.get()
#         current_index = current_index_var.get()
        
#         s.sendall(f"read {current_index} {count}".encode('utf-8'))
#         response = s.recv(4096).decode().strip()
        
#         if response.startswith("ERR"):
#             messagebox.showerror("Error", response[3:])
#             return
        
#         messages = response.split('\n')
#         text_area.config(state='normal')
#         text_area.delete(1.0, tk.END)
        
#         if not messages or messages[0] == "":
#             text_area.insert(tk.END, "No messages to display")
#             next_btn.config(state=tk.DISABLED)
#         else:
#             text_area.insert(tk.END, "\n".join(messages))
#             next_btn.config(state=tk.NORMAL if len(messages) == count else tk.DISABLED)
        
#         text_area.config(state='disabled')
#         prev_btn.config(state=tk.NORMAL if current_index > 0 else tk.DISABLED)
        
#     except Exception as e:
#         messagebox.showerror("Error", f"Connection error: {str(e)}")

# def delete_messages(s, ids_var):
#     ids = ids_var.get().strip()
#     if not ids:
#         messagebox.showerror("Error", "Please enter message IDs to delete")
#         return
    
#     try:
#         ids_list = [int(id.strip()) for id in ids.split(',')]
#     except ValueError:
#         messagebox.showerror("Error", "Invalid message IDs format")
#         return
    
#     try:
#         s.sendall(f"delete {','.join(map(str, ids_list))}".encode('utf-8'))
#         response = s.recv(1024).decode()
#         if response == "OK":
#             messagebox.showinfo("Success", "Messages deleted successfully")
#             ids_var.set("")
#         else:
#             messagebox.showerror("Error", response)
#     except Exception as e:
#         messagebox.showerror("Error", f"Connection error: {str(e)}")

# def launch_messages_window(s):
#     root = tk.Tk()
#     root.title("Message Manager")
#     root.geometry("800x600")

#     # Main container
#     main_frame = ttk.Frame(root)
#     main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

#     # Send Message Section
#     send_frame = ttk.LabelFrame(main_frame, text="Send Message")
#     send_frame.pack(fill=tk.X, pady=5)

#     ttk.Label(send_frame, text="Recipient:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
#     recipient_var = tk.StringVar()
#     ttk.Entry(send_frame, textvariable=recipient_var).grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)

#     ttk.Label(send_frame, text="Message:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
#     message_var = tk.StringVar()
#     ttk.Entry(send_frame, textvariable=message_var).grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

#     ttk.Button(send_frame, text="Send", 
#               command=lambda: send_message(s, recipient_var, message_var)).grid(row=2, column=1, pady=5, sticky=tk.E)

#     # Read Messages Section
#     read_frame = ttk.LabelFrame(main_frame, text="Read Messages")
#     read_frame.pack(fill=tk.BOTH, expand=True, pady=5)

#     controls_frame = ttk.Frame(read_frame)
#     controls_frame.pack(fill=tk.X, pady=5)

#     ttk.Label(controls_frame, text="Messages per page:").pack(side=tk.LEFT, padx=5)
#     count_var = tk.IntVar(value=10)
#     ttk.Spinbox(controls_frame, from_=1, to=100, textvariable=count_var, width=5).pack(side=tk.LEFT, padx=5)

#     current_index_var = tk.IntVar(value=0)

#     text_area = scrolledtext.ScrolledText(read_frame, wrap=tk.WORD)
#     text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
#     text_area.config(state='disabled')

#     nav_frame = ttk.Frame(read_frame)
#     nav_frame.pack(fill=tk.X, pady=5)

#     def update_messages():
#         read_messages(s, count_var, current_index_var, text_area, prev_btn, next_btn)

#     prev_btn = ttk.Button(nav_frame, text="← Previous",
#                          command=lambda: [current_index_var.set(max(0, current_index_var.get() - count_var.get())), update_messages()])
#     prev_btn.pack(side=tk.LEFT, padx=10)
    
#     next_btn = ttk.Button(nav_frame, text="Next →",
#                          command=lambda: [current_index_var.set(current_index_var.get() + count_var.get()), update_messages()])
#     next_btn.pack(side=tk.RIGHT, padx=10)

#     ttk.Button(nav_frame, text="Refresh", command=update_messages).pack(side=tk.BOTTOM, pady=5)

#     # Delete Messages Section
#     delete_frame = ttk.LabelFrame(main_frame, text="Delete Messages")
#     delete_frame.pack(fill=tk.X, pady=5)

#     ttk.Label(delete_frame, text="Message IDs (comma-separated):").pack(side=tk.LEFT, padx=5)
#     ids_var = tk.StringVar()
#     ttk.Entry(delete_frame, textvariable=ids_var, width=30).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
#     ttk.Button(delete_frame, text="Delete", 
#               command=lambda: delete_messages(s, ids_var)).pack(side=tk.RIGHT, padx=5)

#     # Initial load
#     update_messages()

#     root.mainloop()