import socket
from tkinter import messagebox
import screens.login
import screens.signup
import screens.messages

HOST = "127.0.0.1"
PORT = 54400

def connect_socket():
    logged_in_user = None
    current_state = "signup"
    state_data = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            if current_state == "signup":
                screens.signup.launch_window(s)
            elif current_state == "login":
                screens.login.launch_window(s)
            elif current_state == "messages":
                screens.messages.launch_window(s, logged_in_user)

            data = s.recv(1028)
            words = data.decode("utf-8").split()
            
            print(words)

            if words[0] == "login":
                logged_in_user = words[1]
                current_state = "messages"
                print(f"Logged in as {logged_in_user}")
            elif words[0] == "error":
                print(f"Error: {' '.join(words[1:])}")
                messagebox.showerror("Error", f"{' '.join(words[1:])}")
            else: 
                command = " ".join(words)
                print(f"No valid command: {command}")

if __name__ == "__main__":
    connect_socket()