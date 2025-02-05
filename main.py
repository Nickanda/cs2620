import socket
import selectors
import types

sel = selectors.DefaultSelector()

HOST = "127.0.0.1"
PORT = 54400

# 1: Creating an account. The user supplies a unique (login) name. If there is already an account with that name, the user is prompted for the password. If the name is not being used, the user is prompted to supply a password. The password should not be passed as plaintext.

# 2: Log in to an account. Using a login name and password, log into an account. An incorrect login or bad user name should display an error. A successful login should display the number of unread messages.

# 3: List accounts, or a subset of accounts that fit a text wildcard pattern. If there are more accounts than can comfortably be displayed, allow iterating through the accounts.

# 4. Send a message to a recipient. If the recipient is logged in, deliver immediately; if not the message should be stored until the recipient logs in and requests to see the message.

# 5: Read messages. If there are undelivered messages, display those messages. The user should be able to specify the number of messages they want delivered at any single time.

# 6. Delete a message or set of messages. Once deleted messages are gone.

# 7. Delete an account. You will need to specify the semantics of deleting an account that contains unread messages.

# ------------------------------------------------------------------------------
# def login
#   
# def create_account
#
# 

def accept_wrapper(sock):
    conn, addr = sock.accept()
    print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
        else:
            print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            words = data.outb.decode("utf-8").split()
            if words[0] == "count":
                return_data = str((len(words)-1)).encode("utf-8")
            elif words[0] == "translate":
                return_data = trans_to_pig_latin(words[1:])
                return_data = return_data.encode("utf-8")
            else:
                print ("No valid command")
                return_data = "Unknown command".encode("utf-8")
            sent = sock.send(return_data)
            data.outb = data.outb[sent:]

if __name__ == "__main__":
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((HOST, PORT))
    lsock.listen()
    print("Listening on", (HOST, PORT))
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)
    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()


import tkinter as tk
from tkinter import messagebox

def create_user():
    username = entry_username.get()
    email = entry_email.get()
    password = entry_password.get()
    
    if username and email and password:
        print(f"User Created: {username}, {email}")
        messagebox.showinfo("Success", "User created successfully!")
    else:
        messagebox.showerror("Error", "All fields are required!")

# Create main window
root = tk.Tk()
root.title("User Creation")
root.geometry("300x200")

# Username Label and Entry
label_username = tk.Label(root, text="Username:")
label_username.pack()
entry_username = tk.Entry(root)
entry_username.pack()

# Email Label and Entry
label_email = tk.Label(root, text="Email:")
label_email.pack()
entry_email = tk.Entry(root)
entry_email.pack()

# Password Label and Entry
label_password = tk.Label(root, text="Password:")
label_password.pack()
entry_password = tk.Entry(root, show="*")
entry_password.pack()

# Submit Button
button_submit = tk.Button(root, text="Create User", command=create_user)
button_submit.pack()

# Run the Tkinter loop
root.mainloop()
