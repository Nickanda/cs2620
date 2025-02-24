"""
Client-side application for connecting to a server using gRPC.

This script establishes a connection to a gRPC server at a specified host and port,
handling user authentication, navigation between different screens, and processing
responses returned from the UI screens (which in turn use the gRPC stub).

Key Features:
- Uses gRPC-based communication with the server instead of socket/JSON-based communication.
- Supports user authentication (signup, login).
- Manages different UI states: home, messages, user list.
- Receives structured responses (as Python dictionaries) from UI screens.
- Handles errors and displays messages using Tkinter's messagebox.

Last Updated: February 12, 2025
"""

import grpc
from tkinter import messagebox
import screens_rpc.login
import screens_rpc.signup
import screens_rpc.home
import screens_rpc.messages
import screens_rpc.user_list
import database_wrapper
import chat_pb2
import chat_pb2_grpc


def connect_rpc():
    """
    Establishes a gRPC connection to the server and handles UI state transitions based on user actions.
    """
    logged_in_user = None
    current_state = "signup"  # Start in the signup state
    state_data = None

    # Load client settings (host/port for gRPC)
    settings = database_wrapper.load_client_database()
    host = settings["host"]
    port = settings["port"]

    # Create a gRPC channel and stub to call server RPC methods.
    channel = grpc.insecure_channel(f"{host}:{port}")
    stub = chat_pb2_grpc.ChatServiceStub(channel)

    # Main loop to drive UI transitions.
    while True:
        # Launch the appropriate UI screen based on the current state.
        if current_state == "signup":
            response = screens_rpc.signup.launch_window(stub)
        elif current_state == "login":
            response = screens_rpc.login.launch_window(stub)
        elif current_state == "home" and logged_in_user is not None:
            response = screens_rpc.home.launch_window(stub, logged_in_user, state_data)
        elif current_state == "messages" and logged_in_user is not None:
            response = screens_rpc.messages.launch_window(
                stub, state_data if state_data else [], logged_in_user
            )
        elif current_state == "user_list" and logged_in_user is not None:
            response = screens_rpc.user_list.launch_window(
                stub, state_data if state_data else "", logged_in_user
            )
        else:
            # Fallback: default to signup screen.
            response = screens_rpc.signup.launch_window(stub)

        # Each screen returns a response dictionary with a "command" field and optionally a "data" field.
        command = response.get("command")
        data = response.get("data", {})
        print(response)

        # Process the response command and update the current state accordingly.
        if command == "error":
            messagebox.showerror("Error", data.get("error", "Unknown error"))
        elif command == "login":
            # A successful login should return the username and any undelivered messages.
            logged_in_user = data.get("username")
            state_data = data.get("undeliv_messages")
            current_state = "home"
            print(f"Logged in as {logged_in_user}")
        elif command == "user_list":
            current_state = "user_list"
            state_data = data.get("user_list")
        elif command == "refresh_home":
            state_data = data.get("undeliv_messages")
            current_state = "home"
        elif command == "messages":
            state_data = data.get("messages")
            current_state = "messages"
        elif command == "logout":
            logged_in_user = None
            current_state = "signup"
        elif command == "login_screen":
            # This command indicates that the user wants to switch to the login screen.
            current_state = "login"
        else:
            print(f"No valid command received: {command}")


if __name__ == "__main__":
    connect_rpc()
