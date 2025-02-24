"""
grpc_server.py

Server Implementation for a User Messaging System using gRPC

This script sets up a gRPC-based server that handles user registration,
login, searching for user accounts, sending messages, reading messages,
deleting messages, and deleting user accounts using the Protocol Buffers
defined in chat.proto.

Key functionalities include:
- Creating and logging into user accounts
- Searching for users with wildcard patterns
- Sending and receiving messages
- Deleting messages and accounts
- Tracking message delivery status

Last updated: February 24, 2025
"""

import grpc
from concurrent import futures
import fnmatch
import time
import database_wrapper
import chat_pb2
import chat_pb2_grpc

class ChatServicer(chat_pb2_grpc.ChatServiceServicer):
    def __init__(self):
        # Load database
        self.users, self.messages, self.settings = database_wrapper.load_database()
        print(f"Server starting on {self.settings['host']}:{self.settings['port']}")
    
    def save_database(self):
        """Helper method to save the database state"""
        database_wrapper.save_database(self.users, self.messages, self.settings)
    
    def get_new_messages_count(self, username):
        """Count undelivered messages for a user"""
        count = 0
        for msg in self.messages["undelivered"]:
            if msg["receiver"] == username:
                count += 1
        return count
    
    def CreateAccount(self, request, context):
        """Handle account creation requests"""
        username = request.username
        password = request.password
        
        # Check username and password validity
        if not username.isalnum():
            return chat_pb2.LoginResponse(
                success=False, 
                error_message="Username must be alphanumeric"
            )
        
        if username in self.users:
            return chat_pb2.LoginResponse(
                success=False, 
                error_message="Username already exists"
            )
        
        if password.strip() == "":
            return chat_pb2.LoginResponse(
                success=False, 
                error_message="Password cannot be empty"
            )
        
        # Create new user
        self.users[username] = {
            "password": password,
            "logged_in": True,
            "addr": str(context.peer())  # Store peer info as string
        }
        
        self.save_database()
        
        # Return success response
        return chat_pb2.LoginResponse(
            success=True,
            username=username,
            undelivered_count=0
        )
    
    def Login(self, request, context):
        """Handle login requests"""
        username = request.username
        password = request.password
        
        if username not in self.users:
            return chat_pb2.LoginResponse(
                success=False, 
                error_message="Username does not exist"
            )
        
        if self.users[username]["logged_in"]:
            return chat_pb2.LoginResponse(
                success=False, 
                error_message="User already logged in"
            )
        
        if password != self.users[username]["password"]:
            return chat_pb2.LoginResponse(
                success=False, 
                error_message="Incorrect password"
            )
        
        # Mark user as logged in
        self.users[username]["logged_in"] = True
        self.users[username]["addr"] = str(context.peer())
        
        # Count undelivered messages
        undelivered_count = self.get_new_messages_count(username)
        
        self.save_database()
        
        return chat_pb2.LoginResponse(
            success=True,
            username=username,
            undelivered_count=undelivered_count
        )
    
    def Logout(self, request, context):
        """Handle logout requests"""
        username = request.username
        
        if username not in self.users:
            return chat_pb2.LogoutResponse(
                success=False, 
                error_message="Username does not exist"
            )
        
        # Mark user as logged out
        self.users[username]["logged_in"] = False
        self.users[username]["addr"] = ""
        
        self.save_database()
        
        return chat_pb2.LogoutResponse(success=True)
    
    def SearchUsers(self, request, context):
        """Search for users with pattern matching"""
        pattern = request.pattern if request.pattern else "*"
        matched_users = fnmatch.filter(self.users.keys(), pattern)
        
        return chat_pb2.UserListResponse(usernames=matched_users)
    
    def DeleteAccount(self, request, context):
        """Delete a user account and related messages"""
        username = request.username
        
        if username not in self.users:
            return chat_pb2.LogoutResponse(
                success=False, 
                error_message="Account does not exist"
            )
        
        # Remove the user
        del self.users[username]
        
        # Remove related messages
        def del_acct_msgs(msg_obj_lst, acct):
            msg_obj_lst[:] = [
                msg_obj for msg_obj in msg_obj_lst
                if msg_obj["sender"] != acct and msg_obj["receiver"] != acct
            ]
        
        del_acct_msgs(self.messages["delivered"], username)
        del_acct_msgs(self.messages["undelivered"], username)
        
        self.save_database()
        
        return chat_pb2.LogoutResponse(success=True)
    
    def SendMessage(self, request, context):
        """Send a message to another user"""
        sender = request.sender
        receiver = request.receiver
        message = request.message
        
        if receiver not in self.users:
            return chat_pb2.HomeRefreshResponse(
                undelivered_count=self.get_new_messages_count(sender),
                error_message="Receiver does not exist"
            )
        
        # Increment message counter and create message object
        self.settings["counter"] += 1
        msg_obj = {
            "id": self.settings["counter"],
            "sender": sender,
            "receiver": receiver,
            "message": message
        }
        
        # Determine if message should be delivered immediately
        if self.users[receiver]["logged_in"]:
            self.messages["delivered"].append(msg_obj)
        else:
            self.messages["undelivered"].append(msg_obj)
        
        self.save_database()
        
        # Return updated undelivered count for sender
        return chat_pb2.HomeRefreshResponse(
            undelivered_count=self.get_new_messages_count(sender)
        )
    
    def GetUndeliveredMessages(self, request, context):
        """Retrieve undelivered messages for a user"""
        username = request.username
        max_messages = request.max_messages
        
        undelivered_msgs = self.messages["undelivered"]
        delivered_msgs = self.messages["delivered"]
        
        if len(undelivered_msgs) == 0 and max_messages > 0:
            return chat_pb2.MessagesResponse(
                error_message="No undelivered messages"
            )
        
        to_deliver = []
        remove_indices = []
        
        # Find messages to deliver
        for idx, msg_obj in enumerate(undelivered_msgs):
            if max_messages == 0:
                break
                
            if msg_obj["receiver"] == username:
                to_deliver.append(chat_pb2.Message(
                    id=msg_obj["id"],
                    sender=msg_obj["sender"],
                    message=msg_obj["message"]
                ))
                delivered_msgs.append(msg_obj)
                remove_indices.append(idx)
                max_messages -= 1
        
        # Remove delivered messages from undelivered list
        for idx in sorted(remove_indices, reverse=True):
            del undelivered_msgs[idx]
        
        self.save_database()
        
        return chat_pb2.MessagesResponse(messages=to_deliver)
    
    def GetDeliveredMessages(self, request, context):
        """Retrieve delivered messages for a user"""
        username = request.username
        max_messages = request.max_messages
        
        delivered_msgs = self.messages["delivered"]
        
        if len(delivered_msgs) == 0 and max_messages > 0:
            return chat_pb2.MessagesResponse(
                error_message="No delivered messages"
            )
        
        to_deliver = []
        count = 0
        
        # Find messages to deliver
        for msg_obj in delivered_msgs:
            if count >= max_messages:
                break
                
            if msg_obj["receiver"] == username:
                to_deliver.append(chat_pb2.Message(
                    id=msg_obj["id"],
                    sender=msg_obj["sender"],
                    message=msg_obj["message"]
                ))
                count += 1
        
        return chat_pb2.MessagesResponse(messages=to_deliver)
    
    def DeleteMessages(self, request, context):
        """Delete messages for a user"""
        username = request.username
        msg_ids = set(request.message_ids)
        
        # Filter out messages with matching IDs
        self.messages["delivered"] = [
            msg for msg in self.messages["delivered"]
            if not (msg["id"] in msg_ids and msg["receiver"] == username)
        ]
        
        self.save_database()
        
        # Return updated undelivered count
        return chat_pb2.HomeRefreshResponse(
            undelivered_count=self.get_new_messages_count(username)
        )
    
    def RefreshHome(self, request, context):
        """Refresh home screen with updated unread message count"""
        username = request.username
        return chat_pb2.HomeRefreshResponse(
            undelivered_count=self.get_new_messages_count(username)
        )

def serve():
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServicer(), server)
    
    # Load settings to get host and port
    _, _, settings = database_wrapper.load_database()
    server_addr = f"{settings['host']}:{settings['port']}"
    
    server.add_insecure_port(server_addr)
    server.start()
    print(f"Server started on {server_addr}")
    
    try:
        while True:
            time.sleep(86400)  # Sleep for a day
    except KeyboardInterrupt:
        server.stop(0)
        print("Server stopped")

if __name__ == "__main__":
    serve()