import socket
from tkinter import messagebox
import screens.login
import screens.signup
import screens.home
import screens.messages
import screens.user_list

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
            elif current_state == "home" and logged_in_user is not None:
                screens.home.launch_window(s, logged_in_user, 0)
            elif current_state == "messages" and logged_in_user is not None:
                screens.messages.launch_window(s, state_data if state_data else "")
            elif current_state == "user_list" and logged_in_user is not None:
                screens.user_list.launch_window(s, state_data if state_data else "")
            elif current_state == "logout":
                logged_in_user = None
                current_state = "signup"
            else:
                screens.signup.launch_window(s)

            data = s.recv(1024)
            words = data.decode("utf-8").split()

            if words[0] == "login":
                logged_in_user = words[1]
                new_messages = int(words[2])
                state_data = new_messages
                current_state = "home"
                print(f"Logged in as {logged_in_user}")
            elif words[0] == "user_list":
                current_state = "user_list"
                state_data = words[1:]
            elif words[0] == "error":
                print(f"Error: {' '.join(words[1:])}")
                messagebox.showerror("Error", f"{' '.join(words[1:])}")
            elif words[0] == "refresh_home":
                new_messages = int(words[1])
                state_data = new_messages
                current_state = "home"
            else: 
                command = " ".join(words)
                print(f"No valid command: {command}")

if __name__ == "__main__":
    connect_socket()