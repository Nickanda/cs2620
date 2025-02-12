"""
Client-side application for connecting to a server using a socket.

This script establishes a connection to a server at a specified host and port, handling 
user authentication, navigation between different screens, and processing commands received 
from the server.

Key Features:
- Uses JSON-based communication with the server instead of plain text commands.
- Supports user authentication (signup, login).
- Manages different UI states: home, messages, user list.
- Receives server responses as JSON objects, allowing structured data handling.
- Handles errors and displays messages using Tkinter's messagebox.

Last Updated: February 12, 2025
"""

import socket
from tkinter import messagebox
import screens_json.login
import screens_json.signup
import screens_json.home
import screens_json.messages
import screens_json.user_list
import json

# Define the server host and port
HOST = "127.0.0.1"
PORT = 54444


def connect_socket():
    """
    Establishes a connection to the server and handles different UI states based on server responses.
    """
    logged_in_user = None
    current_state = "signup"  # Set initial state
    state_data = None

    # Create a socket and connect to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        while True:
            # Launch the appropriate UI screen based on the current state
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
                screens_json.signup.launch_window(s)  # Default to signup screen

            # Receive and decode data from the server
            data = s.recv(1024)
            words = data.decode("utf-8").split()
            json_data = json.loads(" ".join(words[1:]))

            # Handle different server commands
            if words[0] == "login":
                # Store the logged-in username/undelivered messages and go to home
                logged_in_user = json_data["username"]
                state_data = json_data["undeliv_messages"]
                current_state = "home"
                print(f"Logged in as {logged_in_user}")
            elif words[0] == "user_list":
                # Transition to the user list screen
                current_state = "user_list"
                state_data = json_data["user_list"]
            elif words[0] == "error":
                # Handle errors from the server
                print(f"Error: {json_data['error']}")
                messagebox.showerror("Error", json_data["error"])
            elif words[0] == "refresh_home":
                # Refresh the home screen with undelivered messages
                state_data = json_data["undeliv_messages"]
                current_state = "home"
            elif words[0] == "messages":
                # Transition to the messages screen
                state_data = json_data["messages"]
                current_state = "messages"
            elif words[0] == "logout":
                # Log out the user and go back to the signup screen
                logged_in_user = None
                current_state = "signup"
            else:
                # Handle unknown commands
                command = " ".join(words)
                print(f"No valid command: {command}")


# Run the socket connection when the script is executed
if __name__ == "__main__":
    connect_socket()
