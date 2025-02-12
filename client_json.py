import socket
from tkinter import messagebox
import screens_json.login
import screens_json.signup
import screens_json.home
import screens_json.messages
import screens_json.user_list
import json

HOST = "127.0.0.1"
PORT = 54444


def connect_socket():
    logged_in_user = None
    current_state = "signup"
    state_data = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            if current_state == "signup":
                screens_json.signup.launch_window(s)
            elif current_state == "login":
                screens_json.login.launch_window(s)
            elif current_state == "home" and logged_in_user is not None:
                screens_json.home.launch_window(s, logged_in_user, state_data)
            elif current_state == "messages" and logged_in_user is not None:
                screens_json.messages.launch_window(
                    s, state_data if state_data else [], logged_in_user
                )
            elif current_state == "user_list" and logged_in_user is not None:
                screens_json.user_list.launch_window(
                    s, state_data if state_data else "", logged_in_user
                )
            else:
                screens_json.signup.launch_window(s)

            data = s.recv(1024)
            words = data.decode("utf-8").split()
            json_data = json.loads(" ".join(words[1:]))

            if words[0] == "login":
                logged_in_user = json_data["username"]
                state_data = json_data["undeliv_messages"]
                current_state = "home"
                print(f"Logged in as {logged_in_user}")
            elif words[0] == "user_list":
                current_state = "user_list"
                state_data = json_data["user_list"]
            elif words[0] == "error":
                print(f"Error: {' '.join(words[1:])}")
                messagebox.showerror("Error", f"{' '.join(words[1:])}")
            elif words[0] == "refresh_home":
                state_data = json_data["undeliv_messages"]
                current_state = "home"
            elif words[0] == "messages":
                state_data = json_data["messages"]
                current_state = "messages"
            elif words[0] == "logout":
                logged_in_user = None
                current_state = "signup"
            else:
                command = " ".join(words)
                print(f"No valid command: {command}")


if __name__ == "__main__":
    connect_socket()
