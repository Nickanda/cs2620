"""
grpc_client.py

Client-side application for connecting to a gRPC server.

This script establishes a connection to a gRPC server at a specified host and port,
handling user authentication, navigation between different screens, and processing
responses from the server using the Protocol Buffers definitions.

Key Features:
- Uses gRPC for client-server communication
- Supports user authentication (signup, login)
- Manages different UI states: home, messages, user list
- Processes structured gRPC responses

Last Updated: February 24, 2025
"""

import grpc
import database_wrapper
import chat_pb2
import chat_pb2_grpc
from tkinter import messagebox
import screens.login
import screens.signup
import screens.home
import screens.messages
import screens.user_list

def run_client():
    """
    Establishes a connection to the gRPC server and handles different UI states
    based on server responses.
    """
    # Load settings
    settings = database_wrapper.load_client_database()
    server_addr = f"{settings['host']}:{settings['port']}"
    
    # Set up the gRPC channel
    channel = grpc.insecure_channel(server_addr)
    stub = chat_pb2_grpc.ChatServiceStub(channel)
    
    logged_in_user = None
    current_state = "signup"
    state_data = None
    
    while True:
        try:
            # Launch the appropriate screen based on the current state
            if current_state == "signup":
                action, data = screens.signup.launch_window_grpc(stub)
                
                if action == "create_account":
                    username, password = data
                    response = stub.CreateAccount(
                        chat_pb2.CreateAccountRequest(
                            username=username,
                            password=password
                        )
                    )
                    
                    if response.success:
                        logged_in_user = response.username
                        state_data = response.undelivered_count
                        current_state = "home"
                        print(f"Logged in as {logged_in_user}")
                    else:
                        messagebox.showerror("Error", response.error_message)
                
                elif action == "switch_to_login":
                    current_state = "login"
            
            elif current_state == "login":
                action, data = screens.login.launch_window_grpc(stub)
                
                if action == "login":
                    username, password = data
                    response = stub.Login(
                        chat_pb2.LoginRequest(
                            username=username,
                            password=password
                        )
                    )
                    
                    if response.success:
                        logged_in_user = response.username
                        state_data = response.undelivered_count
                        current_state = "home"
                        print(f"Logged in as {logged_in_user}")
                    else:
                        messagebox.showerror("Error", response.error_message)
                
                elif action == "switch_to_signup":
                    current_state = "signup"
            
            elif current_state == "home" and logged_in_user is not None:
                action, data = screens.home.launch_window_grpc(
                    stub, logged_in_user, state_data
                )
                
                if action == "logout":
                    response = stub.Logout(
                        chat_pb2.LogoutRequest(username=logged_in_user)
                    )
                    logged_in_user = None
                    current_state = "signup"
                
                elif action == "delete_account":
                    response = stub.DeleteAccount(
                        chat_pb2.DeleteAccountRequest(username=logged_in_user)
                    )
                    logged_in_user = None
                    current_state = "signup"
                
                elif action == "view_messages":
                    current_state = "messages"
                    # Reset state data for messages screen
                    state_data = []
                
                elif action == "search_users":
                    current_state = "user_list"
                    pattern = data
                    response = stub.SearchUsers(
                        chat_pb2.SearchUsersRequest(pattern=pattern)
                    )
                    state_data = response.usernames
                
                elif action == "refresh":
                    response = stub.RefreshHome(
                        chat_pb2.RefreshHomeRequest(username=logged_in_user)
                    )
                    state_data = response.undelivered_count
                    current_state = "home"
            
            elif current_state == "messages" and logged_in_user is not None:
                action, data = screens.messages.launch_window_grpc(
                    stub, state_data, logged_in_user
                )
                
                if action == "get_undelivered":
                    max_messages = data
                    response = stub.GetUndeliveredMessages(
                        chat_pb2.GetMessagesRequest(
                            username=logged_in_user,
                            max_messages=max_messages
                        )
                    )
                    
                    if response.error_message:
                        messagebox.showinfo("Info", response.error_message)
                    else:
                        # Convert gRPC messages to the format expected by the UI
                        messages_data = []
                        for msg in response.messages:
                            messages_data.append({
                                "id": msg.id,
                                "sender": msg.sender,
                                "message": msg.message
                            })
                        state_data = messages_data
                        current_state = "messages"
                
                elif action == "get_delivered":
                    max_messages = data
                    response = stub.GetDeliveredMessages(
                        chat_pb2.GetMessagesRequest(
                            username=logged_in_user,
                            max_messages=max_messages
                        )
                    )
                    
                    if response.error_message:
                        messagebox.showinfo("Info", response.error_message)
                    else:
                        # Convert gRPC messages to the format expected by the UI
                        messages_data = []
                        for msg in response.messages:
                            messages_data.append({
                                "id": msg.id,
                                "sender": msg.sender,
                                "message": msg.message
                            })
                        state_data = messages_data
                        current_state = "messages"
                
                elif action == "delete_messages":
                    message_ids = data
                    response = stub.DeleteMessages(
                        chat_pb2.DeleteMessagesRequest(
                            username=logged_in_user,
                            message_ids=message_ids
                        )
                    )
                    
                    # After deletion, refresh the undelivered count
                    state_data = response.undelivered_count
                    current_state = "home"
                
                elif action == "back_to_home":
                    # Refresh home before returning
                    response = stub.RefreshHome(
                        chat_pb2.RefreshHomeRequest(username=logged_in_user)
                    )
                    state_data = response.undelivered_count
                    current_state = "home"
            
            elif current_state == "user_list" and logged_in_user is not None:
                action, data = screens.user_list.launch_window_grpc(
                    stub, state_data, logged_in_user
                )
                
                if action == "send_message":
                    receiver, message = data
                    response = stub.SendMessage(
                        chat_pb2.SendMessageRequest(
                            sender=logged_in_user,
                            receiver=receiver,
                            message=message
                        )
                    )
                    
                    if response.error_message:
                        messagebox.showerror("Error", response.error_message)
                    else:
                        messagebox.showinfo("Success", "Message sent successfully!")
                    
                    # Refresh home after sending a message
                    state_data = response.undelivered_count
                    current_state = "home"
                
                elif action == "back_to_home":
                    # Refresh home before returning
                    response = stub.RefreshHome(
                        chat_pb2.RefreshHomeRequest(username=logged_in_user)
                    )
                    state_data = response.undelivered_count
                    current_state = "home"
                
                elif action == "search":
                    pattern = data
                    response = stub.SearchUsers(
                        chat_pb2.SearchUsersRequest(pattern=pattern)
                    )
                    state_data = response.usernames
                    current_state = "user_list"
            
            else:
                # Default to signup if we're in an invalid state
                current_state = "signup"
                
        except grpc.RpcError as e:
            # Handle gRPC errors
            status_code = e.code()
            detail = e.details()
            messagebox.showerror("gRPC Error", f"Error {status_code}: {detail}")
            # Try to recover from errors by going back to the signup screen
            current_state = "signup"
            logged_in_user = None

if __name__ == "__main__":
    run_client()