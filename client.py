"""
Client-side application for connecting to a server using a socket.

This script establishes a connection to a server at a specified host and port, handling
user authentication, navigation between different screens, and processing commands received
from the server.

Key Features:
- Uses a standard text-based protocol to communicate with the server.
- Supports user authentication (signup, login).
- Manages different UI states: home, messages, user list.
- Receives server responses as space-separated strings and processes them accordingly.
- Handles errors and displays messages using Tkinter's messagebox.

This version of the client handles server messages using simple space-separated commands.

Last Updated: February 12, 2025
"""

import socket
from tkinter import messagebox
import screens.login
import screens.signup
import screens.home
import screens.messages
import screens.user_list
import database_wrapper

# Define the server host and port
HOST = "127.0.0.1"
PORT = 54400


def connect_socket():
    """
    Establishes a connection to the server and handles different UI states based on server responses.
    """
    logged_in_user = None
    current_state = "signup"
    state_data = None

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            # Launch the appropriate screen based on the current state
            if current_state == "signup":
                screens.signup.launch_window(s)
            elif current_state == "login":
                screens.login.launch_window(s)
            elif current_state == "home" and logged_in_user is not None:
                screens.home.launch_window(s, logged_in_user, state_data)
            elif current_state == "messages" and logged_in_user is not None:
                screens.messages.launch_window(
                    s, state_data if state_data else [], logged_in_user
                )
            elif current_state == "user_list" and logged_in_user is not None:
                screens.user_list.launch_window(
                    s, state_data if state_data else "", logged_in_user
                )
            else:
                screens.signup.launch_window(s)

            # Receive data from the server
            data = s.recv(1024)
            words = data.decode("utf-8").split()
            version = words[0]

            if version != "0":
                print("Error: mismatch of API version!")
                messagebox.showerror("Error", "Mismatch of API version!")
            elif words[1] == "login":
                # Store the logged-in username and undelivered messages, then go to home
                logged_in_user = words[1]
                new_messages = int(words[2])
                state_data = new_messages
                current_state = "home"
                print(f"Logged in as {logged_in_user}")
            elif words[1] == "user_list":
                # Transition to the user list screen
                current_state = "user_list"
                state_data = words[1:]
            elif words[1] == "error":
                # Display an error message
                print(f"Error: {' '.join(words[1:])}")
                messagebox.showerror("Error", f"{' '.join(words[1:])}")
            elif words[1] == "refresh_home":
                # Refresh home screen with updated data
                state_data = int(words[1])
                current_state = "home"
            elif words[1] == "messages":
                # Update messages screen
                if len(words) > 1:
                    state_data = [word.split("_") for word in words[1].split("\0")]
                else:
                    state_data = []
                current_state = "messages"
            elif words[1] == "logout":
                # User logged out
                logged_in_user = None
                current_state = "signup"
            else:  # Unrecognized command from server
                command = " ".join(words)
                print(f"No valid command: {command}")


# Run the socket connection when the script is executed
if __name__ == "__main__":
    settings = database_wrapper.load_client_database()

    HOST = settings["host"]
    PORT = settings["port"]

    connect_socket()
